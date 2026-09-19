#!/usr/bin/env python3
"""Development-only local support audit for the PUBLISHED Gambart C point.

Tests if real unprojected NAC correspondences near the camera-grounded
published marker support a smooth local before/after fit. A well-fitting
feature model is NOT DEM-corrected geolocation, landslide sensitivity,
calibrated photometry, or a newly found lunar event.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import cv2
import numpy as np

IDS = {"before":"M1138987659LE","after":"M1200206882LE"}
CROPS = (128, 256, 512)  # ORIGINAL source pixels; report ALL radii
EXCLUSION_ORIGINAL_PX = 64
RATIO = 0.75
THRESH_HALF_PX = 3.0
EXPECTED_WINDOWS = {"before":(8356,10403),"after":(993,3040)}

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def load_source(folder: Path, role: str, meta: list) -> tuple[np.ndarray,dict]:
    pid = IDS[role]
    entries = [d for d in meta if d.get("role")==role and d.get("edr_id")==pid]
    if len(entries)!=1 or len(entries[0].get("screening_windows",[]))!=1:
        raise ValueError(f"not one original PDS source strip for {role}")
    w=entries[0]["screening_windows"][0]
    if (w["first_line"],w["last_line"])!=EXPECTED_WINDOWS[role]:
        raise ValueError(f"original {role} source strip changed")
    arr=np.load(folder/(pid+"_mirror_raw_counts.npy"),mmap_mode="r",allow_pickle=False)
    if arr.shape!=(2048,5064) or arr.dtype!=np.uint8:
        raise ValueError(f"original {role} unsigned byte array mismatch")
    if sha(np.asarray(arr).tobytes())!=w["raw_window_sha256"]:
        raise ValueError(f"{role} original HTTP 206 source bytes changed")
    return cv2.resize(np.asarray(arr),(2532,1024),interpolation=cv2.INTER_AREA),w

def marker(path: Path,role: str, first_line: int) -> tuple[np.ndarray,dict]:
    d=json.loads(path.read_text())
    if d.get("product")!=IDS[role] or d.get("source_role")!=role:
        raise ValueError(f"not {role} exact published source camera")
    for name in ("csminit_linescan","csm_campt_event"):
        if d.get("stages",{}).get(name,{}).get("returncode")!=0:
            raise ValueError(f"not successful {role} camera {name}")
    pvl=d["stages"]["csm_event_pvl"]["pvl_tail"]
    def num(k: str) -> float:
        match=re.search(r"(?m)^\s*"+re.escape(k)+r"\s*=\s*([-+]?[0-9]+(?:\.[0-9]+)?)",pvl)
        if not match:raise ValueError(f"missing camera {role} PVL {k}")
        return float(match.group(1))
    if abs(num("PlanetocentricLatitude")-3.218)>1e-7 or abs(
        num("PositiveEast360Longitude")-348.092)>1e-7:
        raise ValueError(f"unexpected {role} published marker coordinate")
    sample,line=num("Sample"),num("Line")
    if not (1<=sample<=5064 and 1<=line<=27648):
        raise ValueError(f"invalid {role} camera image point")
    if not math.isfinite(num("PixelValue")):
        raise ValueError(f"no {role} finite original-source camera pixel")
    xy=np.array([(sample-1)/2,(line-1-first_line)/2],dtype=np.float64)
    if not (0<=xy[0]<2532 and 0<=xy[1]<1024):
        raise ValueError(f"{role} camera marker falls outside preserved original EDR strip")
    return xy,{"product":IDS[role],"run_id":d["run_id"],
        "marker_isis_sample_line_one_based":[sample,line],
        "marker_half_original_strip_xy":xy.tolist()}

def distance(x: np.ndarray,p: np.ndarray) -> np.ndarray:
    return np.linalg.norm(x-p[None,:],axis=1)

def fitting(src: np.ndarray,dst: np.ndarray,seed: int) -> dict:
    if len(src)<12:
        return {"status":"too_few_tentative_matches","matches":int(len(src))}
    cv2.setRNGSeed(seed)
    M,mask=cv2.estimateAffine2D(src.astype(np.float32),
        dst.astype(np.float32),method=cv2.RANSAC,
        ransacReprojThreshold=THRESH_HALF_PX,maxIters=10000,
        confidence=0.999,refineIters=25)
    if M is None or mask is None or int(mask.sum())<8:
        return {"status":"affine_fit_failed","matches":int(len(src))}
    inl=mask.ravel().astype(bool)
    resid=distance(cv2.transform(src.reshape(-1,1,2).astype(np.float32),M).reshape(-1,2),dst)
    return {"status":"fit","matches":int(len(src)),
        "ransac_inliers":int(inl.sum()),
        "ransac_median_inlier_halfpx":float(np.median(resid[inl])),
        "matrix":M.tolist()}

def audit(folder:Path,before_json:Path,after_json:Path)->dict:
    meta=json.loads((folder/"source_labels_and_windows.json").read_text())
    b,bwindow=load_source(folder,"before",meta)
    a,awindow=load_source(folder,"after",meta)
    bmark,bprov=marker(before_json,"before",bwindow["first_line"])
    amark,aprov=marker(after_json,"after",awindow["first_line"])
    clahe=cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8))
    sift=cv2.SIFT_create(nfeatures=8000)
    bk,bd=sift.detectAndCompute(clahe.apply(b),None)
    ak,ad=sift.detectAndCompute(clahe.apply(a),None)
    if bd is None or ad is None:
        raise RuntimeError("insufficient real-terrain source-image features")
    matches=[]
    for pair in cv2.BFMatcher(cv2.NORM_L2).knnMatch(ad,bd,k=2):
        if len(pair)==2 and pair[0].distance<RATIO*pair[1].distance:
            matches.append(pair[0])
    unique={}
    for m in sorted(matches,key=lambda x:x.distance):
        unique.setdefault(m.trainIdx,m)
    matches=list(unique.values())
    if len(matches)<50:raise RuntimeError("not enough source-verified tentative matches")
    after=np.float64([ak[m.queryIdx].pt for m in matches])
    before=np.float64([bk[m.trainIdx].pt for m in matches])
    dab=distance(after,amark)
    dbb=distance(before,bmark)
    exclusion=(dab>EXCLUSION_ORIGINAL_PX/2)&(dbb>EXCLUSION_ORIGINAL_PX/2)
    global_fit=fitting(after[exclusion],before[exclusion],32711)
    if global_fit["status"]=="fit":
        M=np.asarray(global_fit["matrix"])
        projected=M[:,:2]@amark+M[:,2]
        global_fit["marker_predicted_before_half_strip_xy"]=projected.tolist()
        global_fit["marker_minus_independent_camera_before_original_px"]=(2*(projected-bmark)).tolist()
        global_fit["marker_discrepancy_norm_original_px"]=float(2*distance(projected[None,:],bmark)[0])
    local={}
    for rad in CROPS:
        r=rad/2
        near=(dab<=r)&(dbb<=r)
        train=near&exclusion
        test=near&~exclusion
        fit=fitting(after[train],before[train],32711+rad)
        fit["radius_original_source_px"]=rad
        fit["local_tentative_matches_in_both_marker_disks"]=int(near.sum())
        fit["central_excluded_tentative_matches"]=int(test.sum())
        fit["nearest_before_match_original_px"]=float(2*np.min(dbb[near])) if near.any() else None
        fit["nearest_after_match_original_px"]=float(2*np.min(dab[near])) if near.any() else None
        if fit["status"]=="fit":
            M=np.asarray(fit["matrix"])
            projection=M[:,:2]@amark+M[:,2]
            fit["marker_predicted_before_half_strip_xy"]=projection.tolist()
            fit["marker_minus_independent_camera_before_original_px"]=(2*(projection-bmark)).tolist()
            fit["marker_discrepancy_norm_original_px"]=float(2*distance(projection[None,:],bmark)[0])
            if int(test.sum()):
                pred=cv2.transform(after[test].reshape(-1,1,2).astype(np.float32),
                    M).reshape(-1,2)
                e=np.linalg.norm(pred-before[test],axis=1)
                fit["excluded_central_match_median_residual_halfpx"]=float(np.median(e))
                fit["excluded_central_match_p95_residual_halfpx"]=float(np.percentile(e,95))
        local[str(rad)]=fit
    return {"schema":"gambart-c-camera-marker-local-raw-registration-dev-v1",
        "role":"known_published_positive_development_only",
        "original_edr_ids":IDS,
        "before":bprov,"after":aprov,
        "source_raw_window_sha256":{
            "before":bwindow["raw_window_sha256"],
            "after":awindow["raw_window_sha256"]},
        "features":{"before":len(bk),"after":len(ak),
            "tentative_unique_destination":len(matches),
            "sift_nfeatures":8000,"clahe_clip":2.0,
            "lowe_ratio":RATIO,"global_tentative_excluding_event":int(exclusion.sum()),
            "fixed_exclusion_original_px":EXCLUSION_ORIGINAL_PX},
        "global_excluding_event":global_fit,
        "local_fixed_radii":local,
        "scientific_limit":"Both camera points assume ISIS camera reference radius; original source strips are UNPROJECTED and raw DN is uncalibrated. Geometry mismatch may reflect parallax/topography, model, crop convention, or insufficient local correspondences; does not prove landslide absence, a camera error, or event recovery. Do not choose the best radius post hoc."}

def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--source-folder",type=Path,required=True)
    p.add_argument("--before-camera",type=Path,required=True)
    p.add_argument("--after-camera",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    result=audit(x.source_folder,x.before_camera,x.after_camera)
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"out":str(x.out),"global":result["global_excluding_event"],
       "local":result["local_fixed_radii"]},indent=2),flush=True)
if __name__=="__main__":
    main()
