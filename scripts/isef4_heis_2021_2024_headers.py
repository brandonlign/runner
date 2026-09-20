#!/usr/bin/env python3
"""Strict exact LROC EDR+CDR header confirmation of post-2021 Heis pair.

No event-pixel retrieval or claim from ODE bounding-box membership. Preserves
actual full source length and first PDS3 record digest for camera source gates.
"""
from __future__ import annotations
import argparse,hashlib,json,re,urllib.request
from pathlib import Path
PAIR={"before":"M1376643242LE","after":"M1481045431LE"}
def fetch(url):
    req=urllib.request.Request(url,headers={
        "Range":"bytes=0-5063",
        "User-Agent":"LUNARSHIFT-Heis-post2021-original-NAC-source-gate/0.1"})
    with urllib.request.urlopen(req,timeout=120) as r:
        ct=r.headers.get("Content-Range","")
        m=re.fullmatch(r"bytes 0-5063/(\d+)",ct)
        if r.status!=206 or not m:raise ValueError("not strict original archive HTTP206 5064 record")
        b=r.read(5065)
    if len(b)!=5064:raise ValueError("original first header truncated or too long")
    return b,int(m.group(1))
def fields(b):
    t=b.decode("ascii",errors="replace")
    output={}
    for key in ("PDS_VERSION_ID","PRODUCT_ID","LINES","LINE_SAMPLES",
                "RECORD_BYTES","LABEL_RECORDS","SAMPLE_BITS","SAMPLE_TYPE"):
        m=re.search(r"(?m)^\s*"+key+r"\s*=\s*([^\r\n]+)",t)
        if not m:raise ValueError("missing official field "+key)
        output[key]=m.group(1).strip().strip('"')
    return output
def inside_polygon(wkt,lon=327.792,lat=32.547):
    vertices=[(float(x),float(y)) for x,y in re.findall(r"(-?\\d+(?:\\.\\d+)?)\\s+(-?\\d+(?:\\.\\d+)?)",wkt or "")]
    if len(vertices)<4:raise ValueError("missing actual ODE lunar footprint")
    result=False
    for i in range(len(vertices)):
        ax,ay=vertices[i];bx,by=vertices[(i+1)%len(vertices)]
        if (ay>lat)!=(by>lat) and lon<(bx-ax)*(lat-ay)/(by-ay)+ax:
            result=not result
    return result
def verify(role,epoch,kind):
    edr=PAIR[role]
    if epoch["product"]!=edr or not epoch["original_IMG_URL"]:
        raise ValueError("original ODE ID does not match planned candidate")
    url=epoch["original_IMG_URL"]
    if kind=="CDR":
        cdr=edr[:-1]+"C"
        url=url.replace("/LRO-L-LROC-2-EDR-V1.0/","/LRO-L-LROC-3-CDR-V1.0/")
        url=url.replace("LROLRC_00","LROLRC_10")
        url=url.replace(edr+".IMG",cdr+".IMG")
    else:cdr=edr
    hdr,total=fetch(url)
    f=fields(hdr)
    expected={"PDS_VERSION_ID":"PDS3","PRODUCT_ID":cdr,
        "LINE_SAMPLES":"5064","RECORD_BYTES":"5064","LABEL_RECORDS":"1",
        "SAMPLE_BITS":"16" if kind=="CDR" else "8"}
    for k,v in expected.items():
        if f[k]!=v:raise ValueError(f"{cdr} mismatch {k}: {f[k]} != {v}")
    lines=int(f["LINES"])
    if not 1000<=lines<=100000 or total!=5064*(lines*(2 if kind=="CDR" else 1)+1):
        raise ValueError("unrecognized exact full original PDS3 image length/geometry")
    return {"product_id":cdr,"observation_time":epoch["UTC_start_time"],
        "kind":kind,"source_URL":url,
        "full_original_image_bytes":total,"full_original_lines":lines,
        "header_5064_SHA256":hashlib.sha256(hdr).hexdigest(),
        "PDS3_fields":f,"image_pixel_bytes":2 if kind=="CDR" else 1}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--inventory",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    catalog=json.loads(x.inventory.read_text())
    if catalog["schema"]!="Heis-published-development-site-temporal-archive-inventory-v1":
        raise ValueError("original full ODE inventory incompatible")
    available={r["product"]:r for r in catalog["original_EDR_records_sorted"]}
    result={"schema":"Heis-2021-to-2024-actual-overlap-NAC-source-header-pair-v1",
        "discovery_interval_is_after_paper_2021":True,
        "selected_for_similar_incidence_not_after_viewing_source_changes":True,
        "original_EDR_2021_2024_pair":PAIR,
        "ODE_Heis_inventory_SHA256":hashlib.sha256(x.inventory.read_bytes()).hexdigest(),
        "record":{},"scientific_status":"original post-2021 source header check in progress"}
    x.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        for role,edr in PAIR.items():
            epoch=available[edr]
            if not inside_polygon(epoch["footprint_geometry"]):\n                raise ValueError("chosen NAC footprint does not CONTAIN exact published Heis marker: "+edr)\n            result["record"][role]={"ODE":{k:epoch[k] for k in
                ("product","UTC_start_time","incidence_angle","phase_angle","footprint_geometry")}}
            for kind in ("EDR","CDR"):
                result["record"][role][kind]=verify(role,epoch,kind)
                x.out.write_text(json.dumps(result,indent=2)+"\n")
        result["scientific_status"]="both exact original NAC EDR and CDR headers verified, ODE marker-footprint coverage checked, camera ground point and pixels NOT yet verified"
        x.out.write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps({"science_status":result["scientific_status"],
          "original_headers":{r:{k:{z:result["record"][r][k][z] for z in ("product_id","full_original_image_bytes","full_original_lines","header_5064_SHA256")}
                      for k in ("EDR","CDR")} for r in PAIR}},indent=2),flush=True)
    except Exception as exc:
        result["scientific_status"]="post2021 overlapping original pair source gate blocked"
        result["error"]=type(exc).__name__+": "+str(exc)
        x.out.write_text(json.dumps(result,indent=2)+"\n")
        raise
if __name__=="__main__":main()
