"""Merge evidence without merging distinct deities; import cited site coordinates."""
import csv, json, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/data'
def arr(v):
    return v if isinstance(v,list) else [v] if v else []
merged={}
for filename in ['research-cosmic.json','research-southern.json']:
    for item in json.loads((D/filename).read_text('utf-8-sig')):
        key=item['id']
        if key not in merged:
            merged[key]=item
            for field in ['aliases','domains','notes','originTraditions','cityEvidence','cityIds']:
                merged[key][field]=arr(item.get(field))
            continue
        out=merged[key]
        for field in ['aliases','domains','notes','originTraditions','cityEvidence','cityIds']:
            for value in arr(item.get(field)):
                if value not in out[field]:out[field].append(value)
        if item.get('nameNote') and item['nameNote'] not in out.get('nameNote',''):
            out['nameNote']=(out.get('nameNote','')+' '+item['nameNote']).strip()
for item in merged.values():
    item['cultCityIds']=sorted(set(e['cityId'] for e in item['cityEvidence'] if e.get('cityId')))
    item['originStatus']='documented tradition' if item['originTraditions'] else 'No origin established in the sources checked'
data={
    'title':'The cities of the Mesopotamian gods',
    'scope':'Lower Mesopotamia: Sumerian-language, Akkadian-language and Babylonian traditions. A selected evidence catalogue, not an exhaustive ancient god list.',
    'compiled':'2026-10-18',
    'method':'Birth, creation, conception, childhood, genealogy and cult association are separate claims. Null origin coordinates are deliberate. Documentary attestation is not the date of a deity\u2019s first invention. A city may have many gods and a god many cities.',
    'deities':list(merged.values())}
(D/'research.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
csvpath=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT.parents[1]/'work/research/pleiades/data/gis/places.csv'
rows={r['id']:r for r in csv.DictReader(csvpath.open(encoding='utf-8-sig'))}
selected={
 'sippar':('Sippar','894089'),'sipparamnanum':('Sippar-Amnanum','392373882'),
 'babylon':('Babylon','893951'),'borsippa':('Borsippa','893964'),
 'kutha':('Kutha','893977'),'kish':('Kish','894028'),'dilbat':('Dilbat','893987'),
 'marad':('Marad','912901'),'nippur':('Nippur','912910'),'isin':('Isin','912868'),
 'adab':('Adab','787747618'),'shuruppak':('Shuruppak','326150788'),
 'zabalam':('Zabalam','921099766'),'umma':('Umma','44626252'),
 'uruk':('Uruk','912986'),'larsa':('Larsa','912897'),
 'badtibira':('Bad-tibira','771224406'),'girsu':('Girsu','912855'),
 'lagash':('Lagash','959120263'),'nigin':('Nigin','912909'),
 'ur':('Ur','912985'),'eridu':('Eridu','912845'),'ubaid':('Tell al-Ubaid','339709658'),
 'eshnunna':('Eshnunna','90720956'),'der':('Der','903013')}
cities=[]
for key,(name,pid) in selected.items():
    r=rows[pid]
    cities.append({'id':key,'name':name,'coordinates':[float(r['representative_longitude']),float(r['representative_latitude'])],
      'coordinateSource':r['uri'],'coordinateType':'Pleiades representative site point; not temple or birthplace coordinates',
      'precision':r['location_precision'],'gazetteerTitle':r['title']})
allids={c for v in merged.values() for c in v['cityIds']}
pretty={'eresh':'Eresh','enegi':'Enegi','gimah':'Gi-mah','kesh':'Kesh','karkara':'Karkara','kuara':'Kuara',
 'guabba':'Gu-abba','kiabrig':'Ki-abrig','kinirsha':'Kinirsha','gishbanda':'Gishbanda','agade':'Agade',
 'akkil':'Akkil','murum':'Murum','gaesh':'Gaesh','kazallu':'Kazallu','irikug':'Irikug','sirara':'Sirara',
 'ulmash':'Ulmash','urum':'Urum','dilmun':'Dilmun'}
for key in sorted(allids-set(selected)):
    cities.append({'id':key,'name':pretty.get(key,key.title()),'coordinates':None,
      'coordinateType':'Unlocated, disputed, a sanctuary/district, or a broad region; deliberately not a precise pin',
      'note':{'dilmun':'A changing Gulf region, with Bahrain a major centre; not a single birth coordinate.',
        'kesh':'Tulul al-Baqarat is a proposed identification, not adopted here as certain.',
        'karkara':'Tell Jidr is proposed; no certain point adopted.',
        'eresh':'Identification debated; do not equate automatically with Abu Salabikh.',
        'sirara':'Sanctuary of Nanshe in the Nigin landscape; not a second city.',
        'irikug':'Sacred district in the Girsu landscape; no independent point.'}.get(key,'No sufficiently secure independently verified site point adopted.')})
(D/'cities.json').write_text(json.dumps(cities,ensure_ascii=False,indent=2)+'\n','utf-8')
print(f'{len(merged)} distinct deity records; {sum(len(x["originTraditions"]) for x in merged.values())} origin claims; {len(selected)} cited site anchors')
