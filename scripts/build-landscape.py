"""Build a source-derived relief/landscape illustration and clean river lines.

Relief display is deliberately separate from the native-30m flood calculation.
No elevation from this rendered basemap is used to classify inundation.
"""
from pathlib import Path
import sys, math, json, io, hashlib, zipfile, concurrent.futures, argparse
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cache',type=Path,default=ROOT/'work/terrain')
parser.add_argument('--deps',type=Path,help='Optional additional Python dependency directory')
args=parser.parse_args()
CACHE=args.cache;CACHE.mkdir(parents=True,exist_ok=True)
if args.deps:sys.path.append(str(args.deps))
import requests, numpy as np, shapefile
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter
from shapely.geometry import shape, box, mapping, Polygon, MultiPolygon, LineString
from shapely.ops import unary_union, linemerge
from rasterio.features import rasterize
from rasterio.transform import from_bounds
D=ROOT/'docs/data'
# The terrain study keeps its original, documented geographic frame independently.
terrain_layout=ROOT/'docs/exploration/terrain-layout.json'
L=json.loads((terrain_layout if terrain_layout.exists() else D/'poster-layout.json').read_text('utf8'));p=L['projection']
FRAME=[120,1030,3880,4340];PW,PH=FRAME[2]-FRAME[0],FRAME[3]-FRAME[1]
WEST=p['lon0']+(FRAME[0]-p['x0'])/p['pxPerLon'];EAST=p['lon0']+(FRAME[2]-p['x0'])/p['pxPerLon']
NORTH=p['lat0']-(FRAME[1]-p['y0'])/p['pxPerLat'];SOUTH=p['lat0']-(FRAME[3]-p['y0'])/p['pxPerLat']
BBOX=[WEST,SOUTH,EAST,NORTH];TRANS=from_bounds(*BBOX,PW,PH)
def sha(b):return hashlib.sha256(b).hexdigest()
def download(url,path):
    if not path.exists():
        r=requests.get(url,timeout=90);r.raise_for_status();path.write_bytes(r.content)
    return path.read_bytes()

# HydroRIVERS: modelled river centerlines without reservoir polygons.
hydro_url='https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_eu_shp.zip'
archive=download(hydro_url,CACHE/'HydroRIVERS_v10_eu_shp.zip');z=zipfile.ZipFile(io.BytesIO(archive))
names=z.namelist(); stem=next(n[:-4] for n in names if n.endswith('.shp'))
reader=shapefile.Reader(shp=io.BytesIO(z.read(stem+'.shp')),shx=io.BytesIO(z.read(stem+'.shx')),dbf=io.BytesIO(z.read(stem+'.dbf')))
fields=[f[0] for f in reader.fields[1:]];features=[];frame=box(*BBOX)
for sr in reader.iterShapeRecords(bbox=[41.9,28,50,34]):
    a=dict(zip(fields,sr.record));up=float(a['UPLAND_SKM']);flow=float(a['DIS_AV_CMS'])
    if up<4000 or flow<6:continue
    g=shape(sr.shape.__geo_interface__).intersection(frame)
    if g.is_empty:continue
    features.append({'type':'Feature','properties':{**{k:a[k] for k in ['HYRIV_ID','NEXT_DOWN','UPLAND_SKM','ORD_STRA','DIS_AV_CMS']},'source':'HydroRIVERS v1.0 Europe/Middle East','kind':'river centerline; modern-reference course, no reservoir outline'},'geometry':mapping(g)})
(D/'rivers-display.geojson').write_text(json.dumps({'type':'FeatureCollection','source':hydro_url,'features':features},separators=(',',':')),'utf8')
print('River centerlines:',len(features),flush=True)

