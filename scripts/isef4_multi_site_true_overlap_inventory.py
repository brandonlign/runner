#!/usr/bin/env python3
"""Find meaningful *unexamined* lunar time pairs by original PDS NAC footprints.

Catalog/geometry only: no source-image pixels, known-slide claims or holdout
opening. Only query geographic sites from authenticated Xiao et al. 2025
41-event registry. Original acquisition dates, pixel coverage and illumination
must pass BEFORE choosing any original pixels for analysis.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path
import argparse, hashlib, json, math, re, time, urllib.parse,urllib.request

BASE="https://oderest.rsl.wustl.edu/live2/"
RADIUS_DEG=.115
METERS_PER_LUNAR_DEGREE=30322.0
PAGE=500
MAX_PAGES=3
MIN_SEPARATION_DAYS=90
MAX_INCIDENCE_DELTA=12.0
MAX_PHASE_DELTA=15.0

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utctime(s):
    return datetime.fromisoformat(s.replace("Z","+00:00"))
def polygon(text,around):
    pairs=[(float(x),float(y)) for x,y in re.findall(
      r"(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)",text or "")]
    if len(pairs)<4:return []
    x0=around
    return [(x0+(x-x0+180)%360-180,y) for x,y in pairs]
def spatial(lon,lat,poly):
    if len(poly)<4:return False,0
    inside=False
    for i in range(len(poly)):
        xa,ya=poly[i];xb,yb=poly[(i+1)%len(poly)]
        if (ya>lat)!=(yb>lat) and lon<(xb-xa)*(lat-ya)/(yb-ya)+xa:
            inside=not inside
    distances=[]
    for i in range(len(poly)):
        x,y=poly[i];u,v=poly[(i+1)%len(poly)]
        ax=(lon-x)*math.cos(math.radians(lat));ay=lat-y
        dx=(u-x)*math.cos(math.radians(lat));dy=v-y
        length=dx*dx+dy*dy
        t=min(1.,max(0.,(ax*dx+ay*dy)/length)) if length>0 else 0.
        distances.append(math.hypot(ax-t*dx,ay-t*dy)*METERS_PER_LUNAR_DEGREE)
    return inside,min(distances)
def usable(row):
    pid=str(row.get("pdsid") or row.get("Product_name") or row.get("Product_id") or "").upper().removeprefix("NAC.")
    if not (pid.startswith("M") and pid.endswith(("LE","RE"))):return None
    date=row.get("UTC_start_time")
    try:dt=utctime(date)
    except (ValueError,TypeError):return None
    try:inc=float(row.get("Incidence_angle"));phase=float(row.get("Phase_angle"))
    except (ValueError,TypeError):return None
    files=(row.get("Product_files") or {}).get("Product_file",[])
    if isinstance(files,dict):files=[files]
    original=[z.get("URL") for z in files if isinstance(z,dict) and z.get("URL")
         and str(z.get("FileName","")).upper().endswith(".IMG")]
    return {"product_id":pid,"observed_utc":date,"incidence_deg":inc,
       "phase_deg":phase,"side":pid[-2:],"ODE_polygon":row.get("Footprint_geometry"),
       "original_EDR_URL":original[0] if len(original)==1 else None,
       "date":dt}
def site(entry):
    lat=float(entry["latitude_deg"])
    lon=float(entry["longitude_deg_east_signed"])%360
    key=entry["published_event_identifier"]
    before=entry["before_date"];after=entry["after_date"]
    if entry["terrain_name_source_fill_down"].strip().lower() in ("naumann","copernicus"):
        return {"published_event":key,"site":entry["terrain_name_source_fill_down"],
           "status":"SEALED_GEOGRAPHIC_HOLDOUT_NOT_QUERIED",
           "query_count":0}
    q0={"query":"product","results":"fmpc","output":"JSON",
      "target":"moon","ihid":"LRO","iid":"LROC","pt":"EDRNAC4",
      "westernlon":round(lon-RADIUS_DEG,5),
      "easternlon":round(lon+RADIUS_DEG,5),
      "minlat":round(lat-RADIUS_DEG,5),
      "maxlat":round(lat+RADIUS_DEG,5),"limit":PAGE}
    found={};audits=[]
    for page in range(MAX_PAGES):
        params={**q0,"offset":page*PAGE}
        url=BASE+"?"+urllib.parse.urlencode(params)
        error=None;obj=None
        for retry in range(2):
            try:
                request=urllib.request.Request(url,headers={
                    "User-Agent":"LUNARSHIFT-isef4-original-EDR-coverage-metadata-only/0.1"})
                with urllib.request.urlopen(request,timeout=90) as r:
                    obj=json.load(r)
                break
            except Exception as exc:
                error=type(exc).__name__+": "+str(exc)
                time.sleep(retry+.5)
        if obj is None:
            audits.append({"offset":page*PAGE,"error":error,"query_url":url})
            break
        node=obj.get("ODEResults") or {}
        data=node.get("Products") or {}
        entries=data.get("Product",[]) if isinstance(data,dict) else []
        if isinstance(entries,dict):entries=[entries]
        if not isinstance(entries,list):entries=[]
        audits.append({"offset":page*PAGE,"reported_count":node.get("Count"),
                       "returned":len(entries),"query_url":url})
        for row in entries:
            if not isinstance(row,dict):continue
            z=usable(row)
            if z is None:continue
            poly=polygon(z.pop("ODE_polygon"),lon)
            covers,edge=spatial(lon,lat,poly)
            if not covers:continue
            z["approx_footprint_edge_margin_m"]=round(edge,1)
            z["date"]=z["date"].isoformat()
            found[z["product_id"]]=z
        if len(entries)<PAGE:break
    exact=sorted(found.values(),key=lambda z:z["observed_utc"])
    dated_after=[z for z in exact if z["observed_utc"][:10]>after]
    recent=[z for z in dated_after if z["observed_utc"][:10]>="2021-01-01"]
    # Never call a cataloged product a verified source observation until the
    # independent original PDS header and full CSM camera gate pass.
    pairs=[]
    for i,x in enumerate(recent):
        for y in recent[i+1:]:
            elapsed=(utctime(y["observed_utc"])-utctime(x["observed_utc"])).days
            if elapsed<MIN_SEPARATION_DAYS:continue
            if abs(x["incidence_deg"]-y["incidence_deg"])>MAX_INCIDENCE_DELTA:continue
            if abs(x["phase_deg"]-y["phase_deg"])>MAX_PHASE_DELTA:continue
            if min(x["approx_footprint_edge_margin_m"],y["approx_footprint_edge_margin_m"])<400:continue
            pairs.append({"before_original_EDR":x["product_id"],
                 "after_original_EDR":y["product_id"],
                 "before_utc":x["observed_utc"],"after_utc":y["observed_utc"],
                 "elapsed_days":elapsed,
                 "original_source_resolution_may_differ":True,
                 "incidence_deg":[x["incidence_deg"],y["incidence_deg"]],
                 "phase_deg":[x["phase_deg"],y["phase_deg"]],
                 "delta_incidence_deg":round(abs(x["incidence_deg"]-y["incidence_deg"]),2),
                 "delta_phase_deg":round(abs(x["phase_deg"]-y["phase_deg"]),2),
                 "before_ODE_marker_edge_margin_m":x["approx_footprint_edge_margin_m"],
                 "after_ODE_marker_edge_margin_m":y["approx_footprint_edge_margin_m"],
                 "before_original_EDR_URL":x["original_EDR_URL"],
                 "after_original_EDR_URL":y["original_EDR_URL"]})
    pairs.sort(key=lambda p:(p["delta_incidence_deg"]+p["delta_phase_deg"],-p["elapsed_days"]))
    return {"published_event":key,
        "site":entry["terrain_name_source_fill_down"],
        "coordinate_lat_n_lon_e360":[lat,lon],
        "published_after_date":after,
        "published_before_date":before,
        "paper_attributed_mechanism":entry["source_attributed_mechanism"],
        "paper_original_figure":[v["supplementary_figure"] for v in entry["same_coordinate_figure_candidates"]],
        "query_audit":audits,
        "all_actual_marker_covering_original_EDRs":len(exact),
        "post_paper_marker_covering_EDRs":len(dated_after),
        "post_paper_recent_marker_covering_EDRs":len(recent),
        "recent_original_product_metadata":recent,
        "pair_count_with_close_incidence_phase_and_pixel_margin":len(pairs),
        "candidate_true_covering_repeat_epoch_pairs":pairs[:20],
        "truncated_candidate_pair_count":max(0,len(pairs)-20),
        "status":"metadata_only_not_original_image_validated"}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--registry",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    doc=json.loads(a.registry.read_text())
    if doc["schema_version"]!="xiao2025-published-41-event-source-registry-v1" or doc["event_count"]!=41:
        raise ValueError("not actual published 41-event original source registry")
    rows=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        future={pool.submit(site,z):z for z in doc["events"]}
        for f in as_completed(future):
            item=future[f]
            try:rows.append(f.result())
            except Exception as exc:
                rows.append({"published_event":item["published_event_identifier"],
                    "site":item["terrain_name_source_fill_down"],
                    "status":"unassessable_original_ODE_catalog_error",
                    "error":type(exc).__name__+": "+str(exc)})
    rows.sort(key=lambda x:x["published_event"])
    leader=sorted((x for x in rows if x.get("status")=="metadata_only_not_original_image_validated"),
        key=lambda x:(-x["pair_count_with_close_incidence_phase_and_pixel_margin"],
                      -x["post_paper_recent_marker_covering_EDRs"]))
    result={"schema":"ISEF4-Xiao41-multisite-exact-original-NAC-metadata-pair-search-v1",
      "original_paper_registry_SHA256":sha(a.registry),
      "event_registry_total":41,
      "sealed_sites_never_queried":["Naumann","Copernicus"],
      "source_pixel_reads":0,
      "query_region_halfwidth_deg":RADIUS_DEG,
      "lunar_approx_meters_per_degree":METERS_PER_LUNAR_DEGREE,
      "point_in_polygon_required":True,
      "min_marker_edge_margin_approx_m":400,
      "post_published_after_date_only":True,
      "from_date":"2021-01-01",
      "min_separation_days":MIN_SEPARATION_DAYS,
      "max_incidence_delta_deg":MAX_INCIDENCE_DELTA,
      "max_phase_delta_deg":MAX_PHASE_DELTA,
      "event_sites":rows,
      "top_metadata_sites":[{"site":z["site"],
           "published_event":z["published_event"],
           "post_paper_recent_marker_covering_EDRs":z["post_paper_recent_marker_covering_EDRs"],
           "qualifying_pair_count":z["pair_count_with_close_incidence_phase_and_pixel_margin"],
           "example_pair":z["candidate_true_covering_repeat_epoch_pairs"][0] if z["candidate_true_covering_repeat_epoch_pairs"] else None}
           for z in leader[:20]],
      "scientific_limitations":["ODE footprint polygon vertices are rounded; exact 400m margin approximate, require original CSM camera source pixel and complete 769px ROI.",
       "Illumination incidence and phase are scene-level catalog values, not sufficient BRDF/terrain-shadow controls.",
       "Sites from previously published positive catalog are development/search targets, not unbiased sampling of entire Moon.",
       "A new interval or repeat pair does not imply an unpublished lunar event.",
       "Original geographic holdout Naumann/Copernicus EDR pixels and metadata were not queried."]}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"events":len(rows),
      "fully_queried":sum(z.get("status")=="metadata_only_not_original_image_validated" for z in rows),
      "sealed":sum(z.get("status")=="SEALED_GEOGRAPHIC_HOLDOUT_NOT_QUERIED" for z in rows),
      "sites_with_pairs":sum(z.get("pair_count_with_close_incidence_phase_and_pixel_margin",0)>0 for z in rows),
      "top":result["top_metadata_sites"][:12]},indent=2),flush=True)
if __name__=="__main__":main()
