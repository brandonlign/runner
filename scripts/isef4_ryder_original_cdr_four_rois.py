#!/usr/bin/env python3
"""Restore four exact original Ryder post-2020 calibrated NAC source cutouts.

Only after each original EDR completed its ISIS10 USGS CSM ground camera gate.
Official CDR PDS3 first-record identity, exact byte ranges, row hashes and
0-based native original source coordinates are preserved. Nothing detected yet.
"""
from __future__ import annotations
import argparse,hashlib,json,math,re,time,urllib.request
from pathlib import Path
import numpy as np

RAD=640
WIDTH=5064
LABEL=5064
TARGET=(-44.043,143.514)
ROLES={"baseline_2022":("ryder_2022_2024","before"),
       "followup_2024":("ryder_2022_2024","after"),
       "followup_2026_April":("ryder_2026","before"),
       "followup_2026_May":("ryder_2026","after")}
def sha(x):return hashlib.sha256(x).hexdigest()
def pvlnum(pvl,key):
    m=re.search(r"(?m)^\s*"+re.escape(key)+r"\s*=\s*([-+]?[0-9]+(?:\.[0-9]+)?)",pvl)
    if not m:raise ValueError("missing exact CSM "+key)
    val=float(m.group(1))
    if not math.isfinite(val):raise ValueError("nonfinite CSM "+key)
    return val
def pds(raw,key):
    m=re.search(r"(?m)^\s*"+key+r"\s*=\s*([^\r\n]+)",raw.decode("ascii",errors="replace"))
    if not m:raise ValueError("official original NASA source PDS3 field missing "+key)
    return m.group(1).strip().strip('"')
def get(url,start,end,total):
    if not 0<=start<=end<total:raise ValueError("source interval outside exact full image")
    n=end-start+1
    req=urllib.request.Request(url,headers={
       "Range":f"bytes={start}-{end}",
       "User-Agent":"LUNARSHIFT-Ryder-original-source-pixel-r640/0.1"})
    last=None
    for i in range(3):
        try:
            with urllib.request.urlopen(req,timeout=180) as r:
                if r.status!=206 or r.headers.get("Content-Range")!=f"bytes {start}-{end}/{total}":
                    raise ValueError("source missing verified PDS byte-range identity")
                b=r.read(n+1)
            if len(b)!=n:raise ValueError("source PDS byte-range short or longer than requested")
            return b
        except (OSError,TimeoutError) as exc:
            last=exc
            time.sleep(i+1)
    raise RuntimeError("official CDR source interval failed "+repr(last))
