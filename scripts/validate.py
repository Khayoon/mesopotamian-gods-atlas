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
# Callouts remain in their columns, with a gap between successive text blocks.
for side in ['left','right']:
    labels=sorted([x for x in q['labels'] if x['side']==side],key=lambda a:a['y'])
    for a,b in zip(labels[:-1],labels[1:]):assert a['actualBottom']+8<=b['y'],(a['cityId'],b['cityId'])
for g in q['geographicLabels']:assert g['leaderCollisions']==0
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
paths=q['leaders']
for i,path in enumerate(paths):
    for j,other in enumerate(paths[i+1:],i+1):
        for a,b in zip(path[:-1],path[1:]):
            for c,d in zip(other[:-1],other[1:]):
                assert not (cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0),('Leader crossing',q['labels'][i]['cityId'],q['labels'][j]['cityId'])
for source in l['sources']:assert str(source['number']) in re.findall(r'\d+', ' '.join(x['note'] for x in l['labels']))
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
assert 'data-level-metres="4"' in svg and 'not a dated ancient' in svg
stats={'deityRecords':len(r),'originClaims':sum(len(g['originTraditions']) for g in r),
 'mappedIdentities':len({i for x in l['labels'] for i in x['deityIds']}),'cityLabels':len(l['labels']),
 'pngPixels':[4000,5000],'pngSHA256':hashlib.sha256((ROOT/'docs/mesopotamian-gods.png').read_bytes()).hexdigest(),
 'riverCenterlineFeatures':len(river['features']),
 'floodScenario':{'levelMetresEGM2008':4,'nativeCells':flood['verification']['native_raster_dimensions'],'polygonFeatures':flood['scenarios']['4']['polygon_features'],'classification':'modern terrain; not a dated ancient shoreline'},
 'checks':'data references, required evidence metadata, deliberate null coordinates, raster dimensions, callout separation, zero leader crossings, geographic name / leader separation, width bounds, terrain/flood file hashes, river line geometry, explicit scenario annotation'}
(ROOT/'verification.json').write_text(json.dumps(stats,indent=2)+'\n','utf8')
print(json.dumps(stats,indent=2))
