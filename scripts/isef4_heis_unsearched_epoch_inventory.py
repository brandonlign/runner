#!/usr/bin/env python3
"""Original ODE Heis observation time-series inventory for discovery design.

Metadata only. Event region is published development site. No scientific
search claim, no nominal-coordinate ODE result is proof image covers actual
off-coordinate slope feature.
"""
from __future__ import annotations
import json,urllib.parse,urllib.request
from pathlib import Path
URI="https://oderest.rsl.wustl.edu/live2/"
BASE={"query":"product","results":"fmpc","output":"JSON",
 "target":"moon","ihid":"LRO","iid":"LROC","pt":"EDRNAC4",
 "westernlon":327.562,"easternlon":328.022,
 "minlat":32.317,"maxlat":32.777,"limit":500}
def main():
  records={};audit=[]
  for offset in (0,500,1000,1500):
    query={**BASE,"offset":offset}
    url=URI+"?"+urllib.parse.urlencode(query)
    req=urllib.request.Request(url,headers={"User-Agent":"LUNARSHIFT-Heis-published-site-post-2021-timeline/0.1"})
    try:
      with urllib.request.urlopen(req,timeout=120) as response:
        raw=json.load(response)
      root=raw.get("ODEResults") or {}
      block=root.get("Products") or {}
      values=block.get("Product",[]) if isinstance(block,dict) else []
      if isinstance(values,dict):values=[values]
      audit.append({"offset":offset,"reported":root.get("Count"),"returned":len(values),"url":url})
      for row in values:
        if not isinstance(row,dict):continue
        pid=str(row.get("pdsid") or row.get("Product_name") or row.get("Product_id") or "").upper().removeprefix("NAC.")
        if not (pid.startswith("M") and pid.endswith(("LE","RE"))):continue
        files=row.get("Product_files") or {}
        vals=files.get("Product_file",[]) if isinstance(files,dict) else []
        if isinstance(vals,dict):vals=[vals]
        urls=[r["URL"] for r in vals if r.get("URL") and str(r.get("FileName","")).upper().endswith(".IMG")]
        browse=[r["URL"] for r in vals if r.get("URL") and str(r.get("FileName","")).upper().endswith("_PYR.TIF")]
        records[pid]={"product":pid,"UTC_start_time":row.get("UTC_start_time"),
           "ode_product_type":"EDRNAC4","pixel_resolution_m":row.get("Pixel_resolution"),
           "footprint_geometry":row.get("Footprint_geometry"),
           "incidence_angle":row.get("Incidence_angle"),
           "emission_angle":row.get("Emission_angle"),
           "phase_angle":row.get("Phase_angle"),
           "original_IMG_URL":urls[0] if len(urls)==1 else None,
           "browse_pyramid_URL":browse[0] if len(browse)==1 else None,
           "ODE_product_id":row.get("Product_id")}
      if len(values)<500:break
    except Exception as e:
      audit.append({"offset":offset,"error":type(e).__name__+": "+str(e)})
      break
  result={"schema":"Heis-published-development-site-temporal-archive-inventory-v1",
      "published_location_lat_e360":[32.547,327.792],
      "search_halfwidth_lat_lon_deg":[.23,.23],
      "ODE_original_product_type":"EDRNAC4",
      "query_audit":audit,"unique_exact_lroc_EDR_count":len(records),
      "original_EDR_records_sorted":sorted(records.values(),key=lambda r:r["UTC_start_time"] or ""),
      "note":"a product in search box may or may not actually cover the authors' slide footprint; verify camera-ground pixel and calibrated source before interpreting candidate",
      "prohibition":"No already-published Heis event should be labeled novel and no Naumann/Copernicus source pixels are accessed."}
  out=Path("diagnostics/isef4_heis_unsearched_epoch_inventory.json")
  out.parent.mkdir(exist_ok=True)
  out.write_text(json.dumps(result,indent=2)+"\n")
  print(json.dumps({"unique":len(records),"epochs":[[r["product"],r["UTC_start_time"]] for r in result["original_EDR_records_sorted"]],"queries":audit},indent=2),flush=True)
  if len(records)<2:raise RuntimeError("ODE returned no reproducible Heis LROC timeline")
if __name__=="__main__":main()
