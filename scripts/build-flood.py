"""A native-grid, ocean-connected +4 m EGM2008 *modern-terrain scenario*.

This is not a dated ancient shoreline, a local-MSL conversion, or a hydraulic
simulation. Download only selected TIFF members from the official ZIP archives
using validated HTTP byte ranges. No complete continental archive is fetched.

Requirements: numpy, requests, scipy, rasterio. Optional dependency path can be
provided with --deps. Source tiles are retained in --cache (excluded from Git).
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import time
import zlib

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
SOURCE = "https://data.4tu.nl/file/1da2e70f-6c4d-4b03-86bd-b53e789cc629/"
URLS = {
    "Asia.zip": SOURCE + "672eba4c-1334-44c6-8119-8879ded25912",
    "mask_tiles.zip": SOURCE + "bfe0fbc1-fdf3-40d0-a62c-adc58bfd9478",
    "README.md": SOURCE + "71c77b5f-b340-4fdb-a1b1-1d255b8ddb0f",
    "CHANGELOG.md": SOURCE + "b0403ff2-0aa5-4394-9413-2eb851e0fa50",
}
REQUESTED_BBOX = [45.5, 29.0, 49.85, 32.0]
STEP = 1 / 3600


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_range(url, start=None, end=None, suffix=None):
    import requests
    value = f"bytes=-{suffix}" if suffix else f"bytes={start}-{end}"
    for attempt in range(6):
        r = requests.get(url, headers={"Range": value}, timeout=(30, 180), stream=True)
        if r.status_code not in (429,500,502,503,504):
            break
        status=r.status_code
        r.close()
        if attempt==5:
            raise RuntimeError(f"Repeated HTTP {status} for range {value}")
        delay=min(40,2**(attempt+1))
        print(f"HTTP {status}; retry range after {delay}s",flush=True)
        time.sleep(delay)
    if r.status_code != 206:
        r.close()
        raise RuntimeError(f"Refusing non-range response {r.status_code} for {value}")
    body = r.content
    if not r.headers.get("Content-Range", "").startswith("bytes "):
        raise RuntimeError("Missing Content-Range")
    if len(body) != int(r.headers["Content-Length"]):
        raise RuntimeError("Truncated range response")
    if start is not None:
        returned = r.headers["Content-Range"].split(" ")[1].split("/")[0]
        if returned != f"{start}-{end}" or len(body) != end - start + 1:
            raise RuntimeError(f"Incorrect byte range: {r.headers['Content-Range']}")
    return body, dict(r.headers)


def zip_directory(url, cache, name):
    """Read ZIP/ZIP64 central directory, preserving original member offsets."""
    index_path = cache / (name + ".index.json")
    if index_path.exists():
        return json.loads(index_path.read_text())
    tail, headers = fetch_range(url, suffix=65536)
    i = tail.rfind(b"PK\x05\x06")
    if i < 0:
        raise RuntimeError("No ZIP end record")
    end_record = struct.unpack_from("<4s4H2LH", tail, i)
    count, size, offset = end_record[4:7]
    if size == 0xFFFFFFFF or offset == 0xFFFFFFFF:
        j = tail.rfind(b"PK\x06\x06", 0, i)
        if j < 0:
            raise RuntimeError("ZIP64 end record not in tail")
        end64 = struct.unpack_from("<4sQ2H2L4Q", tail, j)
        count, size, offset = end64[-3:]
    raw, _ = fetch_range(url, offset, offset + size - 1)
    members, q = {}, 0
    while q < len(raw):
        fields = struct.unpack_from("<4s6H3L5H2L", raw, q)
        if fields[0] != b"PK\x01\x02":
            raise RuntimeError("Invalid central directory")
        n, extra_n, comment_n = fields[10:13]
        filename = raw[q+46:q+46+n].decode("utf-8")
        extra = raw[q+46+n:q+46+n+extra_n]
        compressed, uncompressed, local_offset = fields[8], fields[9], fields[16]
        p = 0
        while p + 4 <= len(extra):
            tag, length = struct.unpack_from("<HH", extra, p)
            p += 4
            if tag == 1:
                pos = p
                if uncompressed == 0xFFFFFFFF:
                    uncompressed, = struct.unpack_from("<Q", extra, pos)
                    pos += 8
                if compressed == 0xFFFFFFFF:
                    compressed, = struct.unpack_from("<Q", extra, pos)
                    pos += 8
                if local_offset == 0xFFFFFFFF:
                    local_offset, = struct.unpack_from("<Q", extra, pos)
            p += length
        members[filename] = dict(name=filename, method=fields[4], crc32=fields[7],
                                 compressed_bytes=compressed, bytes=uncompressed,
                                 local_header_offset=local_offset)
        q += 46 + n + extra_n + comment_n
    assert len(members) == count
    result = dict(url=url, archive_bytes=int(headers["Content-Range"].split("/")[1]),
                  etag=headers.get("ETag"), last_modified=headers.get("Last-Modified"),
                  central_directory_offset=offset, central_directory_bytes=size,
                  central_directory_sha256=hashlib.sha256(raw).hexdigest(), members=members)
    index_path.write_text(json.dumps(result, indent=2))
    return result


def get_member(index, member, destination):
    """Byte range extraction, including CRC validation of original TIFF bytes."""
    record = dict(index["members"][member])
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        offset = record["local_header_offset"]
        header, _ = fetch_range(index["url"], offset, offset+29)
        if header[:4] != b"PK\x03\x04":
            raise RuntimeError("Bad local header")
        n, extra_n = struct.unpack_from("<HH", header, 26)
        start = offset + 30 + n + extra_n
        compressed, _ = fetch_range(index["url"], start, start+record["compressed_bytes"]-1)
        if record["method"] == 0:
            body = compressed
        elif record["method"] == 8:
            body = zlib.decompress(compressed, -15)
        else:
            raise RuntimeError("Unsupported ZIP compression")
        if len(body) != record["bytes"] or zlib.crc32(body) != record["crc32"]:
            raise RuntimeError("ZIP member CRC/length verification failed")
        temporary = destination.with_suffix(".partial")
        temporary.write_bytes(body)
        temporary.replace(destination)
        print(f"Downloaded {member}: {len(body):,} bytes", flush=True)
    body_crc = 0
    with destination.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            body_crc = zlib.crc32(chunk, body_crc)
    if destination.stat().st_size != record["bytes"] or body_crc != record["crc32"]:
        raise RuntimeError(f"Cached member verification failed: {destination}")
    return {**record, "sha256":sha_file(destination), "archive_url":index["url"],
            "cache_filename":destination.name}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=WORK/"terrain/deltadtm")
    parser.add_argument("--deps", type=Path, default=WORK/"geo/pydeps")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    # The system NumPy is compatible with the installed scipy; add geospatial
    # wheel directory only after loading it (that directory has another NumPy).
    import numpy as np
    sys.path.insert(0, str(args.deps))
    import requests
    import rasterio
    from rasterio.features import rasterize, shapes
    from rasterio.transform import from_origin
    from rasterio.windows import Window
    from scipy.ndimage import binary_propagation, generate_binary_structure
    from pyproj import Geod
    from shapely.geometry import shape

    cache, out = args.cache, ROOT/"docs/data"
    cache.mkdir(parents=True, exist_ok=True)
    for filename in ("README.md", "CHANGELOG.md"):
        path = cache / filename
        if not path.exists():
            r = requests.get(URLS[filename], timeout=60)
            r.raise_for_status()
            path.write_bytes(r.content)
    dtm_index = zip_directory(URLS["Asia.zip"], cache, "Asia")
    mask_index = zip_directory(URLS["mask_tiles.zip"], cache, "masks")
    names = [f"DeltaDTM_v1_1_N{lat:02d}E{lon:03d}.tif"
             for lat in (29,30,31) for lon in (45,46,47,48,49)]
    records = []
    def download(name):
        if name not in dtm_index["members"]:
            return {"name":name,"available":False}
        rec = get_member(dtm_index, name, cache/name)
        mask_name = "masks/"+name
        if mask_name in mask_index["members"]:
            rec["source_water_mask"] = get_member(mask_index, mask_name, cache/mask_name)
        return rec
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        records = list(executor.map(download, names))

    # Derive the native cell lattice from a real TIFF, never filename assumptions.
    with rasterio.open(cache/"DeltaDTM_v1_1_N30E047.tif") as src:
        anchor_x, anchor_y = src.transform.c, src.transform.f
        assert abs(src.transform.a-STEP) < 1e-12
        assert abs(src.transform.e+STEP) < 1e-12
    west = anchor_x + round((REQUESTED_BBOX[0]-anchor_x)/STEP)*STEP
    north = anchor_y + round((REQUESTED_BBOX[3]-anchor_y)/STEP)*STEP
    width = round((REQUESTED_BBOX[2]-REQUESTED_BBOX[0])/STEP)
    height = round((REQUESTED_BBOX[3]-REQUESTED_BBOX[1])/STEP)
    transform = from_origin(west,north,STEP,STEP)
    bbox = [west,north-height*STEP,west+width*STEP,north]
    print("Native grid:",width,height,bbox,flush=True)
    # Codes in this temporary native classification: 3=<=3m, 4=(3,4],
    # 5=(4,5], 6=>5m, 255=unavailable/clipped; never treat nodata as zero.
    classes = np.memmap(cache/"native-threshold-classes.bin",dtype="uint8",mode="w+",shape=(height,width))
    classes[:] = 255
    for rec in records:
        if rec.get("available") is False:
            continue
        with rasterio.open(cache/rec["name"]) as src:
            assert src.width == src.height == 3600
            assert abs(src.transform.a-STEP)<1e-12 and abs(src.transform.e+STEP)<1e-12
            col = round((src.transform.c-west)/STEP)
            row = round((north-src.transform.f)/STEP)
            assert abs(src.transform.c-(west+col*STEP))<1e-8
            assert abs(src.transform.f-(north-row*STEP))<1e-8
            left,top,right,bottom = max(0,col),max(0,row),min(width,col+src.width),min(height,row+src.height)
            rec.update(bounds=list(src.bounds),transform=list(src.transform)[:6],
                       crs_wkt=src.crs.to_wkt(),nodata=src.nodata,width=src.width,height=src.height,
                       tags=src.tags(),mask_counts={})
            if right<=left or bottom<=top:
                continue
            a=src.read(1,window=Window(left-col,top-row,right-left,bottom-top))
            valid=np.isfinite(a)&(a!=src.nodata)
            c=np.full(a.shape,255,dtype="uint8")
            c[valid]=6
            for level in (5,4,3): c[valid&(a<=level)]=level
            classes[top:bottom,left:right]=c
        if "source_water_mask" in rec:
            with rasterio.open(cache/"masks"/rec["name"]) as source_mask:
                values,counts=np.unique(source_mask.read(1),return_counts=True)
                rec["mask_counts"]={str(v):int(n) for v,n in zip(values,counts)}
    classes.flush()
    coast_path=out/"coastline.geojson"
    coast=json.loads(coast_path.read_text())
    # Only level 1 land/islands: inland lakes remain filled land. None can seed
    # the ocean or connect below-threshold basins artificially.
    land_geoms=[f["geometry"] for f in coast["features"] if f["properties"]["level"]==1]
    land=rasterize(((g,1) for g in land_geoms),out_shape=(height,width),transform=transform,
                   fill=0,all_touched=False,dtype="uint8")
    sea=land==0
    valid_land=(classes!=255)&(land==1)
    unknown_land=int(np.count_nonzero((classes==255)&(land==1)))
    native_path=out/"flood-4m-native.tif"
    geod=Geod(ellps="WGS84")
    row_areas=np.array([abs(geod.polygon_area_perimeter(
        [west,west+STEP,west+STEP,west],
        [north-row*STEP,north-row*STEP,north-(row+1)*STEP,north-(row+1)*STEP])[0])
        for row in range(height)],dtype="float64")
    manifest=dict(
        title="Ocean-connected +4 m EGM2008 modern-terrain scenario",
        dataset_version=dict(repository_version=4,repository_label="DeltaDTM v1.1",actual_processing_version="1.1.1",
            correction_date="2024-12-10",correction="Reprocessed after ICESat-2 processing errors in the previous release caused large inland depressions.",
            changelog_url=URLS["CHANGELOG.md"],changelog_sha256=sha_file(cache/"CHANGELOG.md"),
            readme_url=URLS["README.md"],readme_sha256=sha_file(cache/"README.md")),
        generated_at=datetime.now(timezone.utc).isoformat(),
        requested_bbox_west_south_east_north=REQUESTED_BBOX,
        actual_bbox_west_south_east_north=bbox,
        grid=dict(width=width,height=height,resolution_degrees=STEP,
                  transform=list(transform)[:6],horizontal_crs="EPSG:4326",
                  source_vertical_reference="EGM2008 (EPSG:3855), per official README; GeoTIFFs expose EPSG:4326 horizontal CRS",
                  local_mean_sea_level_conversion="none",classification_resolution="native 1 arcsecond; no resampling"),
        methodology=dict(
            threshold="valid modern DeltaDTM land cell elevation <= chosen level (metres above EGM2008 geoid)",
            connectivity="4-neighbour ocean-connected binary propagation on native grid",
            ocean_seeds="All pixels outside original full-resolution GSHHG 2.3.7 level-1 land polygons; levels 2-4 excluded so inland lakes are filled land, not seeds",
            missing_data="unavailable or clipped land is a barrier, never assumed zero",
            output="Additional flooded land only in GeoJSON; native raster separately distinguishes modern sea, flooded land, dry land, unknown land",
            polygonization="Exact native-grid cell boundaries, 4-neighbour; no geometry simplification",
            sensitivity="3 and 5 m EGM2008 are threshold sensitivity scenarios, not statistical confidence limits"),
        limitations=[
            "This is a static modern-terrain elevation/connectivity scenario, not an ancient shoreline reconstruction.",
            "No sediment deposition, erosion, compaction, tectonics, subsidence, ancient channels, or historical sea-level correction is modelled.",
            "EGM2008 geoid height is not local present mean sea level; the threshold is exactly +4 m EGM2008, not a precise 4 m sea-level rise.",
            "Native 1 arcsecond spacing (roughly 27 x 31 m here) does not imply equivalent elevation or shoreline accuracy.",
            "Published global mean absolute elevation error (v1.1 record: 0.43 m) is not a site-specific error bound; no local ground-truth validation has been performed.",
            "Modern levees, embankments and altered waterways can affect connectivity; 4-neighbour grid connectivity can miss sub-cell channels.",
            "GSHHG modern coast and DeltaDTM can disagree at the shoreline; seeding uses documented full-resolution GSHHG without coastline simplification.",
            "No tides, flow friction, storm surge, waves, barriers removed, or timed hydraulic propagation is modelled."
        ],
        sources=[
            dict(title="DeltaDTM v1.1, official version 4 dataset",url="https://doi.org/10.4121/21997565.v4",license="CC BY 4.0",temporal_coverage="2012-2024"),
            dict(title="Pronk et al. (2024), DeltaDTM: A global coastal digital terrain model",url="https://doi.org/10.1038/s41597-024-03091-9"),
            dict(title="Official v1.1 README, including EGM2008 datum and 30 m clipping",url=URLS["README.md"]),
            dict(title="GSHHG 2.3.7 full-resolution geography",url="https://github.com/GenericMappingTools/gshhg-gmt/releases/tag/2.3.7",local_coast_sha256=sha_file(coast_path)),
        ],
        attribution="DeltaDTM: Maarten Pronk, 2024, CC BY 4.0. Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA; all rights reserved. Derived threshold/connectivity/polygonization by this atlas.",
        input_archives=[{k:v for k,v in index.items() if k!="members"} for index in (dtm_index,mask_index)],
        input_tiles=records,
        native_counts=dict(modern_sea=int(sea.sum()),valid_land=int(valid_land.sum()),unknown_or_clipped_land=unknown_land),
        scenarios={})
    del valid_land
    structure=generate_binary_structure(2,1)
    for level in (3,4,5):
        candidate=(classes<=level)|sea
        flooded=binary_propagation(sea,structure=structure,mask=candidate)
        del candidate
        # Additional inundation: restrict to modern land, never paint sea twice.
        flooded &= land==1
        count=int(flooded.sum())
        counts_by_row=np.count_nonzero(flooded,axis=1)
        area_km2=float(np.sum(counts_by_row*row_areas)/1e6)
        boundary=dict(west=int(np.count_nonzero(flooded[:,0])),east=int(np.count_nonzero(flooded[:,-1])),
                      north=int(np.count_nonzero(flooded[0,:])),south=int(np.count_nonzero(flooded[-1,:])))
        features=[]
        invalid_polygons=0
        for geometry,value in shapes(flooded.astype("uint8"),mask=flooded,transform=transform,connectivity=4):
            # Only numeric formatting is reduced; 7 decimals retain <2 cm,
            # three orders finer than native pixels. Every grid corner retained.
            coords=[[[round(x,7),round(y,7)] for x,y in ring] for ring in geometry["coordinates"]]
            invalid_polygons += int(not shape(dict(type="Polygon",coordinates=coords)).is_valid)
            features.append(dict(type="Feature",properties=dict(kind="modern-terrain scenario",threshold_m_egm2008=level,
                 temporal_claim="none; not an ancient shoreline",native_resolution_arcseconds=1),
                 geometry=dict(type="Polygon",coordinates=coords)))
        path=out/f"flood-{level}m.geojson"
        path.write_text(json.dumps(dict(type="FeatureCollection",bbox=bbox,
             scenario=f"+{level} m EGM2008 ocean-connected modern terrain; not an ancient shoreline",
             features=features),separators=(",",":")),encoding="utf-8")
        manifest["scenarios"][str(level)]=dict(additional_flooded_native_cells=count,additional_area_km2=area_km2,
              polygon_features=len(features),file=path.name,bytes=path.stat().st_size,sha256=sha_file(path),
              flooded_land_cells_on_model_boundary=boundary,invalid_geojson_polygons=invalid_polygons)
        assert invalid_polygons==0
        if level==4:
            mask=np.zeros((height,width),dtype="uint8")
            mask[classes==255]=255
            mask[sea]=1
            mask[flooded]=2
            assert np.count_nonzero((mask==2)&(classes>4))==0
            with rasterio.open(native_path,"w",driver="GTiff",height=height,width=width,count=1,
                    dtype="uint8",crs="EPSG:4326",transform=transform,nodata=255,
                    compress="DEFLATE",tiled=True,blockxsize=512,blockysize=512,BIGTIFF="IF_SAFER") as dst:
                dst.write(mask,1)
                dst.update_tags(title=manifest["title"],category_0="dry land (valid modern elevation)",
                     category_1="modern sea (GSHHG level-1 complement)",category_2="additional ocean-connected land <=4m EGM2008",
                     category_255="land unavailable or clipped above30m in DeltaDTM; barrier",vertical_datum="EGM2008",
                     native_classification="1 arcsecond; no resampling",connectivity="4-neighbour",ancient_reconstruction="NO")
            del mask
            manifest["native_mask"]=dict(file=native_path.name,bytes=native_path.stat().st_size,sha256=sha_file(native_path),
                 values={"0":"dry valid land","1":"modern sea","2":"additional flooded land","255":"unavailable or clipped land; barrier"})
            edge_rows=np.flatnonzero(flooded[:,-1])
            manifest["verification"]=dict(additional_flooded_cells_above_4m_or_nodata=0,
                east_boundary_4m_contact_latitude_range=([north-(int(edge_rows[-1])+0.5)*STEP,north-(int(edge_rows[0])+0.5)*STEP] if edge_rows.size else None),
                boundary_note="Scenario is clipped to documented model domain; edge contact counts are reported per scenario. It is not a closed or Gulf-wide shoreline.")
        print(f"Scenario {level}m: {area_km2:,.1f} additional km², {len(features)} polygons; edge contacts {boundary}",flush=True)
        del features,flooded
    (out/"flood-manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print("Wrote",out/"flood-manifest.json",flush=True)


if __name__=="__main__":
    main()
