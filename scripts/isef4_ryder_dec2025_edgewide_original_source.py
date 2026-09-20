#!/usr/bin/env python3
"""Edge-safe full-width 2025 Dec Ryder calibrated NASA NAC source re-extraction.

The first preselected camera-centered 641px 2025 crop had zero independently
validated off-site matches. Its true original NAC site marker is only ~378 px
from the right sensor edge, so the wider 1281px original source crop shifts
left by the camera-imposed boundary, not by a temporal signal. Camera-ground
marker is recorded OFF-center and passed to all subsequent matching gates.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
from isef4_ryder_original_cdr_four_rois import get,pvlnum,pds,sha

SIZE=1281
PRODUCT="M1520890667LC"
def main():
    p=argparse.ArgumentParser()
    for k in ("original_archive_gate","camera_proof","source_folder","out"):
        p.add_argument("--"+k.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    gate=json.loads(a.original_archive_gate.read_text())
    proof=json.loads(a.camera_proof.read_text())
    if gate["schema"]!="Ryder-2025Dec-official-original-NAC-EDR-CDR-gate-v1" or gate["CDR_ID"]!=PRODUCT:
        raise ValueError("not source-bound actual Ryder 2025Dec CDR")
    edr,cdr=[gate["original_records"][k] for k in ("EDR","CDR")]
    if any(z["status"]!="original_PDS3_header_gate_passed" for z in (edr,cdr)):
        raise ValueError("unverified NASA official source")
    if proof.get("target_key")!="ryder_2025dec" or proof.get("product")!=gate["EDR_ID"]:
        raise ValueError("wrong independent original source camera")
    stages=proof["stages"]
    if any(stages.get(k,{}).get("returncode")!=0 for k in ("csminit_linescan","csm_campt_event","csm_campt_center")):
        raise ValueError("source ground camera failed")
    d=stages["download_IMG"]
    if d["bytes"]!=edr["full_original_IMG_bytes"] or d["source_url"]!=edr["source_URL"] or len(d["sha256"])!=64:
        raise ValueError("full original EDR not independently byte-and-path verified")
    pvl=stages["csm_event_pvl"]["pvl_tail"]
    if abs(pvlnum(pvl,"PlanetocentricLatitude")+44.043)>1e-7 or \
       abs(pvlnum(pvl,"PositiveEast360Longitude")-143.514)>1e-7:
        raise ValueError("wrong actual lunar ground marker")
    sample,line=pvlnum(pvl,"Sample"),pvlnum(pvl,"Line")
    x=math.floor(sample+.5)-1
    y=math.floor(line+.5)-1
    nlines=cdr["original_lines"];nbytes=cdr["full_original_IMG_bytes"]
    if not (0<=x<5064 and 0<=y<nlines):raise ValueError("camera site not in image")
    start_x=min(max(x-SIZE//2,0),5064-SIZE)
    start_y=min(max(y-SIZE//2,0),nlines-SIZE)
    marker=[x-start_x,y-start_y]
    if min(marker)<100 or max(marker)>=SIZE-100:
        raise ValueError("insufficient physically real original source context even with edge-safe crop")
    head=get(cdr["source_URL"],0,5063,nbytes)
    if sha(head)!=cdr["first_5064_PDS3_SHA256"]:
        raise ValueError("new crop downloaded nonidentical PDS3 original source")
    for k,v in {"PDS_VERSION_ID":"PDS3","PRODUCT_ID":PRODUCT,"RECORD_BYTES":"5064",
        "LABEL_RECORDS":"1","LINE_SAMPLES":"5064","LINES":str(nlines),
        "SAMPLE_BITS":"16","SAMPLE_TYPE":"LSB_INTEGER",
        "NULL":"-32768","VALID_MINIMUM":"-32752"}.items():
        if pds(head,k)!=v:raise ValueError("changed original calibrated NAC label "+k)
    scale=float(pds(head,"SCALING_FACTOR"))
    if not math.isclose(scale,3.05185094759972e-5,rel_tol=1e-12):
        raise ValueError("unverified reflectance scale")
    if 5064+nlines*10128!=nbytes:raise ValueError("original NASA source bytes not exact 5064-sample rows")
    begin=5064+start_y*10128
    end=begin+SIZE*10128
    blocks=[];rowhash=hashlib.sha256()
    for ptr in range(begin,end,4*1024*1024):
        b=get(cdr["source_URL"],ptr,min(end,ptr+4*1024*1024)-1,nbytes)
        blocks.append(b);rowhash.update(b)
    array=np.frombuffer(b"".join(blocks),dtype="<i2").reshape(SIZE,5064)
    cut=np.array(array[:,start_x:start_x+SIZE],copy=True)
    if cut.shape!=(SIZE,SIZE) or np.mean(cut>=-32752)<.90:
        raise ValueError("invalid original wide CDR native pixels")
    a.source_folder.mkdir(parents=True,exist_ok=True)
    fname="followup_2025_Dec_original_NAC_CDR_edgewide.npy"
    path=a.source_folder/fname
    np.save(path,cut,allow_pickle=False)
    result={"schema":"Ryder-Dec2025-camera-ground-exact-original-NAC-CDR-edgewide-v1",
        "why":"previous centered 641px original NAC did not pass off-site terrain registration; widen the source scene solely to the original camera edge, not a temporal candidate",
        "original_archive_gate_SHA256":hashlib.sha256(a.original_archive_gate.read_bytes()).hexdigest(),
        "original_camera_proof_SHA256":hashlib.sha256(a.camera_proof.read_bytes()).hexdigest(),
        "source_EDR":gate["EDR_ID"],"source_CDR":PRODUCT,
        "source_CDR_URL":cdr["source_URL"],
        "source_original_camera_1_based_sample_line":[sample,line],
        "source_camera_marker_xy_cutout":marker,
        "source_cutout_0based_xyxy_exclusive":[start_x,start_y,start_x+SIZE,start_y+SIZE],
        "source_cutout_shape":[SIZE,SIZE],
        "original_source_npy_filename":fname,
        "source_camera_sample_resolution_m":pvlnum(pvl,"SampleResolution"),
        "source_camera_line_resolution_m":pvlnum(pvl,"LineResolution"),
        "source_full_original_EDR_sha256":d["sha256"],
        "first_original_CDR_header_SHA256":sha(head),
        "original_CDR_rowband_SHA256":rowhash.hexdigest(),
        "original_CDR_patch_npy_SHA256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "original_CDR_pixel_scale_IoverF":scale,
        "valid_original_pixel_fraction":float(np.mean(cut>=-32752)),
        "scientific_status":"edge-safe bigger original source scene; no registration or temporal feature claim"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    (a.source_folder/"ryder_Dec2025_original_edgewide_manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2),flush=True)
if __name__=="__main__":main()
