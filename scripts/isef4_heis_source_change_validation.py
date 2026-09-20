#!/usr/bin/env python3
"""Test prelocalized Heis S26 elongated figure feature on exact original CDR.

Region is frozen by published-image-only connected components and the
figure->native BEFORE source registration, NOT CDR residual strength.
Report BOTH prespecified partial/full source registrations even on failure.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import cv2,numpy as np
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(folder,manifest,role):
    d=manifest["epochs"][role]
    f=folder/(role+"_Heis_original_CDR_native_r384.npy")
    if sha(f)!=d["saved_npy_SHA256"]:raise ValueError("source digest invalid "+role)
    a=np.load(f,allow_pickle=False)
    if a.dtype!=np.int16 or a.shape!=(769,769):raise ValueError("source shape invalid")
    return a.astype("float32")*d["pixel_scale_IoverF"],a>=-32752
def mask_from_paper(paper,cross):
    rows=[z["fixed_signed_component_sweep"]["2"][0] for z in paper["two_model_results"]]
    if any(z["sign"]!="before_brighter" or z["area_original_paper_px"]<300 for z in rows):
        raise ValueError("figure-only elongated feature no longer exists")
    x0=min(z["bbox_original_S26_before_panel_xywh"][0] for z in rows)
    y0=min(z["bbox_original_S26_before_panel_xywh"][1] for z in rows)
    x1=max(z["bbox_original_S26_before_panel_xywh"][0]+z["bbox_original_S26_before_panel_xywh"][2] for z in rows)
    y1=max(z["bbox_original_S26_before_panel_xywh"][1]+z["bbox_original_S26_before_panel_xywh"][3] for z in rows)
    if [x0,y0,x1,y1]!=[188,234,257,253]:raise ValueError("non-frozen Heis paper feature")
    cases=[z for z in cross["all_cases"] if z["panel_role"]=="before" and z["orientation_ccw"]==0 and z["flipped_h"] and z["ratio"]==.76]
    if len(cases)!=1:raise ValueError("single source transform missing")
    fit=next(z for z in cases[0]["model_trials"] if z["model"]=="full_affine")
    if not fit["crosswalk_gate_passed"] or fit["inliers"]<700:raise ValueError("paper/source fit no longer passes")
    M=np.float64(fit["M_panel_trim_to_oriented_CDR"])
    figure=np.array([[x0,y0],[x1,y0],[x1,y1],[x0,y1]],float)-[16,16]
    orient=figure@M[:,:2].T+M[:,2]
    actual=np.stack([768-orient[:,0],orient[:,1]],axis=1)
    target=np.zeros((769,769),np.uint8)
    cv2.fillConvexPoly(target,np.rint(actual).astype("int32"),1)
    if not 200<target.sum()<3000:raise ValueError("paper-derived source polygon abnormal")
    return target.astype(bool),actual.tolist(),[x0,y0,x1,y1]
def disk(p,r):
    yy,xx=np.ogrid[:769,:769]
    return (xx-p[0])**2+(yy-p[1])**2<=r*r
def stat(z,valid,area):
    support=valid&area
    if support.sum()<.85*area.sum():return {"status":"inadequate_registered_CDR_support","coverage":float(support.sum()/area.sum())}
    v=z[support]
    return {"status":"assessable","n":int(v.size),"median_signed_MAD":float(np.median(v)),
       "median_abs_MAD":float(np.median(np.abs(v))),
       "fraction_positive_2_3_5_7MAD":[float(np.mean(v>t)) for t in (2,3,5,7)],
       "fraction_negative_2_3_5_7MAD":[float(np.mean(v< -t)) for t in (2,3,5,7)]}
def evaluate(data,fit,mode,target,polygon):
    (b,bv),(a,av)=data["before"],data["after"]
    M=np.float64(fit["matrix_after_to_before"])
    aw=cv2.warpAffine(a,M,(769,769),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    am=cv2.warpAffine(av.astype("uint8"),M,(769,769),
           flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)>0
    valid=cv2.erode((bv&am).astype("uint8"),np.ones((9,9),np.uint8))>0
    markers=[np.array([384.,384.]),np.array([384.,384.])@M[:,:2].T+M[:,2]]
    near=disk(markers[0],112)|disk(markers[1],112)
    expanded=cv2.dilate(target.astype("uint8"),np.ones((71,71),np.uint8))>0
    background=valid&~near&~expanded
    if background.sum()<4000:raise ValueError("calibrated source background insufficient")
    gain=1. if mode=="IoverF_no_gain" else float(np.median(b[background])/np.median(aw[background]))
    if not .5<=gain<=2:raise ValueError("unreasonable source gain")
    signed=np.where(valid,b-gain*aw,0).astype("float32")
    smoothed=cv2.GaussianBlur(signed,(0,0),sigmaX=24)
    weight=cv2.GaussianBlur(valid.astype("float32"),(0,0),sigmaX=24)
    diff=signed-smoothed/np.maximum(weight,1e-4)
    med=float(np.median(diff[background]))
    mad=float(1.4826*np.median(np.abs(diff[background]-med)))
    if mad<=1e-8:raise ValueError("source MAD zero")
    standardized=(diff-med)/mad
    center=np.mean(np.array(polygon),axis=0)
    tests=[]
    for grow in (0,8,16):
        footprint=target if grow==0 else cv2.dilate(target.astype("uint8"),
          cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*grow+1,2*grow+1)))>0
        ans=stat(standardized,valid,footprint)
        controls=[]
        for y in range(70,700,85):
            for x in range(70,700,85):
                shift=np.float32([[1,0,x-center[0]],[0,1,y-center[1]]])
                moved=cv2.warpAffine(footprint.astype("uint8"),shift,(769,769),
                          flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)>0
                if moved.sum()!=footprint.sum() or np.any(moved&(near|expanded)):continue
                c=stat(standardized,valid,moved)
                if c["status"]=="assessable":controls.append(c)
        if ans["status"]=="assessable":
            ans["same_pair_control_n"]=len(controls)
            ans["same_pair_controls_at_least_target_positive_2_3_5_7MAD"]=[
              int(sum(q["fraction_positive_2_3_5_7MAD"][i]>=ans["fraction_positive_2_3_5_7MAD"][i] for q in controls))
              for i in range(4)]
            ans["same_pair_control_max_positive_2_3_5_7MAD"]=[
              max((q["fraction_positive_2_3_5_7MAD"][i] for q in controls),default=None) for i in range(4)]
            ans["same_pair_control_rank_is_not_a_p_value"]=True
        tests.append({"dilation_original_source_px":grow,"result":ans})
    components=[]
    for threshold in (2,3,5,7):
        positive=(standardized>threshold)&valid
        n,labels,stats,cent=cv2.connectedComponentsWithStats(positive.astype("uint8"),8)
        matched=[]
        for i in range(1,n):
            intersect=int(((labels==i)&target).sum())
            if intersect<12:continue
            x,y,w,h,area=map(int,stats[i])
            matched.append({"area_original_source_px":area,"within_paper_mask_px":intersect,
               "bbox_source_cutout_xywh":[x,y,w,h],"centroid_xy":cent[i].tolist()})
        components.append({"positive_MAD":threshold,"intersecting_components":sorted(matched,key=lambda z:-z["within_paper_mask_px"])[:12]})
    return {"model":fit["model"],"source_registration_gate_passed":fit["preflight_gate_passed"],
        "photometry":mode,"gain":gain,"off_feature_MAD_IoverF":mad,
        "background_original_source_pixels":int(background.sum()),
        "fixed_paper_mask_coverage":float((target&valid).sum()/target.sum()),
        "score_at_fixed_dilations":tests,"connected_components_overlapping_figure_defined_feature":components}
def main():
    parser=argparse.ArgumentParser()
    for p in ("source_folder","source_manifest","registration","paper_temporal","crosswalk","out"):
        parser.add_argument("--"+p.replace("_","-"),required=True,type=Path)
    p=parser.parse_args()
    meta=json.loads(p.source_manifest.read_text())
    geo=json.loads(p.registration.read_text())
    pap=json.loads(p.paper_temporal.read_text())
    cross=json.loads(p.crosswalk.read_text())
    if geo["source_manifest_sha256"]!=sha(p.source_manifest) or cross["source_manifest_SHA256"]!=sha(p.source_manifest) or cross["paper_temporal_SHA256"]!=sha(p.paper_temporal):
        raise ValueError("original pair/figure evidence incompatible")
    target,poly,box=mask_from_paper(pap,cross)
    pair={role:load(p.source_folder,meta,role) for role in ("before","after")}
    out={"schema":"Heis-S26-frozen-elongated-figure-on-original-calibrated-CDR-v1",
      "source_manifest_SHA256":sha(p.source_manifest),
      "registration_SHA256":sha(p.registration),
      "paper_temporal_SHA256":sha(p.paper_temporal),
      "figure_CDR_crosswalk_SHA256":sha(p.crosswalk),
      "original_figure_before_panel_bbox_xyxy":box,
      "original_before_NAC_cutout_polygon_xy":poly,
      "frozen_native_paper_polygon_area_px":int(target.sum()),
      "all_registrations_and_photometries":[evaluate(pair,g,m,target,poly)
         for g in geo["model_trials"] for m in ("IoverF_no_gain","off_marker_gain")],
      "limits":["Original published positive; not an independent new lunar observation.",
        "Relatively source-affine registered pixels do not establish absolute DEM geodesy.",
        "Same-pair controls do not justify statistical p-values, landslide classification or geographical recall."]}
    p.out.parent.mkdir(parents=True,exist_ok=True)
    p.out.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({"paper_mask_area":int(target.sum()),
      "trials":[{"model":r["model"],"mode":r["photometry"],"MAD":r["off_feature_MAD_IoverF"],
        "region":r["score_at_fixed_dilations"][0]} for r in out["all_registrations_and_photometries"]]},indent=2),flush=True)
if __name__=="__main__":main()
