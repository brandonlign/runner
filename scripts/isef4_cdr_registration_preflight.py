#!/usr/bin/env python3
"""Calibrated, camera-grounded Gambart C pair: registration feasibility only.

Published positive, development-only. The two input CDR patches are ORIGINAL
NASA source-coordinate I/F, not map-projected images. Neither a feature-fit
nor a photometric difference is geological event recovery.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np

ROLES={"before":"M1138987659LC","after":"M1200206882LC"}
EVENT=(512.,512.)
EXCLUSION=160.
RATIO=.75


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(folder,manifest,role):
    row=manifest["epochs"][role]
    if row["cdr_product"]!=ROLES[role] or row["roi_shape_hw"]!=[1025,1025]:
        raise ValueError("unverified calibrated source image "+role)
    path=folder/(role+"_official_cdr_if_r512_original_source.npy")
    if sha(path)!=row["saved_roi_npy_sha256"]:
        raise ValueError("CDR artifact SHA differs from live-source manifest")
    im=np.load(path,allow_pickle=False)
    if im.shape!=(1025,1025) or im.dtype!=np.int16:
        raise ValueError("original CDR source I/F array shape/type changed")
    valid=(im>=-32752)
    if valid.mean()<.85:
        raise ValueError("too much unassessable CDR original source terrain")
    return im.astype(np.float32)*float(row["scaling_factor"]),valid


def view(image,valid):
    q=np.percentile(image[valid],[1,99])
    if q[1]<=q[0]:raise ValueError("degenerate CDR reflectance image")
    x=np.clip((image-q[0])*255/(q[1]-q[0]),0,255).astype(np.uint8)
    x[~valid]=0
    return cv2.createCLAHE(clipLimit=2.,tileGridSize=(8,8)).apply(x)


def cell(pt):
    return (min(7,int(pt[0]*8/1025)),min(7,int(pt[1]*8/1025)))


def assess(name,src,dst,train,withheld):
    row={"model":name,"training_tentative":int(train.sum()),
         "withheld_tentative":int(withheld.sum())}
    if train.sum()<20:return row,None
    cv2.setRNGSeed(20260919)
    fit=(cv2.estimateAffinePartial2D if name=="partial_affine"
         else cv2.estimateAffine2D)
    M,mask=fit(src[train],dst[train],
               method=cv2.RANSAC,ransacReprojThreshold=3.,
               confidence=.999,maxIters=15000,refineIters=20)
    if M is None or mask is None:
        row["status"]="ransac_failed"
        return row,None
    good=mask.ravel().astype(bool)
    train_pts=dst[train][good]
    row["inliers"]=int(good.sum())
    row["inlier_cells_8x8"]=len(set(cell(xy) for xy in train_pts))
    row["near_marker_annulus_inliers_160_to_350px"]=int(np.sum(
        (np.linalg.norm(train_pts-np.asarray(EVENT),axis=1)<350)))
    predicted=cv2.transform(src[withheld].reshape(-1,1,2),M).reshape(-1,2)
    errors=np.linalg.norm(predicted-dst[withheld],axis=1)
    row["withheld_median_px"]=float(np.median(errors)) if errors.size else None
    row["withheld_p95_px"]=float(np.percentile(errors,95)) if errors.size else None
    row["withheld_fraction_under_3px"]=float(np.mean(errors<3)) if errors.size else None
    target=cv2.transform(np.float32([[EVENT]]),M)[0,0]
    row["mapped_after_camera_marker_in_before_crop"]=target.tolist()
    row["camera_marker_discordance_px"]=float(np.linalg.norm(target-EVENT))
    row["matrix_after_to_before"]=M.tolist()
    row["status"]="fit"
    row["preflight_gate_passed"]=bool(
        row["inliers"]>=50 and row["inlier_cells_8x8"]>=10
        and row["near_marker_annulus_inliers_160_to_350px"]>=5
        and errors.size>=20 and np.median(errors)<2
        and np.percentile(errors,95)<5)
    return row,M


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-folder",type=Path,required=True)
    p.add_argument("--source-manifest",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    metadata=json.loads(x.source_manifest.read_text())
    if metadata.get("schema")!="exact-Gambart-C-two-epoch-native-CDR-r512-v1":
        raise ValueError("not independently verified original calibrated pair")
    b,bmask=load(x.source_folder,metadata,"before")
    a,amask=load(x.source_folder,metadata,"after")
    B,A=view(b,bmask),view(a,amask)
    sift=cv2.SIFT_create(nfeatures=6000,contrastThreshold=.01)
    kp_b,desc_b=sift.detectAndCompute(B,bmask.astype(np.uint8)*255)
    kp_a,desc_a=sift.detectAndCompute(A,amask.astype(np.uint8)*255)
    if desc_a is None or desc_b is None:
        raise ValueError("no calibrated terrain features")
    raw=cv2.BFMatcher(cv2.NORM_L2).knnMatch(desc_a,desc_b,k=2)
    matches=[m for pair in raw if len(pair)==2 for m,n in [pair]
             if m.distance<RATIO*n.distance]
    src=np.float32([kp_a[m.queryIdx].pt for m in matches]).reshape(-1,2)
    dst=np.float32([kp_b[m.trainIdx].pt for m in matches]).reshape(-1,2)
    if len(src)<35:raise ValueError("no defensible real CDR correspondences")
    bdist=np.linalg.norm(dst-np.asarray(EVENT),axis=1)
    adist=np.linalg.norm(src-np.asarray(EVENT),axis=1)
    outside=(bdist>EXCLUSION)&(adist>EXCLUSION)
    cells=[cell(pt) for pt in dst]
    held=np.array([(17*u+7*v)%5==0 for u,v in cells])
    train=outside&~held
    test=outside&held
    fitted=[]
    for name in ("partial_affine","full_affine"):
        row,M=assess(name,src,dst,train,test)
        fitted.append(row)
    result={
        "schema":"known-published-Gambart-C-CDR-native-registration-preflight-v1",
        "published_marker_lat_lon_e360":[3.218,348.092],
        "source_manifest_sha256":sha(x.source_manifest),
        "source_patch_sha256":{
           role:metadata["epochs"][role]["saved_roi_npy_sha256"]
           for role in ROLES},
        "source_status":"two REAL camera-grounded calibrated original NASA CDR images; not in common map",
        "features":{"before":len(kp_b),"after":len(kp_a),
                    "ratio_filtered":len(src),
                    "outside_source_markers":int(outside.sum()),
                    "training":int(train.sum()),
                    "withheld_spatial_controls":int(test.sum()),
                    "predeclared_exclusion_radius_source_px":EXCLUSION,
                    "eight_by_eight_spatial_holdout":"(17*xcell+7*ycell)%5==0"},
        "model_trials":fitted,
        "interpretation":"No landslide recovery, illumination-invariant detection, geographical holdout or novel lunar event is claimed. Source cameras were validated independently, but an affine pixel registration is not absolute lunar geolocation.",
    }
    x.out.parent.mkdir(parents=True,exist_ok=True)
    x.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"result":str(x.out),"features":result["features"],
                      "trials":fitted,"no_discovery":True},indent=2))


if __name__=="__main__":
    main()
