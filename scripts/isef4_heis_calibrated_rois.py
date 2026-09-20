#!/usr/bin/env python3
"""Retrieve only verified original calibrated Heis S26 NAC marker ROIs.

Requires BOTH independent published-coordinate ISIS/CSM camera solutions.
Strict PDS3 header identity, byte-range verification, checksums and complete
per-role source provenance. Development only; no geographical holdout access.
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

SOURCE={"before":("M1197976848LE","M1197976848LC",217797576,21504,
                   "ec9d63f8d02ad5a4ddebd4fbc8f7383aedc230ec17f45463c6c0405805c8f12f"),
        "after":("M1376643242LE","M1376643242LC",528929736,52224,
                  "a51de9835e6048b40be52609e6be0a877f0807afce918348005208b84d45b2ed")}
MARKER=(32.547,327.792)
SAMPLES=5064
LABEL_BYTES=5064
RAD=384
def digest(raw):return hashlib.sha256(raw).hexdigest()
def pvlnum(pvl,key):
    match=re.search(r"(?m)^\s*"+re.escape(key)+r"\s*=\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)",pvl)
    if not match:raise ValueError("missing "+key+" camera field")
    x=float(match.group(1))
    if not math.isfinite(x):raise ValueError("nonfinite "+key)
    return x
def get_range(url,start,end,total):
    assert 0<=start<=end<total
    size=end-start+1
    req=urllib.request.Request(url,headers={"Range":f"bytes={start}-{end}",
        "User-Agent":"LUNARSHIFT-Heis-S26-original-calibrated-roi/0.1"})
    last=None
    for repeat in range(3):
        try:
            with urllib.request.urlopen(req,timeout=160) as r:
                h=r.headers.get("Content-Range")
                if r.status!=206 or h!=f"bytes {start}-{end}/{total}":
                    raise ValueError(f"unverified PDS CDR range {h}")
                b=r.read(size+1)
            if len(b)!=size:raise ValueError("short or overlong original CDR bytes")
            return b
        except (OSError,TimeoutError) as e:
            last=e
            if repeat<2:time.sleep(repeat+1)
    raise RuntimeError("source byte-range request failed: "+repr(last))
def header_fields(header):
    text=header.decode("ascii",errors="replace")
    result={}
    for name in ("PDS_VERSION_ID","PRODUCT_ID","RECORD_BYTES","LABEL_RECORDS",
                 "LINES","LINE_SAMPLES","SAMPLE_BITS","SAMPLE_TYPE",
                 "SCALING_FACTOR","NULL","VALID_MINIMUM"):
        m=re.search(r"(?m)^\s*"+name+r"\s*=\s*([^\r\n]+)",text)
        if not m:raise ValueError("missing PDS3 field "+name)
        result[name]=m.group(1).strip().strip('"')
    return result
def camera_proof(blob,role):
    edr,cdr,total,lines,head_sha=SOURCE[role]
    if blob.get("product")!=edr or blob.get("source_role")!=role:
        raise ValueError("incorrect original source camera role or EDR ID")
    if blob.get("target_latitude_deg_n")!=MARKER[0] or blob.get("target_longitude_deg_e")!=MARKER[1]:
        raise ValueError("wrong Heis source location")
    stages=blob.get("stages",{})
    if stages.get("csminit_linescan",{}).get("returncode")!=0 or stages.get("csm_campt_event",{}).get("returncode")!=0:
        raise ValueError("independent Heis original camera not successfully initialized")
    pvl=stages.get("csm_event_pvl",{}).get("pvl_tail","")
    if not pvl:raise ValueError("missing camera-ground verified marker pvl")
    if abs(pvlnum(pvl,"PlanetocentricLatitude")-MARKER[0])>1e-7 or abs(pvlnum(pvl,"PositiveEast360Longitude")-MARKER[1])>1e-7:
        raise ValueError("camera returned incorrect published coordinate")
    if not math.isfinite(pvlnum(pvl,"PixelValue")):raise ValueError("source marker nonfinite")
    sample,line=pvlnum(pvl,"Sample"),pvlnum(pvl,"Line")
    x=math.floor(sample+.5)-1;y=math.floor(line+.5)-1
    if not (RAD<=x<SAMPLES-RAD and RAD<=y<lines-RAD):
        raise ValueError("Heis published marker lacks bounded 769-square original source ROI")
    original=stages.get("download_IMG",{})
    if original.get("bytes")!=LABEL_BYTES+SAMPLES*lines or len(original.get("sha256",""))!=64:
        raise ValueError("complete exact verified original EDR not present")
    return {"marker_sample_line_isis_one_based":[sample,line],
            "marker_source_xy_zero_based":[x,y],
            "source_EDR_SHA256":original["sha256"],
            "camera_run_id":blob.get("run_id")}
def recover(role,cam,ode,outdir):
    edr,cdr,total,lines,head_sha=SOURCE[role]
    coord=camera_proof(cam,role)
    source=ode["verified_products"].get(cdr)
    if not source or source["product_type"]!="CDRNAC4":
        raise ValueError("exact official calibrated product unavailable")
    if source["full_length_from_content_range"]!=str(total) or source["first_5064_header_sha256"]!=head_sha or not source["PDS3_header_declares_product"]:
        raise ValueError("CDR source length/header mismatches original ODE verification")
    urls=source["img_urls"]
    if len(urls)!=1 or cdr+".IMG" not in urls[0]:
        raise ValueError("ambiguous original calibrated CDR image")
    url=urls[0]
    original_header=get_range(url,0,LABEL_BYTES-1,total)
    if digest(original_header)!=head_sha:raise ValueError("exact independent calibrated header SHA changed")
    fields=header_fields(original_header)
    expected={"PDS_VERSION_ID":"PDS3","PRODUCT_ID":cdr,"RECORD_BYTES":"5064",
        "LABEL_RECORDS":"1","LINES":str(lines),"LINE_SAMPLES":"5064",
        "SAMPLE_BITS":"16","SAMPLE_TYPE":"LSB_INTEGER","NULL":"-32768","VALID_MINIMUM":"-32752"}
    for k,v in expected.items():
        if fields[k]!=v:raise ValueError(f"calibrated PDS field {k}: {fields[k]} != {v}")
    scale=float(fields["SCALING_FACTOR"])
    if not math.isclose(scale,3.05185094759972e-5,rel_tol=1e-12):
        raise ValueError("unrecognized calibrated reflectance scale")
    x,y=coord["marker_source_xy_zero_based"]
    y0=y-RAD
    row_bytes=SAMPLES*2
    start=LABEL_BYTES+y0*row_bytes
    stop=start+(2*RAD+1)*row_bytes
    if LABEL_BYTES+lines*row_bytes!=total:raise ValueError("PDS3 byte geometry wrong")
    pieces=[];hashing=hashlib.sha256()
    for first in range(start,stop,4*1024*1024):
        last=min(first+4*1024*1024,stop)-1
        data=get_range(url,first,last,total)
        pieces.append(data);hashing.update(data)
    binary=b"".join(pieces)
    full=np.frombuffer(binary,dtype="<i2").reshape(2*RAD+1,SAMPLES)
    roi=np.array(full[:,x-RAD:x+RAD+1],copy=True)
    if roi.shape!=(769,769):raise ValueError("invalid marker window dimensions")
    valid=roi>=-32752
    if valid.mean()<.90:raise ValueError("less than 90 percent finite CDR source pixels")
    outdir.mkdir(parents=True,exist_ok=True)
    path=outdir/(role+"_Heis_original_CDR_native_r384.npy")
    np.save(path,roi,allow_pickle=False)
    vals=roi[valid].astype(float)*scale
    return {"EDR_id":edr,"CDR_id":cdr,"CDR_URL":url,
       "first_5064_header_sha256":head_sha,"full_CDR_byte_count":total,
       "full_original_lines":lines,
       "native_source_roi_xyxy_exclusive":[x-RAD,y-RAD,x+RAD+1,y+RAD+1],
       "source_row_band_0based_inclusive":[y0,y+RAD],
       "original_CDR_row_band_SHA256":hashing.hexdigest(),
       "saved_npy_SHA256":digest(path.read_bytes()),"invalid_fraction":float(1-valid.mean()),
       "pixel_scale_IoverF":scale,
       "valid_IoverF_percentiles_01_50_99":np.percentile(vals,[1,50,99]).tolist(),**coord}
def main():
    p=argparse.ArgumentParser()
    for name in ("ode_manifest","before_camera","after_camera","output_dir","out"):
        p.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    ode=json.loads(a.ode_manifest.read_text())
    if not ode.get("EDR_IDs_exact_from_public_ODE") or not ode.get("CDR_IDs_exact_from_public_ODE"):
        raise ValueError("verified Heis exact observation source inventory missing")
    cams={"before":json.loads(a.before_camera.read_text()),"after":json.loads(a.after_camera.read_text())}
    result={"schema":"isef4-Heis-S26-source-grounded-original-CDR-r384-v1",
        "published_positive_not_new":True,"coordinate_lat_n_lon_e360":MARKER,
        "original_published_Figure_S26_SHA256":"1e642c9ebf0f0716cecef1141f52f2d8fd7c2e274ad806a07447f8012dee3ea8",
        "source_ODE_manifest_SHA256":digest(a.ode_manifest.read_bytes()),
        "source_radius_pixels":RAD,"epochs":{},
        "science_status":"not yet both source pixels verified"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        for role in ("before","after"):
            result["epochs"][role]=recover(role,cams[role],ode,a.output_dir)
            a.out.write_text(json.dumps(result,indent=2)+"\n")
        result["science_status"]="both original source-verified calibrated NAC cutouts; no geometric co-registration or Heis landslide recovered"
        a.out.write_text(json.dumps(result,indent=2)+"\n")
        (a.output_dir/"heis_s26_original_cdr_r384_source_manifest.json").write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps({"stage":result["science_status"],"source_roi":{k:v["native_source_roi_xyxy_exclusive"] for k,v in result["epochs"].items()}}),flush=True)
    except Exception as exc:
        result["science_status"]="source-cutout gate failed; cannot claim Heis original source recovery"
        result["failure"]=type(exc).__name__+": "+str(exc)
        a.out.write_text(json.dumps(result,indent=2)+"\n")
        raise
if __name__=="__main__":main()
