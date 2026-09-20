#!/usr/bin/env python3
"""Ryder 2022/2024/2026 original-source lunar terrain registration only.

Never observe source time differences until off-published-site camera-aware
registration and spatial withheld terrain verification are frozen. All
orientations, independent source-scene preprocessing, match ratios and rejected
fits survive in the complete diagnostic.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
import cv2,numpy as np

BASE="baseline_2022"
LATER=("followup_2024","followup_2026_April","followup_2026_May")
N=1281
C=np.array([640.,640.])
EXCLUDE=190.
THREE_MODES=("CLAHE","highpass")
RATIOS=(.76,.84)
def sha(p):return hashlib.sha256(p if isinstance(p,bytes) else p.read_bytes()).hexdigest()
def original(root,manifest,tag):
    row=manifest["source_products"][tag]
    path=root/(tag+"_original_NAC_CDR_r640.npy")
    if sha(path)!=row["original_native_CDR_patch_npy_sha256"]:
        raise ValueError("exact original NASA calibrated Ryder "+tag+" SHA-256 mismatch")
    z=np.load(path,allow_pickle=False)
    if z.shape!=(N,N) or z.dtype!=np.int16:
        raise ValueError("wrong original Ryder NAC camera source format")
    mask=z>=-32752
    if mask.mean()<.88:raise ValueError("unassessable original source")
    return z.astype("float32")*row["reflectance_scaling_IoverF"],mask
def scene_view(img,mask,mode):
    lo,hi=np.percentile(img[mask],[1,99])
    if hi<=lo:raise ValueError("flat source calibration")
    scaled=np.uint8(np.rint(np.clip((img-lo)/(hi-lo)*255,0,255)))
    scaled[~mask]=0
    contrast=cv2.createCLAHE(clipLimit=2,tileGridSize=(8,8))
    if mode=="CLAHE":
        return contrast.apply(scaled)
    if mode=="highpass":
        b=scaled.astype(np.float32)
        h=b-cv2.GaussianBlur(b,(0,0),sigmaX=16)
        bound=np.percentile(np.abs(h[mask]),99)
        filtered=np.uint8(np.rint(np.clip(128+127*h/max(bound,1.),0,255)))
        filtered[~mask]=0
        return contrast.apply(filtered)
    raise ValueError("not frozen source preprocessing")
def orient(img,valid,rot,flip):
    a=np.ascontiguousarray(np.rot90(img,rot))
    m=np.ascontiguousarray(np.rot90(valid,rot))
    if flip:a=np.ascontiguousarray(np.fliplr(a));m=np.ascontiguousarray(np.fliplr(m))
    return a,m
def matrix_original_to_oriented(rot,flip):
    if rot==0:
        if flip:return np.array([[-1,0],[0,1]],float),np.array([N-1,0],float)
        return np.eye(2),np.zeros(2)
    if rot==2:
        if flip:return np.array([[1,0],[0,-1]],float),np.array([0,N-1],float)
        return -np.eye(2),np.array([N-1,N-1],float)
    raise ValueError("only fixed two image orientations")
def trial(src,dst,train,test,rot,flip,tag,metadata):
    result={"model":"full_affine","off_both_camera_marker_train":int(train.sum()),
         "heldout_spatial_features":int(test.sum())}
    if train.sum()<45 or test.sum()<15:
        return dict(result,status="insufficient_off_marker_features",registration_gate_passed=False)
    cv2.setRNGSeed(20260920)
    mat,inliers=cv2.estimateAffine2D(src[train].astype(np.float32),
         dst[train].astype(np.float32),method=cv2.RANSAC,
         ransacReprojThreshold=3.,maxIters=15000,confidence=.999,refineIters=25)
    if mat is None or inliers is None:
        return dict(result,status="no_robust_consensus",registration_gate_passed=False)
    good=inliers.reshape(-1).astype(bool)
    pts=dst[train][good]
    spatial=np.clip((pts*10/N).astype(int),0,9)
    predicted=src[test]@mat[:,:2].T+mat[:,2]
    errors=np.linalg.norm(predicted-dst[test],axis=1)
    linear,shift=matrix_original_to_oriented(rot,flip)
    native=np.column_stack((mat[:,:2]@linear,mat[:,:2]@shift+mat[:,2]))
    scales=np.linalg.norm(native[:,:2],axis=0)
    lhs=metadata["source_products"][BASE];rhs=metadata["source_products"][tag]
    expected=np.array([rhs["source_camera_sample_resolution_m"]/lhs["source_camera_sample_resolution_m"],
                       rhs["source_camera_line_resolution_m"]/lhs["source_camera_line_resolution_m"]])
    comparable=scales/expected
    mapped=C@native[:,:2].T+native[:,2]
    result.update({"status":"fit","training_inliers":int(good.sum()),
       "fraction_training_inliers":float(np.mean(good)),
       "inlier_10_by_10_cells":len(set(zip(spatial[:,0],spatial[:,1]))),
       "near_marker_annulus_190_to_510_inliers":int(np.sum((np.linalg.norm(pts-C,axis=1)>EXCLUDE)&
                                                    (np.linalg.norm(pts-C,axis=1)<510))),
       "withheld_median_baseline_source_px":float(np.median(errors)),
       "withheld_fraction_under_3px":float(np.mean(errors<3)),
       "withheld_fraction_under_5px":float(np.mean(errors<5)),
       "withheld_p95_baseline_source_px":float(np.percentile(errors,95)),
       "matrix_oriented_epoch_to_baseline":mat.tolist(),
       "matrix_original_epoch_to_original_baseline":native.tolist(),
       "determinant_native_original":float(np.linalg.det(native[:,:2])),
       "original_native_source_column_scales":scales.tolist(),
       "expected_scale_ratios_from_independent_CSM":expected.tolist(),
       "empirical_over_camera_source_scale":comparable.tolist(),
       "mapped_nominal_epoch_camera_marker_in_2022_source":mapped.tolist(),
       "nominal_marker_discordance_native_px":float(np.linalg.norm(mapped-C)),
       "native_pixel_axis_chirality_not_forced":True})
    result["registration_gate_passed"]=bool(good.sum()>=80
       and result["inlier_10_by_10_cells"]>=12
       and result["near_marker_annulus_190_to_510_inliers"]>=8
       and test.sum()>=25 and np.median(errors)<2
       and np.mean(errors<3)>.70
       and np.all(np.abs(comparable-1.)<.20)
       and .50<abs(np.linalg.det(native[:,:2]))/np.prod(expected)<1.50)
    return result
def main():
    p=argparse.ArgumentParser()
    for name in ("source_folder","source_manifest","out"):
        p.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    src=json.loads(a.source_manifest.read_text())
    if src["schema"]!="Ryder-2022-2024-2026-four-original-calibrated-source-r640-v1" or len(src["source_products"])!=4:
        raise ValueError("not four fully verified original Ryder NASA calibrated EDR camera products")
    imgs={name:original(a.source_folder,src,name) for name in (BASE,)+LATER}
    cv2.setNumThreads(2)
    sift=cv2.SIFT_create(nfeatures=11500,contrastThreshold=.007,edgeThreshold=16,sigma=1.25)
    b,bvalid=imgs[BASE]
    rows=[]
    for mode in THREE_MODES:
        bk,bd=sift.detectAndCompute(scene_view(b,bvalid,mode),bvalid.astype("uint8")*255)
        for tag in LATER:
            source,valid=imgs[tag]
            for rot in (0,2):
                for flip in (False,True):
                    r,m=orient(source,valid,rot,flip)
                    ak,ad=sift.detectAndCompute(scene_view(r,m,mode),m.astype("uint8")*255)
                    if bd is None or ad is None:
                        rows.append({"source":tag,"preprocessing":mode,"rot_ccw":rot,
                            "flip_h":flip,"status":"no_original_source_descriptors"})
                        continue
                    matches=cv2.BFMatcher(cv2.NORM_L2).knnMatch(ad,bd,k=2)
                    for ratio in RATIOS:
                        good=[z for pair in matches if len(pair)==2
                              for z,next_ in [pair] if z.distance<ratio*next_.distance]
                        a_pts=np.array([ak[z.queryIdx].pt for z in good],float).reshape(-1,2)
                        b_pts=np.array([bk[z.trainIdx].pt for z in good],float).reshape(-1,2)
                        off=(np.linalg.norm(a_pts-C,axis=1)>EXCLUDE)&(np.linalg.norm(b_pts-C,axis=1)>EXCLUDE)
                        cell=np.clip((b_pts*10/N).astype(int),0,9)
                        held=(17*cell[:,0]+7*cell[:,1])%5==0
                        fit=trial(a_pts,b_pts,off&~held,off&held,rot,flip,tag,src)
                        rows.append({"source":tag,"preprocessing":mode,
                          "rot_ccw":rot,"flip_h":flip,"ratio":ratio,
                          "matched":len(good),"off_markers":int(off.sum()),"fit":fit})
    # Geometry is selected *only* on off-marker terrain matches, before
    # any scene temporal difference is computed.
    picked={}
    for tag in LATER:
        eligible=[r for r in rows if r.get("source")==tag and
                  r.get("fit",{}).get("registration_gate_passed")]
        eligible.sort(key=lambda r:(
           -r["fit"]["withheld_fraction_under_3px"],
           -r["fit"]["training_inliers"],
           r["fit"]["withheld_median_baseline_source_px"],
           0 if r["preprocessing"]=="CLAHE" else 1))
        picked[tag]=eligible[0] if eligible else None
    result={"schema":"Ryder-four-original-calibrated-NAC-off-marker-terrain-registration-v1",
        "source_manifest_SHA256":sha(a.source_manifest.read_bytes()),
        "source_products":{key:src["source_products"][key]["CDR_product"] for key in (BASE,)+LATER},
        "source_pixel_access":"four original NASA camera-grounded calibrated r640 patches; no other lunar sites opened",
        "reference_epoch":BASE,
        "fixed_preprocessing":THREE_MODES,"fixed_ratio":RATIOS,
        "fixed_rotation_ccw":[0,2],"horizontal_mirror_tried":[False,True],
        "both_marker_exclusion_radius_source_px":EXCLUDE,
        "spatial_holdout":"(17*source_2022_xcell+7*source_2022_ycell)%5==0; 10x10",
        "all_source_geometry_models":rows,
        "selected_off_change_geometry_by_epoch":picked,
        "any_complete_four_epoch_source_registration":all(picked.values()),
        "limits":["Full-affine original NASA terrain registration is not DEM-georeferenced absolute lunar ground truth.",
          "No image differences or novel lunar events were assessed to select geometry.",
          "Source camera pixel axis parity can be negative; source camera resolution columns constrain affine magnitude.",
          "The originally published Ryder event is a DEVELOPMENT site and remains already known."]}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"scanned_models":len(rows),
       "registration_gate_passed":sum(bool(z.get("fit",{}).get("registration_gate_passed")) for z in rows),
       "selected":{tag:None if z is None else
          {"mode":z["preprocessing"],"rotation":z["rot_ccw"],"flipped":z["flip_h"],
           "ratio":z["ratio"],"fit":z["fit"]}
          for tag,z in picked.items()}},indent=2),flush=True)
if __name__=="__main__":main()
