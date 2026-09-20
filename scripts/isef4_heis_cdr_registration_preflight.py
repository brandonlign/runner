#!/usr/bin/env python3
"""Original calibrated Heis S26 scene registration, *before* looking at residuals.

Fixed off-published-marker SIFT/RANSAC. Both partial/full models reported with
spatial terrain holdouts. Exact source-patch digest and PDS ID gates.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np

ROLES={"before":"M1197976848LC","after":"M1376643242LC"}
CENTER=np.array([384.,384.])
EXCLUDE=112
RATIO=.78
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def image(path,meta,role):
    info=meta["epochs"][role]
    if info["CDR_id"]!=ROLES[role] or info["native_source_roi_xyxy_exclusive"][2]-info["native_source_roi_xyxy_exclusive"][0]!=769:
        raise ValueError("not authentic published calibrated Heis source")
    f=path/(role+"_Heis_original_CDR_native_r384.npy")
    if sha(f)!=info["saved_npy_SHA256"]:raise ValueError("original Heis CDR SHA mismatch")
    img=np.load(f,allow_pickle=False)
    if img.shape!=(769,769) or img.dtype!=np.int16:raise ValueError("bad original native CDR")
    valid=img>=-32752
    if valid.mean()<.90:raise ValueError("CDR validity failed")
    return img.astype(np.float32)*info["pixel_scale_IoverF"],valid
def view(img,mask):
    a,b=np.percentile(img[mask],[1,99])
    if b<=a:raise ValueError("degenerate original CDR reflectance")
    gray=np.uint8(np.rint(np.clip((img-a)*255/(b-a),0,255)))
    gray[~mask]=0
    return cv2.createCLAHE(clipLimit=2,tileGridSize=(8,8)).apply(gray)
def assess(src,dst,train,test,name):
    est=cv2.estimateAffinePartial2D if name=="partial_affine" else cv2.estimateAffine2D
    row={"model":name,"source":"after_CDR","target":"before_CDR",
         "training":int(train.sum()),"withheld":int(test.sum())}
    if train.sum()<40 or test.sum()<20:
        return dict(row,status="too_few_spatial_matches",preflight_gate_passed=False)
    cv2.setRNGSeed(20260920)
    M,mask=est(src[train].astype("float32"),dst[train].astype("float32"),
       method=cv2.RANSAC,ransacReprojThreshold=3.0,
       maxIters=15000,confidence=.999,refineIters=35)
    if M is None or mask is None:
        return dict(row,status="no_ransac_consensus",preflight_gate_passed=False)
    kept=mask.reshape(-1).astype(bool)
    predicted=src[test]@M[:,:2].T+M[:,2]
    err=np.linalg.norm(predicted-dst[test],axis=1)
    inlier_pts=dst[train][kept]
    cell=lambda xy:(np.clip((xy[:,0]*8/769).astype(int),0,7),
                   np.clip((xy[:,1]*8/769).astype(int),0,7))
    cc=cell(inlier_pts)
    ann=np.linalg.norm(inlier_pts-CENTER,axis=1)
    moved=CENTER@M[:,:2].T+M[:,2]
    row.update({"status":"fit","inliers":int(kept.sum()),
        "train_fraction":float(kept.mean()),
        "inlier_cells_8by8":len(set(zip(cc[0],cc[1]))),
        "near_marker_annulus_inliers_112_to_290px":int(np.sum((ann>EXCLUDE)&(ann<290))),
        "withheld_median_before_px":float(np.median(err)),
        "withheld_p95_before_px":float(np.percentile(err,95)),
        "withheld_fraction_under_3px":float(np.mean(err<3)),
        "matrix_after_to_before":M.tolist(),
        "mapped_after_camera_marker_before_crop_xy":moved.tolist(),
        "discordance_of_both_nominal_ground_markers_source_px":float(np.linalg.norm(moved-CENTER))})
    row["preflight_gate_passed"]=bool(row["inliers"]>=75 and row["inlier_cells_8by8"]>=10
        and row["near_marker_annulus_inliers_112_to_290px"]>=10
        and len(err)>=20 and np.median(err)<2 and np.percentile(err,95)<5)
    return row
def main():
    p=argparse.ArgumentParser()
    for x in ("source_folder","source_manifest","out"):
        p.add_argument("--"+x.replace("_","-"),type=Path,required=True)
    args=p.parse_args()
    meta=json.loads(args.source_manifest.read_text())
    if meta.get("schema")!="isef4-Heis-S26-source-grounded-original-CDR-r384-v1" or len(meta.get("epochs",{}))!=2:
        raise ValueError("both original camera-calibrated Heis sources not verified")
    b,bvalid=image(args.source_folder,meta,"before")
    a,avalid=image(args.source_folder,meta,"after")
    sift=cv2.SIFT_create(nfeatures=8500,contrastThreshold=.007,edgeThreshold=15,sigma=1.25)
    bk,bd=sift.detectAndCompute(view(b,bvalid),bvalid.astype("uint8")*255)
    ak,ad=sift.detectAndCompute(view(a,avalid),avalid.astype("uint8")*255)
    if ad is None or bd is None:raise ValueError("no source terrain features")
    tentative=cv2.BFMatcher(cv2.NORM_L2).knnMatch(ad,bd,k=2)
    good=[x for pair in tentative if len(pair)==2 for x,y in [pair] if x.distance<RATIO*y.distance]
    src=np.float64([ak[m.queryIdx].pt for m in good])
    dst=np.float64([bk[m.trainIdx].pt for m in good])
    off=(np.linalg.norm(src-CENTER,axis=1)>EXCLUDE)&(np.linalg.norm(dst-CENTER,axis=1)>EXCLUDE)
    # Also avoid invalid terrain margin for image registration.
    cells=np.clip((dst/769*8).astype(int),0,7)
    hold=(17*cells[:,0]+7*cells[:,1])%5==0
    train=off&~hold;test=off&hold
    results=[assess(src,dst,train,test,name) for name in ("partial_affine","full_affine")]
    out={"schema":"Heis-S26-original-source-native-CDR-registration-v1",
         "source_manifest_sha256":sha(args.source_manifest),
         "published_coordinate":[32.547,327.792],
         "source_image_products":ROLES,
         "source_image_sha256":{r:meta["epochs"][r]["saved_npy_SHA256"] for r in ROLES},
         "predeclared_camera_marker_crop_xy":CENTER.tolist(),
         "ratio":RATIO,"exclusion_radius_around_BOTH_rounded_camera_markers_px":EXCLUDE,
         "heldout_rule":"(17*before_xcell+7*before_ycell)%5==0, eight-by-eight grid",
         "features":{"before":len(bk),"after":len(ak),
             "ratio_tentative":len(good),"outside_markers":int(off.sum()),
             "train":int(train.sum()),"withheld":int(test.sum())},
         "model_trials":results,
         "scientific_limits":["Different native source-pixel scales and lunar terrain parallax remain.",
           "Rounded published coordinate may not be unique physical terrain point at correct relief.",
           "Source-pixel affine is NOT an independent geodesy/DEM registration.",
           "Spatial withholding within SAME pair is not independent event validation.",
           "Registration only: no photo residual was inspected or event recovered."]}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({"features":out["features"],"models":results},indent=2),flush=True)
if __name__=="__main__":main()
