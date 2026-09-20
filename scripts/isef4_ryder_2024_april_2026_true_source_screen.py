#!/usr/bin/env python3
"""Original Ryder 2024->April2026 true source temporal screen; no event claim.

Two independently off-source terrain-recovered alignments (CLAHE / highpass)
and two frozen original calibrated I/F scalings. The published Ryder site
and both nominal source markers are excluded from novelty search. Preserve
signed residuals, spatial connected components and hard controls.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
import cv2

N=1281;C=np.array([640.,640.])
B="followup_2024"
A="followup_2026_April"
TH=(3,5,7)
KNOWN_EXCLUSION=185
def sha(p):return hashlib.sha256(p if isinstance(p,bytes) else p.read_bytes()).hexdigest()
def load(folder,meta,key):
    row=meta["source_products"][key]
    name=folder/(key+"_original_NAC_CDR_r640.npy")
    if sha(name)!=row["original_native_CDR_patch_npy_sha256"]:
        raise ValueError("not exact original camera-ground NASA calibrated Ryder "+key)
    arr=np.load(name,allow_pickle=False)
    if arr.shape!=(N,N) or arr.dtype!=np.int16:raise ValueError("not original NAC source cutout")
    return arr.astype(np.float32)*row["reflectance_scaling_IoverF"],arr>=-32752
def disk(pt,r):
    yy,xx=np.ogrid[:N,:N]
    return (xx-pt[0])**2+(yy-pt[1])**2<=r*r
def eligible_geometry(geo,kind):
    rows=[r for r in geo["all_source_geometry_models"] if r["source"]==A and
          r["preprocessing"]==kind and r["ratio"]==.76 and
          r["rot_ccw"]==2 and r["flip_h"] is True and
          r["fit"]["registration_gate_passed"]]
    if len(rows)!=1:raise ValueError("not frozen independent "+kind+" Ryder original off-site geometry")
    r=rows[0]
    if r["fit"]["withheld_median_baseline_source_px"]>2:
        raise ValueError("withheld source terrain registration not strong enough")
    return r
def rows(z,mask,forbidden,threshold,sign):
    binary=((z>threshold) if sign=="2024_brighter" else (z< -threshold))&mask&~forbidden
    n,label,stat,cen=cv2.connectedComponentsWithStats(binary.astype(np.uint8),8)
    found=[]
    for i in range(1,n):
        x,y,w,h,area=map(int,stat[i])
        if area<20 or min(x,y,N-x-w,N-y-h)<35:continue
        ys,xs=np.where(label==i)
        eig=np.maximum(np.linalg.eigvalsh(np.cov(np.column_stack([xs,ys]),rowvar=False)),0)
        found.append({"bbox_2024_native_cutout_xywh":[x,y,w,h],
         "centroid_2024_native_cutout_xy":cen[i].tolist(),
         "original_connected_pixel_count":area,
         "axis_ratio":float(math.sqrt((eig[-1]+1e-6)/(eig[0]+1e-6))),
         "signed_median_original_CDR_change_MAD":float(np.median(z[label==i])),
         "distance_to_published_Ryder_site_camera_marker_px":float(np.linalg.norm(cen[i]-C))})
    return sorted(found,key=lambda r:-r["original_connected_pixel_count"])[:60],len(found)
def trial(images,registration,phot,debug):
    before,bm=images[B];after,am=images[A]
    M=np.asarray(registration["fit"]["matrix_original_epoch_to_original_baseline"],dtype=float)
    warped=cv2.warpAffine(after,M,(N,N),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    avalid=cv2.warpAffine(am.astype(np.uint8),M,(N,N),
             flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)>0
    good=cv2.erode((bm&avalid).astype(np.uint8),np.ones((9,9),np.uint8))>0
    moved=C@M[:,:2].T+M[:,2]
    excluded=disk(C,KNOWN_EXCLUSION)|disk(moved,KNOWN_EXCLUSION)
    background=good&~excluded
    if background.sum()<150000:raise ValueError("too few Ryder off-slide common pixel controls")
    gain=1.
    if phot=="offsite_gain":
        gain=float(np.median(before[background])/np.median(warped[background]))
        if not .5<=gain<=2:raise ValueError("implausible NASA I/F normalizing gain")
    elif phot!="physical_IoverF_gain_one":
        raise ValueError("unfrozen source photometry")
    difference=np.where(good,before-gain*warped,0).astype(np.float32)
    smoothed=cv2.GaussianBlur(difference,(0,0),sigmaX=24)
    support=cv2.GaussianBlur(good.astype(np.float32),(0,0),sigmaX=24)
    detail=difference-smoothed/np.maximum(support,1e-4)
    middle=float(np.median(detail[background]))
    mad=float(1.4826*np.median(np.abs(detail[background]-middle)))
    if mad<=1e-8:raise ValueError("original NASA Ryder temporal noise is degenerate")
    z=(detail-middle)/mad
    inspect=good.copy();inspect[:35]=False;inspect[-35:]=False;inspect[:,:35]=False;inspect[:,-35:]=False
    peaks={}
    for t in TH:
        peaks[str(t)]={}
        for sign in ("2024_brighter","2026_April_brighter"):
            cs,n=rows(z,inspect,excluded,t,sign)
            peaks[str(t)][sign]={"count_ge20_original_px":n,"largest_60":cs}
    preview=np.uint8(np.rint(np.clip(z/8*127+128,0,255)))
    preview[~inspect]=0
    cv2.imwrite(str(debug),preview)
    return {"source_geometric_model":{
      "preprocessing":registration["preprocessing"],"orientation_rot_ccw":registration["rot_ccw"],
      "orientation_horizontal_flip":registration["flip_h"],"source_sift_ratio":registration["ratio"],
      "inliers_outside_site":registration["fit"]["training_inliers"],
      "withheld_terrain_median_native_px":registration["fit"]["withheld_median_baseline_source_px"],
      "withheld_fraction_lt3_native_px":registration["fit"]["withheld_fraction_under_3px"],
      "original_2026_camera_marker_mapped_to_2024_xy":moved.tolist()},
      "photometry":phot,"original_reflectance_gain":gain,
      "original_common_valid_fraction":float(good.mean()),
      "background_original_pixel_count":int(background.sum()),
      "background_original_calibrated_IoverF_MAD":mad,
      "fraction_offsite_positive_3_5_7_MAD":[float(np.mean(z[background]>t)) for t in TH],
      "fraction_offsite_negative_3_5_7_MAD":[float(np.mean(z[background]< -t)) for t in TH],
      "novelty_screen_excluding_original_published_site_and_camera_centers":peaks}
def main():
    p=argparse.ArgumentParser()
    for key in ("source_folder","source_manifest","registration","out","debug_folder"):
        p.add_argument("--"+key.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    meta=json.loads(a.source_manifest.read_text())
    geo=json.loads(a.registration.read_text())
    if meta["schema"]!="Ryder-2022-2024-2026-four-original-calibrated-source-r640-v1" or \
        geo["schema"]!="Ryder-four-original-calibrated-NAC-off-marker-terrain-registration-v1" or \
        geo["reference_epoch"]!=B or geo["source_manifest_SHA256"]!=sha(a.source_manifest):
        raise ValueError("not authentic pre-change Ryder 2024 to April 2026 NASA source geometry")
    images={k:load(a.source_folder,meta,k) for k in (B,A)}
    a.debug_folder.mkdir(parents=True,exist_ok=True)
    trials=[]
    for kind in ("CLAHE","highpass"):
        reg=eligible_geometry(geo,kind)
        for phot in ("physical_IoverF_gain_one","offsite_gain"):
            debug=a.debug_folder/f"original_Ryder_2024_to_April2026_{kind}_{phot}.png"
            trials.append(trial(images,reg,phot,debug))
    results={"schema":"Ryder-exact-original-NAC-2024-April2026-temporal-screen-v1",
       "2024_source_product":meta["source_products"][B]["CDR_product"],
       "2026_April_source_product":meta["source_products"][A]["CDR_product"],
       "source_manifest_SHA256":sha(a.source_manifest),
       "geometry_frozen_before_temporal_differences_SHA256":sha(a.registration),
       "published_Ryder_site_and_source_marker_excluded_native_source_radius_px":KNOWN_EXCLUSION,
       "original_native_source_signed_component_thresholds_MAD":list(TH),
       "minimum_connected_source_pixels":20,
       "all_four_fixed_registration_photometry_trials":trials,
       "scientific_status":"exploratory temporal residual screening only; no confirmed new landslide",
       "limitations":["2022 and May2026 images did not pass original source terrain registration; they cannot validate temporal features here.",
          "2024 and April2026 still differ in illumination and spacecraft viewing geometry; no local DEM/BRDF correction.",
          "Original published Ryder slide excluded from novelty candidate search.",
          "Same-pair off-site pixel control is not an event false-discovery p-value."]}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(results,indent=2)+"\n")
    print(json.dumps({"trials":[{"geometry":r["source_geometric_model"],
      "photometry":r["photometry"],"gain":r["original_reflectance_gain"],
      "mad":r["background_original_calibrated_IoverF_MAD"],
      "components":{t:{sign:{"count":v["count_ge20_original_px"],"top":v["largest_60"][:10]}
          for sign,v in row.items()}
           for t,row in r["novelty_screen_excluding_original_published_site_and_camera_centers"].items()}}
      for r in trials]},indent=2),flush=True)
if __name__=="__main__":main()
