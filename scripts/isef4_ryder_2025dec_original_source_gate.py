#!/usr/bin/env python3
"""Strict single original Ryder December 2025 NASA NAC source gate.

Chosen before opening 2025 source pixels: M1520890667LE actually covers
published Ryder marker, 2024 incidence 49.78 vs 2025 48.34 and phase 50.72
vs 49.57. Not selected by a 2024->2026 residual location.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from isef4_ryder_original_source_gate import gate,query_cdr,SITE,SITE_ID

PRODUCT="M1520890667LE"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--inventory",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    inventory=json.loads(a.inventory.read_text())
    if inventory["schema"]!="ISEF4-Xiao41-multisite-exact-original-NAC-metadata-pair-search-v1":
        raise ValueError("not original full-site published event registry")
    record=next(z for z in inventory["event_sites"] if z.get("published_event")==SITE_ID)
    if record["coordinate_lat_n_lon_e360"]!=list(SITE):
        raise ValueError("site provenance mismatch")
    candidates=[x for x in record["recent_original_product_metadata"]
       if x["product_id"]==PRODUCT and x["observed_utc"][:10]=="2025-12-20"]
    if len(candidates)!=1 or candidates[0]["approx_footprint_edge_margin_m"]<400:
        raise ValueError("2025Dec candidate not true Ryder marker-covering NAC source")
    o=candidates[0]
    cds,query=query_cdr()
    result={"schema":"Ryder-2025Dec-official-original-NAC-EDR-CDR-gate-v1",
      "inventory_SHA256":sha(a.inventory),
      "lat_n_lon_e360":SITE,
      "EDR_ID":PRODUCT,"CDR_ID":PRODUCT[:-1]+"C",
      "original_acquisition_utc":o["observed_utc"],
      "illumination_incidence_deg":o["incidence_deg"],
      "illumination_phase_deg":o["phase_deg"],
      "approx_marker_inside_ODE_polygon_edge_m":o["approx_footprint_edge_margin_m"],
      "original_EDR_archive_URL":o["original_EDR_URL"],
      "ODE_CDR_query":query,"original_records":{},"source_pixel_reads":0}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    for typ,pid,url in (
        ("EDR",PRODUCT,o["original_EDR_URL"]),
        ("CDR",PRODUCT[:-1]+"C",cds.get(PRODUCT[:-1]+"C",{}).get("IMG_URL"))):
        try:result["original_records"][typ]={"status":"original_PDS3_header_gate_passed",**gate(pid,url,typ)}
        except Exception as exc:
            result["original_records"][typ]={"status":"source_unavailable_or_unverified",
              "error":type(exc).__name__+": "+str(exc),"original_url":url}
        a.out.write_text(json.dumps(result,indent=2)+"\n")
    if any(z["status"]!="original_PDS3_header_gate_passed"
           for z in result["original_records"].values()):
        raise RuntimeError("original 2025 source product identity not confirmed")
    result["status"]="both exact original 2025Dec NAC EDR/CDR PDS3 header identities and full byte lengths verified; NO image pixels checked"
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"records":result["original_records"]},indent=2),flush=True)
if __name__=="__main__":main()
