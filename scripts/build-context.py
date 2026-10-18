"""Muted geographic context for the portrait poster; no flood reconstruction.

First build-landscape.py caches source elevation. Then run this builder with
--elevation PATH_TO_display-elevation.npz, followed by render-poster.py.
"""
from pathlib import Path
import argparse, hashlib, json, math
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import map_coordinates, gaussian_filter
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/data'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--elevation',type=Path,default=ROOT/'work/terrain/display-elevation.npz')
args=parser.parse_args();L=json.loads((D/'poster-layout.json').read_text('utf8'));P=L['projection']
x1,y1,x2,y2=L['mapFrame'];W,H=x2-x1,y2-y1
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def merc(lat):return math.log(math.tan(math.pi/4+math.radians(lat)/2))
def project(lon,lat):return P['x0']+P['scale']*math.radians(lon-P['lon0'])-x1,P['y0']+P['scale']*(merc(P['lat0'])-merc(lat))-y1
xs=np.arange(W)+x1+.5;ys=np.arange(H)+y1+.5
lons=P['lon0']+np.degrees((xs-P['x0'])/P['scale'])
lats=np.degrees(2*np.arctan(np.exp(merc(P['lat0'])-(ys-P['y0'])/P['scale']))-math.pi/2)
source=np.load(args.elevation);z=source['elevation'];west,south,east,north=source['bbox']
assert lons.min()>=west and lons.max()<=east and lats.min()>=south and lats.max()<=north
xx=(lons-west)/(east-west)*z.shape[1]-.5;yy=(north-lats)/(north-south)*z.shape[0]-.5
elev=map_coordinates(z,np.array(np.broadcast_arrays(yy[:,None],xx[None,:])),order=1,mode='nearest')
def mask(features):
    im=Image.new('L',(W,H),0);draw=ImageDraw.Draw(im)
    for feat in features:
        g=feat['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
        for rings in polys:
            draw.polygon([project(*v[:2]) for v in rings[0]],fill=255)
            for ring in rings[1:]:draw.polygon([project(*v[:2]) for v in ring],fill=0)
    return np.array(im,dtype=np.float32)/255
coast=json.loads((D/'coastline.geojson').read_text('utf8'))['features']
# GSHHG level 1 only: omit inland-lake/reservoir holes as in the poster.
land=mask([dict(f,geometry=dict(f['geometry'],coordinates=[f['geometry']['coordinates'][0]])) if f['geometry']['type']=='Polygon' else f for f in coast if f['properties']['level']==1])
eco=json.loads((D/'ecoregions.geojson').read_text('utf8'))['features']
marsh=gaussian_filter(mask([f for f in eco if f['properties']['ECO_ID']==747]),18)*land
# River-bounded lowland wash; not permanent marsh or a dated vegetation extent.
segments=[]
for f in json.loads((D/'rivers-display.geojson').read_text('utf8'))['features']:
    if f['properties']['UPLAND_SKM']<85000:continue
    g=f['geometry'];paths=g['coordinates'] if g['type']=='MultiLineString' else [g['coordinates']]
    for path in paths:segments.extend((a[0],a[1],b[0],b[1]) for a,b in zip(path[:-1],path[1:]) if a[1]!=b[1])
seg=np.array(segments);bounds=[]
for lat in lats:
    hit=(lat>=np.minimum(seg[:,1],seg[:,3]))&(lat<np.maximum(seg[:,1],seg[:,3]))
    s=seg[hit];values=s[:,0]+(lat-s[:,1])*(s[:,2]-s[:,0])/(s[:,3]-s[:,1]);values=values[values<47.25]
    bounds.append((values.min(),values.max()) if len(values)>1 and 30.7<lat<33.6 else (np.nan,np.nan))
bounds=np.array(bounds);good=np.isfinite(bounds[:,0]);row=np.arange(H)
for i in [0,1]:bounds[:,i]=np.interp(row,row[good],bounds[good,i])
taper=np.clip((lats-30.7)/.35,0,1)*np.clip((33.6-lats)/.35,0,1)
between=(lons[None,:]>=bounds[:,0,None])&(lons[None,:]<=bounds[:,1,None])&(elev<130)
alluvial=gaussian_filter(between.astype(np.float32)*taper[:,None],22)*land
rgb=np.zeros((H,W,3),np.float32);rgb[:]=[235,228,213]
def blend(colour,weight):
    global rgb
    a=weight[:,:,None];rgb=rgb*(1-a)+np.array(colour)*a
blend([224,229,208],alluvial*.85)
blend([204,218,196],marsh*.55)
high=np.clip((elev-150)/1350,0,1)*land
blend([221,220,201],high*.50)
sm=gaussian_filter(elev,.85)
metres_per_pixel=6371008.8*np.cos(np.radians(lats))/P['scale']
dy,dx=np.gradient(sm);dx/=metres_per_pixel[:,None];dy/=metres_per_pixel[:,None]
slope=np.arctan(np.hypot(dx,dy)*2.0);aspect=np.arctan2(-dx,dy)
shade=np.zeros_like(elev)
for az,weight in [(315,.65),(45,.35)]:
    shade+=weight*(np.cos(slope)*math.sin(math.radians(45))+np.sin(slope)*math.cos(math.radians(45))*np.cos(math.radians(az)-aspect))
rgb+=(shade-.7071)[:,:,None]*24*np.clip((elev-100)/500,0,1)[:,:,None]*land[:,:,None]
rgb[land<.5]=[218,232,227]
Image.fromarray(np.clip(rgb,0,255).astype(np.uint8)).save(D/'context-base.png',optimize=True)
manifest={'projection':P,'mapFrame':L['mapFrame'],'pixels':[W,H],
 'sources':{'elevationCacheSHA256':sha(args.elevation),'sourceTerrainManifest':'landscape-manifest.json','sourceTerrainManifestSHA256':sha(D/'landscape-manifest.json'),'coastlineSHA256':sha(D/'coastline.geojson'),'ecoregionsSHA256':sha(D/'ecoregions.geojson'),'riversSHA256':sha(D/'rivers-display.geojson')},
 'method':'Bilinear reprojection of documented Mapzen terrain to the Mercator poster grid. Full-resolution GSHHG land mask. Lowland colour follows major river envelopes; marsh colour follows RESOLVE 2017 region 747. Display-only twofold hillshade exaggeration with restrained contrast.',
 'limits':'Modern-reference relief and broad ecological setting, not dated ancient channels, vegetation, marsh boundaries or shorelines. No flood overlay.',
 'outputSHA256':sha(D/'context-base.png')}
(D/'context-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n','utf8')
print('Muted context built',W,H,flush=True)
