#!/usr/bin/env python3
"""Development-only generic CDR residual controls; NEVER landslide detection.

Two real NASA calibrated native I/F source patches are warped with EACH
predeclared source-terrain affine model. Report all fixed spatial windows
around BOTH independently derived nominal camera-marker anchors, and
non-overlapping same-pair off-marker controls. No candidate is a new event.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import cv2
import numpy as np

RADII=(32,64,128)
CENTER=np.float32([512.,512.])


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_pair(folder,metadata):
    values={}
    for role in ("before","after"):
        row=metadata["epochs"][role]
        file=folder/(role+"_official_cdr_if_r512_original_source.npy")
        if sha(file)!=row["saved_roi_npy_sha256"]:
            raise ValueError("original calibrated source pixel digest changed")
        im=np.load(file,allow_pickle=False)
        if im.shape!=(1025,1025) or im.dtype!=np.int16:
            raise ValueError("wrong original CDR geometry")
        mask=(im>=-32752)
        values[role]=(im.astype(np.float32)*row["scaling_factor"],mask)
    return values


def disk(shape,center,r):
    yy,xx=np.ogrid[:shape[0],:shape[1]]
    return (xx-center[0])**2+(yy-center[1])**2<=r*r


def control_centers(shape,r,anchors):
    step=max(128,2*r+32)
    pts=[]
    for y in range(r,shape[0]-r,step):
        for x in range(r,shape[1]-r,step):
            p=np.array([float(x),float(y)])
            if min(np.linalg.norm(p-a) for a in anchors)>r+160:
                pts.append([x,y])
    return pts


def window_stats(residual,active,center,r):
    region=disk(residual.shape,center,r)
    valid=region&active
    cover=valid.sum()/max(1,region.sum())
    out={"center_xy":[float(center[0]),float(center[1])],
         "radius_source_px":r,
         "geometric_overlap_fraction":float(cover),
         "valid_source_pixels":int(valid.sum())}
    if cover<.90 or valid.sum()<100:
        out["status"]="unassessable_lt90pct_source_support"
    else:
        vals=residual[valid]
        out.update({"status":"assessable",
                    "median_abs_if":float(np.median(vals)),
                    "p95_abs_if":float(np.percentile(vals,95))})
    return out


def evaluate(b,a,bmask,amask,row,mode):
    M=np.asarray(row["matrix_after_to_before"],dtype=np.float64)
    if M.shape!=(2,3) or not np.isfinite(M).all():
        raise ValueError("unverified affine matrix")
    height,width=b.shape
    shifted=cv2.warpAffine(a,M,(width,height),flags=cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    support=cv2.warpAffine(amask.astype(np.uint8),M,(width,height),
                           flags=cv2.INTER_NEAREST,
                           borderMode=cv2.BORDER_CONSTANT,borderValue=0).astype(bool)
    valid=bmask&support&np.isfinite(shifted)&np.isfinite(b)
    if valid.mean()<.50:
        raise ValueError("real source overlap insufficient")
    after_anchor=cv2.transform(CENTER.reshape(1,1,2),M)[0,0]
    anchors=[CENTER,after_anchor]
    outside=valid
    for origin in anchors:
        outside=outside&~disk(b.shape,origin,160)
    gain=1.
    if mode=="outside-marker-median-gain":
        if outside.sum()<5000:
            raise ValueError("too little independent background for photometric gain")
        meda=np.median(shifted[outside])
        if meda<=0:raise ValueError("nonpositive original CDR I/F background")
        gain=float(np.median(b[outside])/meda)
        if not .5<=gain<=2.:
            raise ValueError("unphysical pilot photometric gain")
    residual=np.abs(b-gain*shifted)
    windows={}
    for radius in RADII:
        controls=[]
        for p in control_centers(b.shape,radius,anchors):
            v=window_stats(residual,valid,np.asarray(p),radius)
            if v["status"]=="assessable":controls.append(v)
        observed={}
        for name,pt in (("before_camera",CENTER),
                        ("mapped_after_camera",after_anchor)):
            v=window_stats(residual,valid,pt,radius)
            if v["status"]=="assessable" and controls:
                baseline=[c["median_abs_if"] for c in controls]
                v["control_median_of_medians_abs_if"]=float(np.median(baseline))
                v["control_median_range_abs_if"]=[float(min(baseline)),
                                                   float(max(baseline))]
                v["rank_lte_event_median_among_controls"]=int(
                    sum(z<=v["median_abs_if"] for z in baseline))
                v["control_count"]=len(baseline)
                v["rank_is_not_pvalue"]=True
            observed[name]=v
        windows[str(radius)]={
            "anchors":observed,
            "nonoverlapping_control_diameter_step_source_px":
                   max(128,2*radius+32),
            "control_count_assessable":len(controls),
            "control_sites_xy":[c["center_xy"] for c in controls],
            "control_median_abs_if":[c["median_abs_if"] for c in controls],
            "control_p95_abs_if":[c["p95_abs_if"] for c in controls]}
    return {"geometry_model":row["model"],
            "photometry":mode,"gain_before_over_after":gain,
            "active_source_fraction":float(valid.mean()),
            "registration_withheld_median_px":row["withheld_median_px"],
            "registration_withheld_p95_px":row["withheld_p95_px"],
            "fixed_windows":windows,
            "interpretation":"Descriptive photometric residual distributions; no event recognition, geological morphology or p-values."}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-folder",required=True,type=Path)
    p.add_argument("--source-manifest",required=True,type=Path)
    p.add_argument("--registration",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    x=p.parse_args()
    metadata=json.loads(x.source_manifest.read_text())
    reg=json.loads(x.registration.read_text())
    if (metadata["schema"]!="exact-Gambart-C-two-epoch-native-CDR-r512-v1" or
        reg["schema"]!="known-published-Gambart-C-CDR-native-registration-preflight-v1" or
        reg["source_manifest_sha256"]!=sha(x.source_manifest)):
        raise ValueError("registration not bound to this NASA CDR source inventory")
    values=read_pair(x.source_folder,metadata)
    b,bmask=values["before"];a,amask=values["after"]
    results=[]
    for row in reg["model_trials"]:
        if row["status"]!="fit" or not row["preflight_gate_passed"]:
            results.append({"model":row["model"],"status":"registration_gate_failed"})
            continue
        for mode in ("original-IoverF","outside-marker-median-gain"):
            results.append(evaluate(b,a,bmask,amask,row,mode))
    out={"schema":"GambartC-known-positive-calibrated-IoverF-generic-residual-controls-v1",
         "source_manifest_sha256":sha(x.source_manifest),
         "registration_result_sha256":sha(x.registration),
         "fixed_radii_source_px":list(RADII),
         "models_and_photometric_modes":results,
         "important_limits":[
          "Source pixels registered relatively, NOT in one independently validated lunar DEM/map.",
          "The two camera markers disagree by about 58 source pixels; report both, not a cherry-picked center.",
          "All windows and controls are from the SAME PUBLISHED event's pair; no geographic holdout.",
          "No point-window score or control rank is a statistical p-value or a geological identification.",
          "Illumination, shadows and relief can dominate residuals despite calibrated NASA reflectance.",
          "No new lunar surface event has been established." ]}
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({"out":str(x.out),
        "completed_models":len(results),
        "summary":[{"model":v.get("geometry_model"),
                    "mode":v.get("photometry"),
                    "r64":v.get("fixed_windows",{}).get("64")}
                   for v in results]},indent=2))


if __name__=="__main__":
    main()
