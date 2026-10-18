"""Extract original, unsimplified GSHHG 2.3.7 geography for the atlas.

Requires shapely. Use --archive PATH to reuse a previously downloaded official
archive; otherwise download the official release. No simplification is applied.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import urllib.request
import zipfile

try:
    from shapely.geometry import Polygon, LineString, box, mapping
    from shapely import make_valid
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "work/geo/pydeps"))
    from shapely.geometry import Polygon, LineString, box, mapping
    from shapely import make_valid

ROOT = Path(__file__).resolve().parents[1]
URL = "https://github.com/GenericMappingTools/gshhg-gmt/releases/download/2.3.7/gshhg-bin-2.3.7.zip"
BBOX = [40.0, 25.0, 52.0, 35.0]
FRAME = box(*BBOX)
CLASSES = {0:"river lake",1:"permanent major river",2:"additional major river",3:"additional river",4:"minor river",6:"intermittent major river",7:"intermittent additional river",8:"intermittent minor river",10:"major canal",11:"canal",12:"irrigation canal"}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def vertices(geom):
    if geom.is_empty: return 0
    if geom.geom_type == "Polygon":
        return len(geom.exterior.coords) + sum(len(r.coords) for r in geom.interiors)
    if hasattr(geom, "geoms"):
        return sum(vertices(g) for g in geom.geoms)
    return len(geom.coords)

def records(data):
    offset=0
    while offset < len(data):
        h=struct.unpack_from(">11i", data, offset)
        offset += 44
        n=h[1]
        if n < 0 or offset + 8*n > len(data): raise ValueError("Invalid GSHHG record")
        if h[4]/1e6 >= BBOX[0] and h[3]/1e6 <= BBOX[2] and h[6]/1e6 >= BBOX[1] and h[5]/1e6 <= BBOX[3]:
            coords=[]
            for x,y in struct.iter_unpack(">2i", memoryview(data)[offset:offset+8*n]):
                lon=x/1e6
                # The Eurasia ring crosses Greenwich, but its Chukotka coast
                # extends east of 180. Shift only its western, 270–360 branch.
                if ((h[2] >> 16) & 1) and lon > 270: lon -= 360
                coords.append((lon,y/1e6))
            yield h,coords
        offset += 8*n

def extract(data, polygon):
    features=[]
    source_count=inside_count=repairs=0
    for h,coords in records(data):
        level=h[2]&255
        if polygon and level > 4: continue
        geom=Polygon(coords) if polygon else LineString(coords)
        if not geom.is_valid:
            geom=make_valid(geom)
            repairs+=1
        clipped=geom.intersection(FRAME)
        if clipped.is_empty: continue
        source_count += len(coords)
        inside_count += sum(BBOX[0] <= x <= BBOX[2] and BBOX[1] <= y <= BBOX[3] for x,y in coords)
        properties={"gshhg_id":h[0],"level":level,"source":"GSHHG 2.3.7 / " + ("GSHHS" if polygon else "WDBII"),"resolution":"full (f)","epoch":"modern reference geography; not an ancient reconstruction","source_vertices":len(coords),"clipped_vertices":vertices(clipped)}
        if polygon:
            properties.update(kind={1:"land",2:"lake or river-lake",3:"island in lake",4:"pond in island"}[level],container_id=h[9],river_lake=bool((h[2]>>25)&1))
        else:
            properties.update(kind=CLASSES.get(level,"river class "+str(level)))
        features.append({"type":"Feature","properties":properties,"geometry":mapping(clipped)})
    return features, {"features":len(features),"source_vertices_in_selected_records":source_count,"original_vertices_inside_frame":inside_count,"output_vertices":sum(f['properties']['clipped_vertices'] for f in features),"invalid_input_geometries_repaired":repairs}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--cache",type=Path,default=ROOT/"../../work/geo")
    args=parser.parse_args()
    args.cache.mkdir(parents=True,exist_ok=True)
    archive=args.archive or args.cache/"gshhg-bin-2.3.7.zip"
    if not archive.exists(): urllib.request.urlretrieve(URL,archive)
    archive_bytes=archive.read_bytes()
    z=zipfile.ZipFile(archive)
    out=ROOT/"docs/data"
    out.mkdir(parents=True,exist_ok=True)
    stats={"bbox_west_south_east_north":BBOX,"crs":"WGS 84 longitude/latitude, EPSG:4326","archive_url":URL,"archive_bytes":len(archive_bytes),"archive_sha256":sha(archive_bytes),"simplification":"none; polygon/line intersection with bounding rectangle only","files":{}}
    for member,output,polygon in [("gshhs_f.b","coastline.geojson",True),("wdb_rivers_f.b","rivers.geojson",False)]:
        raw=z.read(member)
        features,counts=extract(raw,polygon)
        fc={"type":"FeatureCollection","bbox":BBOX,"source":"GSHHG 2.3.7, original full-resolution "+member,"geography_note":"Modern reference geography, not an ancient shoreline or channel reconstruction.","features":features}
        (out/output).write_text(json.dumps(fc,separators=(",",":")),encoding="utf-8")
        stats["files"][output]={"input_member":member,"input_bytes":len(raw),"input_sha256":sha(raw),**counts,"output_sha256":sha((out/output).read_bytes())}
    for member,output in [("LICENSE.TXT","GSHHG-LICENSE.txt"),("COPYING.LESSERv3","GSHHG-COPYING.LESSERv3.txt"),("README.TXT","GSHHG-README.txt")]:
        (out/output).write_bytes(z.read(member))
    (out/"geography-manifest.json").write_text(json.dumps(stats,indent=2),encoding="utf-8")
    print(json.dumps(stats,indent=2))

if __name__ == "__main__": main()
