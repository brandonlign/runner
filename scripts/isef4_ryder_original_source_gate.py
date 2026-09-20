#!/usr/bin/env python3
"""Pre-pixel original NASA NAC archival gate for Ryder true repeat-epoch search.

Anchors chosen from the 41-site point-in-polygon and incidence audit, NOT
change measurements. Original EDR and CDR must each pass full-byte PDS3 header
geometry and exact ODE product identity, even at novel NASA PDS4 URL hosts.
"""
from __future__ import annotations
import argparse,hashlib,json,re,urllib.parse,urllib.request,time
from pathlib import Path

SITE_ID="xiao2025-table2-row27"
SITE=(-44.043,143.514)
PRODUCTS=[
 ("baseline_2022","M1418893006RE","2022-09-27"),
 ("followup_2024","M1488112243LE","2024-12-06"),
 ("followup_2026_April","M1531340568LE","2026-04-20"),
 ("followup_2026_May","M1533682639LE","2026-05-17"),
]
SOURCE_URL="https://oderest.rsl.wustl.edu/live2/"
def sha(b):return hashlib.sha256(b).hexdigest()
def query_cdr():
    q={"query":"product","results":"fmpc","output":"JSON",
       "target":"moon","ihid":"LRO","iid":"LROC","pt":"CDRNAC4",
       "westernlon":SITE[1]-.115,"easternlon":SITE[1]+.115,
       "minlat":SITE[0]-.115,"maxlat":SITE[0]+.115,"limit":500,"offset":0}
    url=SOURCE_URL+"?"+urllib.parse.urlencode(q)
    req=urllib.request.Request(url,headers={"User-Agent":"LUNARSHIFT-Ryder-original-source-metadata/0.1"})
    with urllib.request.urlopen(req,timeout=90) as r:
        root=json.load(r).get("ODEResults") or {}
    meta=root.get("Products") or {}
    rows=meta.get("Product",[]) if isinstance(meta,dict) else []
    if isinstance(rows,dict):rows=[rows]
    exact={}
    for p in rows:
        if not isinstance(p,dict):continue
        pid=str(p.get("pdsid") or p.get("Product_name") or p.get("Product_id") or "").upper().removeprefix("NAC.")
        files=(p.get("Product_files") or {}).get("Product_file",[])
        if isinstance(files,dict):files=[files]
        urls=[r.get("URL") for r in files if isinstance(r,dict) and r.get("URL")
              and str(r.get("FileName","")).upper().endswith(".IMG")]
        exact[pid]={"ODE_product_id":p.get("Product_id"),
            "IMG_URL":urls[0] if len(urls)==1 else None}
    return exact,{"query_url":url,"count_reported":root.get("Count"),
                    "returned":len(rows),"page_limit":500,
                    "complete":len(rows)<500}
def header(url):
    if not url:raise ValueError("no exact NASA original IMG URL")
    last=None
    for i in range(2):
        try:
            req=urllib.request.Request(url,headers={"Range":"bytes=0-5063",
              "User-Agent":"LUNARSHIFT-Ryder-original-PDS-EDR-CDR/0.1"})
            with urllib.request.urlopen(req,timeout=90) as r:
                status=r.status
                range_=r.headers.get("Content-Range","")
                data=r.read(5065)
            m=re.fullmatch(r"bytes 0-5063/(\d+)",range_)
            if status!=206 or not m or len(data)!=5064:
                raise ValueError("unverified exact 5064-byte source PDS header "+range_)
            return data,int(m.group(1))
        except (OSError,TimeoutError) as exc:
            last=exc
            time.sleep(i+.5)
    raise RuntimeError("source first-record retrieval failed "+repr(last))
def parse(raw):
    text=raw.decode("ascii",errors="replace")
    keys=("PDS_VERSION_ID","PRODUCT_ID","RECORD_BYTES","LABEL_RECORDS",
          "LINES","LINE_SAMPLES","SAMPLE_BITS","SAMPLE_TYPE")
    result={}
    for key in keys:
        m=re.search(r"(?m)^\s*"+key+r"\s*=\s*([^\r\n]+)",text)
        if m is None:raise ValueError("missing exact original PDS3 "+key)
        result[key]=m.group(1).strip().strip('"')
    return result
