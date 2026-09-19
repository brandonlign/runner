#!/usr/bin/env python3
"""Bounded original NASA NAC CDR source-pixel acquisition for a published positive.

These are native, unprojected calibrated I/F samples, not coincident ground
pixels across observations; NO before/after differencing is authorized here.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output"/"isef4_gambart_cdr"
DIAG=ROOT/"diagnostics"/"isef4_gambart_native_cdr_crops.json"
SCALE=3.05185094759972e-5
SOURCES={
 "before":("M1138987659LC","LROLRC_1017/DATA/ESM/2013317/NAC/",155571144),
 "after":("M1200206882LC","LROLRC_1025/DATA/ESM2/2015296/NAC/",280024008),
}
BASE="https://pds.lroc.im-ldi.com/data/LRO-L-LROC-3-CDR-V1.0/"
NROWS=1024
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def request_range(url:str,start:int,end:int,total:int|None=None)->tuple[bytes,int]:
 req=urllib.request.Request(url,headers={"Range":f"bytes={start}-{end}","User-Agent":"LUNARSHIFT-scientific-CDR-source/1.0"})
 with urllib.request.urlopen(req,timeout=180) as response:
  header=response.headers.get("Content-Range","")
  m=re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)",header)
  if response.status!=206 or not m or tuple(map(int,m.groups()[:2]))!=(start,end):
   raise RuntimeError(f"invalid strict HTTP 206: {response.status}, {header}")
  size=int(m.group(3))
  if total is not None and size!=total:raise RuntimeError(f"source byte size changed: {size}!={total}")
  raw=response.read(end-start+2)
 if len(raw)!=end-start+1:raise RuntimeError("short or overlong source range")
 return raw,size
def pds_fields(raw:bytes)->dict:
 s=raw.decode("ascii","replace")
 keys=("PRODUCT_ID","LINES","LINE_SAMPLES","SAMPLE_BITS","SAMPLE_TYPE","LABEL_RECORDS","RECORD_BYTES","SCALING_FACTOR","NULL","VALID_MINIMUM")
 d={}
 for name in keys:
  m=re.search(r"(?m)^\s*"+name+r"\s*=\s*([^\r\n/]+)",s)
  if m:d[name]=m.group(1).strip().strip('"')
 return d
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 diag={"schema":"gambart-c-exact-native-CDR-marker-ranges-v1","role":"published_known_positive_development_only","coordinate":[3.218,348.092],"epochs":{},"scientific_status":"calibrated mission CDR source pixels; not geometrically mapped across epochs"}
 for role,(product,rel,total) in SOURCES.items():
  marker=json.loads((ROOT/"diagnostics"/f"isef4_gambart_{role}_grounded_raw_crop.json").read_text())
  if marker["source_role"]!=role or marker["source_product"]!=product[:-1]+"E":
   raise RuntimeError("camera marker source identity mismatch")
  if marker["source_ground_coord_lat_lon_e360"]!=[3.218,348.092]:
   raise RuntimeError("marker latitude/longitude changed")
  url=BASE+rel+product+".IMG"
  head,n=request_range(url,0,8191,total)
  fields=pds_fields(head)
  expect={"PRODUCT_ID":product,"SAMPLE_BITS":"16","SAMPLE_TYPE":"LSB_INTEGER","SCALING_FACTOR":str(SCALE)}
  for k,v in expect.items():
   if k=="SCALING_FACTOR":
    if not math.isclose(float(fields[k]),SCALE,rel_tol=1e-8):raise RuntimeError("CDR scale mismatch")
   elif fields.get(k)!=v:raise RuntimeError(f"CDR PDS {k} mismatch: {fields.get(k)}")
  lines=int(fields["LINES"]);samples=int(fields["LINE_SAMPLES"])
  offset=int(fields["LABEL_RECORDS"])*int(fields["RECORD_BYTES"])
  if samples!=5064 or int(fields["RECORD_BYTES"])!=5064 or offset!=5064:
   raise RuntimeError("unsupported NAC original label layout")
  if offset+lines*samples*2!=total:raise RuntimeError("CDR size inconsistent with PDS")
  x,y=marker["nearest_original_edr_index_zero_based_xy"]
  if not(0<=x<samples and 0<=y<lines):raise RuntimeError("marker outside source CDR")
  row0=max(0,min(lines-NROWS,y-NROWS//2))
  start=offset+row0*samples*2
  end=start+NROWS*samples*2-1
  raw,_=request_range(url,start,end,total)
  image=np.frombuffer(raw,dtype="<i2").reshape((NROWS,samples))
  local=y-row0
  if not 0<=local<NROWS:raise RuntimeError("marker crop outside acquired CDR rows")
  valid=(image>=int(fields["VALID_MINIMUM"]))&(image<=32767)
  if not valid[local,x]:raise RuntimeError("published marker CDR source sample is special")
  r=400
  crop=image[max(0,local-r):min(NROWS,local+r+1),max(0,x-r):min(samples,x+r+1)].copy()
  if crop.shape!=(801,801):raise RuntimeError("event crop truncated; increase row-window")
  npy=OUT/f"{product}_native_i2_marker_r400.npy"
  np.save(npy,crop,allow_pickle=False)
  f=crop.astype(np.float32)*SCALE
  fv=crop>=int(fields["VALID_MINIMUM"])
  lo,hi=np.percentile(f[fv],[1,99])
  if not hi>lo:raise RuntimeError("degenerate native calibrated CDR crop")
  preview=np.zeros(crop.shape,np.uint8)
  preview[fv]=np.rint(255*np.clip((f[fv]-lo)/(hi-lo),0,1)).astype(np.uint8)
  png=OUT/f"{product}_visualization_only.png"
  Image.fromarray(preview).save(png)
  diag["epochs"][role]={
   "source_id":product,"url":url,"source_image_total_bytes":total,
   "pds":fields,"pds_header_sha256_first_8192":sha(head),
   "original_source_marker_xy_zero_based":[x,y],
   "source_marker_native_int16":int(image[local,x]),
   "source_marker_i_over_f":float(image[local,x]*SCALE),
   "source_crop_rows_original_zero_based":[row0,row0+NROWS-1],
   "source_byte_range":[start,end],"source_byte_range_sha256":sha(raw),
   "source_crop_rect_xyxy_original_exclusive":[x-400,y-400,x+401,y+401],
   "crop_shape":list(crop.shape),"valid_fraction":float(fv.mean()),
   "crop_i_over_f_p01_p50_p99":np.percentile(f[fv],[1,50,99]).tolist(),
   "crop_npy_sha256":sha(npy.read_bytes()),"preview_sha256":sha(png.read_bytes()),
   "interpretation":"Native source pixels only; same index is not same ground location in other epoch",
  }
  DIAG.parent.mkdir(parents=True,exist_ok=True)
  DIAG.write_text(json.dumps(diag,indent=2)+"\n")
  print(f"{role} {product} CDR marker={int(image[local,x])} range_sha={sha(raw)}",flush=True)
 print(json.dumps({"diagnostic":str(DIAG),"roles":list(diag["epochs"])}),flush=True)
if __name__=="__main__":main()
