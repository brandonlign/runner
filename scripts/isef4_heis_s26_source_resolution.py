#!/usr/bin/env python3
"""Resolve exact original NASA NAC products of published non-impact Heis S26.

Metadata and PDS header verification only; Heis is an already designated
development target, not Copernicus/Naumann geographic holdout.
"""
from __future__ import annotations
import hashlib
import json
import urllib.request
import urllib.parse
from pathlib import Path

BEFORE="M1197976848LE"
AFTER="M1376643242LE"
TARGET=(32.547,327.792)
S26_SHA="1e642c9ebf0f0716cecef1141f52f2d8fd7c2e274ad806a07447f8012dee3ea8"
DEST=Path("diagnostics/isef4_heis_s26_exact_edr_resolution.json")
def request(url,range_bytes=False):
    headers={"User-Agent":"LUNARSHIFT-Heis-S26-published-development-only/0.1"}
    if range_bytes:headers["Range"]="bytes=0-5063"
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=95) as r:
        d=r.read(6_000_000 if not range_bytes else 5065)
        if range_bytes:
            if r.status!=206 or not r.headers.get("Content-Range","").startswith("bytes 0-5063/") or len(d)!=5064:
                raise ValueError("unverified PDS original 5064-byte header range")
        elif len(d)>=6_000_000:
            raise ValueError("oversized ODE response")
        return d,dict(r.headers),r.status
def clean_id(row):
    val=str(row.get("pdsid") or row.get("Product_name") or row.get("Product_id") or "").upper().strip()
    return val.removeprefix("NAC.")
def files(row):
    node=row.get("Product_files") or {}
    values=node.get("Product_file",[]) if isinstance(node,dict) else []
    if isinstance(values,dict):values=[values]
    return [{"url":v.get("URL"),"name":v.get("FileName"),"kib":v.get("KBytes")}
            for v in values if isinstance(v,dict)]
def main():
    result={"schema":"isef4-nonimpact-S26-Heis-exact-public-source-gate-v1",
       "published_positive":"Xiao et al. 2025 Supplementary Fig S26, Heis",
       "author_attributed_mechanism":"endogenic seismic activity, NOT independently established",
       "before_EDR":BEFORE,"after_EDR":AFTER,
       "coordinates_lat_n_lon_e360":TARGET,"figure_media":"word/media/image26.jpeg",
       "figure_sha256":S26_SHA,
       "published_original_docx_sha256":"c03eec6514c69c04730f7f38ba8e43242eccc6455774938264f84e37dc67e513",
       "target_role":"development, no Naumann or Copernicus original EDR pixels",
       "query_audit":[],"verified_products":{}}
    wanted={BEFORE,AFTER,BEFORE[:-1]+"C",AFTER[:-1]+"C"}
    for pt in ("EDRNAC4","CDRNAC4"):
        for offset in (0,500,1000,1500,2000,2500,3000):
            q={"query":"product","results":"fmpc","output":"JSON",
               "target":"moon","ihid":"LRO","iid":"LROC","pt":pt,
               "westernlon":TARGET[1]-.13,"easternlon":TARGET[1]+.13,
               "minlat":TARGET[0]-.13,"maxlat":TARGET[0]+.13,
               "limit":500,"offset":offset}
            url="https://oderest.rsl.wustl.edu/live2/?"+urllib.parse.urlencode(q)
            try:
                raw,_h,_status=request(url)
                data=json.loads(raw)
                root=data.get("ODEResults",{})
                group=root.get("Products") or {}
                products=group.get("Product",[]) if isinstance(group,dict) else []
                if isinstance(products,dict):products=[products]
                if not isinstance(products,list):raise ValueError("no ODE product list")
                result["query_audit"].append({"product_type":pt,"offset":offset,
                     "returned":len(products),"reported_count":root.get("Count"),
                     "url":url})
                for p in products:
                    if not isinstance(p,dict):continue
                    pid=clean_id(p)
                    if pid not in wanted or ((pt=="EDRNAC4")!=pid.endswith("E")):continue
                    current=result["verified_products"].get(pid)
                    if current and current["product_type"]==pt:continue
                    result["verified_products"][pid]={
                        "ode_pdsid":p.get("pdsid"),
                        "product_type":pt,"UTC_start_time":p.get("UTC_start_time"),
                        "resolution":p.get("Map_scale") or p.get("Pixel_resolution"),
                        "label_URL":p.get("LabelURL"),
                        "files":files(p)}
                if len(products)<500:break
                if all(k in result["verified_products"] for k in wanted):break
            except Exception as exc:
                result["query_audit"].append({"product_type":pt,"offset":offset,
                     "error":type(exc).__name__+": "+str(exc)})
                break
    for pid,entry in result["verified_products"].items():
        paths=[v["url"] for v in entry["files"] if v.get("url") and
               str(v.get("name") or v["url"]).upper().split("?")[0].endswith(".IMG")]
        entry["img_urls"]=paths
        if paths:
            try:
                hdr,h,status=request(paths[0],range_bytes=True)
                entry["first_5064_range_status"]=status
                entry["first_5064_header_sha256"]=hashlib.sha256(hdr).hexdigest()
                entry["full_length_from_content_range"]=h.get("Content-Range","").split("/")[-1]
                entry["PDS3_header_declares_product"]=pid.encode() in hdr
            except Exception as exc:
                entry["source_header_range_error"]=type(exc).__name__+": "+str(exc)
    result["EDR_IDs_exact_from_public_ODE"] = BEFORE in result["verified_products"] and AFTER in result["verified_products"]
    result["CDR_IDs_exact_from_public_ODE"] = (BEFORE[:-1]+"C") in result["verified_products"] and (AFTER[:-1]+"C") in result["verified_products"]
    result["scientific_status"]="metadata and first-header acquisition only; no NASA source pixels used to fit or select detector"
    DEST.parent.mkdir(exist_ok=True)
    DEST.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"EDRs_found":result["EDR_IDs_exact_from_public_ODE"],
         "CDRs_found":result["CDR_IDs_exact_from_public_ODE"],
         "products":result["verified_products"],"query_count":len(result["query_audit"])},flush=True))
    if not result["EDR_IDs_exact_from_public_ODE"]:
        raise RuntimeError("original HEIS S26 EDRs not both found in queried public ODE window")
if __name__=="__main__":main()