# RESOLVE 2017 ecological regions: full returned geometries, no generalization.
eco_url='https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/Resolve_Ecoregions/FeatureServer/0/query'
eco_path=CACHE/'ecoregions-source.json'
if not eco_path.exists():
    params={'f':'json','where':'1=1','geometry':','.join(map(str,BBOX)),'geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'*','returnGeometry':'true','outSR':4326}
    r=requests.get(eco_url,params=params,timeout=90);r.raise_for_status();eco_path.write_bytes(r.content)
raw=json.loads(eco_path.read_bytes());ecof=[]
for f in raw['features']:
    rings=f['geometry']['rings'];outside=[];holes=[]
    for ring in rings:
        polygon=Polygon(ring)
        # ArcGIS exterior rings are clockwise; hole rings counter-clockwise.
        (holes if polygon.exterior.is_ccw else outside).append(polygon)
    geom=unary_union(outside)
    if holes:geom=geom.difference(unary_union(holes))
    geom=geom.intersection(frame)
    ecof.append({'type':'Feature','properties':f['attributes'],'geometry':mapping(geom)})
(D/'ecoregions.geojson').write_text(json.dumps({'type':'FeatureCollection','source':eco_url,'license':'CC BY 4.0','features':ecof},separators=(',',':')),'utf8')

# Terrain Tiles Terrarium at z=9 (~260 m ground cells at 31 degrees latitude).
ZOOM=9;N=2**ZOOM
def tx(lon):return (lon+180)/360*N
def ty(lat):return (1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*N
xmin,xmax=math.floor(tx(WEST)),math.floor(tx(EAST));ymin,ymax=math.floor(ty(NORTH)),math.floor(ty(SOUTH))
tiles=[(x,y) for x in range(xmin,xmax+1) for y in range(ymin,ymax+1)]
tilecache=CACHE/'terrarium';tilecache.mkdir(exist_ok=True)
def get_tile(t):
    x,y=t;url=f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{ZOOM}/{x}/{y}.png'
    fn=tilecache/f'{ZOOM}-{x}-{y}.png';b=download(url,fn)
    rgb=np.array(Image.open(io.BytesIO(b)).convert('RGB'),dtype=np.float32)
    return x,y,rgb[:,:,0]*256+rgb[:,:,1]+rgb[:,:,2]/256-32768,{'url':url,'sha256':sha(b),'bytes':len(b)}
montage=np.zeros(((ymax-ymin+1)*256,(xmax-xmin+1)*256),np.float32);tilemanifest=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    for i,(x,y,elev,meta) in enumerate(pool.map(get_tile,tiles),1):
        montage[(y-ymin)*256:(y-ymin+1)*256,(x-xmin)*256:(x-xmin+1)*256]=elev;tilemanifest.append(meta)
        if i%24==0:print('Terrain tiles',i,'/',len(tiles),flush=True)
lons=np.linspace(WEST+(EAST-WEST)/PW/2,EAST-(EAST-WEST)/PW/2,PW,dtype=np.float32)
lats=np.linspace(NORTH-(NORTH-SOUTH)/PH/2,SOUTH+(NORTH-SOUTH)/PH/2,PH,dtype=np.float32)
xx=(lons+180)/360*N*256-xmin*256-.5
yy=(1-np.arcsinh(np.tan(np.radians(lats)))/np.pi)/2*N*256-ymin*256-.5
elev=map_coordinates(montage,np.array(np.broadcast_arrays(yy[:,None],xx[None,:])),order=1,mode='nearest')
np.savez_compressed(CACHE/'display-elevation.npz',elevation=elev,bbox=BBOX)
land_shapes=[]
for f in json.loads((D/'coastline.geojson').read_text())['features']:
    if f['properties']['level']==1:land_shapes.append((f['geometry'],1))
land=rasterize(land_shapes,out_shape=(PH,PW),transform=TRANS,dtype='uint8')>0
eco_index=rasterize([(f['geometry'],int(f['properties']['ECO_ID'])) for f in ecof],out_shape=(PH,PW),transform=TRANS,dtype='uint16')

# The interfluve is a cartographic landform wash bounded by actual river lines.
# It is not an archaeological vegetation reconstruction or a wetland boundary.
# At each latitude use the main western/eastern perennial routes as envelopes.
mainpaths=[shape(f['geometry']) for f in features if f['properties']['UPLAND_SKM']>85000]
xs_by_y=[]
for lat in lats:
    if not 30.8<=lat<=33.5:xs_by_y.append((float('nan'),float('nan')));continue
    section=LineString([(43,lat),(48,lat)]);vals=[]
    for g in mainpaths:
        q=g.intersection(section)
        if q.geom_type=='Point':vals.append(q.x)
        elif q.geom_type=='MultiPoint':vals.extend(a.x for a in q.geoms)
    vals=[v for v in vals if v<47.25]
    xs_by_y.append((min(vals),max(vals)) if len(vals)>=2 else (float('nan'),float('nan')))
bounds=np.array(xs_by_y,dtype=np.float32)
good=np.isfinite(bounds[:,0]);row=np.arange(PH)
for i in [0,1]:bounds[:,i]=np.interp(row,row[good],bounds[good,i])
between=(lons[None,:]>=bounds[:,0,None])&(lons[None,:]<=bounds[:,1,None])&(lats[:,None]<=33.5)&(lats[:,None]>=30.8)&(elev<100)
taper=np.clip((lats-30.8)/.35,0,1)*np.clip((33.5-lats)/.35,0,1)
floodplain=gaussian_filter(between.astype(np.float32)*taper[:,None],sigma=27)*land
marsh=(eco_index==747).astype(np.float32);marsh=gaussian_filter(marsh,14)*land

# Neutral desert ochre; green alluvium; darker marshes; elevation-driven Zagros relief.
rgb=np.empty((PH,PW,3),np.float32);rgb[:]=[237,224,198]
green=np.array([204,219,183]);wet=np.array([171,200,171]);water=np.array([214,231,225])
rgb=rgb*(1-floodplain[:,:,None]*.78)+green*floodplain[:,:,None]*.78
rgb=rgb*(1-marsh[:,:,None]*.70)+wet*marsh[:,:,None]*.70
high=np.clip((elev-170)/1500,0,1)*land
mount=np.array([205,199,175]);rgb=rgb*(1-high[:,:,None]*.65)+mount*high[:,:,None]*.65
# Multidirectional hillshade, 2.5x display-only exaggeration. Flood uses no exaggeration.
sm=gaussian_filter(elev,.65)
dy,dx=np.gradient(sm,((NORTH-SOUTH)*111320/PH),((EAST-WEST)*111320*math.cos(math.radians(31))/PW))
slope=np.arctan(np.hypot(dx,dy)*2.5);aspect=np.arctan2(-dx,dy)
shade=np.zeros_like(elev)
for az,weight in [(315,.65),(45,.35)]:
    shade+=weight*(np.cos(slope)*math.sin(math.radians(45))+np.sin(slope)*math.cos(math.radians(45))*np.cos(math.radians(az)-aspect))
relief=(shade-.7071)*40*np.clip((elev-50)/500,0,1)
rgb+=relief[:,:,None]
rgb[~land]=water
result=Image.fromarray(np.clip(rgb,0,255).astype(np.uint8),'RGB')
result.save(D/'landscape-base.png',optimize=True)
manifest={'created':'2026-10-18','bbox':BBOX,'posterFrame':FRAME,'rasterPixels':[PW,PH],
 'terrain':{'dataset':'Mapzen / Tilezen Terrain Tiles','registry':'https://registry.opendata.aws/terrain-tiles/','docs':'https://github.com/tilezen/joerd/blob/master/docs/formats.md','attribution':'https://github.com/tilezen/joerd/blob/master/docs/attribution.md','zoom':ZOOM,'nominalGroundSpacingAt31DegreesMetres':40075016.686*math.cos(math.radians(31))/(256*N),'displayOnly':True,'usedForFloodClassification':False,'hillshadeVerticalExaggeration':2.5,'tiles':tilemanifest},
 'ecoregions':{'dataset':'RESOLVE Ecoregions 2017 / Dinerstein et al. 2017','url':eco_url,'license':'CC BY 4.0','rawResponseSHA256':sha(eco_path.read_bytes()),'marshId':747,'interpretation':'Regional potential landscape, not a dated vegetation reconstruction. Interfluve green wash is computed from main-river envelopes and terrain below 100m; it does not assert permanent marsh across the whole interfluve.'},
 'rivers':{'dataset':'HydroRIVERS v1.0 Europe/Middle East','url':hydro_url,'archiveSHA256':sha(archive),'features':len(features),'selection':'Catchment >=4000km², modeled mean flow >=6m³/s; centerlines only; no reservoir/lake polygons. No coordinate simplification applied.'},
 'outputs':{n:sha((D/n).read_bytes()) for n in ['landscape-base.png','rivers-display.geojson','ecoregions.geojson']}}
(D/'landscape-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n','utf8')
print('Landscape complete',PW,PH,'terrain tiles',len(tiles),flush=True)