def gate(pid,url,kind):
    b,n=header(url)
    x=parse(b)
    if x["PDS_VERSION_ID"]!="PDS3" or x["PRODUCT_ID"]!=pid:
        raise ValueError("not original NASA source image PDS3 "+pid)
    wanted={"RECORD_BYTES":"5064","LABEL_RECORDS":"1","LINE_SAMPLES":"5064",
            "SAMPLE_BITS":"8" if kind=="EDR" else "16",
            "SAMPLE_TYPE":"LSB_INTEGER"}
    for k,v in wanted.items():
        if x[k]!=v:raise ValueError(pid+" "+k+" "+x[k]+" != "+v)
    lines=int(x["LINES"])
    factor=1 if kind=="EDR" else 2
    if not 2000<=lines<=110000 or n!=5064*(lines*factor+1):
        raise ValueError("source first record/full image byte geometry failed "+pid)
    return {"product":pid,"kind":kind,"source_URL":url,
            "full_original_IMG_bytes":n,"original_lines":lines,
            "first_5064_PDS3_SHA256":sha(b),"PDS3_fields":x,
            "original_pixel_bytewidth":factor}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--inventory",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    inv=json.loads(a.inventory.read_text())
    if inv["schema"]!="ISEF4-Xiao41-multisite-exact-original-NAC-metadata-pair-search-v1":
        raise ValueError("not authenticated true-covering original source inventory")
    ryder=[z for z in inv["event_sites"] if z.get("published_event")==SITE_ID]
    if len(ryder)!=1 or ryder[0]["coordinate_lat_n_lon_e360"]!=list(SITE):
        raise ValueError("wrong Ryder event or full-site marker")
    site=ryder[0]
    meta={z["product_id"]:z for z in site["recent_original_product_metadata"]}
    # Freeze exact source candidates before any EDR/CDR pixel access.
    for tag,pid,date in PRODUCTS:
        if pid not in meta or meta[pid]["observed_utc"][:10]!=date:
            raise ValueError("not independently inventoried post-published Ryder source "+pid)
        if meta[pid]["approx_footprint_edge_margin_m"]<400:
            raise ValueError("source too close to rounded ODE footprint boundary "+pid)
    cdr,ode_audit=query_cdr()
    result={"schema":"Ryder-original-2022-2024-2026-NAC-source-gate-v1",
       "original_multisite_inventory_SHA256":sha(a.inventory.read_bytes()),
       "published_Ryder_event":SITE_ID,"ground_coordinate_lat_n_lon_e360":SITE,
       "selection":"2022-09-27, 2024-12-06, 2026-04-20, 2026-05-17, before reviewing temporal image differences",
       "source_pixel_reads":0,"ODE_CDR_query":ode_audit,"epochs":{}}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    for tag,pid,date in PRODUCTS:
        row={"EDR_ID":pid,"CDR_ID":pid[:-1]+"C",
             "UTC":meta[pid]["observed_utc"],
             "incidence_deg":meta[pid]["incidence_deg"],
             "phase_deg":meta[pid]["phase_deg"],
             "approx_ODE_lunar_marker_edge_margin_m":meta[pid]["approx_footprint_edge_margin_m"],
             "probed_source_kind":{}}
        for kind,source_id,url in (
            ("EDR",pid,meta[pid]["original_EDR_URL"]),
            ("CDR",pid[:-1]+"C",cdr.get(pid[:-1]+"C",{}).get("IMG_URL"))):
            try:row["probed_source_kind"][kind]={"status":"original_header_validated",**gate(source_id,url,kind)}
            except Exception as exc:
                row["probed_source_kind"][kind]={"status":"unassessable_PDS_original_source",
                    "error":type(exc).__name__+": "+str(exc),"source_URL":url}
        result["epochs"][tag]=row
        a.out.write_text(json.dumps(result,indent=2)+"\n")
    both=all(result["epochs"][tag]["probed_source_kind"][kind]["status"]=="original_header_validated"
             for tag in ("baseline_2022","followup_2024") for kind in ("EDR","CDR"))
    result["2022_2024_exact_original_NAC_pair_source_gate_passed"]=both
    result["scientific_status"]="exact archives only; need ground-camera checks and original source pixels, then registration and geological corroboration"
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"base_source_gate":both,
       "epochs":{k:{part:{"status":v["status"],"product":v.get("product"),
                          "bytes":v.get("full_original_IMG_bytes"),"error":v.get("error")}
                       for part,v in row["probed_source_kind"].items()}
                 for k,row in result["epochs"].items()}},indent=2),flush=True)
    if not both:raise RuntimeError("base Ryder actual-overlap original source pair NOT fully verified")
if __name__=="__main__":main()
