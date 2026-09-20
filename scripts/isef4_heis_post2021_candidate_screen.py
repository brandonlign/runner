#!/usr/bin/env python3
"""Original NASA Heis 2021->2024 known-site temporal screen: NO discovery claims.

Actual source images and camera-constrained off-slide geometry only. Every
chosen registration and photometry is predeclared before looking at differences.
Older 2015->2021 published landslide is NOT a novel 2021->2024 event.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
import cv2,numpy as np
ORIGINAL_2021_SLIDE_CENTER=np.array([355.3774151321759,350.80725149578325])
MARKER=np.array([384.,384.])
THRESHOLDS=(3,5,7)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(folder,meta,role):
    name="before_2021" if role=="before" else "after_2024"
    row=meta["stages"]["before_2021_reused_verified_original_CDR" if role=="before" else "after_2024_new_verified_original_CDR"]
    p=folder/(name+"_Heis_original_CDR_native_r384.npy")
    if sha(p)!=row["npy_SHA256"]:raise ValueError("not the EXACT original calibrated LROC "+role)
    z=np.load(p,allow_pickle=False)
    if z.shape!=(769,769) or z.dtype!=np.int16:raise ValueError("not original native NAC geometry")
    return z.astype(np.float32)*row["scale"],z>=-32752
def disk(pt,r):
    yy,xx=np.ogrid[:769,:769]
    return (xx-pt[0])**2+(yy-pt[1])**2<=r*r
def model(geometry,mode,ratio):
    choices=[q for q in geometry["all_models"] if q.get("photometric_input")==mode
            and q.get("rot_ccw_90deg")==0 and q.get("flip_after_rotation") is True
            and q.get("ratio")==ratio]
    if len(choices)!=1:raise ValueError("predeclared independent geometry not unique")
    row=next(m for m in choices[0]["models"] if m["model"]=="full_affine")
    if not row["gate"] or row["inliers"]<400:raise ValueError("camera-ground source geometry failed")
    return row
def score_window(z,valid,pt,r):
    m=disk(pt,r);v=z[m&valid]
    if v.size<.90*m.sum():return {"status":"insufficient_valid_original_source"}
    return {"n":int(v.size),
      "median_signed_MAD":float(np.median(v)),
      "fraction_positive_gt3_gt5_gt7":[float(np.mean(v>th)) for th in THRESHOLDS],
      "fraction_negative_ltminus3_ltminus5_ltminus7":[float(np.mean(v< -th)) for th in THRESHOLDS]}
def components(z,valid,exclusion,threshold,sign):
    mask=((z>threshold) if sign=="2021_brighter" else (z< -threshold))&valid&~exclusion
    n,labels,stats,cent=cv2.connectedComponentsWithStats(mask.astype("uint8"),8)
    rows=[]
    for i in range(1,n):
        x,y,w,h,area=map(int,stats[i])
        if area<20:continue
        cx,cy=map(float,cent[i])
        if not 35<=cx<=734 or not 35<=cy<=734:continue
        ys,xs=np.where(labels==i)
        cov=np.cov(np.column_stack([xs,ys]).astype(float),rowvar=False)
        eig=np.maximum(np.linalg.eigvalsh(cov),0)
        aspect=float(np.sqrt((eig[-1]+1e-6)/(eig[0]+1e-6)))
        rows.append({"area_source_px":area,"bbox_source_xywh":[x,y,w,h],
             "centroid_2021_source_cutout_xy":[cx,cy],
             "PCA_axis_ratio":aspect,
             "signed_median_change_in_component_MAD":float(np.median(z[labels==i])),
             "distance_to_published_2021_slide_source_px":float(math.dist((cx,cy),ORIGINAL_2021_SLIDE_CENTER)),
             "distance_to_2021_nominal_camera_marker_px":float(math.dist((cx,cy),MARKER))})
    return sorted(rows,key=lambda q:-q["area_source_px"])[:40],len(rows)
def trial(pair,registration,mode,debug):
    (b,bmask),(a,amask)=pair["before"],pair["after"]
    M=np.float64(registration["matrix_original_2024_to_original_2021"])
    aw=cv2.warpAffine(a,M,(769,769),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    av=cv2.warpAffine(amask.astype("uint8"),M,(769,769),
                    flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)>0
    valid=cv2.erode((bmask&av).astype("uint8"),np.ones((9,9),np.uint8),iterations=1)>0
    after=MARKER@M[:,:2].T+M[:,2]
    # The original 2015->2021 slide is an already-known prior feature and must
    # not be called NEW in the 2021->2024 interval even if illumination differs.
    exclusion=disk(MARKER,112)|disk(after,112)|disk(ORIGINAL_2021_SLIDE_CENTER,100)
    back=valid&~exclusion
    if back.sum()<6000:raise ValueError("insufficient original NAC off-slide background")
    gain=1.
    if mode=="off_marker_gain":
        gain=float(np.median(b[back])/np.median(aw[back]))
        if not .5<=gain<=2:raise ValueError("bad original physical I/F correction")
    signed=np.where(valid,b-gain*aw,0).astype("float32")
    blurred=cv2.GaussianBlur(signed,(0,0),sigmaX=24)
    weight=cv2.GaussianBlur(valid.astype("float32"),(0,0),sigmaX=24)
    details=signed-blurred/np.maximum(weight,1e-4)
    base=float(np.median(details[back]))
    sigma=float(1.4826*np.median(np.abs(details[back]-base)))
    if sigma<1e-8:raise ValueError("bad actual NASA source robust sigma")
    z=(details-base)/sigma
    inspection=valid.copy()
    inspection[:35]=False;inspection[-35:]=False;inspection[:,:35]=False;inspection[:,-35:]=False
    seen={}
    for t in THRESHOLDS:
        rows=[]
        for sign in ("2021_brighter","2024_brighter"):
            top,n=components(z,inspection,exclusion,t,sign)
            rows.append({"sign":sign,"total_components_area_at_least20":n,
                  "largest_40_outside_already_published_site":top})
        seen[str(t)]=rows
    site={}
    for rad in (8,20,40):
        site[str(rad)]=score_window(z,valid,ORIGINAL_2021_SLIDE_CENTER,rad)
    # Spatial hard controls are SAME-PAIR image terrain, not statistical pvalues.
    controls=[]
    for y in range(64,704,96):
        for x in range(64,704,96):
            pt=np.array([float(x),float(y)])
            if np.min([np.linalg.norm(pt-p) for p in (MARKER,after,ORIGINAL_2021_SLIDE_CENTER)])<160:continue
            v=score_window(z,valid,pt,20)
            if v.get("n"):controls.append(v)
    region=site["20"]
    if region.get("n"):
        region["same_pair_20px_control_n"]=len(controls)
        region["same_pair_controls_at_least_published_old_site_positive_gt3_gt5_gt7"]=[
            int(sum(q["fraction_positive_gt3_gt5_gt7"][i]>=region["fraction_positive_gt3_gt5_gt7"][i] for q in controls))
            for i in range(3)]
        region["control_rank_not_a_pvalue"]=True
    if debug is not None:
        preview=np.uint8(np.rint(np.clip(z/8*127+128,0,255)))
        preview[~inspection]=0
        cv2.imwrite(str(debug),preview)
    return {"independent_source_registration_input":registration["source_image_variant"],
      "descriptor_ratio":registration["descriptor_ratio"],
      "registration_inliers":registration["inliers"],
      "registration_withheld_median_px":registration["withheld_median_original_2021_px"],
      "photometry":mode,"gain":gain,
      "nominal_2024_marker_warped_onto_2021":[float(q) for q in after],
      "background_MAD_original_CDR_IoverF":sigma,
      "background_pixel_count":int(back.sum()),
      "valid_common_source_fraction":float(valid.mean()),
      "previously_published_2015_to_2021_site_response":site,
      "same_pair_old_site_control_count":len(controls),
      "candidate_exploration_outside_published_slide_and_both_rounded_camera_markers":seen}
def main():
    p=argparse.ArgumentParser()
    for n in ("source_folder","source_manifest","registration","out","debug_folder"):
        p.add_argument("--"+n.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    meta=json.loads(a.source_manifest.read_text())
    geo=json.loads(a.registration.read_text())
    if geo["schema"]!="Heis-2021-to-2024-true-camera-chirality-source-registration-v2" or geo["source_manifest_SHA256"]!=sha(a.source_manifest):
        raise ValueError("not independently validated true post-2021 source pair")
    pair={r:load(a.source_folder,meta,r) for r in ("before","after")}
    a.debug_folder.mkdir(parents=True,exist_ok=True)
    trials=[]
    for representation,ratio in (("CLAHE",.84),("highpass",.84)):
        reg=model(geo,representation,ratio)
        reg={**reg,"source_image_variant":representation,"descriptor_ratio":ratio}
        for mode in ("calibrated_IoverF_gain_one","off_marker_gain"):
            path=a.debug_folder/f"heis2021to2024_{representation}_{mode}.png"
            trials.append(trial(pair,reg,mode,path))
    result={"schema":"Heis-2021-to-2024-original-calibrated-unreported-interval-screen-v1",
      "source_manifest_SHA256":sha(a.source_manifest),
      "registration_SHA256":sha(a.registration),
      "source_CDR_pair":["M1376643242LC","M1481045431LC"],
      "old_slideregion_center_original_2021_cutout_xy":ORIGINAL_2021_SLIDE_CENTER.tolist(),
      "unsearched_2021_to_2024_interval":True,
      "scanned_only_native_common_patch":True,
      "frozen_details":{"original_CDR_highpass_blur_sigma_px":24,
         "geometries":[["CLAHE",.84,"full_affine"],["highpass",.84,"full_affine"]],
         "photometry":["calibrated_IoverF_gain_one","off_marker_gain"],
         "signed_abs_MAD_thresholds":[3,5,7],"minimum_connected_source_px":20,
         "published_slide_exclusion_radius_px":100,
         "both_nominal_camera_markers_exclusion_radius_px":112},
      "all_geometry_photometry_trials":trials,
      "limits":["This is local exploratory image difference screening, not a lunar landslide detector or independent discovery.",
        "2021 and 2024 have 19-degree incidence-angle difference and reverse source camera line direction.",
        "Previously published 2015-2021 Heis slide is excluded; unknown changes may be shadows/relief/parallax.",
        "No withheld independent geographic source-image controls or repeat acquisition confirmation."]}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"trials":[{"representation":r["independent_source_registration_input"],
       "photometry":r["photometry"],"gain":r["gain"],"mad":r["background_MAD_original_CDR_IoverF"],
       "previous_slide":r["previously_published_2015_to_2021_site_response"]["20"],
       "5MAD":r["candidate_exploration_outside_published_slide_and_both_rounded_camera_markers"]["5"]}
       for r in trials]},indent=2),flush=True)
if __name__=="__main__":main()
