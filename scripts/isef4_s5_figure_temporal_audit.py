#!/usr/bin/env python3
"""Independent published S5 before/after temporal check at prelocalized native-CDR residual.

Uses *only* the original, verified published image, not the author's ratio panel
for model fitting. This is a known-positive developmental concordance test and
cannot validate a new discovery, lunar geodesy or original landslide morphology.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import zipfile
from pathlib import Path
import cv2
import numpy as np

ZIP_SHA="132f3d2c2d6c8a5fcb102fe9dcfa5e2d33c6e60b6600c1c94d0d2bafb282c233"
FIG_SHA="3d0e494c40b92e7de66ce54f8317c646ad1d8a19e328bc2811cd7cc13d48dc7f"
# Figure S5 native-CDR full-affine-only residual. Not the published event center.
PAPER_RESIDUAL=(162.8151412412844,319.91052926398964)
PAPER_CAMERA_B=(208.3038669751132,263.52804575669654)
PAPER_CAMERA_A=(628.4925337010993,267.2780565047147)
R=(6,12,24,36)
def sha(x):return hashlib.sha256(x).hexdigest()
def source_figure(path):
    raw=path.read_bytes()
    if sha(raw)!=ZIP_SHA:
        with zipfile.ZipFile(io.BytesIO(raw)) as outer:
            raw=outer.read("nwaf384_supplemental_files.zip")
    if sha(raw)!=ZIP_SHA:raise ValueError("published supplemental ZIP SHA-256 failed")
    with zipfile.ZipFile(io.BytesIO(raw)) as outer:
        doc=outer.read("2025-434-supplementarymaterials.docx")
    with zipfile.ZipFile(io.BytesIO(doc)) as outer:
        jpg=outer.read("word/media/image5.jpeg") # image BEFORE S5 caption
    if sha(jpg)!=FIG_SHA:raise ValueError("real S5 image5.jpeg hash invalid")
    figure=cv2.imdecode(np.frombuffer(jpg,np.uint8),cv2.IMREAD_COLOR)
    if figure is None or figure.shape[:2]!=(469,1430):raise ValueError("wrong published S5 shape")
    return figure
def panel(figure,role):
    i=0 if role=="before" else 1
    a,b=round(i*figure.shape[1]/3),round((i+1)*figure.shape[1]/3)
    return figure[16:-16,a+16:b-16]
def pcoord(point,role):
    return np.array([point[0]-16-(0 if role=="before" else round(1430/3)),point[1]-16],np.float64)
def clip_mask(rgb):
    hsv=cv2.cvtColor(rgb,cv2.COLOR_BGR2HSV)
    # Restrict colored paper arrows and saturated graphic overlays, not geology.
    return (hsv[:,:,1]<85)&(hsv[:,:,2]>7)&(hsv[:,:,2]<247)
def pair_match(before,after):
    sift=cv2.SIFT_create(nfeatures=10000,contrastThreshold=.007,
                         edgeThreshold=18,sigma=1.3)
    clahe=cv2.createCLAHE(clipLimit=2,tileGridSize=(8,8))
    bk,bd=sift.detectAndCompute(clahe.apply(cv2.cvtColor(before,cv2.COLOR_BGR2GRAY)),None)
    ak,ad=sift.detectAndCompute(clahe.apply(cv2.cvtColor(after,cv2.COLOR_BGR2GRAY)),None)
    raw=cv2.BFMatcher(cv2.NORM_L2).knnMatch(bd,ad,k=2)
    good=[m for m,n in raw if m.distance<.78*n.distance]
    b=np.float64([bk[m.queryIdx].pt for m in good]);a=np.float64([ak[m.trainIdx].pt for m in good])
    candidate=pcoord(PAPER_RESIDUAL,"before")
    markerb=pcoord(PAPER_CAMERA_B,"before")
    markera=pcoord(PAPER_CAMERA_A,"after")
    allowed=(np.linalg.norm(b-candidate,axis=1)>45)&(np.linalg.norm(b-markerb,axis=1)>34)&(np.linalg.norm(a-markera,axis=1)>34)
    b,a=b[allowed],a[allowed]
    if len(b)<50:raise RuntimeError("too few independent off-candidate S5 figure matches")
    # Spatial cell holdout; neither candidate region nor camera-marker region trained.
    bx=np.clip((b[:,0]/before.shape[1]*8).astype(int),0,7)
    by=np.clip((b[:,1]/before.shape[0]*8).astype(int),0,7)
    withheld=(17*bx+7*by)%5==0
    return b,a,withheld
def fit(before,after,withheld,model):
    method=cv2.estimateAffinePartial2D if model=="partial_affine" else cv2.estimateAffine2D
    cv2.setRNGSeed(20260919)
    M,mask=method(before[~withheld].astype(np.float32),after[~withheld].astype(np.float32),
                  method=cv2.RANSAC,ransacReprojThreshold=2.0,maxIters=14000,
                  confidence=.999,refineIters=30)
    if M is None or mask is None or mask.sum()<50:raise RuntimeError("no reproducible off-candidate model "+model)
    error=np.linalg.norm(before[withheld]@M[:,:2].T+M[:,2]-after[withheld],axis=1)
    return M,{"model":model,"training":int((~withheld).sum()),
        "training_inliers":int(mask.sum()),"withheld":int(withheld.sum()),
        "withheld_median_px":float(np.median(error)),
        "withheld_p95_px":float(np.percentile(error,95)),
        "matrix_before_to_after":M.tolist()}
def score(before,after,mask,model,which,M):
    h,w=before.shape[:2]
    gray_b=cv2.cvtColor(before,cv2.COLOR_BGR2GRAY).astype(np.float32)
    gray_a=cv2.cvtColor(after,cv2.COLOR_BGR2GRAY).astype(np.float32)
    corrected=cv2.warpAffine(gray_a,cv2.invertAffineTransform(M),(w,h),
                    flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    valid=cv2.warpAffine(clip_mask(after).astype("uint8"),cv2.invertAffineTransform(M),(w,h),
                    flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT,borderValue=0)>0
    valid&=clip_mask(before)
    valid[:20]=False;valid[-20:]=False;valid[:,:20]=False;valid[:,-20:]=False
    candidate=pcoord(PAPER_RESIDUAL,"before")
    marker=pcoord(PAPER_CAMERA_B,"before")
    yy,xx=np.indices((h,w))
    rad=lambda p:np.hypot(xx-p[0],yy-p[1])
    excluded=(rad(candidate)<50)|(rad(marker)<50)
    background=valid&~excluded
    if background.sum()<20000:raise RuntimeError("insufficient S5 paper background")
    gain=float(np.median(gray_b[background])/np.median(corrected[background]))
    if not .5<=gain<=2.:raise RuntimeError("bad figure photometric gain")
    signed=gray_b-corrected*(gain if which=="median_gain" else 1.)
    # Remove broad image-processing differences, not localized change; fixed sigma.
    blur=cv2.GaussianBlur(signed,(0,0),sigmaX=24)
    weights=cv2.GaussianBlur(valid.astype(np.float32),(0,0),sigmaX=24)
    detail=signed-blur/np.maximum(weights,.01)
    med=float(np.median(detail[background]))
    sigma=float(1.4826*np.median(np.abs(detail[background]-med)))
    if sigma<.1:raise RuntimeError("degenerate published-image robust sigma")
    normalized=(detail-med)/sigma
    centers=[(x,y) for y in range(52,h-52,52) for x in range(52,w-52,52)
             if math.dist((x,y),candidate)>100 and math.dist((x,y),marker)>85]
    def windows_at(point):
        result={}
        for radius in R:
            inside=(rad(point)<=radius)
            coverage=float((inside&valid).sum()/max(1,inside.sum()))
            if coverage<.65:
                result[str(radius)]={"coverage":coverage,"status":"unassessable"};continue
            v=normalized[inside&valid]
            result[str(radius)]={"coverage":coverage,"signed_median_sigma":float(np.median(v)),
                 "absolute_median_sigma":float(np.median(np.abs(v))),
                 "fraction_abs_above_5sigma":float(np.mean(np.abs(v)>5)),
                 "fraction_positive_above_5sigma":float(np.mean(v>5)),
                 "fraction_negative_below_minus_5sigma":float(np.mean(v< -5))}
        return result
    target=windows_at(candidate)
    control=[windows_at(pt) for pt in centers]
    for radius in R:
        k=str(radius);row=target[k]
        if row.get("status"):continue
        co=[c[k]["fraction_abs_above_5sigma"] for c in control if "fraction_abs_above_5sigma" in c[k]]
        row["background_control_count"]=len(co)
        row["background_control_at_least_candidate"]=int(sum(v>=row["fraction_abs_above_5sigma"] for v in co))
        row["background_control_max_fraction"]=max(co) if co else None
        row["control_rank_is_not_a_pvalue"]=True
    # Independently enumerate complete positive/negative difference components in
    # the published paper, without centering connected-component search on the
    # earlier CDR residual. Use the published marker as the bounded target.
    component_summary={}
    for sign,selection in (("positive",normalized>5),("negative",normalized< -5)):
        number,labels,stats,centroids=cv2.connectedComponentsWithStats(
            (selection&valid).astype(np.uint8),8)
        rows=[]
        for i in range(1,number):
            x,y,ww,hh,area=map(int,stats[i])
            if area<6:continue
            px,py=map(float,centroids[i])
            if math.dist((px,py),marker)>110:continue
            rows.append({"centroid_original_S5_xy":[px+16,py+16],
                         "bbox_original_S5_xywh":[x+16,y+16,ww,hh],
                         "area_paper_px":area,
                         "distance_to_CDR_residual_paper_px":math.dist((px,py),candidate),
                         "distance_to_published_marker_paper_px":math.dist((px,py),marker),
                         "candidate_point_inside_component":bool(
                           0<=int(round(candidate[1]))<h and
                           0<=int(round(candidate[0]))<w and
                           labels[int(round(candidate[1])),int(round(candidate[0]))]==i)})
        component_summary[sign]=sorted(rows,key=lambda z:-z["area_paper_px"])
    # Fixed sensitivity sweep to determine whether the localized paper change
    # grows into an extended runout-like component or remains a compact scar.
    # This remains purely morphology *of paper contrast*, not a rockslide label.
    threshold_sweep={}
    for factor in (2,3,4,5):
        fixed={}
        for sign,selection in (("positive",normalized>factor),("negative",normalized< -factor)):
            number,labels,stats,centroids=cv2.connectedComponentsWithStats(
                (selection&valid).astype(np.uint8),8)
            rows=[]
            for i in range(1,number):
                x,y,bw,bh,area=map(int,stats[i])
                if area<12:continue
                cx,cy=map(float,centroids[i])
                if math.dist((cx,cy),marker)>110:continue
                component_xy=np.column_stack(np.where(labels==i))[:,::-1].astype(float)
                if len(component_xy)>1:
                    cov=np.cov(component_xy,rowvar=False)
                    eig=np.maximum(np.linalg.eigvalsh(cov),0)
                    elongation=float(np.sqrt((eig[-1]+1e-6)/(eig[0]+1e-6)))
                else:
                    elongation=1.0
                rows.append({"centroid_original_S5_xy":[cx+16,cy+16],
                    "bbox_original_S5_xywh":[x+16,y+16,bw,bh],
                    "area_paper_px":area,"elongation_covariance_axis_ratio":elongation,
                    "centroid_distance_to_calibrated_residual_paper_px":math.dist((cx,cy),candidate),
                    "centroid_distance_to_published_marker_paper_px":math.dist((cx,cy),marker),
                    "contains_prelocalized_CDR_residual_point":bool(
                        labels[int(round(candidate[1])),int(round(candidate[0]))]==i)})
            fixed[sign]=sorted(rows,key=lambda z:-z["area_paper_px"])[:25]
        threshold_sweep[str(factor)]=fixed
    return {"registration":model,"photometry":which,"gain":gain,
            "marker_bounded_component_sensitivity_at_fixed_2_3_4_5MAD":threshold_sweep,
            "marker_bounded_components_threshold_5sigma_min_area_6":component_summary,
            "published_paper_noise_gray_level":sigma,
            "valid_fraction":float(valid.mean()),
            "candidate_point_full_S5_xy":PAPER_RESIDUAL,
            "candidate_point_before_panel_trimmed_xy":candidate.tolist(),
            "nominal_before_camera_marker_full_S5_xy":PAPER_CAMERA_B,
            "target_fixed_radius_windows":target,
            "camera_marker_windows":windows_at(marker),
            "same_pair_spatial_control_count":len(centers)}
def main():
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    figure=source_figure(args.source)
    before=panel(figure,"before");after=panel(figure,"after")
    if before.shape[0]!=437 or after.shape[0]!=437:raise ValueError("bad panel")
    b,a,withheld=pair_match(before,after)
    trials=[]
    for model in ("partial_affine","full_affine"):
        M,info=fit(b,a,withheld,model)
        info["scores"]=[score(before,after,None,model,mode,M) for mode in ("raw_gray","median_gain")]
        trials.append(info)
    data={"schema":"true-S5-published-panel-morphology-sensitivity-audit-v3",
          "source":"Xiao et al. 2025 real Figure S5 image5.jpeg",
          "figure_sha256":FIG_SHA,
          "scoring_policy":"fixed candidate from earlier CALIBRATED full-affine-only CDR residual, NOT trained on paper difference",
          "fixed_window_radii_paper_pixels":R,"excluded_from_training":{
             "candidate_radius_paper_pixels":45,"camera_marker_radius_before_after":34},
          "independent_background": "same-figure off-marker, off-candidate windows; NOT statistical independent events",
          "figure_panel_match":{"tentative_off_candidate":len(b),
              "spatial_withheld":int(withheld.sum()),"frozen_ratio":.78,
              "frozen_fit_RANSAC_threshold_px":2.0},
          "model_trials":trials,
          "scientific_limits":["Published panels may include different crops/arrows and author processing.",
             "Neither ratio panel nor publication labels were used to fit the temporal registration.",
             "Residual location comes from a model-dependent calibrated change candidate.",
             "Paper concordance alone cannot identify landslide vs impact vs shadow.",
             "No independent DEM or ground control, no new lunar event, no scientific recovery claim."]}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({"fits":[{"model":x["model"],"train":x["training_inliers"],
         "withheld":x["withheld_median_px"],
         "candidate_24px":[{"mode":s["photometry"],"values":s["target_fixed_radius_windows"]["24"]}
                           for s in x["scores"]]} for x in trials]}),flush=True)
if __name__=="__main__":main()
