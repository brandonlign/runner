#!/usr/bin/env python3
"""Evaluate original calibrated CDR at the independently located REAL S5 paper change.

Use the original S5 before/after independently fitted component; transform
through BEFORE paper->EDR terrain correspondences at both descriptor ratios.
Then test both already-prespecified calibrated CDR geometry models. No model
selection on CDR response and no claim of unpublished lunar discovery.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import cv2
import numpy as np
from isef4_gambart_cdr_generic_residual_pilot import read_pair, disk, control_centers

FIG_SHA="3d0e494c40b92e7de66ce54f8317c646ad1d8a19e328bc2811cd7cc13d48dc7f"
R=(4,8,12,24)
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def source_point(case,paper_xy,model):
    if case["role"]!="before" or case["rotation_90_ccw"]!=0 or not case["flip_after_rotation"]:
        raise ValueError("not unrotated BEFORE source fit with explicitly mirrored array")
    x,y=paper_xy[0]-19,paper_xy[1]-19
    m=np.float64(case["models"][model]["matrix"])
    a=m[:,:2]@np.array([x,y])+m[:,2]
    x0,y0,x1,y1=case["crop_xyxy_half_source"]
    return np.array([2*(x0+x1-x0-1-a[0]),8356+2*(y0+a[1])],np.float64)
def local_stats(z,valid,center,r):
    mask=disk(z.shape,center,r)
    support=valid&mask
    frac=float(support.sum()/mask.sum())
    if frac<.9:
        return {"status":"unassessable","fraction":frac}
    a=z[support]
    return {"status":"assessable","fraction":frac,"pixels":int(support.sum()),
            "median_signed_robust_sigma":float(np.median(a)),
            "median_absolute_robust_sigma":float(np.median(np.abs(a))),
            "fraction_positive_gt5":float(np.mean(a>5)),
            "fraction_negative_ltminus5":float(np.mean(a< -5)),
            "fraction_absolute_gt5":float(np.mean(np.abs(a)>5))}
def eval_model(pair,fit,mode,locations):
    (b,bmask),(a,amask)=pair["before"],pair["after"]
    M=np.float64(fit["matrix_after_to_before"])
    h,w=b.shape
    aw=cv2.warpAffine(a,M,(w,h),flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    av=cv2.warpAffine(amask.astype("uint8"),M,(w,h),
            flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT,
            borderValue=0).astype(bool)
    valid=cv2.erode((bmask&av).astype("uint8"),np.ones((9,9),np.uint8),
                  iterations=1).astype(bool)
    cam_b=np.array([512.,512.])
    cam_a=cv2.transform(cam_b.reshape(1,1,2).astype("float32"),M)[0,0].astype(float)
    outside=valid&~disk(b.shape,cam_b,160)&~disk(b.shape,cam_a,160)
    if outside.sum()<5000:raise ValueError("insufficient off-marker calibrated pixels")
    gain=1.
    if mode=="off_marker_gain":
        gain=float(np.median(b[outside])/np.median(aw[outside]))
        if not .5<=gain<=2.:raise ValueError("bad off-marker photometric gain")
    signed=np.where(valid,b-gain*aw,0).astype(np.float32)
    blur=cv2.GaussianBlur(signed,(0,0),sigmaX=24)
    weight=cv2.GaussianBlur(valid.astype(np.float32),(0,0),sigmaX=24)
    detail=signed-blur/np.maximum(weight,1e-4)
    med=float(np.median(detail[outside]))
    sigma=float(1.4826*np.median(np.abs(detail[outside]-med)))
    if sigma<=1e-7:raise ValueError("bad original CDR noise")
    normalized=(detail-med)/sigma
    controls={}
    for rad in R:
        pts=control_centers(b.shape,rad,[cam_b,cam_a])
        pts=[np.array(z,dtype=float) for z in pts]
        vals=[local_stats(normalized,valid,z,rad) for z in pts]
        controls[str(rad)]=[z for z in vals if z["status"]=="assessable"]
    source_origin=np.array([3432.,8893.])
    candidates=[]
    for item in locations:
        pt=np.array(item["original_before_source_xy"],dtype=float)-source_origin
        if np.any(pt<24) or np.any(pt>1000):raise ValueError("paper-derived source point outside authenticated calibrated ROI")
        scores={}
        for rad in R:
            value=local_stats(normalized,valid,pt,rad)
            co=controls[str(rad)]
            if value["status"]=="assessable":
                value["control_count"]=len(co)
                value["controls_positive_fraction_at_least_target"]=sum(
                    v["fraction_positive_gt5"]>=value["fraction_positive_gt5"] for v in co)
                value["control_max_positive_fraction"]=max(
                    (v["fraction_positive_gt5"] for v in co),default=None)
                value["same_pair_controls_not_p_values"]=True
            scores[str(rad)]=value
        candidates.append({"paper_detection_fit":item["figure_fit"],
                           "source_fig_match":item["source_fit"],
                           "ratio":item["descriptor_ratio"],
                           "original_before_source_xy":item["original_before_source_xy"],
                           "calibrated_before_cutout_xy":pt.tolist(),
                           "fixed_radius_results":scores})
    # Fixed native CDR 5-MAD component audit, no optimizing for the paper.
    binary=(normalized>5)&valid
    cc,labels,stats,centroids=cv2.connectedComponentsWithStats(binary.astype("uint8"),8)
    comps=[]
    for i in range(1,cc):
        x,y,bw,bh,area=map(int,stats[i])
        if area<12:continue
        c=np.float64(centroids[i])
        if min(np.linalg.norm(c-(np.float64(z["original_before_source_xy"])-source_origin)) for z in locations)>36:continue
        comps.append({"source_roi_centroid_xy":c.tolist(),"bbox_xywh":[x,y,bw,bh],
                      "area_px":area})
    return {"model":fit["model"],"photometric_mode":mode,
            "global_gain":gain,"off_marker_MAD_gaussian_sigma_IoverF":sigma,
            "withheld_registration_p95_source_px":fit["withheld_p95_px"],
            "paper_defined_points":candidates,
            "all_native_CDR_positive_5MAD_components_within_36px_of_paper_centers":comps}
def main():
    a=argparse.ArgumentParser()
    for name in ("source_folder","source_manifest","registration","paper_audit","raw_crosswalk","out"):
        a.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    x=a.parse_args()
    meta=json.loads(x.source_manifest.read_text())
    reg=json.loads(x.registration.read_text())
    paper=json.loads(x.paper_audit.read_text())
    cross=json.loads(x.raw_crosswalk.read_text())
    if reg["source_manifest_sha256"]!=sha(x.source_manifest):
        raise ValueError("calibrated CDR registration not bound to retrieved official source")
    if cross["original_figure_sha256"]!=FIG_SHA or paper["figure_sha256"]!=FIG_SHA:
        raise ValueError("wrong published Figure S5")
    if paper["schema"] not in ("true-S5-published-panel-localized-components-audit-v2",\n                             "true-S5-published-panel-morphology-sensitivity-audit-v3"):
        raise ValueError("no independent figure component before source scoring")
    before_cases=[z for z in cross["anchored_search"]["cases"]
                  if z["role"]=="before" and z["rotation_90_ccw"]==0
                  and z["flip_after_rotation"] and z["ratio"] in (.78,.88)]
    if len(before_cases)!=2:raise ValueError("two fixed BEFORE-paper source fits missing")
    points=[]
    for fit in paper["model_trials"]:
        change=fit["scores"][0]["marker_bounded_components_threshold_5sigma_min_area_6"]["positive"]
        if not change:raise RuntimeError("paper positive not found in fixed marker window")
        # The independent paper segmentation was fixed before this CDR score.
        # Check the first-paper-component footprint is inside r100 around marker.
        observed=change[0]["centroid_original_S5_xy"]
        if change[0]["area_paper_px"]<50 or change[0]["distance_to_published_marker_paper_px"]>100:
            raise RuntimeError("no localized paper-positive component")
        for case in before_cases:
            for method in ("partial","full"):
                src=source_point(case,observed,method)
                if not np.isfinite(src).all():raise ValueError("nonfinite paper source crosswalk")
                points.append({"figure_fit":fit["model"],"source_fit":method,
                    "descriptor_ratio":case["ratio"],
                    "original_before_source_xy":src.tolist()})
    pair=read_pair(x.source_folder,meta)
    trials=[]
    for fit in reg["model_trials"]:
        if fit["status"]!="fit" or not fit["preflight_gate_passed"]:
            raise RuntimeError("predeclared source registration not assessable")
        for mode in ("native_gain_one","off_marker_gain"):
            trials.append(eval_model(pair,fit,mode,points))
    out={"schema":"published-S5-independent-component-to-NASA-calibrated-source-test-v1",
         "figure_sha256":FIG_SHA,"source_EDRs":["M1138987659LE","M1200206882LE"],
         "CDRs":["M1138987659LC","M1200206882LC"],
         "native_CDR_manifest_sha256":sha(x.source_manifest),
         "registration_sha256":sha(x.registration),
         "paper_temporal_audit_sha256":sha(x.paper_audit),
         "figure_to_source_crosswalk_sha256":sha(x.raw_crosswalk),
         "source_figure_selected_without_CDR_score":True,
         "fixed_native_source_pixel_radii":R,
         "trials":trials,"scientific_limits":[
           "Independent pixel location from original Figure S5 does not mean independent lunar observations.",
           "No original mass-wasting polygon has been independently traced.",
           "Other CDR registration models can fail even when processed-paper models pass.",
           "Off-marker controls come from same observation pair and are not p-values.",
           "No DEM-supported absolute ground control or new lunar discovery."]}
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(out,indent=2)+"\n")
    for z in trials:
        q=z["paper_defined_points"][0]["fixed_radius_results"]
        print(json.dumps({"model":z["model"],"mode":z["photometric_mode"],
             "MAD_IF":z["off_marker_MAD_gaussian_sigma_IoverF"],
             "r4":q["4"],"r12":q["12"],
             "comps":z["all_native_CDR_positive_5MAD_components_within_36px_of_paper_centers"]}),flush=True)
if __name__=="__main__":main()
