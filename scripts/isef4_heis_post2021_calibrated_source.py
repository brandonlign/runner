#!/usr/bin/env python3
"""Exact original 2024 Heis calibrated NAC ROI and reused 2021 published positive.

A real 2021-to-2024 source pair centered on the same independently verified
published lunar coordinate. This does NOT imply any new lunar event occurred.
"""
from __future__ import annotations
import argparse,hashlib,json,math,re,shutil,time,urllib.request
from pathlib import Path
import numpy as np

EDR="M1481045431LE"
CDR="M1481045431LC"
EXPECTED=(32.547,327.792)
RAD=384
def sha(x):return hashlib.sha256(x).hexdigest()
def pvlnum(s,key):
    m=re.search(r"(?m)^\s*"+re.escape(key)+r"\s*=\s*([-+]?[0-9]+(?:\.[0-9]+)?)",s)
    if not m:raise ValueError("missing actual camera PVL "+key)
    z=float(m.group(1))
    if not math.isfinite(z):raise ValueError("nonfinite camera "+key)
    return z
def exact(url,start,end,total):
    if not 0<=start<=end<total:raise ValueError("wrong NASA source byte window")
    need=end-start+1
    req=urllib.request.Request(url,headers={"Range":f"bytes={start}-{end}",
        "User-Agent":"LUNARSHIFT-Heis-post-2021-original-CDR-ROI/0.1"})
    last=None
    for retry in range(3):
        try:
            with urllib.request.urlopen(req,timeout=160) as r:
                if r.status!=206 or r.headers.get("Content-Range")!=f"bytes {start}-{end}/{total}":
                    raise ValueError("LROC PDS3 source range identity failed")
                buf=r.read(need+1)
            if len(buf)!=need:raise ValueError("truncated NASA range")
            return buf
        except (OSError,TimeoutError) as e:
            last=e
            if retry<2:time.sleep(retry+1)
    raise RuntimeError("NASA source interval failed: "+repr(last))
def field(data,key):
    m=re.search(r"(?m)^\s*"+key+r"\s*=\s*([^\r\n]+)",data.decode("ascii",errors="replace"))
    if m is None:raise ValueError("missing NASA field "+key)
    return m.group(1).strip().strip('"')
