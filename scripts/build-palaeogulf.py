"""Trace the explicitly suggested Gulf in Forti et al. (2022), Figure 14.

This is a cartographic adaptation of a published reconstruction, not a DEM
threshold, a surveyed coastline, or a precise boundary for all ancient periods.
The retained source figure is CC BY 4.0. Requires numpy, scipy and Pillow.
"""
from pathlib import Path
import hashlib, json
import numpy as np
from PIL import Image
from scipy.ndimage import label, binary_fill_holes

ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'docs/data'
source=D/'sources/forti-2022-figure14.jpg'
rgb=np.asarray(Image.open(source).convert('RGB'),dtype=np.int16)
r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
water=(b>195)&(g>170)&(r>95)&(g-r>18)&(b-g>8)
# The frame itself is not a shore. Keep the source drawing's interior only.
domain=np.zeros(water.shape,bool); domain[17:607,16:858]=True
components,n=label(water&domain)
counts=np.bincount(components.ravel()); counts[0]=0
sea=binary_fill_holes(components==counts.argmax())&domain
assert 80000<sea.sum()<200000
# Exact pixel-edge polygonization; no invented small-scale shore detail.
edges={}
for y,x in np.argwhere(sea):
    for outside,a,z in [
        (y==0 or not sea[y-1,x],(x,y),(x+1,y)),
        (x==sea.shape[1]-1 or not sea[y,x+1],(x+1,y),(x+1,y+1)),
        (y==sea.shape[0]-1 or not sea[y+1,x],(x+1,y+1),(x,y+1)),
        (x==0 or not sea[y,x-1],(x,y+1),(x,y)),
    ]:
        if outside:
            assert a not in edges, 'Ambiguous diagonal boundary'
            edges[a]=z
start=min(edges); pixel_ring=[start]; cursor=start
while True:
    cursor=edges[cursor];pixel_ring.append(cursor)
    if cursor==start:break
    assert len(pixel_ring)<=len(edges)+1
assert len(pixel_ring)==len(edges)+1

# Two labelled graticules per axis in the original 875 x 623 figure.
# Their affine geographic calibration is independently checked on Ur / Uruk.
def geo(p):
    x,y=p
    return [46.5+(float(x)-310)*1.5/316,31.9-(float(y)-143)*1.1/232]
ring=[geo(p) for p in pixel_ring]
# Separate the real drawn boundary from the figure's right/bottom crop edges.
segments=[]; current=[]
for a,z in zip(pixel_ring[:-1],pixel_ring[1:]):
    crop=(min(a[0],z[0])>=855 or min(a[1],z[1])>=605)
    if not crop:
        if not current:current=[geo(a)]
        current.append(geo(z))
    elif current:
        segments.append(current);current=[]
if current:segments.append(current)
properties={
 'source':'Forti et al. (2022), Quaternary Research 110, 165–183, Figure 14',
 'doi':'https://doi.org/10.1017/qua.2022.22',
 'periodAsPublished':'5000–4000 years ago',
 'claim':'Suggested position of the Persian Gulf coastline',
 'precision':'Approximate cartographic reconstruction; source pixels about 450–530 m. Not a surveyed or universally accepted shoreline.',
 'license':'CC BY 4.0; adapted from the source figure; original copyright University of Washington, 2022',
}
fc={'type':'FeatureCollection','features':[
 {'type':'Feature','properties':dict(properties,role='suggested-water-area'),'geometry':{'type':'Polygon','coordinates':[ring]}},
 {'type':'Feature','properties':dict(properties,role='suggested-shore'),'geometry':{'type':'MultiLineString','coordinates':segments}},
]}
target=D/'palaeogulf.geojson';target.write_text(json.dumps(fc,separators=(',',':'))+'\n','utf8')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
checks=[]
cities={c['id']:c for c in json.loads((D/'cities.json').read_text('utf8'))}
for name,pixel in [('ur',[227,342]),('uruk',[128,264])]:
    actual=cities[name]['coordinates'];estimated=geo(pixel)
    error=((actual[0]-estimated[0])**2+(actual[1]-estimated[1])**2)**.5
    assert error<.012
    checks.append({'city':name,'sourcePixel':pixel,'estimatedCoordinates':estimated,'siteCoordinates':actual,'angularResidualDegrees':error})
manifest={
 'source':properties,
 'articleURL':'https://www.cambridge.org/core/journals/quaternary-research/article/paleoenvironment-and-depositional-context-of-the-sumerian-site-of-abu-tbeirah-nasiriyah-southern-mesopotamia-iraq/FE5F0F666EEF1BEC71C3C5AC58999322',
 'officialRepositoryURL':'https://iris.cnr.it/handle/20.500.14243/441568',
 'retrievedPDFMirror':'https://www.ancientportsantiques.com/wp-content/uploads/Documents/PLACES/IndOc-Gulf/AbuTbeirah-Forti2022.pdf',
 'sourceFigure':{'file':str(source.relative_to(D)).replace('\\','/'),'pixels':[875,623],'sha256':sha(source)},
 'graticuleControl':{'longitude':[[310,46.5],[626,48]],'latitude':[[143,31.9],[375,30.8]]},
 'independentSiteChecks':checks,
 'method':'Largest connected cyan region in the retained source figure; internal text holes filled. Exact pixel-edge tracing, affine graticule registration, with crop edges excluded from the shoreline. No shoreline was moved to meet archaeological sites.',
 'limits':'One published suggested configuration, not an ancient DEM or a dated coastline for every deity tradition. It does not make Girsu or Nigin open-sea ports. Deltaic freshwater/brackish marshes extended beyond the marine Gulf. Modern rivers and GSHHG coast remain reference layers. The +4 m EGM2008 scenario is retained separately and is not this reconstruction.',
 'output':{'file':target.name,'sha256':sha(target),'boundaryVertices':len(ring)},
}
(D/'palaeogulf-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n','utf8')
print('Published suggested Gulf traced:',len(ring),'vertices; graticule checks passed.')
