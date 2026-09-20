#!/usr/bin/env python3
"""Localize original published Heis S26 elongated difference on *original* NASA CDR.

Source/figure registration is independent of the subsequent temporal residual
experiment. Report every attempted orientation, model, ratio and bad fit; do
not select source target location from NASA temporal residual strength.
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

SUPPLEMENT_SHA="132f3d2c2d6c8a5fcb102fe9dcfa5e2d33c6e60b6600c1c94d0d2bafb282c233"
FIG_SHA="1e642c9ebf0f0716cecef1141f52f2d8fd7c2e274ad806a07447f8012dee3ea8"
ROLES={"before":"M1197976848LC","after":"M1376643242LC"}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def stretch(img,mask):
    lo,hi=np.percentile(img[mask],[1,99])
    x=np.uint8(np.rint(np.clip((img-lo)/(hi-lo)*255,0,255)))
    x[~mask]=0
    return cv2.createCLAHE(clipLimit=2,tileGridSize=(8,8)).apply(x)
def source_image(folder,meta,role):
    row=meta["epochs"][role]
    if row["CDR_id"]!=ROLES[role]:raise ValueError("incorrect Heis source CDR")
    path=folder/(role+"_Heis_original_CDR_native_r384.npy")
    if sha(path.read_bytes())!=row["saved_npy_SHA256"]:
        raise ValueError("Heis original source SHA mismatch")
    arr=np.load(path,allow_pickle=False)
    if arr.shape!=(769,769) or arr.dtype!=np.int16:raise ValueError("wrong CDR native array")
    valid=arr>=-32752
    return stretch(arr.astype(np.float32),valid),valid
def paper(path):
    data=path.read_bytes()
    if sha(data)!=SUPPLEMENT_SHA:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            data=z.read("nwaf384_supplemental_files.zip")
    if sha(data)!=SUPPLEMENT_SHA:raise ValueError("not verified published original archive")
    with zipfile.ZipFile(io.BytesIO(data)) as z:docx=z.read("2025-434-supplementarymaterials.docx")
    with zipfile.ZipFile(io.BytesIO(docx)) as z:raw=z.read("word/media/image26.jpeg")
    if sha(raw)!=FIG_SHA:raise ValueError("not original Heis S26 image")
    image=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
    if image.shape[:2]!=(469,1430):raise ValueError("wrong S26 image shape")
    return image
def panel(img,role):
    n=0 if role=="before" else 1
    x0=round(n*1430/3)
    x1=round((n+1)*1430/3)
    return cv2.cvtColor(img[16:-16,x0+16:x1-16],cv2.COLOR_BGR2GRAY)
def oriented(base,valid,rot,flipped):
    result=np.ascontiguousarray(np.rot90(base,rot))
    mask=np.ascontiguousarray(np.rot90(valid,rot))
    if flipped:
        result=np.ascontiguousarray(np.fliplr(result))
        mask=np.ascontiguousarray(np.fliplr(mask))
    return result,mask
def undo_orient(point,shape,rot,flip):
    # cv2 uses x,y. Unflip before undoing numpy CCW 90-degree rotations.
    x,y=point
    h,w=shape
    if flip:x=w-1-x
    for k in range(rot):
        x,y=w-1-y,x
    return [float(x),float(y)]
def fit(points_src,points_dst,train,withheld,model):
    row={"model":model,"training":int(train.sum()),"withheld":int(withheld.sum())}
    if train.sum()<18 or withheld.sum()<6:return dict(row,status="not_enough_off_signal_matched_features")
    est=cv2.estimateAffinePartial2D if model=="partial_affine" else cv2.estimateAffine2D
    cv2.setRNGSeed(20260920)
    M,mask=est(points_src[train].astype(np.float32),points_dst[train].astype(np.float32),
        method=cv2.RANSAC,ransacReprojThreshold=4.,maxIters=12000,
        confidence=.999,refineIters=30)
    if M is None or mask is None:return dict(row,status="no_terrain_consensus")
    k=mask.reshape(-1).astype(bool)
    predicted=points_src[withheld]@M[:,:2].T+M[:,2]
    err=np.linalg.norm(predicted-points_dst[withheld],axis=1)
    arr=points_src[train][k]
    bins=np.clip((arr/np.array([445.,437.])*6).astype(int),0,5)
    row.update({"status":"fit","inliers":int(k.sum()),
        "inlier_fraction":float(k.mean()),
        "inlier_spatial_cells_6x6":len(set(zip(bins[:,0],bins[:,1]))),
        "withheld_median_oriented_CDR_px":float(np.median(err)),
        "withheld_p95_oriented_CDR_px":float(np.percentile(err,95)),
        "M_panel_trim_to_oriented_CDR":M.tolist()})
    row["crosswalk_gate_passed"]=bool(row["inliers"]>=40 and
         row["inlier_spatial_cells_6x6"]>=8 and withheld.sum()>=10
         and row["withheld_median_oriented_CDR_px"]<3
         and row["withheld_p95_oriented_CDR_px"]<10)
    return row
def main():
    p=argparse.ArgumentParser()
    for n in ("source_folder","source_manifest","supplement_artifact","paper_temporal","out"):
        p.add_argument("--"+n.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    meta=json.loads(a.source_manifest.read_text())
    temporal=json.loads(a.paper_temporal.read_text())
    if meta["schema"]!="isef4-Heis-S26-source-grounded-original-CDR-r384-v1" or temporal["figure_sha256"]!=FIG_SHA:
        raise ValueError("not real Heis original source and independent measured original paper")
    fig=paper(a.supplement_artifact)
    source={role:source_image(a.source_folder,meta,role) for role in ROLES}
    sift=cv2.SIFT_create(nfeatures=8000,contrastThreshold=.007,edgeThreshold=18,sigma=1.3)
    local_component={m["model"]:m["fixed_signed_component_sweep"]["2"][0] for m in temporal["two_model_results"]}
    # Both published-panel fits are concordant, target centroid fixed before
    # any attempt to match to the original NASA data.
    centroid=np.median([z["centroid_original_S26_before_panel_xy"] for z in local_component.values()],axis=0)
    if not (200<centroid[0]<250 and 225<centroid[1]<255):
        raise ValueError("fixed original S26 positive footprint changed")
    rows=[]
    for role in ROLES:
        pp=panel(fig,role)
        original_shift=16+round((0 if role=="before" else 1)*1430/3)
        candidate=centroid-np.array([16.,16.])
        # Both BEFORE and AFTER paper panels crop to same coordinate frame,
        # and their measured relative shift is ~3 paper pixels.
        if role=="after":
            fm=np.float64(temporal["two_model_results"][1]["matrix_before_to_after"])
            candidate=candidate@fm[:,:2].T+fm[:,2]
        gray=cv2.createCLAHE(clipLimit=2,tileGridSize=(8,8)).apply(pp)
        kp,desc=sift.detectAndCompute(gray,None)
        src,valid=source[role]
        for rot in range(4):
            for flip in (False,True):
                oriented_gray,oriented_valid=oriented(src,valid,rot,flip)
                sk,sd=sift.detectAndCompute(oriented_gray,oriented_valid.astype("uint8")*255)
                raw=cv2.BFMatcher(cv2.NORM_L2).knnMatch(desc,sd,k=2)
                for ratio in (.76,.84):
                    selected=[match for pair in raw if len(pair)==2
                              for match,runner in [pair]
                              if match.distance<ratio*runner.distance]
                    pf=np.float64([kp[x.queryIdx].pt for x in selected])
                    sf=np.float64([sk[x.trainIdx].pt for x in selected])
                    off=np.linalg.norm(pf-candidate,axis=1)>45
                    # Exclude paper annotation and text/scale corners.
                    off&=(pf[:,1]>50)&(pf[:,1]<pp.shape[0]-70)
                    bins=np.clip((pf/np.array([pp.shape[1],pp.shape[0]])*6).astype(int),0,5)
                    withheld=(17*bins[:,0]+7*bins[:,1])%5==0
                    train=off&~withheld;test=off&withheld
                    trials=[]
                    for model in ("partial_affine","full_affine"):
                        fit_result=fit(pf,sf,train,test,model)
                        if fit_result.get("status")=="fit":
                            M=np.float64(fit_result["M_panel_trim_to_oriented_CDR"])
                            derived=candidate@M[:,:2].T+M[:,2]
                            before_undo=undo_orient(derived,src.shape,rot,flip)
                            fit_result["independent_paper_change_center_original_role_CDR_cutout_xy"]=before_undo
                            roi=meta["epochs"][role]["native_source_roi_xyxy_exclusive"]
                            fit_result["independent_paper_change_center_original_role_NAC_xy"]=[
                                float(before_undo[0]+roi[0]),float(before_undo[1]+roi[1])]
                            fit_result["marker_crop_center_distance_px"]=float(np.linalg.norm(np.array(before_undo)-[384.,384.]))
                        trials.append(fit_result)
                    rows.append({"panel_role":role,"original_NAC_role":role,
                       "orientation_ccw":rot,"flipped_h":flip,
                       "ratio":ratio,"tentative":len(selected),
                       "off_paper_change":int(off.sum()),
                       "spatial_withheld":int(test.sum()),
                       "model_trials":trials})
    result={"schema":"Heis-S26-original-paper-to-original-calibrated-CDR-exploratory-crosswalk-v1",
        "paper_figure_SHA256":FIG_SHA,
        "source_manifest_SHA256":sha(a.source_manifest.read_bytes()),
        "paper_temporal_SHA256":sha(a.paper_temporal.read_bytes()),
        "paper_declared_before_panel_slope_change_center":[float(x) for x in centroid],
        "tested_orig_source_pairs":ROLES,"fixed_paper_source_exclusion_radius_px":45,
        "orientation_search":"4 CCW rotations x horizontal mirror x descriptor-ratio 0.76/0.84; all reported",
        "all_cases":rows,
        "scientific_limits":["A source/figure match cannot prove the author's geological polygon.",
            "Published panel transforms and original NAC camera terrain align locally but absolute lunar ground model remains unchecked.",
            "Exploratory orientation screen on same known-positive target; no new event sensitivity claim.",
            "The paper change center was fixed by the independently executed original S26 figure test."]}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"cases":len(rows),
        "top":sorted([{"role":row["panel_role"],"r":row["orientation_ccw"],"flip":row["flipped_h"],
           "ratio":row["ratio"],**m} for row in rows for m in row["model_trials"]
           if m.get("status")=="fit"],key=lambda x:-x["inliers"])[:12]},indent=2),flush=True)
if __name__=="__main__":main()
