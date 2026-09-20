#!/usr/bin/env python3
"""Search independently registered original Ryder 2022/2024/2026 NAC epochs.

Two predefined step-change tests only, with same-site 2026 April/May repeats:
  A: 2022 -> 2024 positive/negative change persists in BOTH 2026 images;
  B: 2024 -> 2026 positive/negative change in BOTH April and May.
No event name, physical footprint or discovery asserted; all detections are
exploratory under a known published slide development site, and sunlight
differences/absolute DEM remain unresolved.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
import cv2,numpy as np

TAGS=("baseline_2022","followup_2024","followup_2026_April","followup_2026_May")
PAIRS=(("baseline_2022","followup_2024"),
       ("baseline_2022","followup_2026_April"),
       ("baseline_2022","followup_2026_May"),
       ("followup_2024","followup_2026_April"),
       ("followup_2024","followup_2026_May"),
       ("followup_2026_April","followup_2026_May"))
REF=TAGS[0]
N=1281
C=np.array([640.,640.])
EXCLUDE=185
MIN_AREA=20
TH=(2,3,5)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def disk(point,r):
    yy,xx=np.ogrid[:N,:N]
    return (xx-point[0])**2+(yy-point[1])**2<=r*r
def source(folder,manifest,tag):
    row=manifest["source_products"][tag]
    file=folder/(tag+"_original_NAC_CDR_r640.npy")
    if sha(file)!=row["original_native_CDR_patch_npy_sha256"]:
        raise ValueError("NASA original Ryder source SHA mismatch "+tag)
    a=np.load(file,allow_pickle=False)
    if a.dtype!=np.int16 or a.shape!=(N,N):
        raise ValueError("not exact source pixels "+tag)
    m=a>=-32752
    if m.mean()<.88:raise ValueError("too much invalid lunar surface "+tag)
    return a.astype(np.float32)*row["reflectance_scaling_IoverF"],m
def detect(arr,valid,mask,sign,threshold=3):
    pixels=((arr>threshold) if sign=="early_brighter" else (arr< -threshold))&valid&~mask
    n,labels,stats,cent=cv2.connectedComponentsWithStats(pixels.astype(np.uint8),8)
    rows=[]
    for i in range(1,n):
        x,y,w,h,area=map(int,stats[i])
        if area<MIN_AREA:continue
        if min(x,y,N-x-w,N-y-h)<38:continue
        center=cent[i]
        coords=np.column_stack(np.where(labels==i))[:,::-1].astype(float)
        eig=np.maximum(np.linalg.eigvalsh(np.cov(coords,rowvar=False)),0)
        axis=float(math.sqrt((eig[-1]+1e-6)/(eig[0]+1e-6)))
        rows.append({"native_reference_bbox_xywh":[x,y,w,h],
           "centroid_native_2022_source_xy":center.tolist(),
           "connected_original_source_px":area,
           "PCA_elongation_ratio":axis,
           "signed_component_median_MAD":float(np.median(arr[labels==i]))})
    return sorted(rows,key=lambda r:-r["connected_original_source_px"])[:45],len(rows)
def all_epochs(folder,meta,registration):
    if any(registration["selected_off_change_geometry_by_epoch"].get(tag) is None
           for tag in TAGS[1:]):
        raise ValueError("one of Ryder three independent off-feature 2022-based geometry gates FAILED")
    original={k:source(folder,meta,k) for k in TAGS}
    result={REF:original[REF]}
    for tag in TAGS[1:]:
        selected=registration["selected_off_change_geometry_by_epoch"][tag]
        fit=selected["fit"]
        if not fit["registration_gate_passed"] or fit["status"]!="fit":
            raise ValueError("cannot score failed original Ryder source registration")
        M=np.array(fit["matrix_original_epoch_to_original_baseline"],np.float64)
        img,valid=original[tag]
        warped=cv2.warpAffine(img,M,(N,N),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        valid_w=cv2.warpAffine(valid.astype(np.uint8),M,(N,N),
                               flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)>0
        result[tag]=(warped,valid_w)
    return result
def summaries(warped,mode):
    common=np.logical_and.reduce([m for x,m in warped.values()])
    valid=cv2.erode(common.astype(np.uint8),np.ones((9,9),np.uint8))>0
    valid[:38]=False;valid[-38:]=False;valid[:,:38]=False;valid[:,-38:]=False
    geometry=geo["selected_off_change_geometry_by_epoch"]
    positions={tag:(C if tag==REF else
        C@np.array(geometry[tag]["fit"]["matrix_original_epoch_to_original_baseline"])[:,:2].T+
           np.array(geometry[tag]["fit"]["matrix_original_epoch_to_original_baseline"])[:,2])
       for tag in TAGS}
    exclude=np.zeros((N,N),bool)
    for pt in positions.values():exclude|=disk(pt,EXCLUDE)
    off=valid&~exclude
    if off.sum()<120000:raise ValueError("Ryder common source terrain too little for contamination-resistant robust noise")
    base=warped[REF][0]
    gains={}
    if mode=="physical_IoverF_gain_one":
        gains={k:1. for k in TAGS}
    elif mode=="offsite_median_gain":
        for k,(img,mask) in warped.items():
            gain=float(np.median(base[off])/np.median(img[off]))
            if not .5<=gain<=2:raise ValueError("unreasonable Ryder calibration gain "+k)
            gains[k]=gain
    else:raise ValueError("unsupported fixed Ryder normalization")
    adjusted={k:img*gains[k] for k,(img,m) in warped.items()}
    maps={};noises={}
    for earlier,later in PAIRS:
        key=earlier+"__"+later
        difference=np.where(valid,adjusted[earlier]-adjusted[later],0).astype(np.float32)
        base=cv2.GaussianBlur(difference,(0,0),sigmaX=24)
        support=cv2.GaussianBlur(valid.astype(np.float32),(0,0),sigmaX=24)
        residual=difference-base/np.maximum(support,1e-4)
        center=float(np.median(residual[off]))
        mad=float(1.4826*np.median(np.abs(residual[off]-center)))
        if mad<1e-8:raise ValueError("degenerate original NASA Ryder source temporal MAD")
        z=(residual-center)/mad
        maps[key]=z
        noises[key]={"signed_robust_MAD_IoverF":mad,
           "offsite_reference_pixel_count":int(off.sum()),
           "fraction_abs_over3_on_offsite_terrain":float(np.mean(np.abs(z[off])>3))}
    return valid,exclude,positions,gains,adjusted,maps,noises
def evaluate(zmaps,valid,exclude,adjusted):
    candidates={}
    results={}
    for pair,z in zmaps.items():
        results[pair]={}
        for t in TH:
            per={}
            for sign in ("early_brighter","late_brighter"):
                tops,count=detect(z,valid,exclude,sign,t)
                per[sign]={"connected_components_at_least20px":count,
                            "largest_45":tops}
            results[pair][str(t)]=per
    protocols={
      "A_2022_to_2024_and_persistent_both_2026":(
        ["baseline_2022__followup_2024",
         "baseline_2022__followup_2026_April",
         "baseline_2022__followup_2026_May"],
        ["followup_2024__followup_2026_April",
         "followup_2024__followup_2026_May",
         "followup_2026_April__followup_2026_May"]),
      "B_2024_to_2026_repeated_April_and_May":(
        ["followup_2024__followup_2026_April",
         "followup_2024__followup_2026_May"],
        ["baseline_2022__followup_2024",
         "followup_2026_April__followup_2026_May"]),
    }
    for name,(required,comparators) in protocols.items():
        candidates[name]={}
        for sign in ("early_brighter","late_brighter"):
            selection=valid&~exclude
            for name_key in required:
                z=zmaps[name_key]
                selection&=z>3 if sign=="early_brighter" else z< -3
            count,lab,stats,cent=cv2.connectedComponentsWithStats(selection.astype(np.uint8),8)
            objects=[]
            for i in range(1,count):
                x,y,w,h,area=map(int,stats[i])
                if area<MIN_AREA or min(x,y,N-x-w,N-y-h)<38:continue
                center=cent[i]
                member=lab==i
                eig=np.maximum(np.linalg.eigvalsh(np.cov(np.column_stack(np.where(member))[:,::-1],rowvar=False)),0)
                aspect=float(math.sqrt((eig[-1]+1e-6)/(eig[0]+1e-6)))
                rows={key:{"median_MAD":float(np.median(zmaps[key][member])),
                    "fraction_ABS_gt3MAD":float(np.mean(np.abs(zmaps[key][member])>3)),
                    "fraction_ABS_gt5MAD":float(np.mean(np.abs(zmaps[key][member])>5))}
                    for key in required+comparators}
                epoch_if={k:float(np.median(img[member])) for k,img in adjusted.items()}
                objects.append({"centroid_original_2022_cutout_xy":center.tolist(),
                   "bbox_original_2022_cutout_xywh":[x,y,w,h],
                   "consensus_original_NAC_source_px":area,
                   "consensus_axis_ratio":aspect,
                   "required_sign":sign,
                   "physical_source_median_adjusted_IoverF_each_epoch":epoch_if,
                   "fixed_pairwise_residuals_with_comparators":rows,
                   "distance_to_known_published_Ryder_coordinate_marker_px":float(np.linalg.norm(center-C)),
                   "scientific_status":"unclassified explorational NASA temporal component; NO new lunar landslide inferred"})
            candidates[name][sign]={"count_components_20px":len(objects),
                  "top_40":sorted(objects,key=lambda o:-o["consensus_original_NAC_source_px"])[:40]}
    return results,candidates
def main():
    p=argparse.ArgumentParser()
    for name in ("source_folder","source_manifest","registration","debug_folder","out"):
        p.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    a=p.parse_args()
    global geo
    geo=json.loads(a.registration.read_text())
    meta=json.loads(a.source_manifest.read_text())
    if geo["schema"]!="Ryder-four-original-calibrated-NAC-off-marker-terrain-registration-v1" or
       geo["source_manifest_SHA256"]!=sha(a.source_manifest.read_bytes()):
        raise ValueError("not a frozen camera-ground original NASA Ryder geometry")
    if meta["schema"]!="Ryder-2022-2024-2026-four-original-calibrated-source-r640-v1":
        raise ValueError("not exact official four Ryder source images")
    warped=all_epochs(a.source_folder,meta,geo)
    trials=[]
    a.debug_folder.mkdir(parents=True,exist_ok=True)
    for mode in ("physical_IoverF_gain_one","offsite_median_gain"):
        valid,excluded,markers,gains,adj,zmap,noise=summaries(warped,mode)
        results,objects=evaluate(zmap,valid,excluded,adj)
        for key,z in zmap.items():
            png=a.debug_folder/(mode+"_"+key+"_normalized_Ryder_change.png")
            render=np.uint8(np.rint(np.clip(128+127*z/8,0,255)))
            render[~(valid&~excluded)]=0
            cv2.imwrite(str(png),render)
        trials.append({"photometry":mode,
          "original_four_epoch_common_valid_fraction":float(valid.mean()),
          "source_site_and_original_marker_excluded_fraction":float(excluded.mean()),
          "camera_markers_registered_to_original_2022_native_cutout":{
              k:np.array(x).tolist() for k,x in markers.items()},
          "offsite_source_reflectance_gain_each_epoch":gains,
          "independent_original_NAC_pairwise_noise":noise,
          "all_six_pairwise_signed_component_sweeps":results,
          "two_predeclared_multiepoch_persistent_change_patterns":objects})
    out={"schema":"Ryder-exact-original-2022-2024-2026-persistent-temporal-difference-pilot-v1",
       "original_NASA_source_manifest_SHA256":sha(a.source_manifest.read_bytes()),
       "frozen_source_registration_SHA256":sha(a.registration.read_bytes()),
       "original_source_products":[meta["source_products"][t]["CDR_product"] for t in TAGS],
       "chronology":list(TAGS),
       "fixed_photometries":["physical_IoverF_gain_one","offsite_median_gain"],
       "fixed_signed_original_source_MAD_thresholds":list(TH),
       "source_temporal_highpass_sigma_px":24,
       "minimum_connected_temporal_source_area_px":MIN_AREA,
       "source_camera_markers_excluded_radius_px":EXCLUDE,
       "selection":"Original off-marker-only camera-constrained SIFT fits were frozen before any NASA temporal residuals",
       "all_fixed_trials":trials,
       "limitations":["No original event classification, absolute DEM geodesy, statistically independent event-wise specificity or discovery claim.",
          "Ryder already has a published slide by 2020; novel interval ≠ novel feature.",
          "2026 April-May repeat is closer in time but may share solar/processing biases.",
          "Any surviving component requires image-level geological morphology, cross-epoch coordinate confirmation and hard negatives."]}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({"trials":[{
         "mode":x["photometry"],"noise":x["independent_original_NAC_pairwise_noise"],
         "persistent":{
            k:{s:{"count":v["count_components_20px"],"top":v["top_40"][:6]}
               for s,v in row.items()}
            for k,row in x["two_predeclared_multiepoch_persistent_change_patterns"].items()}}
         for x in trials]},indent=2),flush=True)
if __name__=="__main__":main()
