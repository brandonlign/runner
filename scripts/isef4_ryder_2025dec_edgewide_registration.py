#!/usr/bin/env python3
"""Independently align EDGE-WIDE third Ryder Dec2025 original NAC to Dec2024.

Strict source SHA from PDS3 original camera-ground cutouts; freeze geometry
using only terrain outside BOTH published-site camera markers. This program
does NOT look at 2024/2025/2026 temporal intensity differences.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np,cv2

BASE="followup_2024"
BEFORE_N=1281;BEFORE_C=np.array([640.,640.])
RATIOS=(.72,.80,.86)
MODES=("CLAHE","highpass")
def sha(p):return hashlib.sha256(p if isinstance(p,bytes) else p.read_bytes()).hexdigest()
def extract(path,want,shape,scale):
    if sha(path)!=want:raise ValueError("not SHA-verified exact original camera-calibrated lunar source")
    a=np.load(path,allow_pickle=False)
    if a.shape!=shape or a.dtype!=np.int16:raise ValueError("wrong original source camera crop")
    return a.astype(np.float32)*scale,a>=-32752
def vis(img,valid,mode):
    lo,hi=np.percentile(img[valid],[1,99])
    a=np.uint8(np.rint(np.clip((img-lo)/max(hi-lo,1e-5)*255,0,255)))
    a[~valid]=0
    clahe=cv2.createCLAHE(clipLimit=2,tileGridSize=(8,8))
    if mode=="CLAHE":return clahe.apply(a)
    if mode=="highpass":
        high=a.astype(np.float32)-cv2.GaussianBlur(a.astype(np.float32),(0,0),sigmaX=16)
        bound=np.percentile(np.abs(high[valid]),99)
        b=np.uint8(np.rint(np.clip(128+127*high/max(bound,1),0,255)))
        b[~valid]=0
        return clahe.apply(b)
    raise ValueError("bad model")
def orient(a,m,rot,flip):
    aa=np.ascontiguousarray(np.rot90(a,rot))
    mm=np.ascontiguousarray(np.rot90(m,rot))
    if flip:aa=np.ascontiguousarray(np.fliplr(aa));mm=np.ascontiguousarray(np.fliplr(mm))
    return aa,mm
def affine_shape_from_oriented(M,side,rot,flip):
    if rot==0:
        Q=np.diag([-1.,1.]) if flip else np.eye(2)
        tr=np.array([side-1.,0.]) if flip else np.zeros(2)
    elif rot==2:
        Q=np.diag([1.,-1.]) if flip else -np.eye(2)
        tr=np.array([0.,side-1.]) if flip else np.array([side-1.,side-1.])
    else:raise ValueError("only predeclared source camera chirality")
    return np.column_stack([M[:,:2]@Q,M[:,:2]@tr+M[:,2]])
def fit(src,dst,side,rot,flip,expected,original_marker,oriented_marker):
    first=np.linalg.norm(src-oriented_marker,axis=1)
    second=np.linalg.norm(dst-BEFORE_C,axis=1)
    off=(first>155)&(second>185)
    grid=np.clip((dst*10/BEFORE_N).astype(int),0,9)
    held=(17*grid[:,0]+7*grid[:,1])%5==0
    training=off&~held;validation=off&held
    r={"original_candidate_off_site":int(off.sum()),
       "off_site_training":int(training.sum()),
       "off_site_heldout":int(validation.sum())}
    if training.sum()<50 or validation.sum()<16:
        return dict(r,status="insufficient_independent_off_site_matching",gate=False)
    cv2.setRNGSeed(20260920)
    M,mask=cv2.estimateAffine2D(src[training].astype(np.float32),dst[training].astype(np.float32),
       method=cv2.RANSAC,ransacReprojThreshold=3.,maxIters=18000,
       confidence=.999,refineIters=30)
    if M is None or mask is None:
        return dict(r,status="no_camera_plausible_terrain_consensus",gate=False)
    inliers=mask.reshape(-1).astype(bool)
    pts=dst[training][inliers]
    cc=np.clip((pts*10/BEFORE_N).astype(int),0,9)
    errors=np.linalg.norm(src[validation]@M[:,:2].T+M[:,2]-dst[validation],axis=1)
    native=affine_shape_from_oriented(M,side,rot,flip)
    scales=np.linalg.norm(native[:,:2],axis=0)
    q=scales/expected
    predicted=(original_marker@native[:,:2].T+native[:,2])
    r.update({"status":"off_site_fit",
        "training_inliers":int(inliers.sum()),
        "inlier_10by10_spatial_cells":int(len(set(zip(cc[:,0],cc[:,1])))),
        "fraction_training_inliers":float(np.mean(inliers)),
        "withheld_median_native_2024_px":float(np.median(errors)),
        "withheld_p95_native_2024_px":float(np.percentile(errors,95)),
        "withheld_fraction_under3":float(np.mean(errors<3)),
        "withheld_fraction_under5":float(np.mean(errors<5)),
        "matrix_original_Dec2025_to_native_2024":native.tolist(),
        "source_column_scales":scales.tolist(),
        "independent_camera_expected_column_scale":expected.tolist(),
        "measured_over_camera_scale_ratio":q.tolist(),
        "source_camera_2025_nominal_marker_in_2024_reference":predicted.tolist(),
        "source_camera_marker_discordance_2024_pixels":float(np.linalg.norm(predicted-BEFORE_C)),
        "full_native_affine_determinant":float(np.linalg.det(native[:,:2]))})
    r["gate"]=bool(r["training_inliers"]>=60 and r["inlier_10by10_spatial_cells"]>=12
           and validation.sum()>=20 and r["withheld_median_native_2024_px"]<2.
           and r["withheld_fraction_under3"]>=.7
           and np.all(np.abs(q-1)<.2)
           and .50<abs(r["full_native_affine_determinant"])/np.prod(expected)<1.5)
    return r
def main():
    p=argparse.ArgumentParser()
    for key in ("original_four_manifest","original_four_folder",
        "dec2025_manifest","dec2025_folder","out"):
        p.add_argument("--"+key.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    m=json.loads(a.original_four_manifest.read_text())
    d=json.loads(a.dec2025_manifest.read_text())
    if m["schema"]!="Ryder-2022-2024-2026-four-original-calibrated-source-r640-v1" or \
       d["schema"]!="Ryder-Dec2025-camera-ground-exact-original-NAC-CDR-edgewide-v1":
        raise ValueError("source manifest not an independent verified NASA Ryder original")
    base=m["source_products"][BASE]
    image,bm=extract(a.original_four_folder/(BASE+"_original_NAC_CDR_r640.npy"),
          base["original_native_CDR_patch_npy_sha256"],(BEFORE_N,BEFORE_N),
          base["reflectance_scaling_IoverF"])
    sz=d["source_cutout_shape"][0]
    if d["source_cutout_shape"]!=[sz,sz] or sz!=1281:raise ValueError("not edge-safe 1281 native source crop")
    orig_marker=np.array(d["source_camera_marker_xy_cutout"],dtype=float)
    newer,nm=extract(a.dec2025_folder/d["original_source_npy_filename"],
          d["original_CDR_patch_npy_SHA256"],(sz,sz),d["original_CDR_pixel_scale_IoverF"])
    expected=np.array([d["source_camera_sample_resolution_m"]/base["source_camera_sample_resolution_m"],
         d["source_camera_line_resolution_m"]/base["source_camera_line_resolution_m"]],dtype=float)
    detector=cv2.SIFT_create(nfeatures=12500,contrastThreshold=.007,
             edgeThreshold=16,sigma=1.25)
    cv2.setNumThreads(2)
    results=[]
    for mode in MODES:
        bpoints,bd=detector.detectAndCompute(vis(image,bm,mode),bm.astype(np.uint8)*255)
        for rot in (0,2):
            for flip in (False,True):
                o,om=orient(newer,nm,rot,flip)
                pts,descriptor=detector.detectAndCompute(vis(o,om,mode),om.astype(np.uint8)*255)
                if bd is None or descriptor is None:continue
                raw=cv2.BFMatcher(cv2.NORM_L2).knnMatch(descriptor,bd,k=2)
                for ratio in RATIOS:
                    good=[first for pair in raw if len(pair)==2
                          for first,second in [pair] if first.distance<ratio*second.distance]
                    s=np.array([pts[x.queryIdx].pt for x in good],float).reshape(-1,2)
                    t=np.array([bpoints[x.trainIdx].pt for x in good],float).reshape(-1,2)
                    rotated_marker=orig_marker.copy()
                    if rot==2:rotated_marker=np.array([sz-1.,sz-1.])-rotated_marker
                    if flip:rotated_marker[0]=sz-1.-rotated_marker[0]
                    fit_result=fit(s,t,sz,rot,flip,expected,orig_marker,rotated_marker)
                    results.append({"representation":mode,"orientation_rot_ccw":rot,
                        "horizontal_flip":flip,"descriptor_ratio":ratio,
                        "sift_tentative_matches":len(good),"fit":fit_result})
    passed=[z for z in results if z["fit"].get("gate")]
    passed.sort(key=lambda q:(
        -q["fit"]["withheld_fraction_under3"],
        -q["fit"]["training_inliers"],
         q["fit"]["withheld_median_native_2024_px"],
         0 if q["representation"]=="CLAHE" else 1))
    doc={"schema":"Ryder-independent-Dec2025-edgewide-original-NAC-to-2024-terrain-registration-v1",
       "original_four_manifest_SHA256":sha(a.original_four_manifest),
       "original_2025_manifest_SHA256":sha(a.dec2025_manifest),
       "original_2024_CDR":base["CDR_product"],
       "original_Dec2025_CDR":d["source_CDR"],
       "source_2025_native_cutout_size":sz,
       "source_camera_marker_2025_native_xy":orig_marker.tolist(),
       "fixed_only_off_published_Ryder_camera_marker_correspondences":True,
       "all_frozen_registration_trials":results,
       "passed_count":len(passed),
       "best_pre_change_source_registration":passed[0] if passed else None,
       "scientific_limits":["No lunar temporal difference or event morphology considered to select registration.",
          "2025 source scene chosen using actual polygon coverage and scene-level sunlight only.",
          "No claimed new Ryder lunar mass movement; historical site already published."]}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(doc,indent=2)+"\n")
    print(json.dumps({"candidate_fit_count":len(results),"passed":len(passed),
       "best":passed[0] if passed else None,
       "top_failed":sorted(results,key=lambda x:-x["fit"].get("training_inliers",0))[:3]},
       indent=2),flush=True)
if __name__=="__main__":main()
