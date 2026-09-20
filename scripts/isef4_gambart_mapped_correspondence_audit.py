#!/usr/bin/env python3
"""Reproduce exact published Gambart C sphere-map correspondence and Figure S5 crosswalk.

This is development-only. Ground coordinates agreeing by construction on the
same spherical map are NOT independent physical terrain co-registration.
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
import rasterio

PAIR_IDS={"before":"M1138987659LE","after":"M1200206882LE"}
ZIP_SHA="132f3d2c2d6c8a5fcb102fe9dcfa5e2d33c6e60b6600c1c94d0d2bafb282c233"
FIG_SHA="3d0e494c40b92e7de66ce54f8317c646ad1d8a19e328bc2811cd7cc13d48dc7f"
MARKER=np.array([253.5,253.3819459058],np.float64)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def browse(im):
 lo,hi=np.nanpercentile(im,[1,99.5])
 if not hi>lo:raise ValueError("bad source stretch")
 return np.rint(np.clip((im-lo)/(hi-lo)*255,0,255)).astype("uint8")
def descr(im,n=8000):
 sift=cv2.SIFT_create(nfeatures=n,contrastThreshold=.007,edgeThreshold=18,sigma=1.3)
 im=cv2.createCLAHE(clipLimit=2,tileGridSize=(8,8)).apply(im)
 return sift.detectAndCompute(im,None)
def good_matches(desc1,desc2,ratio):
 if desc1 is None or desc2 is None:return []
 raw=cv2.BFMatcher(cv2.NORM_L2).knnMatch(desc1,desc2,k=2)
 return [a for pair in raw if len(pair)==2 for a,b in [pair] if a.distance<ratio*b.distance]
def fit(x,y,model,thresh=2.,seed=20260919):
 method=cv2.estimateAffinePartial2D if model=="partial_affine" else cv2.estimateAffine2D
 if len(x)<6:return {"status":"fewer_than_six_pairs","pairs":len(x)}
 cv2.setRNGSeed(seed)
 M,mask=method(x.astype(np.float32),y.astype(np.float32),method=cv2.RANSAC,
               ransacReprojThreshold=thresh,maxIters=15000,confidence=.999,
               refineIters=30)
 if M is None or mask is None:return {"status":"no_ransac_consensus","pairs":len(x)}
 members=mask.reshape(-1).astype(bool)
 return {"status":"fit","pairs":len(x),"inliers":int(members.sum()),
         "matrix":M.tolist(),"inlier_fraction":float(members.mean())}
def read_maps(folder,marker_proof):
 maps={}
 for role in ("before","after"):
  stage=marker_proof["stages"][role+"_mapped_location"]
  cube=folder/f"{role}.commonmap.cub"
  if sha(cube.read_bytes())!=stage["output_mapped_cube_sha256"]:
   raise ValueError("exact source spherical cube SHA mismatch "+role)
  with rasterio.open(cube) as src:
   im=src.read(1,masked=True).filled(np.nan)
   if (im.shape!=(506,505) or src.count!=1 or abs(src.transform.a-1.2)>1e-6):
    raise ValueError("unrecognized fixed common-sphere map raster")
   maps[role]=im
 return maps
def pair_geometry(im):
 before=browse(im["before"]);after=browse(im["after"])
 bk,bd=descr(before,5000);ak,ad=descr(after,5000)
 match=good_matches(ad,bd,.75)
 x=np.float64([ak[m.queryIdx].pt for m in match])
 y=np.float64([bk[m.trainIdx].pt for m in match])
 off=(np.linalg.norm(x-MARKER,axis=1)>48)&(np.linalg.norm(y-MARKER,axis=1)>48)
 x=x[off];y=y[off]
 if len(x)<100:raise RuntimeError("not enough matches outside source marker")
 cellx=np.minimum(7,(y[:,0]/before.shape[1]*8).astype(int))
 celly=np.minimum(7,(y[:,1]/before.shape[0]*8).astype(int))
 train=(cellx*17+celly*7)%5!=0
 rows=[]
 for model in ("partial_affine","full_affine"):
  r=fit(x[train],y[train],model)
  if r["status"]=="fit":
   M=np.float64(r["matrix"])
   estimated=MARKER@M[:,:2].T+M[:,2]
   withheld=x[~train]@M[:,:2].T+M[:,2]
   errors=np.linalg.norm(withheld-y[~train],axis=1)
   r.update({"withheld_matches":int((~train).sum()),
      "withheld_median_map_px":float(np.median(errors)),
      "withheld_p95_map_px":float(np.percentile(errors,95)),
      "marker_warped_after_to_before_xy":estimated.tolist(),
      "marker_offset_from_shared_nominal_sphere_xy_px":(estimated-MARKER).tolist(),
      "source_terrain_shift_m_approx":((estimated-MARKER)*1.2).tolist(),
      "spatial_inlier_cells_total":len(set(zip(cellx[train].tolist(),celly[train].tolist())))})
  r["model"]=model
  rows.append(r)
 return {"map_shape":list(before.shape),"sift_kps":{"before":len(bk),"after":len(ak)},
   "tentative_matches":len(match),"off_marker_matches":len(x),
   "training":int(train.sum()),"withheld":int((~train).sum()),
   "fixed_exclusion_radius_px":48,
   "fixed_spatial_holdout_rule":"(17*xcell+7*ycell)%5==0",
   "fits":rows}
def primary_figure(path):
 # actions/download-artifact extracts the outer GitHub ZIP already.
 # The supplied path is normally the ORIGINAL PMC supplementary ZIP.
 if sha(path.read_bytes())==ZIP_SHA:
  data=path.read_bytes()
 else:
  with zipfile.ZipFile(path) as z:
   data=z.read("nwaf384_supplemental_files.zip")
 if sha(data)!=ZIP_SHA:raise ValueError("published source ZIP changed")
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  docx=z.read("2025-434-supplementarymaterials.docx")
 with zipfile.ZipFile(io.BytesIO(docx)) as z:
  raw=z.read("word/media/image5.jpeg")
 if sha(raw)!=FIG_SHA:raise ValueError("not verified original Figure S5")
 img=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
 if img.shape[:2]!=(469,1430):raise ValueError("unexpected original panel dimensions")
 return img
def figure_match(figure,im):
 panels={}
 for i,role in enumerate(("before","after")):
  a,b=round(i*figure.shape[1]/3),round((i+1)*figure.shape[1]/3)
  gray=cv2.cvtColor(figure[:,a:b],cv2.COLOR_BGR2GRAY)
  panels[role]=gray[16:-16,16:-16]
 rows=[]
 for p_role,p in panels.items():
  pk,pd=descr(p)
  for m_role,base in im.items():
   raw=browse(base)
   for rotation in range(4):
    rotated=np.ascontiguousarray(np.rot90(raw,rotation))
    for flip in (False,True):
     oriented=np.ascontiguousarray(np.fliplr(rotated)) if flip else rotated
     mk,md=descr(oriented)
     matches=good_matches(pd,md,.82)
     source=np.float64([pk[m.queryIdx].pt for m in matches])
     target=np.float64([mk[m.trainIdx].pt for m in matches])
     result=fit(source,target,"full_affine",thresh=4.)
     # Only a high-support source-panel fit warrants a reported pixel crosswalk.
     if result.get("inliers",0)>=100:
      M=np.float64(result["matrix"])
      residual=np.linalg.norm(source@M[:,:2].T+M[:,2]-target,axis=1)
      agree=residual<=4.
      ix=cv2.invertAffineTransform(M)
      origin=(MARKER@ix[:,:2].T+ix[:,2])
      result["source_marker_in_published_panel_cropped_xy"]=origin.tolist()
      result["source_marker_in_original_S5_image_xy"]=[
         float(origin[0]+16+round((0 if p_role=="before" else 1)*figure.shape[1]/3)),
         float(origin[1]+16)]
      result["corresponding_points_within_4px"]=int(agree.sum())
      result["tentative_fit_residual_median_px"]=float(np.median(residual[agree]))
      result["tentative_fit_residual_p95_px"]=float(np.percentile(residual[agree],95))
     rows.append({"published_panel":p_role,"source_map":m_role,
       "orientation_90deg_ccw":rotation,"flipped_horizontal":flip,
       "ratio":.82,"tentative":len(matches),"affine_inliers":result.get("inliers",0),
       "status":result["status"],
       "panel_to_source_affine":result.get("matrix"),
       "map_nominal_marker_in_original_S5_xy":result.get("source_marker_in_original_S5_image_xy"),
       "map_nominal_marker_in_panel_cropped_xy":result.get("source_marker_in_published_panel_cropped_xy"),
       "residual_p95_mapped_px":result.get("tentative_fit_residual_p95_px"),
       "agreement_count_4px":result.get("corresponding_points_within_4px")})
 return {"image_sha256":FIG_SHA,"source_figure":"Xiao et al. 2025 Supplementary Figure S5 (image5.jpeg)",
         "model":"SIFT+CLAHE+full-affine 4px RANSAC; exploratory 32-case orientation screen",
         "tested_cases":len(rows),"max_affine_inliers":max(z["affine_inliers"] for z in rows),
         "all_cases":rows,
         "scope":"Lack of feature consensus is not proof source figure lies outside exact EDR; paper panels may have different map projections or crop extents."}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--map-artifact-folder",type=Path,required=True)
 p.add_argument("--supplement-artifact",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 x=p.parse_args()
 proof=json.loads((x.map_artifact_folder.parents[1]/"diagnostics"/
                    "isef4_gambart_csm_common_map_probe.json").read_text())
 if proof["source_ids"]!=PAIR_IDS or proof["mapped_marker_disagreement_px"]!={"sample":0.,"line":0.}:
  raise ValueError("not the exact source-verified successful paired map")
 raw=read_maps(x.map_artifact_folder,proof)
 geometry=pair_geometry(raw)
 figure=figure_match(primary_figure(x.supplement_artifact),raw)
 out={"schema":"Gambart-C-correct-figure-S5-spherical-map-pixel-crosswalk-v3",
    "camera_result_source_run_id":"35459076420",
    "source_image_ids":PAIR_IDS,"source_map_nominal_m_per_px":1.2,
    "source_map_projection":"shared spherical Moon reference; no DEM",
    "relative_terrain_registration":geometry,
    "published_Figure_S5_correspondence_exploratory":figure,
    "hard_limits":[
      "A common map-grid marker agreement is exact by construction; it does NOT establish physical terrain alignment.",
      "A single source-pair spatial withholding is NOT independent ground truth or scientific detection sensitivity.",
      "Before/after map cubes contain raw ingested EDR values, not physically comparable radiance/I/F.",
      "A failed figure feature match is not proof the original figure pair IDs are wrong.",
      "No new landslide and no recovered published landslide are established."]}
 x.out.parent.mkdir(parents=True,exist_ok=True)
 x.out.write_text(json.dumps(out,indent=2)+"\n")
 print(json.dumps({"map_relative_fits":geometry["fits"],
  "published_Figure_S5_max_inliers":figure["max_affine_inliers"]},indent=2),flush=True)
if __name__=="__main__":main()
