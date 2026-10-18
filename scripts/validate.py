"""Bounded content, geography, and layout integrity checks for this poster."""
import json, re, hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'docs/data'
r=json.loads((D/'research.json').read_text('utf8'))['deities']
c=json.loads((D/'cities.json').read_text('utf8')); ids={x['id'] for x in r};cities={x['id']:x for x in c}
l=json.loads((D/'poster-layout.json').read_text('utf8'))
assert len(ids)==len(r)==90
for g in r:
    for field in ['originTraditions','cityEvidence']:
        for e in g[field]:
            assert all(e.get(k) for k in ['summary','work','passage','url','period']),(g['id'],e)
            assert e['url'].startswith('https://'),e['url']
            if e.get('cityId'):assert e['cityId'] in cities
    assert all(cid in cities for cid in g['cityIds'])
for row in l['labels']:
    assert cities[row['cityId']]['coordinates']
    assert all(i in ids for i in row['deityIds'])
for cid in ['eresh','kesh','karkara','kuara','agade','dilmun']:
    assert cities[cid]['coordinates'] is None
assert Image.open(ROOT/'docs/mesopotamian-gods.png').size==(4000,5000)
q=json.loads((ROOT/'layout-verification.json').read_text('utf8'))
# Free-positioned callouts, sampled quadratic curves and fixed geographic pins.
blocks=q['calloutBoxes'];paths=q['leaders']
assert len(blocks)==22 and len({i for row in l['labels'] for i in row['deityIds']})==41
def overlap(a,b,pad=16):
    return min(a[2],b[2])-max(a[0],b[0])>-pad and min(a[3],b[3])-max(a[1],b[1])>-pad
def inside(p,r,pad=6):return r[0]-pad<p[0]<r[2]+pad and r[1]-pad<p[1]<r[3]+pad
for i,a in enumerate(blocks):
    for b in blocks[i+1:]:assert not overlap(a['box'],b['box']),('Callout overlap',a['cityId'],b['cityId'])
for path in paths:
    for block in blocks:
        assert not any(inside(p,block['box']) for p in path['points']),('Leader through caption',path['cityId'],block['cityId'])
    lon,lat=cities[path['cityId']]['coordinates'];p=l['projection']
    import math
    merc=lambda a:math.log(math.tan(math.pi/4+math.radians(a)/2))
    expected=[p['x0']+p['scale']*math.radians(lon-p['lon0']),p['y0']+p['scale']*(merc(p['lat0'])-merc(lat))]
    assert all(abs(a-b)<1e-7 for a,b in zip(expected,path['points'][0])),path['cityId']
for g in q['geographicLabels']:
    assert not any(overlap(g['box'],b['box']) for b in blocks),g['text']
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
for i,path in enumerate(paths):
    for j,other in enumerate(paths[i+1:],i+1):
        for a,b in zip(path['points'][:-1],path['points'][1:]):
            for c,d in zip(other['points'][:-1],other['points'][1:]):
                assert not (cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0),('Leader crossing',q['labels'][i]['cityId'],q['labels'][j]['cityId'])
for source in l['sources']:assert source['number'] in {n for x in l['labels'] for n in x['refs']}
assert all(x['box'][2]<3900 for x in q['textBoxes']), 'Text exceeds page width'
# Verify distributed terrain/flood assets against their recorded source-derived outputs.
terrain=json.loads((D/'landscape-manifest.json').read_text('utf8'))
flood=json.loads((D/'flood-manifest.json').read_text('utf8'))
for name,digest in terrain['outputs'].items():
    assert hashlib.sha256((D/name).read_bytes()).hexdigest()==digest,('Terrain hash',name)
for asset in [*flood['scenarios'].values(),flood['native_mask']]:
    data=(D/asset['file']).read_bytes()
    assert len(data)==asset['bytes'] and hashlib.sha256(data).hexdigest()==asset['sha256'],asset['file']
river=json.loads((D/'rivers-display.geojson').read_text('utf8'))
assert len(river['features'])==terrain['rivers']['features']
assert all(f['geometry']['type'] in ['LineString','MultiLineString'] for f in river['features'])
svg=(ROOT/'docs/mesopotamian-gods.svg').read_text('utf8')
assert 'flood-overlay' not in svg and 'labelwash' not in svg and '<image' not in svg
assert svg.count('data-curve="quadratic"')==22
assert 'flood-overlay' in (ROOT/'docs/exploration/terrain-study.svg').read_text('utf8')
stats={'deityRecords':len(r),'originClaims':sum(len(g['originTraditions']) for g in r),
 'mappedIdentities':len({i for x in l['labels'] for i in x['deityIds']}),'cityLabels':len(l['labels']),
 'pngPixels':[4000,5000],'pngSHA256':hashlib.sha256((ROOT/'docs/mesopotamian-gods.png').read_bytes()).hexdigest(),
 'riverCenterlineFeatures':len(river['features']),
 'floodScenario':{'levelMetresEGM2008':4,'nativeCells':flood['verification']['native_raster_dimensions'],'polygonFeatures':flood['scenarios']['4']['polygon_features'],'classification':'modern terrain; not a dated ancient shoreline'},
 'defaultPoster':'quiet geography; individual curved leaders; terrain and flood study separate',
 'checks':'data references, required evidence metadata, deliberate null coordinates, raster dimensions, callout separation, no leaders through captions, zero leader crossings, fixed geographic pin coordinates, geographic name separation, width bounds, retained terrain/flood file hashes, river line geometry, separate optional exploration'}
(ROOT/'verification.json').write_text(json.dumps(stats,indent=2)+'\n','utf8')
print(json.dumps(stats,indent=2))
