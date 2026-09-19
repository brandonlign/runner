#!/usr/bin/env python3
"""Fixed sparse-sign residual component audit on an ALREADY published landslide.

No new detection, p value, polygon agreement, or mass-wasting classification
can follow from this within-pair development diagnostic alone.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from isef4_gambart_cdr_generic_residual_pilot import read_pair, disk, control_centers

R=(32,64,128)
SIGMAS=(5.,7.)
AREA=12
CENTER=np.float64([512.,512.])
KERNEL=np.ones((9,9),np.uint8)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def group_components(residual,valid,threshold,positive):
 mask=((residual>=threshold) if positive else (residual<=-threshold)) & valid
 number, lab, stats, cent=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
 selected=[]
 for i in range(1,number):
  x,y,w,h,area=map(int,stats[i])
  if area<AREA:continue
  point=cent[i]
  selected.append({"centroid_xy":point.tolist(),"area_px":area,
                   "rect_xywh":[x,y,w,h],
                   "sign":"positive" if positive else "negative"})
 return selected

def summarize(components,center,r):
 rows=[v for v in components if np.linalg.norm(np.array(v["centroid_xy"])-center)<=r]
 return {"count_centroids":len(rows),"max_component_area_px":max((x["area_px"] for x in rows),default=0),
         "sum_component_area_px":sum(x["area_px"] for x in rows),
         "largest_three":[dict(x) for x in sorted(rows,key=lambda a:-a["area_px"])[:3]]}

def evaluate(pair,reg,mode,out):
 b,bmask=pair["before"];a,amask=pair["after"]
 M=np.asarray(reg["matrix_after_to_before"],dtype=np.float64)
 if M.shape!=(2,3) or not np.isfinite(M).all():raise ValueError("not a valid frozen affine")
 h,w=b.shape
 aw=cv2.warpAffine(a,M,(w,h),flags=cv2.INTER_LINEAR,
                   borderMode=cv2.BORDER_CONSTANT,borderValue=0)
 av=cv2.warpAffine(amask.astype(np.uint8),M,(w,h),flags=cv2.INTER_NEAREST,
                   borderMode=cv2.BORDER_CONSTANT,borderValue=0).astype(bool)
 valid=cv2.erode((bmask&av).astype(np.uint8),KERNEL,iterations=1).astype(bool)
 after=cv2.transform(CENTER.reshape(1,1,2).astype(np.float32),M)[0,0].astype(np.float64)
 anchors={"before_camera":CENTER,"mapped_after_camera":after}
 outside=valid.copy()
 for center in anchors.values():outside &= ~disk(b.shape,center,160)
 if outside.sum()<5000:raise ValueError("insufficient off-marker source support")
 gain=1.
 if mode=="outside-marker-median-gain":
  denominator=np.median(aw[outside])
  if denominator<=0:raise ValueError("bad reference scene level")
  gain=float(np.median(b[outside])/denominator)
  if not .5<=gain<=2:raise ValueError("unstable gain")
 signed=np.where(valid,b-gain*aw,0).astype(np.float32)
 smooth=cv2.GaussianBlur(signed,(0,0),sigmaX=24)
 weight=cv2.GaussianBlur(valid.astype(np.float32),(0,0),sigmaX=24)
 detail=signed-smooth/np.maximum(weight,1e-4)
 center_median=float(np.median(detail[outside]))
 sigma=float(1.4826*np.median(np.abs(detail[outside]-center_median)))
 if sigma<1e-7:raise ValueError("sparse contrast noise estimate degenerate")
 thresholds={}
 for factor in SIGMAS:
  threshold=factor*sigma
  comps=group_components(detail-center_median,valid,threshold,True)
  comps+=group_components(detail-center_median,valid,threshold,False)
  windows={}
  for radius in R:
   controls=[]
   for c in control_centers(b.shape,radius,list(anchors.values())):
    cp=np.asarray(c,dtype=np.float64)
    if (disk(b.shape,cp,radius)&valid).sum()<.90*disk(b.shape,cp,radius).sum():continue
    controls.append(summarize(comps,cp,radius))
   observed={}
   for name,pt in anchors.items():
    region=disk(b.shape,pt,radius)
    fraction=float((valid&region).sum()/region.sum())
    row={"center_xy":pt.tolist(),"valid_fraction":fraction}
    if fraction>=.90:
     row.update(summarize(comps,pt,radius))
     if controls:
      metric=[z["max_component_area_px"] for z in controls]
      row["control_count"]=len(metric)
      row["control_max_component_area_px"]=metric
      row["count_controls_max_component_area_at_least_anchor"]=int(sum(z>=row["max_component_area_px"] for z in metric))
      row["descriptive_control_rank_not_pvalue"]=True
    else:row["status"]="unassessable"
    observed[name]=row
   windows[str(radius)]={"anchors":observed,"control_count":len(controls)}
  thresholds[str(int(factor))]={"absolute_i_over_f_threshold":float(threshold),
     "components_minimum_area_px":AREA,"components_total":len(comps),"windows":windows}
  image=np.clip((detail-center_median)/(7*sigma)*127+128,0,255).astype(np.uint8)
  image[~valid]=0
  filename=out.parent/(f"gambart_sparse_{reg['model']}_{mode}_{int(factor)}sigma.png")
  cv2.imwrite(str(filename),image)
 return {"registration_model":reg["model"],"photometry":mode,"gain":gain,
         "off_marker_median_residual_i_over_f":center_median,
         "off_marker_MAD_gaussian_sigma_i_over_f":sigma,
         "active_eroded_support_fraction":float(valid.mean()),
         "anchors_xy":{k:v.tolist() for k,v in anchors.items()},
         "thresholds":thresholds}

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--source-folder",type=Path,required=True)
 p.add_argument("--source-manifest",type=Path,required=True)
 p.add_argument("--registration",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 args=p.parse_args()
 meta=json.loads(args.source_manifest.read_text())
 reg=json.loads(args.registration.read_text())
 if meta.get("schema")!="exact-Gambart-C-two-epoch-native-CDR-r512-v1":
  raise ValueError("not verified Gambart calibrated source inventory")
 if reg.get("source_manifest_sha256")!=sha(args.source_manifest):
  raise ValueError("registration provenance mismatch")
 args.out.parent.mkdir(parents=True,exist_ok=True)
 pair=read_pair(args.source_folder,meta)
 trials=[]
 for fit in reg["model_trials"]:
  if fit.get("status")!="fit" or fit.get("preflight_gate_passed") is not True:
   trials.append({"model":fit["model"],"status":"registration_not_usable"})
   continue
  for mode in ("original-IoverF","outside-marker-median-gain"):
   trials.append(evaluate(pair,fit,mode,args.out))
 result={"schema":"known-Gambart-C-sparse-signed-CDR-components-v1",
         "published_event_not_new":True,"source_manifest_sha256":sha(args.source_manifest),
         "registration_sha256":sha(args.registration),
         "fixed_window_radii_px":list(R),"fixed_thresholds_MAD_sigma":list(SIGMAS),
         "fixed_min_connected_component_area_px":AREA,"background_blur_sigma_px":24,
         "support_erosion_9x9":True,"all_models_and_modes":trials,
         "limits":["These are source-pixel relative affines, NOT independent absolute DEM-projected pixels.",
          "Published coordinate is rounded and lies ~58 source pixels from its opposite camera marker under image registration.",
          "Signed high-pass residuals may represent shadow or parallax; component areas are NOT landslide areas.",
          "Controls are correlated and all from the known event pair; no p-value or target-disjoint recall can be calculated.",
          "This audit does not verify the original author-annotated landslide polygon."]}
 args.out.write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps({"diagnostic":str(args.out),"trial_count":len(trials),
                  "median_abs_noise":[r.get("off_marker_MAD_gaussian_sigma_i_over_f") for r in trials]}),flush=True)
if __name__=="__main__":main()