def extract(tag,original,proof,output):
    target,role=ROLES[tag]
    row=original["epochs"][tag]
    EDR,CDR=row["EDR_ID"],row["CDR_ID"]
    src=row["probed_source_kind"]["CDR"]
    edr=row["probed_source_kind"]["EDR"]
    if src["status"]!="original_header_validated" or edr["status"]!="original_header_validated":
        raise ValueError("pre-pixel Ryder source archive rejected exact product "+tag)
    if proof.get("target_key")!=target or proof.get("source_role")!=role or proof.get("product")!=EDR:
        raise ValueError("not exact originally selected Ryder camera product "+tag)
    if proof.get("target_latitude_deg_n")!=TARGET[0] or proof.get("target_longitude_deg_e")!=TARGET[1]:
        raise ValueError("other lunar coordinate wrongly substituted "+tag)
    stages=proof["stages"]
    if stages.get("csminit_linescan",{}).get("returncode")!=0 or stages.get("csm_campt_event",{}).get("returncode")!=0:
        raise ValueError("full original EDR did not initialize or map Ryder marker "+tag)
    edr_archive=stages.get("download_IMG",{})
    if edr_archive.get("bytes")!=edr["full_original_IMG_bytes"] or len(edr_archive.get("sha256",""))!=64:
        raise ValueError("full source original EDR SHA missing "+tag)
    if edr_archive.get("source_url")!=edr["source_URL"]:
        raise ValueError("camera EDR URL differs from independently probed ODE URL")
    pvl=stages["csm_event_pvl"]["pvl_tail"]
    if abs(pvlnum(pvl,"PlanetocentricLatitude")-TARGET[0])>1e-7 or abs(pvlnum(pvl,"PositiveEast360Longitude")-TARGET[1])>1e-7:
        raise ValueError("source camera returned different true Ryder lunar location")
    sam,line=pvlnum(pvl,"Sample"),pvlnum(pvl,"Line")
    x=math.floor(sam+.5)-1;y=math.floor(line+.5)-1
    lines=src["original_lines"];total=src["full_original_IMG_bytes"]
    if not (RAD<=x<WIDTH-RAD and RAD<=y<lines-RAD):
        raise ValueError("rounded catalogue polygon included source marker but r640 pixels NOT available")
    h=get(src["source_URL"],0,LABEL-1,total)
    if sha(h)!=src["first_5064_PDS3_SHA256"]:
        raise ValueError("actual source CDR first record differs from independent archive probe")
    wanted={"PDS_VERSION_ID":"PDS3","PRODUCT_ID":CDR,"LINE_SAMPLES":"5064",
       "RECORD_BYTES":"5064","LABEL_RECORDS":"1","LINES":str(lines),
       "SAMPLE_BITS":"16","SAMPLE_TYPE":"LSB_INTEGER",
       "NULL":"-32768","VALID_MINIMUM":"-32752"}
    for k,v in wanted.items():
        if pds(h,k)!=v:raise ValueError("invalid official original calibrated PDS field "+k)
    scale=float(pds(h,"SCALING_FACTOR"))
    if not math.isclose(scale,3.05185094759972e-5,rel_tol=1e-12):
        raise ValueError("unknown original NASA NAC reflectance scale")
    row_bytes=WIDTH*2
    start=LABEL+(y-RAD)*row_bytes
    end=start+(2*RAD+1)*row_bytes
    if LABEL+lines*row_bytes!=total:raise ValueError("PDS3 source geometry or total length mismatch")
    hraw=hashlib.sha256();blocks=[]
    for pos in range(start,end,4*1024*1024):
        buf=get(src["source_URL"],pos,min(end,pos+4*1024*1024)-1,total)
        hraw.update(buf);blocks.append(buf)
    native=np.frombuffer(b"".join(blocks),dtype="<i2").reshape(2*RAD+1,WIDTH)
    patch=np.array(native[:,x-RAD:x+RAD+1],copy=True)
    if patch.shape!=(2*RAD+1,2*RAD+1):raise ValueError("bad extracted NASA original image dimensions")
    valid=patch>=-32752
    if valid.mean()<.88:raise ValueError("insufficient original Ryder source valid pixels "+tag)
    output.mkdir(parents=True,exist_ok=True)
    saved=output/(tag+"_original_NAC_CDR_r640.npy")
    np.save(saved,patch,allow_pickle=False)
    return {"EDR_product":EDR,"CDR_product":CDR,
       "source_CDR_IMG_URL":src["source_URL"],
       "full_original_EDR_SHA256":edr_archive["sha256"],
       "original_full_CDR_bytes":total,"original_full_lines":lines,
       "source_camera_1_based_sample_line":[sam,line],
       "source_camera_sample_resolution_m":pvlnum(pvl,"SampleResolution"),
       "source_camera_line_resolution_m":pvlnum(pvl,"LineResolution"),
       "original_source_cutout_0based_xyxy_exclusive":[x-RAD,y-RAD,x+RAD+1,y+RAD+1],
       "original_source_rowband_sha256":hraw.hexdigest(),
       "first_source_CDR_record_SHA256":sha(h),
       "original_native_CDR_patch_npy_sha256":sha(saved.read_bytes()),
       "reflectance_scaling_IoverF":scale,
       "valid_original_source_fraction":float(valid.mean()),
       "source_camera_workflow_run_id":proof.get("run_id"),
       "origin":"NASA official calibrated PDS3 NAC source, NOT author's processed figure"}
def main():
    p=argparse.ArgumentParser()
    for n in ("original_gate","camera_2022","camera_2024",
              "camera_2026_april","camera_2026_may","output_folder","out"):
        p.add_argument("--"+n.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    original=json.loads(a.original_gate.read_text())
    if original["schema"]!="Ryder-original-2022-2024-2026-NAC-source-gate-v1" or not original["2022_2024_exact_original_NAC_pair_source_gate_passed"]:
        raise ValueError("not exact independently source-verified Ryder archive")
    cams={r:json.loads(p.read_text()) for r,p in
       (("baseline_2022",a.camera_2022),("followup_2024",a.camera_2024),
        ("followup_2026_April",a.camera_2026_april),("followup_2026_May",a.camera_2026_may))}
    output={"schema":"Ryder-2022-2024-2026-four-original-calibrated-source-r640-v1",
       "ground_marker_lat_n_lon_e360":TARGET,
       "independent_original_archive_gate_SHA256":sha(a.original_gate.read_bytes()),
       "source_patch_halfwidth_native_px":RAD,
       "source_products":{},"status":"original source recovery in progress"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        for tag in ROLES:
            output["source_products"][tag]=extract(tag,original,cams[tag],a.output_folder)
            a.out.write_text(json.dumps(output,indent=2)+"\n")
        output["status"]="all four original Ryder source-calibrated PDS3 image ROIs hash-verified; NO image registration or novel lunar feature assessed"
        a.out.write_text(json.dumps(output,indent=2)+"\n")
        (a.output_folder/"ryder_four_epochs_original_source_manifest.json").write_text(json.dumps(output,indent=2)+"\n")
        print(json.dumps({"status":output["status"],"sources":{
             tag:{"product":v["CDR_product"],"ROI":v["original_source_cutout_0based_xyxy_exclusive"],
                  "valid":v["valid_original_source_fraction"]}
             for tag,v in output["source_products"].items()}},indent=2),flush=True)
    except Exception as exc:
        output["status"]="failed exact original Ryder source pixel gate"
        output["error"]=type(exc).__name__+": "+str(exc)
        a.out.write_text(json.dumps(output,indent=2)+"\n")
        raise
if __name__=="__main__":main()