def main():
    p=argparse.ArgumentParser()
    for x in ("candidate_headers","camera","reference_2021_manifest","reference_2021_folder","output_folder","out"):
        p.add_argument("--"+x.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    cand=json.loads(a.candidate_headers.read_text())
    camera=json.loads(a.camera.read_text())
    original=json.loads(a.reference_2021_manifest.read_text())
    if cand["schema"]!="Heis-2021-to-2024-actual-overlap-NAC-source-header-pair-v1":
        raise ValueError("not actual camera-covering post-2021 Heis exact source")
    curr=cand["record"]["after"]["CDR"]
    if curr["product_id"]!=CDR:raise ValueError("wrong 2024 NAC calibrated source")
    for k,v in (("product",EDR),("source_role","after"),("target_key","heis_post2021")):
        if camera.get(k)!=v:raise ValueError("wrong actual 2024 original camera "+k)
    if camera.get("target_latitude_deg_n")!=EXPECTED[0] or camera.get("target_longitude_deg_e")!=EXPECTED[1]:
        raise ValueError("unapproved lunar ground target")
    stages=camera["stages"]
    if stages.get("csminit_linescan",{}).get("returncode")!=0 or stages.get("csm_campt_event",{}).get("returncode")!=0:
        raise ValueError("2024 original camera marker not authenticated")
    if stages.get("download_IMG",{}).get("bytes")!=cand["record"]["after"]["EDR"]["full_original_image_bytes"]:
        raise ValueError("original 2024 EDR incomplete")
    pvl=stages["csm_event_pvl"]["pvl_tail"]
    if abs(pvlnum(pvl,"PlanetocentricLatitude")-EXPECTED[0])>1e-7 or abs(pvlnum(pvl,"PositiveEast360Longitude")-EXPECTED[1])>1e-7:
        raise ValueError("original camera returned other ground")
    s,l=pvlnum(pvl,"Sample"),pvlnum(pvl,"Line")
    x=math.floor(s+.5)-1;y=math.floor(l+.5)-1
    if not (RAD<=x<5064-RAD and RAD<=y<curr["full_original_lines"]-RAD):
        raise ValueError("2024 actual ground marker too close to original NAC edge")
    url=curr["source_URL"];total=curr["full_original_image_bytes"]
    head=exact(url,0,5063,total)
    if sha(head)!=curr["header_5064_SHA256"]:raise ValueError("original 2024 CDR header differs from archive-probed source")
    expected={"PDS_VERSION_ID":"PDS3","PRODUCT_ID":CDR,
       "LINES":str(curr["full_original_lines"]),"LINE_SAMPLES":"5064",
       "RECORD_BYTES":"5064","LABEL_RECORDS":"1","SAMPLE_BITS":"16",
       "SAMPLE_TYPE":"LSB_INTEGER","NULL":"-32768","VALID_MINIMUM":"-32752"}
    for k,v in expected.items():
        if field(head,k)!=v:raise ValueError("unexpected original calibrated PDS3 field "+k)
    scale=float(field(head,"SCALING_FACTOR"))
    if not math.isclose(scale,3.05185094759972e-5,rel_tol=1e-12):
        raise ValueError("unknown official calibrated reflectance unit")
    row_bytes=5064*2
    if 5064+curr["full_original_lines"]*row_bytes!=total:
        raise ValueError("original PDS3 source length mismatch")
    start=5064+(y-RAD)*row_bytes
    end=start+(2*RAD+1)*row_bytes
    h=hashlib.sha256();buf=[]
    for off in range(start,end,4*1024*1024):
        piece=exact(url,off,min(off+4*1024*1024,end)-1,total)
        h.update(piece);buf.append(piece)
    arr=np.frombuffer(b"".join(buf),dtype="<i2").reshape(769,5064)
    roi=np.array(arr[:,x-RAD:x+RAD+1],copy=True)
    if roi.shape!=(769,769) or np.mean(roi>=-32752)<.90:
        raise ValueError("invalid 2024 original calibrated ROI")
    source_old=original["epochs"]["after"]
    if source_old["CDR_id"]!="M1376643242LC" or source_old["native_source_roi_xyxy_exclusive"][2]-source_old["native_source_roi_xyxy_exclusive"][0]!=769:
        raise ValueError("not same previously verified real 2021 Heis source")
    old=a.reference_2021_folder/"after_Heis_original_CDR_native_r384.npy"
    if sha(old.read_bytes())!=source_old["saved_npy_SHA256"]:
        raise ValueError("reused 2021 source pixels SHA mismatch")
    a.output_folder.mkdir(parents=True,exist_ok=True)
    old_dest=a.output_folder/"before_2021_Heis_original_CDR_native_r384.npy"
    shutil.copyfile(old,old_dest)
    now=a.output_folder/"after_2024_Heis_original_CDR_native_r384.npy"
    np.save(now,roi,allow_pickle=False)
    old_record={"product":"M1376643242LC","original_roi":source_old["native_source_roi_xyxy_exclusive"],
        "npy_SHA256":sha(old_dest.read_bytes()),"scale":source_old["pixel_scale_IoverF"],
        "provenance_prior_manifest_SHA256":sha(a.reference_2021_manifest.read_bytes())}
    new_record={"product":CDR,"original_roi":[x-RAD,y-RAD,x+RAD+1,y+RAD+1],
        "npy_SHA256":sha(now.read_bytes()),"scale":scale,
        "original_image_bytes":total,"header_5064_SHA256":sha(head),
        "original_source_row_band_SHA256":h.hexdigest(),
        "original_CSM_sample_line_1_based":[s,l],
        "invalid_fraction":float(np.mean(roi< -32752)),
        "original_EDR_SHA256":stages["download_IMG"]["sha256"],
        "source_camera_run_id":camera["run_id"]}
    result={"schema":"actual-overlap-Heis-2021-2024-two-original-calibrated-source-ROIs-v1",
      "coordinate_lat_n_lon_e360":EXPECTED,
      "candidate_archive_SHA256":sha(a.candidate_headers.read_bytes()),
      "source_radius":RAD,
      "stages":{"before_2021_reused_verified_original_CDR":old_record,
                "after_2024_new_verified_original_CDR":new_record},
      "science_status":"two original NASA calibrated source cutouts; NO terrain alignment, new change or novel event established"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    (a.output_folder/"heis_2021_2024_original_pair_manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2),flush=True)
if __name__=="__main__":main()
