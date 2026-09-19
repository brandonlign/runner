#!/usr/bin/env python3
"""Development-only fixed-map ISIS 10 / CSM geometry gate for published Gambart C.

Run *after* the source-verified BEFORE and AFTER ISIS 10 camera triages within
the same job. This probe does NOT classify a landslide or claim new discovery.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output"/"isef4_csm_common_map"
DIAG=ROOT/"diagnostics"/"isef4_gambart_csm_common_map_probe.json"
MAP=OUT/"gambart_fixed_common_sphere.map"
ROLES=("before","after")
PRODUCTS={"before":"M1138987659LE","after":"M1200206882LE"}
TRIAGE={"before":"isis10_before","after":"isis10_after"}
NUM=re.compile(r"(?m)^\\s*([A-Za-z][A-Za-z0-9_]*)\\s*=\\s*([-+]?\\d+(?:\\.\\d+)?(?:[eE][-+]?\\d+)?)")
STATE={"schema":"gambart-c-official-CSM-common-map-first-gate-v1","published_positive_only":True,
       "source_ids":PRODUCTS,"published_lat_lon_e360":[3.218,348.092],
       "map_radius_m":1737400,"pixel_resolution_m":1.2,
       "projection":"Equirectangular spherical reference-radius only, no independently validated DEM",
       "stages":{},"scientific_status":"not yet verified"}
def save():
 DIAG.parent.mkdir(parents=True,exist_ok=True)
 DIAG.write_text(json.dumps(STATE,indent=2)+"\n")
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as stream:
  for b in iter(lambda:stream.read(4*1024*1024),b""):h.update(b)
 return h.hexdigest()
def run(name,args,timeout=240):
 log=OUT/(name+".log")
 try:
  p=subprocess.run([str(x) for x in args],capture_output=True,text=True,
                   errors="replace",timeout=timeout,check=False)
  data=p.stdout+"\n"+p.stderr
  code=p.returncode
 except Exception as exc:
  data=type(exc).__name__+": "+str(exc)
  code=-1
 log.write_text(data)
 STATE["stages"][name]={"command":[str(x) for x in args],"returncode":code,
                         "log_file":log.name,"log_tail":data[-2400:],
                         "log_bytes":len(data.encode("utf8"))}
 save()
 if code!=0:raise RuntimeError(f"{name}: {data[-800:]}")
 return data
def get_num(p,field):
 m=re.search(r"(?m)^\\s*"+re.escape(field)+r"\\s*=\\s*([-+]?\\d+(?:\\.\\d+)?(?:[eE][-+]?\\d+)?)",p.read_text(errors="replace"))
 if not m:raise RuntimeError(f"missing numeric {field} in {p}")
 val=float(m.group(1))
 if not math.isfinite(val):raise RuntimeError("nonfinite "+field)
 return val
def marker(role):
 p=ROOT/"diagnostics"/f"isef4_gambart_{role}_grounded_raw_crop.json"
 d=json.loads(p.read_text())
 if d["source_role"]!=role or d["source_product"]!=PRODUCTS[role]:
  raise RuntimeError("wrong camera marker product "+role)
 if d["source_ground_coord_lat_lon_e360"]!=[3.218,348.092]:
  raise RuntimeError("different coordinate")
 return d
def make_map():
 MAP.write_text(
  "Group = Mapping\n"
  "  TargetName = Moon\n"
  "  ProjectionName = Equirectangular\n"
  "  EquatorialRadius = 1737400 <meters>\n"
  "  PolarRadius = 1737400 <meters>\n"
  "  LatitudeType = Planetocentric\n"
  "  LongitudeDirection = PositiveEast\n"
  "  LongitudeDomain = 360\n"
  "  CenterLatitude = 3.218\n"
  "  CenterLongitude = 348.092\n"
  "  MinimumLatitude = 3.208\n"
  "  MaximumLatitude = 3.228\n"
  "  MinimumLongitude = 348.082\n"
  "  MaximumLongitude = 348.102\n"
  "  PixelResolution = 1.2 <meters/pixel>\n"
  "End_Group\nEnd\n")
 STATE["map_file_sha256"]=digest(MAP);save()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 save()
 try:
  make_map()
  for role in ROLES:
   d=marker(role)
   sample,line=d["campt_sample_line_one_based"]
   start_s=int(math.floor(sample))-400
   start_l=int(math.floor(line))-400
   if start_s<1 or start_l<1:raise RuntimeError("negative ISIS source crop")
   source=ROOT/"output"/("triage_"+TRIAGE[role])/(role+".raw.cub")
   if not source.is_file():raise RuntimeError(f"verified {role} camera cube is absent")
   cube=OUT/(role+".native.crop.cub")
   run(role+"_native_crop",["crop",f"from={source}",f"to={cube}",
       f"sample={start_s}",f"line={start_l}","nsamples=801","nlines=801",
       "propspice=true"],timeout=180)
   pvl=OUT/(role+".native.marker.pvl")
   run(role+"_crop_ground_marker",["campt",f"from={cube}",
       "type=ground","latitude=3.218","longitude=348.092",
       "allowoutside=false",f"to={pvl}"],timeout=150)
   sx,sy=get_num(pvl,"Sample"),get_num(pvl,"Line")
   expected=[sample-start_s+1,line-start_l+1]
   err=max(abs(sx-expected[0]),abs(sy-expected[1]))
   STATE["stages"][role+"_crop_coordinate"]={
     "camera_ground_marker_sample_line_cropped":[sx,sy],
     "camera_full_source_sample_line":[sample,line],
     "crop_start_sample_line_isis_one_based":[start_s,start_l],
     "expected_crop_marker_sample_line":expected,
     "error_px":err,"camera_pvl_tail":pvl.read_text(errors="replace")[-3500:],
     "source_input_cube_sha256":digest(source)}
   save()
   if err>0.1:raise RuntimeError(f"{role} CSM crop changed camera marker geometry")
   projected=OUT/(role+".commonmap.cub")
   run(role+"_cam2map",["cam2map",f"from={cube}",f"to={projected}",
       f"map={MAP}","matchmap=true","interp=bilinear"],timeout=500)
   mapped_pvl=OUT/(role+".mapped.marker.pvl")
   run(role+"_mapped_ground_marker",["mappt",f"from={projected}",
       "type=ground","coordsys=universal","latitude=3.218","longitude=348.092",
       "allowoutside=false",f"to={mapped_pvl}"],timeout=150)
   mm={k:get_num(mapped_pvl,k) for k in ("Sample","Line")}
   text=mapped_pvl.read_text(errors="replace")
   pm=re.search(r"(?m)^\\s*PixelValue\\s*=\\s*(\\S+)",text)
   pixel=pm.group(1) if pm else None
   STATE["stages"][role+"_mapped_location"]={
      "sample":mm["Sample"],"line":mm["Line"],
      "pixel_value":pixel,"pvl_tail":text[-3000:],
      "output_mapped_cube_sha256":digest(projected)}
   save()
   if pixel is None or pixel.lower() in ("null","nan"):
    raise RuntimeError(f"{role} mapped marker lands on NULL source image")
  a=STATE["stages"]["after_mapped_location"]
  b=STATE["stages"]["before_mapped_location"]
  errors={z:abs(a[z]-b[z]) for z in ("sample","line")}
  STATE["mapped_marker_disagreement_px"]=errors
  for role in ROLES:
   p=OUT/(role+".commonmap.cub")
   # Identical map projection and grid must be verified from both cube labels.
   values={}
   for field in ("UpperLeftCornerX","UpperLeftCornerY","PixelResolution"):
    values[field]=float(run(role+"_mapping_"+field,[
       "getkey",f"from={p}","grpname=Mapping",f"keyword={field}"],timeout=40).strip())
   STATE["stages"][role+"_mapping"]=values
  b=STATE["stages"]["before_mapping"];a=STATE["stages"]["after_mapping"]
  for k in b:
   if abs(b[k]-a[k])>1e-6:raise RuntimeError("nonidentical common map grid "+k)
  if max(errors.values())>0.05:raise RuntimeError("marker disagreement in common mapped coordinate exceeds 0.05 px")
  STATE["scientific_status"]="Both CSM source crops retain camera coordinates and return finite published-marker pixels on an identical spherical common map; not DEM-corrected or calibrated event recovery."
  save()
 except Exception as exc:
  STATE["scientific_status"]="geometry gate failed; NO published event recovery"
  STATE["failure"]=type(exc).__name__+": "+str(exc)
  save()
  raise
 print(json.dumps({"status":STATE["scientific_status"],"map_marker_disagreement":STATE["mapped_marker_disagreement_px"]}),flush=True)
if __name__=="__main__":main()
