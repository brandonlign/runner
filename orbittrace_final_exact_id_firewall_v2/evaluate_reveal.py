#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

YEARS=(2022,2023)
FULL_RANK_MAX=25
PARTIAL_RANK_MAX=100
MIN_OVERLAP_PER_YEAR=4
MIN_OVERLAP_TOTAL=8
TARGET_SCHEMA="orbittrace-withheld-exact-ids-v2"
STAGE_A_SCHEMA="orbittrace-final-stage-a-ranked-families-v2"


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def canonical_bytes(value:Any)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()


def sha256(value:Any)->str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_stage_a(path:Path)->dict[str,Any]:
    obj=json.loads(path.read_text())
    require(obj.get("schema")==STAGE_A_SCHEMA,"wrong Stage-A schema")
    require(obj.get("years")==list(YEARS),"wrong Stage-A years")
    require(obj.get("target_reference_accessed") is False,"Stage A accessed target reference")
    require(obj.get("catalogue_shower_labels_used") is False,"Stage A used catalogue shower labels")
    families=obj.get("primary_families")
    require(isinstance(families,list) and families,"Stage A primary family list missing")
    ranks=[]; ids=set()
    for family in families:
        require(set(family)=={"family_id","rank","years","event_ids_by_year"},"unexpected Stage-A family field")
        fid=str(family["family_id"]); require(fid not in ids,"duplicate family ID"); ids.add(fid)
        rank=int(family["rank"]); ranks.append(rank)
        require(sorted(int(y) for y in family["years"])==list(YEARS),f"family {fid} does not span exact discovery years")
        by_year=family["event_ids_by_year"]
        require(set(by_year)=={"2022","2023"},f"family {fid} year-ID schema changed")
        for year in YEARS:
            values=by_year[str(year)]
            require(isinstance(values,list) and len(values)==len(set(str(x) for x in values)),f"family {fid} duplicate IDs {year}")
    require(sorted(ranks)==list(range(1,len(ranks)+1)),"primary ranks must be contiguous from 1")
    return obj


def load_target_ids(path:Path)->tuple[dict[int,set[str]],dict[str,Any]]:
    obj=json.loads(path.read_text())
    require(set(obj).issubset({"schema","events","provenance"}),"withheld target payload contains forbidden top-level fields")
    require(obj.get("schema")==TARGET_SCHEMA,"wrong withheld exact-ID schema")
    events=obj.get("events"); require(isinstance(events,list) and events,"withheld target events missing")
    by_year={year:set() for year in YEARS}; seen=set()
    for event in events:
        require(isinstance(event,dict) and set(event)=={"id","year"},"withheld target event contains forbidden non-ID fields")
        event_id=str(event["id"]); year=int(event["year"])
        require(year in YEARS,"withheld target contains event outside discovery years")
        require(event_id and event_id not in seen,"blank/duplicate withheld target ID")
        seen.add(event_id); by_year[year].add(event_id)
    return by_year,obj


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--stage-a",required=True,type=Path)
    p.add_argument("--target-exact-ids",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args(); args.output.parent.mkdir(parents=True,exist_ok=True)

    stage=load_stage_a(args.stage_a)
    target,target_obj=load_target_ids(args.target_exact_ids)
    rows=[]
    for family in stage["primary_families"]:
        by_year={year:set(str(x) for x in family["event_ids_by_year"][str(year)]) for year in YEARS}
        overlap={year:sorted(by_year[year]&target[year]) for year in YEARS}
        counts={year:len(overlap[year]) for year in YEARS}; total=sum(counts.values())
        support=all(counts[year]>=MIN_OVERLAP_PER_YEAR for year in YEARS) and total>=MIN_OVERLAP_TOTAL
        rows.append({"family_id":str(family["family_id"]),"rank":int(family["rank"]),"overlap_ids_by_year":{str(y):overlap[y] for y in YEARS},"overlap_count_by_year":{str(y):counts[y] for y in YEARS},"overlap_total":total,"meets_exact_support":support})

    full=[r for r in rows if r["rank"]<=FULL_RANK_MAX and r["meets_exact_support"]]
    partial=[r for r in rows if r["rank"]<=PARTIAL_RANK_MAX and r["meets_exact_support"]]
    if full:
        verdict="FULL_BLIND_RECOVERY"; selected=min(full,key=lambda r:r["rank"])
    elif partial:
        verdict="PARTIAL_BLIND_RECOVERY"; selected=min(partial,key=lambda r:r["rank"])
    else:
        verdict="NO_BLIND_RECOVERY"; selected=None

    result={"verdict":verdict,"configuration":{"years":list(YEARS),"full_rank_max":FULL_RANK_MAX,"partial_rank_max":PARTIAL_RANK_MAX,"min_overlap_per_year":MIN_OVERLAP_PER_YEAR,"min_overlap_total":MIN_OVERLAP_TOTAL,"matching":"exact stable event-ID set intersection only","post_reveal_geometry_search":False,"post_reveal_reranking":False},"stage_a_sha256":sha256(stage),"withheld_exact_id_payload_sha256":sha256(target_obj),"selected_family":selected,"qualifying_full":[r for r in full],"qualifying_top100":[r for r in partial],"all_family_overlap_counts":[{"family_id":r["family_id"],"rank":r["rank"],"overlap_count_by_year":r["overlap_count_by_year"],"overlap_total":r["overlap_total"],"meets_exact_support":r["meets_exact_support"]} for r in rows],"claim_boundary":"Exact-ID blind recovery only; no post-reveal coordinate/orbit/activity matching performed."}
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"verdict":verdict,"selected_family":selected},indent=2),flush=True)
    return 0


if __name__=="__main__": raise SystemExit(main())
