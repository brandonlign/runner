#!/usr/bin/env python3
"""Actual-coverage 2021/2024 original Heis NAC orientation and light invariance.

This is registration ONLY, not a change search. Both marker neighborhoods are
withheld. Full model sweep and all failures are published; valid source
camera pixel-size anisotropy is an independent plausibility condition.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import cv2,numpy as np
CENTER=np.array([384.,384.])
CAMERA_SCALE=np.array([0.81295771063689/0.8274110597957,
                       0.88492726466775/0.90910835439268])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(folder,meta,role):
    name="before_2021" if role=="before" else "after_2024"
    row=meta["stages"]["before_2021_reused_verified_original_CDR" if role=="before" else "after_2024_new_verified_original_CDR"]
    p=folder/(name+"_Heis_original_CDR_native_r384.npy")
    if sha(p)!=row["npy_SHA256"]:raise ValueError("actual original source SHA mismatch")
    a=np.load(p,allow_pickle=False)
    if a.shape!=(769,769) or a.dtype!=np.int16:raise ValueError("bad NASA calibrated source geometry")
    return a.astype(np.float32)*row["scale"],a>=-32752
def standard(im,valid):
    lo,hi=np.percentile(im[valid],[1,99])
    g=np.uint8(np.rint(np.clip((im-lo)/(hi-lo)*255,0,255)))
    g[~valid]=0
    return g
def preprocess(im,mask,mode):
    x=standard(im,mask)
    if mode=="CLAHE":
        return cv2.createCLAHE(clipLimit=2,tileGridSize=(8,8)).apply(x)
    if mode=="gradient":
        gx=cv2.Scharr(x,cv2.CV_32F,1,0)
        gy=cv2.Scharr(x,cv2.CV_32F,0,1)
        mag=cv2.magnitude(gx,gy)
        lo,hi=np.percentile(mag[mask],[5,99])
        out=np.uint8(np.rint(np.clip((mag-lo)/(hi-lo)*255,0,255)))
        out[~mask]=0
        return cv2.createCLAHE(clipLimit=2,tileGridSize=(8,8)).apply(out)
    if mode=="highpass":
        a=x.astype("float32")
        f=a-cv2.GaussianBlur(a,(0,0),sigmaX=16)
        hi=np.percentile(np.abs(f[mask]),99)
        out=np.uint8(np.rint(np.clip(f/max(hi,1.)*127+128,0,255)))
        out[~mask]=0
        return cv2.createCLAHE(clipLimit=2,tileGridSize=(8,8)).apply(out)
    raise ValueError("unrecognized fixed preprocessing")
def oriented(im,mask,rot,flip):
    v=np.ascontiguousarray(np.rot90(im,rot))
    m=np.ascontiguousarray(np.rot90(mask,rot))
    if flip:v=np.ascontiguousarray(np.fliplr(v));m=np.ascontiguousarray(np.fliplr(m))
    return v,m
def orient_to_raw(rot,flip):
    if rot==0:
        return np.array([[-1,0],[0,1]],float) if flip else np.eye(2)
    if rot==2:
        return np.array([[1,0],[0,-1]],float) if flip else -np.eye(2)
    raise ValueError("only declared 0/180 orientations permitted")
def assess(src,dst,train,held,model,rot,flip):
    row={"model":model,"off_published_marker_train":int(train.sum()),"withheld":int(held.sum())}
    if train.sum()<35 or held.sum()<12:return dict(row,status="not_enough_off_marker_features",gate=False)
    est=cv2.estimateAffinePartial2D if model=="partial_affine" else cv2.estimateAffine2D
    cv2.setRNGSeed(20260920)
    M,mask=est(src[train].astype(np.float32),dst[train].astype(np.float32),
        method=cv2.RANSAC,ransacReprojThreshold=3.0,
        maxIters=10000,confidence=.999,refineIters=25)
    if M is None or mask is None:return dict(row,status="no_consensus",gate=False)
    kept=mask.reshape(-1).astype(bool)
    pts=dst[train][kept]
    c=np.clip((pts*8/769).astype(int),0,7)
    errors=np.linalg.norm(src[held]@M[:,:2].T+M[:,2]-dst[held],axis=1)
    O=orient_to_raw(rot,flip);t=CENTER-O@CENTER
    raw_M=np.column_stack([M[:,:2]@O,M[:,:2]@t+M[:,2]])
    columns=np.linalg.norm(raw_M[:,:2],axis=0)
    scaled=[float(x) for x in columns]
    col_ratio=columns/CAMERA_SCALE
    mapped=CENTER@raw_M[:,:2].T+raw_M[:,2]
    row.update({"status":"fit","inliers":int(kept.sum()),
       "inlier_fraction":float(kept.mean()),
       "inlier_cells_8x8":len(set(zip(c[:,0],c[:,1]))),
       "withheld_median_original_2021_px":float(np.median(errors)),
       "withheld_fraction_under_3_px":float(np.mean(errors<3)),
       "withheld_fraction_under_8_px":float(np.mean(errors<8)),
       "withheld_inlier_subset_p95_px":float(np.percentile(errors[errors<8],95)) if np.any(errors<8) else None,
       "matrix_oriented_2024_to_original_2021":M.tolist(),
       "matrix_original_2024_to_original_2021":raw_M.tolist(),
       "native_after_to_before_column_scales":scaled,
       "independent_camera_scale_ratios":CAMERA_SCALE.tolist(),
       "column_scale_over_camera_expected":col_ratio.tolist(),
       "relative_orientation_determinant":float(np.linalg.det(raw_M[:,:2])),
       "mapped_2024_camera_marker_in_2021_roi":mapped.tolist(),
       "nominal_ground_marker_discordance_px":float(np.linalg.norm(mapped-CENTER))})
    plausible=bool(np.linalg.det(raw_M[:,:2])>0 and np.all(np.abs(col_ratio-1)<.15))
    row["camera_scale_plausible"]=plausible
    row["gate"]=bool(plausible and kept.sum()>=60 and row["inlier_cells_8x8"]>=8
         and held.sum()>=18 and np.median(errors)<3 and np.mean(errors<3)>.55)
    return row
def main():
    p=argparse.ArgumentParser()
    for n in ("source_folder","source_manifest","out"):
        p.add_argument("--"+n.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    meta=json.loads(a.source_manifest.read_text())
    if meta["schema"]!="actual-overlap-Heis-2021-2024-two-original-calibrated-source-ROIs-v1":
        raise ValueError("not both genuine original NASA CDR sources")
    before,bmask=load(a.source_folder,meta,"before")
    after,amask=load(a.source_folder,meta,"after")
    cv2.setNumThreads(2)
    sift=cv2.SIFT_create(nfeatures=9000,contrastThreshold=.006,edgeThreshold=17,sigma=1.25)
    allcases=[]
    for mode in ("CLAHE","gradient","highpass"):
        bg=preprocess(before,bmask,mode)
        bk,bd=sift.detectAndCompute(bg,bmask.astype("uint8")*255)
        for rot in (0,2):
            for flip in (False,True):
                oa,ov=oriented(after,amask,rot,flip)
                ag=preprocess(oa,ov,mode)
                ak,ad=sift.detectAndCompute(ag,ov.astype("uint8")*255)
                if ad is None or bd is None:
                    allcases.append({"mode":mode,"rot":rot,"flipped_horizontal":flip,"status":"no_descriptors"});continue
                pairs=cv2.BFMatcher(cv2.NORM_L2).knnMatch(ad,bd,k=2)
                for ratio in (.84,.90):
                    good=[m for pair in pairs if len(pair)==2 for m,n in [pair] if m.distance<ratio*n.distance]
                    src=np.float64([ak[m.queryIdx].pt for m in good])
                    dst=np.float64([bk[m.trainIdx].pt for m in good])
                    off=(np.linalg.norm(src-CENTER,axis=1)>112)&(np.linalg.norm(dst-CENTER,axis=1)>112)
                    bins=np.clip((dst*8/769).astype(int),0,7)
                    held=(17*bins[:,0]+7*bins[:,1])%5==0
                    fits=[assess(src,dst,off&~held,off&held,m,rot,flip)
                          for m in ("partial_affine","full_affine")]
                    allcases.append({"photometric_input":mode,"rot_ccw_90deg":rot,
                        "flip_after_rotation":flip,"ratio":ratio,"matches":len(good),
                        "off_nominal_markers":int(off.sum()),
                        "models":fits})
    out={"schema":"Heis-2021-to-2024-orientation-illumination-invariant-original-source-geometry-v1",
        "source_manifest_SHA256":sha(a.source_manifest),
        "actual_calibrated_products":["M1376643242LC","M1481045431LC"],
        "pixel_scales_expected_from_USGS_CSM":CAMERA_SCALE.tolist(),
        "known_2021_published_slide_masked_for_registration":True,
        "both_nominal_marker_exclusion_radius_source_px":112,
        "fixed_descriptor_ratios":[.84,.90],
        "photometric_inputs":["CLAHE","gradient","highpass"],
        "orientation_screen":"original and 180deg rotation, with and without horizontal flip",
        "all_models":allcases,
        "scientific_limits":["No source temporal differencing performed; geometric feasibility only.",
             "Significant incidence-angle mismatch may make true surface features look changed.",
             "No novelty or new lunar landslide established."]}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2)+"\n")
    best=sorted(({"mode":q.get("photometric_input"),"rotation":q.get("rot_ccw_90deg"),
                "flip":q.get("flip_after_rotation"),"ratio":q.get("ratio"),**m}
                for q in allcases for m in q.get("models",[])
                if m.get("status")=="fit"),key=lambda z:-z["inliers"])[:12]
    print(json.dumps({"tested":len(allcases),"passed":sum(m.get("gate",False) for q in allcases for m in q.get("models",[])),
       "top":best},indent=2),flush=True)
if __name__=="__main__":main()
