#!/usr/bin/env python3
"""Heis 2021-to-2024 original calibrated post-publication terrain registration.

Do not fit on published known positive nor use temporal residual for geometry.
Report every ratio and partial/full-affine model; independent spatial holdout
within the pair, not absolute lunar geodesy or event validation.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import cv2,numpy as np
ROLES={"before":"before_2021","after":"after_2024"}
EVENT=np.array([384.,384.])
EXCLUDE=112.
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(folder,meta,role):
    f=folder/(ROLES[role]+"_Heis_original_CDR_native_r384.npy")
    row=meta["stages"]["before_2021_reused_verified_original_CDR" if role=="before" else "after_2024_new_verified_original_CDR"]
    if sha(f)!=row["npy_SHA256"]:raise ValueError("post2021 exact NASA source digest mismatch "+role)
    a=np.load(f,allow_pickle=False)
    if a.shape!=(769,769) or a.dtype!=np.int16:raise ValueError("wrong original calibrated array")
    return a.astype(np.float32)*row["scale"],a>=-32752
def grayscale(img,valid):
    lo,hi=np.percentile(img[valid],[1,99])
    if hi<=lo:raise ValueError("degenerate source I/F")
    g=np.uint8(np.rint(np.clip((img-lo)/(hi-lo)*255,0,255)))
    g[~valid]=0
    return cv2.createCLAHE(clipLimit=2,tileGridSize=(8,8)).apply(g)
def assess(source,target,train,held,model):
    row={"model":model,"training":int(train.sum()),"withheld":int(held.sum())}
    if train.sum()<40 or held.sum()<15:
        return dict(row,status="insufficient_reproducible_source_terrain",gate=False)
    method=cv2.estimateAffinePartial2D if model=="partial_affine" else cv2.estimateAffine2D
    cv2.setRNGSeed(20260920)
    M,mask=method(source[train].astype(np.float32),target[train].astype(np.float32),
        method=cv2.RANSAC,ransacReprojThreshold=3.,
        maxIters=15000,confidence=.999,refineIters=35)
    if M is None or mask is None:
        return dict(row,status="no_off_marker_geometric_consensus",gate=False)
    keep=mask.reshape(-1).astype(bool)
    predicted=source[held]@M[:,:2].T+M[:,2]
    err=np.linalg.norm(predicted-target[held],axis=1)
    support=target[train][keep]
    cells=np.clip((support*8/769).astype(int),0,7)
    near=np.linalg.norm(support-EVENT,axis=1)
    mapped=EVENT@M[:,:2].T+M[:,2]
    row.update({"status":"fit","inliers":int(keep.sum()),
       "inlier_fraction":float(keep.mean()),
       "inlier_8x8_terrain_cells":len(set(zip(cells[:,0],cells[:,1]))),
       "inliers_in_marker_annulus_112_to_290":int(np.sum((near>EXCLUDE)&(near<290))),
       "withheld_median_before_native_px":float(np.median(err)),
       "withheld_p95_before_native_px":float(np.percentile(err,95)),
       "fraction_withheld_under_3px":float(np.mean(err<3)),
       "matrix_2024_to_2021":M.tolist(),
       "mapped_2024_nominal_camera_marker_in_2021_roi":mapped.tolist(),
       "nominal_camera_marker_discordance_px":float(np.linalg.norm(mapped-EVENT)),
       "matrix_determinant":float(np.linalg.det(M[:,:2])),
       "column_pixel_scales":[float(np.linalg.norm(M[:,:2][:,i])) for i in range(2)]})
    row["gate"]=bool(row["inliers"]>=65 and row["inlier_8x8_terrain_cells"]>=8
       and row["inliers_in_marker_annulus_112_to_290"]>=8
       and len(err)>=25 and np.median(err)<2 and np.percentile(err,95)<6)
    return row
def main():
    p=argparse.ArgumentParser()
    for n in ("source_folder","source_manifest","out"):
        p.add_argument("--"+n.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    meta=json.loads(a.source_manifest.read_text())
    if meta.get("schema")!="actual-overlap-Heis-2021-2024-two-original-calibrated-source-ROIs-v1":
        raise ValueError("not actual same-lunar-coordinate original NASA calibrated pair")
    imgs={r:load(a.source_folder,meta,r) for r in ROLES}
    sift=cv2.SIFT_create(nfeatures=8500,contrastThreshold=.007,edgeThreshold=15,sigma=1.25)
    b,bmask=imgs["before"];q,qmask=imgs["after"]
    bk,bd=sift.detectAndCompute(grayscale(b,bmask),bmask.astype("uint8")*255)
    ak,ad=sift.detectAndCompute(grayscale(q,qmask),qmask.astype("uint8")*255)
    if bd is None or ad is None:raise ValueError("no original lunar terrain features")
    tentative=cv2.BFMatcher(cv2.NORM_L2).knnMatch(ad,bd,k=2)
    records=[]
    for ratio in (.72,.78):
        good=[m for pair in tentative if len(pair)==2
              for m,n in [pair] if m.distance<ratio*n.distance]
        src=np.float64([ak[m.queryIdx].pt for m in good])
        dst=np.float64([bk[m.trainIdx].pt for m in good])
        outside=(np.linalg.norm(src-EVENT,axis=1)>EXCLUDE)&(np.linalg.norm(dst-EVENT,axis=1)>EXCLUDE)
        bins=np.clip((dst*8/769).astype(int),0,7)
        held=(17*bins[:,0]+7*bins[:,1])%5==0
        results=[assess(src,dst,outside&~held,outside&held,m) for m in ("partial_affine","full_affine")]
        records.append({"ratio":ratio,"matched":len(good),
            "off_both_nominal_markers":int(outside.sum()),
            "spatial_training":int((outside&~held).sum()),
            "spatial_withheld":int((outside&held).sum()),
            "models":results})
    result={"schema":"Heis-2021-to-2024-original-calibrated-off-marker-registration-v1",
        "source_manifest_SHA256":sha(a.source_manifest),
        "exact_products":["M1376643242LC","M1481045431LC"],
        "nominal_2021_2024_marker":[32.547,327.792],
        "fixed_marker_exclusion_radius_both_native_px":EXCLUDE,
        "fixed_ratio_screen":[.72,.78],
        "eight_by_eight_spatial_holdout":"(17*2021-xcell+7*2021-ycell)%5==0",
        "keypoints":{"2021":len(bk),"2024":len(ak)},
        "all_models":records,
        "scientific_status":"registration only; no source temporal residual, landslide, or novelty claim",
        "limits":["A source plane terrain affine can align local features, not absolutely correct DEM/geodesy.",
          "The 2021 known landslide neighborhood was excluded from source registration.",
          "Different illumination 2021 vs 2024 can create false temporal changes.",
          "No sealed geographic holdout pixels accessed."]}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"features":result["keypoints"],"fits":records},indent=2),flush=True)
if __name__=="__main__":main()
