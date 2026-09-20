#!/usr/bin/env python3
"""True non-impact Heis Supplementary Figure S26 paper temporal baseline.

Independent published positive on a designated development target. Do not
confuse paper-assigned endogenic hypothesis with proven triggering mechanism.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path
import cv2
import numpy as np

SOURCE_SHA="132f3d2c2d6c8a5fcb102fe9dcfa5e2d33c6e60b6600c1c94d0d2bafb282c233"
FIG_SHA="1e642c9ebf0f0716cecef1141f52f2d8fd7c2e274ad806a07447f8012dee3ea8"
def get_s26(path):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SOURCE_SHA:
        with zipfile.ZipFile(io.BytesIO(data)) as outer:
            data=outer.read("nwaf384_supplemental_files.zip")
    if hashlib.sha256(data).hexdigest()!=SOURCE_SHA:
        raise ValueError("not authentic supplemental original ZIP")
    with zipfile.ZipFile(io.BytesIO(data)) as arc:
        doc=arc.read("2025-434-supplementarymaterials.docx")
    with zipfile.ZipFile(io.BytesIO(doc)) as word:
        jpg=word.read("word/media/image26.jpeg")
    if hashlib.sha256(jpg).hexdigest()!=FIG_SHA:
        raise ValueError("not genuine preceding-caption S26 Figure")
    im=cv2.imdecode(np.frombuffer(jpg,np.uint8),cv2.IMREAD_COLOR)
    if im is None or im.shape[:2]!=(469,1430):
        raise ValueError("wrong S26 original figure shape")
    return im
def label_free(image):
    hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
    return (hsv[:,:,1]<85)&(hsv[:,:,2]>7)&(hsv[:,:,2]<247)
def model(b,a,xb,xa,train,held,method):
    fn=cv2.estimateAffinePartial2D if method=="partial_affine" else cv2.estimateAffine2D
    cv2.setRNGSeed(20260919)
    M,inliers=fn(xb[train].astype(np.float32),xa[train].astype(np.float32),
                 method=cv2.RANSAC,ransacReprojThreshold=2.0,maxIters=14000,
                 confidence=.999,refineIters=30)
    if M is None or inliers is None or inliers.sum()<100:
        raise RuntimeError("not a usable known-figure registration "+method)
    errors=np.linalg.norm(xb[held]@M[:,:2].T+M[:,2]-xa[held],axis=1)
    h,w=b.shape[:2]
    inv=cv2.invertAffineTransform(M)
    grayb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY).astype(np.float32)
    gray_a=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY).astype(np.float32)
    warped=cv2.warpAffine(gray_a,inv,(w,h),flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    valid=label_free(b)&(cv2.warpAffine(label_free(a).astype("uint8"),inv,(w,h),
                         flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT,borderValue=0)>0)
    valid[:20]=False;valid[-20:]=False;valid[:,:20]=False;valid[:,-20:]=False
    # The published scale bars and printed panel letters are graphics, not lunar
    # surface. Exclude their fixed corner regions from both noise and detections.
    valid[-75:]=False;valid[:,-75:]=False;valid[:55,:55]=False
    if valid.sum()<70000:
        raise RuntimeError("insufficient non-graphic paper surface")
    signed=np.where(valid,grayb-warped,0).astype(np.float32)
    smooth=cv2.GaussianBlur(signed,(0,0),sigmaX=24)
    weight=cv2.GaussianBlur(valid.astype(np.float32),(0,0),sigmaX=24)
    detail=signed-smooth/np.maximum(weight,.01)
    median=float(np.median(detail[valid]))
    sigma=float(1.4826*np.median(np.abs(detail[valid]-median)))
    if sigma<=.1:raise RuntimeError("invalid publication-figure MAD")
    z=(detail-median)/sigma
    all_components={}
    for th in (2,3,4,5):
        rows=[]
        for sign,sel in (("before_brighter",z>th),("after_brighter",z< -th)):
            n,labels,stats,cent=cv2.connectedComponentsWithStats((sel&valid).astype("uint8"),8)
            for i in range(1,n):
                x,y,wid,hei,area=map(int,stats[i])
                if area<12:continue
                cx,cy=map(float,cent[i])
                coords=np.column_stack(np.where(labels==i))[:,::-1].astype(float)
                eig=np.linalg.eigvalsh(np.cov(coords,rowvar=False)) if len(coords)>1 else np.array([1.,1.])
                ratio=float(np.sqrt((max(eig[-1],0)+1e-6)/(max(eig[0],0)+1e-6)))
                rows.append({"sign":sign,
                    "centroid_original_S26_before_panel_xy":[cx+16,cy+16],
                    "bbox_original_S26_before_panel_xywh":[x+16,y+16,wid,hei],
                    "area_original_paper_px":area,"PCA_elongation":ratio})
        all_components[str(th)]=sorted(rows,key=lambda r:-r["area_original_paper_px"])[:40]
    return {"model":method,"training_inliers":int(inliers.sum()),
        "training_tentative":int(train.sum()),"spatial_withheld_matches":int(held.sum()),
        "withheld_median_px":float(np.median(errors)),"withheld_p95_px":float(np.percentile(errors,95)),
        "matrix_before_to_after":M.tolist(),"noise_graylevel_MAD":sigma,
        "fixed_signed_component_sweep":all_components}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--supplement-artifact",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    image=get_s26(args.supplement_artifact)
    b=image[16:-16,16:round(1430/3)-16]
    a=image[16:-16,round(1430/3)+16:round(2*1430/3)-16]
    clahe=cv2.createCLAHE(clipLimit=2,tileGridSize=(8,8))
    sift=cv2.SIFT_create(nfeatures=10000,contrastThreshold=.007,edgeThreshold=18,sigma=1.3)
    bk,bd=sift.detectAndCompute(clahe.apply(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY)),None)
    ak,ad=sift.detectAndCompute(clahe.apply(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY)),None)
    pairs=cv2.BFMatcher(cv2.NORM_L2).knnMatch(bd,ad,k=2)
    good=[u for u,v in pairs if u.distance<.78*v.distance]
    xb=np.float64([bk[m.queryIdx].pt for m in good])
    xa=np.float64([ak[m.trainIdx].pt for m in good])
    # Exclude author yellow annotation near (190,205) from image fitting.
    off=(np.linalg.norm(xb-np.array([174.,188.]),axis=1)>24)&(
        np.linalg.norm(xa-np.array([174.,188.]),axis=1)>24)
    xb,xa=xb[off],xa[off]
    cellx=np.clip((xb[:,0]/b.shape[1]*8).astype(int),0,7)
    celly=np.clip((xb[:,1]/b.shape[0]*8).astype(int),0,7)
    withheld=(17*cellx+7*celly)%5==0
    result={"schema":"Heis-S26-real-published-nonimpact-temporal-baseline-v1",
        "development_only":True,"source_figure":"real original image26.jpeg before S26 caption",
        "figure_sha256":FIG_SHA,
        "exact_original_EDRs":["M1197976848LE","M1376643242LE"],
        "original_event_coordinate_N_E360":[32.547,327.792],
        "paper_triggering_mechanism":"endogenic activity (author interpretation, not independently demonstrated)",
        "registration_ratio":.78,"annotation_mask":"saturation and fixed corner exclusions",
        "fixed_thresholds_MAD":[2,3,4,5],"connected_min_area_paper_px":12,
        "two_model_results":[model(b,a,xb,xa,~withheld,withheld,m)
                            for m in ("partial_affine","full_affine")],
        "limitations":["Paper pixels are processed, not calibrated original NASA pixels.",
                       "The paper attributed a mechanism; this code does not establish lunar quakes.",
                       "No geographic holdout source pixels opened or new landslide discovered.",
                       "More than one connected region may be shadow, residual warp or processing artifact."]}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+"\n")
    for row in result["two_model_results"]:
        print(json.dumps({"model":row["model"],"inliers":row["training_inliers"],
              "holdout":row["withheld_median_px"],"2MAD":row["fixed_signed_component_sweep"]["2"][:3],
              "3MAD":row["fixed_signed_component_sweep"]["3"][:3]}),flush=True)
if __name__=="__main__":main()
