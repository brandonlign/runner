#!/usr/bin/env python3
"""Trace only stable low-threshold post-2021 Heis spots through 2015/2021/2024.

All source pixels are hash-checked originals; all image transformations come
from PREVIOUS independent off-marker fits. Candidate locations are extracted
automatically from frozen prior four-trial screen, not invented after seeing
third-epoch pixels. A stable spot is still NOT a new landslide.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
import cv2
import numpy as np

RADS=(5,9)
ANNULUS=(18,34)
CENTER=np.array([384.,384.])
OLD_SLIDE=np.array([355.3774151321759,350.80725149578325])
MIN_N=20
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def original(folder,path,checksum,scale):
    fn=folder/path
    if sha(fn)!=checksum:raise ValueError("NASA original CDR SHA mismatch "+path)
    a=np.load(fn,allow_pickle=False)
    if a.shape!=(769,769) or a.dtype!=np.int16:raise ValueError("native source pixel geometry changed")
    mask=a>=-32752
    return a.astype(np.float32)*scale,mask
def patches(p2021,p1515,folder21,folder15):
    prior=p1515["epochs"];post=p2021["stages"]
    before15=prior["before"]
    before21=post["before_2021_reused_verified_original_CDR"]
    after24=post["after_2024_new_verified_original_CDR"]
    if before21["npy_SHA256"]!=prior["after"]["saved_npy_SHA256"]:
        raise ValueError("same EXACT 2021 image not shared by independent earlier 2015-2021 experiment")
    return {
       "2015":original(folder15,"before_Heis_original_CDR_native_r384.npy",
                      before15["saved_npy_SHA256"],before15["pixel_scale_IoverF"]),
       "2021":original(folder21,"before_2021_Heis_original_CDR_native_r384.npy",
                      before21["npy_SHA256"],before21["scale"]),
       "2024":original(folder21,"after_2024_Heis_original_CDR_native_r384.npy",
                      after24["npy_SHA256"],after24["scale"])
    }
def candidates(screen):
    trials=screen["all_geometry_photometry_trials"]
    if len(trials)!=4 or {z["independent_source_registration_input"] for z in trials}!={"CLAHE","highpass"}:
        raise ValueError("frozen four original post-2021 source tests changed")
    first=trials[0]["candidate_exploration_outside_published_slide_and_both_rounded_camera_markers"]["3"]
    used=set();out=[]
    for group in first:
        for original in group["largest_40_outside_already_published_site"]:
            xy=np.array(original["centroid_2021_source_cutout_xy"])
            matches=[]
            for t,trial in enumerate(trials):
                aligned=[]
                for signed in trial["candidate_exploration_outside_published_slide_and_both_rounded_camera_markers"]["3"]:
                    if signed["sign"]!=group["sign"]:continue
                    aligned.extend(z for z in signed["largest_40_outside_already_published_site"]
                                   if np.linalg.norm(np.array(z["centroid_2021_source_cutout_xy"])-xy)<6)
                if aligned:
                    match=min(aligned,key=lambda z:np.linalg.norm(np.array(z["centroid_2021_source_cutout_xy"])-xy))
                    matches.append({"trial":t,"area":match["area_source_px"],
                       "PCA_axis_ratio":match["PCA_axis_ratio"],
                       "bbox_xywh":match["bbox_source_xywh"],
                       "centroid_xy":match["centroid_2021_source_cutout_xy"]})
            if len(matches)!=4:continue
            pts=np.asarray([z["centroid_xy"] for z in matches])
            centroid=np.median(pts,axis=0)
            key=(group["sign"],round(centroid[0]/5),round(centroid[1]/5))
            if key in used:continue
            used.add(key)
            out.append({"sign":group["sign"],"frozen_consensus_center_2021_xy":centroid.tolist(),
                 "source_screen_four_trials":matches,
                 "minimum_area_four_trials":int(min(z["area"] for z in matches)),
                 "mean_aspect_four_trials":float(np.mean([z["PCA_axis_ratio"] for z in matches]))})
    return out
def disk(xy,r):
    yy,xx=np.ogrid[:769,:769]
    return (xx-xy[0])**2+(yy-xy[1])**2<=r*r
def sample(data,pt):
    inner={}
    annulus=disk(pt,ANNULUS[1])&~disk(pt,ANNULUS[0])
    for r in RADS:
        interior=disk(pt,r)
        if any(np.sum(mask&interior)<.90*np.sum(interior)
               or np.sum(mask&annulus)<.90*np.sum(annulus)
               for _name,(img,mask) in data.items()):
            inner[str(r)]={"status":"source_patch_incomplete"};continue
        epochs={}
        for name,(img,mask) in data.items():
            val=img[interior&mask]
            surrounding=img[annulus&mask]
            epochs[name]={"median_reflectance_IoverF":float(np.median(val)),
                          "mean_reflectance_IoverF":float(np.mean(val)),
                          "local_disk_minus_same_epoch_annulus_IoverF":float(np.median(val)-np.median(surrounding)),
                          "local_dark_fraction_relative_to_surrounding":float(np.mean(val<np.percentile(surrounding,10))),
                          "local_bright_fraction_relative_to_surrounding":float(np.mean(val>np.percentile(surrounding,90)))}
        epoch_15,epoch_21,epoch_24=[epochs[str(y)] for y in (2015,2021,2024)]
        def delta(field,a,b):return b[field]-a[field]
        inner[str(r)]={"status":"assessable","epochs":epochs,
              "absolute_disk_median_delta_2015_to_2021_IoverF":delta("median_reflectance_IoverF",epoch_15,epoch_21),
              "absolute_disk_median_delta_2021_to_2024_IoverF":delta("median_reflectance_IoverF",epoch_21,epoch_24),
              "local_contrast_delta_2015_to_2021_IoverF":delta("local_disk_minus_same_epoch_annulus_IoverF",epoch_15,epoch_21),
              "local_contrast_delta_2021_to_2024_IoverF":delta("local_disk_minus_same_epoch_annulus_IoverF",epoch_21,epoch_24)}
    return inner
def main():
    p=argparse.ArgumentParser()
    for name in ("source_2021_2024_folder","source_2015_2021_folder","manifest_2021_2024",
            "manifest_2015_2021","reg_2015_2021","reg_2021_2024","screen","out"):
        p.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    old=json.loads(a.manifest_2015_2021.read_text())
    recent=json.loads(a.manifest_2021_2024.read_text())
    oldreg=json.loads(a.reg_2015_2021.read_text())
    newreg=json.loads(a.reg_2021_2024.read_text())
    screen=json.loads(a.screen.read_text())
    if oldreg["source_manifest_sha256"]!=sha(a.manifest_2015_2021) or newreg["source_manifest_SHA256"]!=sha(a.manifest_2021_2024):
        raise ValueError("registration sources no longer authentic")
    if screen["source_manifest_SHA256"]!=sha(a.manifest_2021_2024) or screen["registration_SHA256"]!=sha(a.reg_2021_2024):
        raise ValueError("third epoch not independent of frozen 2021-2024 screening evidence")
    imgs=patches(recent,old,a.source_2021_2024_folder,a.source_2015_2021_folder)
    M2015=np.asarray(next(z["matrix_after_to_before"] for z in oldreg["model_trials"]
                          if z["model"]=="full_affine" and z["preflight_gate_passed"]),float)
    M2024=np.asarray(next(z["matrix_original_2024_to_original_2021"] for q in newreg["all_models"]
                        if q.get("photometric_input")=="CLAHE" and q.get("rot_ccw_90deg")==0 and q.get("flip_after_rotation") is True
                        and q.get("ratio")==.84 for z in q["models"]
                        if z["model"]=="full_affine" and z["gate"]),float)
    common={"2021":imgs["2021"]}
    for epoch,m in (("2015",cv2.invertAffineTransform(M2015)),("2024",M2024)):
        arr,mask=imgs[epoch]
        warp=cv2.warpAffine(arr,m,(769,769),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        valid=cv2.warpAffine(mask.astype(np.uint8),m,(769,769),
                       flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)>0
        common[epoch]=(warp,valid)
    common_mask=cv2.erode(np.logical_and.reduce([q[1] for q in common.values()]).astype(np.uint8),
                         np.ones((9,9),np.uint8))>0
    checked={k:(img,mask&common_mask) for k,(img,mask) in common.items()}
    spots=candidates(screen)
    if len(spots)<1:raise ValueError("no prespecified stable 3MAD spots")
    for item in spots:
        xy=np.array(item["frozen_consensus_center_2021_xy"])
        item["three_epoch_original_CDR_local_photometry"]=sample(checked,xy)
        item["before_2021_full_original_source_xy"]=(xy+np.array([762.,33490.])).tolist()
        item["2015_original_camera_source_cutout_xy"]=(
             xy@M2015[:,:2].T+M2015[:,2]).tolist()
        item["2024_original_camera_source_cutout_xy"]=(
             xy@np.linalg.inv(M2024[:,:2]).T-np.linalg.solve(M2024[:,:2],M2024[:,2])).tolist()
    historical=sample(checked,OLD_SLIDE)
    evidence={"schema":"Heis-three-original-observation-weak-spot-temporal-control-v1",
        "source_2015_2021_SHA256":sha(a.manifest_2015_2021),
        "source_2021_2024_SHA256":sha(a.manifest_2021_2024),
        "source_2021_2024_screen_SHA256":sha(a.screen),
        "registration_2015_2021_SHA256":sha(a.reg_2015_2021),
        "registration_2021_2024_SHA256":sha(a.reg_2021_2024),
        "epochs":["2015-09-27","2021-05-26","2024-09-15"],
        "source_products":["M1197976848LC","M1376643242LC","M1481045431LC"],
        "stable_3MAD_2021_bright_candidate_n":len(spots),
        "stable_four_source_screen_consensus_spots":spots,
        "previous_published_2015_to_2021_landslide_2021_source_center":OLD_SLIDE.tolist(),
        "previous_published_site_three_epoch_original_CDR_local_photometry":historical,
        "three_epoch_native_2021_common_valid_fraction":float(common_mask.mean()),
        "fixed_disk_radii_source_px":list(RADS),
        "fixed_local_annulus_source_px":list(ANNULUS),
        "scientific_limits":["Third epoch is pre-event 2015 and already published 2021; no true fourth independent post-2024 lunar observation.",
           "Six small 3MAD features selected on 2021-2024 data; retrospective validation on older 2015 is not an untouched positive detection.",
           "2024 incidence angle differs by ~19 degrees from 2021 and any local reflectance change can be shadow geometry.",
           "Only local source relative affines used; absolute physical surface DEM not verified.",
           "No unpublished landslide is claimed."]}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps({"three_epoch_common_fraction":evidence["three_epoch_native_2021_common_valid_fraction"],
       "candidate_count":len(spots),
       "spots":[{"xy":q["frozen_consensus_center_2021_xy"],"min_area":q["minimum_area_four_trials"],
          "r5":q["three_epoch_original_CDR_local_photometry"]["5"]}
          for q in spots],"known_site_r5":historical["5"]},indent=2),flush=True)
if __name__=="__main__":main()
