#!/usr/bin/env python3
"""Exact NASA LROC CDR source-pixel ROIs for a published development event.

Read only a deterministic 1025 x 1025 native-calibrated pixel window
around each independently verified ISIS CSM source point, from the original
16-bit LROC CDR counterpart. Commit hashes/stats only, keep pixels in an
expiring workflow artifact. NEVER compare native source-index pixels directly
across the two differently oriented epochs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import time
import urllib.request
from pathlib import Path

import numpy as np

RADIUS = 512
ROLES = {
    "before": {"product": "M1138987659LC", "edr": "M1138987659LE",
               "full_bytes": 155571144, "lines": 15360},
    "after": {"product": "M1200206882LC", "edr": "M1200206882LE",
              "full_bytes": 280024008, "lines": 27648},
}
LABEL_BYTES = 5064
SAMPLES = 5064
SAMPLE_BYTES = 2
ROW_BYTES = SAMPLES * SAMPLE_BYTES
MAX_RANGE_BYTES = 4 * 1024 * 1024
SOURCE_MARKER = (3.218, 348.092)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pvl_value(text: str, key: str) -> float:
    m = re.search(r"(?m)^\s*" + re.escape(key)
                  + r"\s*=\s*([-+]?\d+(?:\.\d+)?)", text)
    if m is None:
        raise ValueError("missing camera PVL " + key)
    return float(m.group(1))


def marker(camera: dict, role: str) -> tuple[int,int,dict]:
    expected = ROLES[role]
    if camera.get("source_role") != role or camera.get("product") != expected["edr"]:
        raise ValueError(f"{role} camera isn't exact Gambart C original EDR")
    if any(camera.get("stages", {}).get(key, {}).get("returncode") != 0
           for key in ("csminit_linescan", "csm_campt_event")):
        raise ValueError(f"{role} camera has not passed CSM source-point geometry")
    pvl = camera["stages"]["csm_event_pvl"]["pvl_tail"]
    lat = pvl_value(pvl, "PlanetocentricLatitude")
    lon = pvl_value(pvl, "PositiveEast360Longitude")
    if abs(lat-SOURCE_MARKER[0])>1e-7 or abs(lon-SOURCE_MARKER[1])>1e-7:
        raise ValueError("not the predeclared published marker")
    sample = pvl_value(pvl, "Sample")
    line = pvl_value(pvl, "Line")
    if not all(math.isfinite(v) for v in (sample,line,pvl_value(pvl,"PixelValue"))):
        raise ValueError("non-finite CSM source point")
    x = math.floor(sample + 0.5) - 1
    y = math.floor(line + 0.5) - 1
    if not (RADIUS<=x<SAMPLES-RADIUS and
            RADIUS<=y<expected["lines"]-RADIUS):
        raise ValueError(f"{role} source marker too close to boundary for fixed CDR ROI")
    return x,y,{"camera_run_id":camera["run_id"],
                "edr_sha256":camera["stages"]["download_IMG"]["sha256"],
                "published_marker_isis_sample_line_one_based":[sample,line],
                "source_marker_xy_zero_based":[x,y]}


def fetch_exact(url: str,start: int,end: int,total: int) -> bytes:
    if not (0<=start<=end<total):
        raise ValueError("invalid strict original source byte window")
    want = end-start+1
    req=urllib.request.Request(url,headers={
        "Range":f"bytes={start}-{end}",
        "User-Agent":"LUNARSHIFT-published-CDR-reproducibility/1.0",
    })
    last=None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=100) as r:
                if r.status!=206 or r.headers.get("Content-Range")!=(
                        f"bytes {start}-{end}/{total}"):
                    raise ValueError("CDR archive failed strict HTTP 206 range/size identity")
                raw=r.read(want+1)
            if len(raw)!=want:
                raise ValueError("short/overlong NASA CDR range response")
            return raw
        except (OSError, TimeoutError) as e:
            last=e
            if attempt<2: time.sleep(attempt+1)
    raise RuntimeError("CDR range unavailable: "+repr(last))


def validated_pds_header(url: str, role: str, source: dict) -> str:
    total=source["full_bytes"]
    header=fetch_exact(url,0,LABEL_BYTES-1,total)
    text=header.decode("ascii",errors="replace")
    fields={}
    for key in ("PDS_VERSION_ID","PRODUCT_ID","RECORD_BYTES","LABEL_RECORDS",
                "LINES","LINE_SAMPLES","SAMPLE_BITS","SAMPLE_TYPE",
                "SCALING_FACTOR","NULL","VALID_MINIMUM"):
        m=re.search(r"(?m)^\s*"+key+r"\s*=\s*([^\r\n]+)",text)
        if not m: raise ValueError(f"missing official PDS header {key}")
        fields[key]=m.group(1).strip().strip('"')
    checks={
        "PDS_VERSION_ID":"PDS3",
        "PRODUCT_ID":source["product"],
        "RECORD_BYTES":"5064",
        "LABEL_RECORDS":"1",
        "LINES":str(source["lines"]),
        "LINE_SAMPLES":"5064",
        "SAMPLE_BITS":"16",
        "SAMPLE_TYPE":"LSB_INTEGER",
        "NULL":"-32768",
        "VALID_MINIMUM":"-32752",
    }
    for key,want in checks.items():
        if fields[key]!=want:
            raise ValueError(f"{role} CDR {key} mismatch {fields[key]!r} != {want!r}")
    if not math.isclose(float(fields["SCALING_FACTOR"]),
                        3.05185094759972e-5,rel_tol=1e-12):
        raise ValueError("unknown official CDR reflectance scaling")
    if LABEL_BYTES+source["lines"]*ROW_BYTES!=total:
        raise ValueError("inconsistent original PDS CDR fixed record geometry")
    return digest(header)


def cdr_roi(role: str, verified: dict, camera: dict,
            output: Path) -> dict:
    source=ROLES[role]
    matches=verified.get("verified_matches",{}).get(role,[])
    if len(matches)!=1 or matches[0].get("verification")!=(
            "verified_CDR_PDS3_source_header"):
        raise ValueError("exact NASA CDR provenance not unique and verified")
    url=matches[0]["url"]
    if source["product"]+".IMG" not in url:
        raise ValueError("wrong archive product URL")
    if matches[0]["full_image_bytes"]!=source["full_bytes"]:
        raise ValueError("independently verified CDR total byte length changed")
    x,y,geo=marker(camera,role)
    header_sha=validated_pds_header(url,role,source)
    y0=y-RADIUS
    number_of_rows=2*RADIUS+1
    begin=LABEL_BYTES+y0*ROW_BYTES
    stop=begin+number_of_rows*ROW_BYTES
    h=hashlib.sha256()
    pieces=[]
    for first in range(begin,stop,MAX_RANGE_BYTES):
        end=min(first+MAX_RANGE_BYTES,stop)-1
        b=fetch_exact(url,first,end,source["full_bytes"])
        h.update(b)
        pieces.append(b)
    full=b"".join(pieces)
    if len(full)!=number_of_rows*ROW_BYTES:
        raise ValueError("CDR source strip bytes do not have expected length")
    allrows=np.frombuffer(full,dtype="<i2").reshape(number_of_rows,SAMPLES)
    native=np.array(allrows[:,x-RADIUS:x+RADIUS+1],copy=True)
    if native.shape!=(1025,1025):
        raise ValueError("CDR marker source crop shape unexpected")
    valid=native>=-32752
    if np.mean(valid)<0.85:
        raise ValueError("CDR published marker ROI lacks >=85% valid I/F pixels")
    scale=float(matches[0]["pds_fields"]["SCALING_FACTOR"])
    values=native[valid].astype(np.float64)*scale
    output.mkdir(parents=True,exist_ok=True)
    out=output/(role+"_official_cdr_if_r512_original_source.npy")
    np.save(out,native,allow_pickle=False)
    return {"role":role,"cdr_product":source["product"],"source_url":url,
        "cdr_total_image_bytes":source["full_bytes"],
        "pds3_header_5064_sha256":header_sha,
        "source_raw_rows_first_last_inclusive":[y0,y+RADIUS],
        "source_raw_rows_bytes_sha256":h.hexdigest(),
        "original_source_roi_xyxy_exclusive":[x-RADIUS,y-RADIUS,
             x+RADIUS+1,y+RADIUS+1],
        "roi_shape_hw":[1025,1025],
        "saved_roi_npy_sha256":digest(out.read_bytes()),
        "original_source_row_byte_window_inclusive":[begin,stop-1],
        "invalid_special_pixel_fraction":float(np.mean(~valid)),
        "valid_cdr_if_p01_p50_p99":[float(v) for v in np.percentile(values,[1,50,99])],
        "valid_raw_int16_p01_p50_p99":[float(v) for v in np.percentile(native[valid],[1,50,99])],
        "scaling_factor":scale,"valid_minimum_original_int16":-32752,
        "scientific_limit":"Original calibrated CDR I/F values remain in different unprojected native source coordinate systems; do NOT subtract these ROIs without scene registration/terrain/photon controls.",
        **geo}


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--pds-probe",type=Path,required=True)
    p.add_argument("--before-camera",type=Path,required=True)
    p.add_argument("--after-camera",type=Path,required=True)
    p.add_argument("--artifact-folder",type=Path,required=True)
    p.add_argument("--diagnostic",type=Path,required=True)
    a=p.parse_args()
    probe=json.loads(a.pds_probe.read_text())
    if probe.get("input_published_EDRs")!=[
            ROLES["before"]["edr"], ROLES["after"]["edr"]]:
        raise ValueError("published EDR pair changed")
    cameras={k:json.loads(path.read_text()) for k,path in (
        ("before",a.before_camera),("after",a.after_camera))}
    result={"schema":"exact-Gambart-C-two-epoch-native-CDR-r512-v1",
        "development_only":True,
        "published_marker_lat_lon_e360":list(SOURCE_MARKER),
        "source_pixel_radius":RADIUS,
        "methods":"original NASA calibrated LROC CDR; exact HTTP206 source pixel ranges; 16-bit little-endian signed; fixed PDS scale",
        "epochs":{}}
    for role in ("before","after"):
        result["epochs"][role]=cdr_roi(role,probe,cameras[role],a.artifact_folder)
    result["interpretation"]=(
        "Both calibrated original NASA CDR source patches were recovered at "
        "independently camera-derived coordinates. They are NOT in common "
        "ground projection and contain NO landslide recovery claim.")
    a.diagnostic.parent.mkdir(parents=True,exist_ok=True)
    a.diagnostic.write_text(json.dumps(result,indent=2)+"\n")
    (a.artifact_folder/"cdr_source_patch_manifest.json").write_text(
        json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2),flush=True)


if __name__=="__main__":
    main()
