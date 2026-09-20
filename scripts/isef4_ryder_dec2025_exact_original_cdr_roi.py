#!/usr/bin/env python3
"""Restore independent preselected Ryder Dec-2025 original camera-ground CDR.

The lunar event is already published (2020); this is an unrelated later
acquisition. Source-crop radius is chosen from source-camera image margins,
never residual intensity or a claimed discovery. Preserve whole-row hashes,
first-record ID, exact original pixel coordinates and complete npy SHA.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
from isef4_ryder_original_cdr_four_rois import get,pvlnum,pds,sha

TARGET=(-44.043,143.514)
RADIUS_OPTIONS=(384,320,256)
def main():
    p=argparse.ArgumentParser()
    for key in ("original_archive_gate","camera_proof","source_folder","out"):
        p.add_argument("--"+key.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    gate=json.loads(a.original_archive_gate.read_text())
    cam=json.loads(a.camera_proof.read_text())
    if gate["schema"]!="Ryder-2025Dec-official-original-NAC-EDR-CDR-gate-v1" or \
       gate["EDR_ID"]!="M1520890667LE" or gate["CDR_ID"]!="M1520890667LC":
        raise ValueError("unexpected original Ryder Dec2025 preselected source product")
    edr=gate["original_records"]["EDR"];cdr=gate["original_records"]["CDR"]
    for role in (edr,cdr):
        if role["status"]!="original_PDS3_header_gate_passed":
            raise ValueError("unverified NASA archive source product")
    if cam.get("target_key")!="ryder_2025dec" or cam.get("product")!=gate["EDR_ID"] or cam.get("source_role")!="before":
        raise ValueError("wrong original NASA camera acquisition")
    stages=cam["stages"]
    if any(stages.get(k,{}).get("returncode")!=0 for k in ("csminit_linescan","csm_campt_event","csm_campt_center")):
        raise ValueError("Dec2025 camera ground-coordinate query not independently verified")
    archive=stages["download_IMG"]
    if archive.get("bytes")!=edr["full_original_IMG_bytes"] or \
       archive.get("source_url")!=edr["source_URL"] or len(archive.get("sha256",""))!=64:
        raise ValueError("original December2025 full 264 MB EDR not exact NASA source")
    pvl=stages["csm_event_pvl"]["pvl_tail"]
    if abs(pvlnum(pvl,"PlanetocentricLatitude")-TARGET[0])>1e-7 or \
       abs(pvlnum(pvl,"PositiveEast360Longitude")-TARGET[1])>1e-7:
        raise ValueError("NASA CSM camera did not locate precise Ryder site")
    sample,line=pvlnum(pvl,"Sample"),pvlnum(pvl,"Line")
    x=math.floor(sample+.5)-1;y=math.floor(line+.5)-1
    nlines=cdr["original_lines"]
    margin=min(x,5063-x,y,nlines-1-y)
    available=[r for r in RADIUS_OPTIONS if r<=margin-5]
    if not available:
        raise ValueError("no >=256-pixel 2025 source scene around true lunar site; do not pad with invented pixels")
    radius=available[0]
    url=cdr["source_URL"];total=cdr["full_original_IMG_bytes"]
    head=get(url,0,5063,total)
    if sha(head)!=cdr["first_5064_PDS3_SHA256"]:
        raise ValueError("actual downloaded source header changed from pre-pixel independent gate")
    needed={"PDS_VERSION_ID":"PDS3","PRODUCT_ID":"M1520890667LC",
       "RECORD_BYTES":"5064","LABEL_RECORDS":"1","LINE_SAMPLES":"5064",
       "LINES":str(nlines),"SAMPLE_BITS":"16","SAMPLE_TYPE":"LSB_INTEGER",
       "NULL":"-32768","VALID_MINIMUM":"-32752"}
    for k,v in needed.items():
        if pds(head,k)!=v:raise ValueError("original calibrated PDS3 source mismatch "+k)
    scale=float(pds(head,"SCALING_FACTOR"))
    if not math.isclose(scale,3.05185094759972e-5,rel_tol=1e-12):
        raise ValueError("unexpected original NASA I/F scale")
    begin=5064+(y-radius)*10128
    end=begin+(2*radius+1)*10128
    if 5064+nlines*10128!=total:
        raise ValueError("NASA original file byte geometry inconsistent with calibrated detector samples")
    blocks=[];full=hashlib.sha256()
    for start in range(begin,end,4*1024*1024):
        buf=get(url,start,min(start+4*1024*1024,end)-1,total)
        blocks.append(buf);full.update(buf)
    entire=np.frombuffer(b"".join(blocks),dtype="<i2").reshape(2*radius+1,5064)
    roi=np.array(entire[:,x-radius:x+radius+1],copy=True)
    if roi.shape!=(2*radius+1,2*radius+1):
        raise ValueError("source-cutout dimensions invalid")
    valid=roi>=-32752
    if valid.mean()<.90:raise ValueError("original December2025 source too many missing pixels")
    a.source_folder.mkdir(parents=True,exist_ok=True)
    name=a.source_folder/"followup_2025_Dec_original_NAC_CDR_native.npy"
    np.save(name,roi,allow_pickle=False)
    meta={"schema":"Ryder-Dec2025-camera-ground-exact-original-NAC-CDR-patch-v1",
      "original_archive_gate_SHA256":hashlib.sha256(a.original_archive_gate.read_bytes()).hexdigest(),
      "original_camera_proof_SHA256":hashlib.sha256(a.camera_proof.read_bytes()).hexdigest(),
      "source_EDR":"M1520890667LE","source_CDR":"M1520890667LC",
      "source_CDR_URL":url,
      "source_original_camera_1_based_sample_line":[sample,line],
      "source_cutout_0based_xyxy_exclusive":[x-radius,y-radius,x+radius+1,y+radius+1],
      "source_radius_px":radius,"source_cutout_shape":list(roi.shape),
      "source_camera_sample_resolution_m":pvlnum(pvl,"SampleResolution"),
      "source_camera_line_resolution_m":pvlnum(pvl,"LineResolution"),
      "source_full_original_EDR_sha256":archive["sha256"],
      "first_original_CDR_header_SHA256":sha(head),
      "original_CDR_rowband_SHA256":full.hexdigest(),
      "original_CDR_patch_npy_SHA256":hashlib.sha256(name.read_bytes()).hexdigest(),
      "original_CDR_pixel_scale_IoverF":scale,"valid_original_pixel_fraction":float(valid.mean()),
      "science_status":"third-epoch NASA 2025 true source pixels recovered; NOT independently registered or event screened"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(meta,indent=2)+"\n")
    (a.source_folder/"ryder_2025Dec_original_manifest.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta,indent=2),flush=True)
if __name__=="__main__":main()
