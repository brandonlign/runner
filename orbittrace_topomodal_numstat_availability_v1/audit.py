#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

from gmn_python_api import data_directory as dd

YEARS = (2022, 2023)
MONTHS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
DENOMS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
EXPECTED = {(128,0):5567,(128,1):5840,(128,2):5857,(128,3):5816,(1024,0):677,(1024,1):739,(1024,2):736,(1024,3):766}
MIN_COMPLETE = 0.95


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def clean_header(x: str) -> str:
    return " ".join(x.replace("#", "").strip().split())


def selected_columns(text: str) -> tuple[int, int, int, list[str]]:
    lines = text.splitlines()
    top = next((ln for ln in lines if ln.lstrip().startswith("#") and "Unique trajectory" in ln and "Sol lon" in ln and "Participating" in ln), None)
    bottom = next((ln for ln in lines if ln.lstrip().startswith("#") and "identifier" in ln and "stat" in ln and "stations" in ln), None)
    req(top is not None and bottom is not None, "GMN monthly two-row schema header not found")
    a = [clean_header(x) for x in top.split(";")]
    b = [clean_header(x) for x in bottom.split(";")]
    req(len(a) == len(b) and len(a) > 70, f"unexpected GMN header width {len(a)} vs {len(b)}")
    def one(t: str, u: str) -> int:
        hits = [i for i, (x, y) in enumerate(zip(a, b)) if x == t and y == u]
        req(len(hits) == 1, f"header field {(t,u)} not unique: {hits}")
        return hits[0]
    return one("Unique trajectory", "identifier"), one("Sol lon", "deg"), one("Num", "stat"), lines


def parse_month_for_manifest(text: str, month: str, allowed_month: dict[str,str]) -> list[tuple[str,float,int|None]]:
    id_col, sol_col, stat_col, lines = selected_columns(text)
    out=[]
    for line in lines:
        s=line.strip()
        if not s or s.startswith('#'): continue
        cells=[x.strip() for x in line.split(';')]
        req(id_col < len(cells), f"short ID row in {month}")
        eid=cells[id_col]
        # Do not parse solar longitude or Num(stat) for rows outside the already-frozen manifest.
        if allowed_month.get(eid) != month:
            continue
        req(max(sol_col,stat_col) < len(cells), f"short manifest row in {month}: {eid}")
        req(re.fullmatch(r"[A-Za-z0-9_]+",eid) is not None, f"unsafe event id {eid!r}")
        sol=float(cells[sol_col]); req(math.isfinite(sol) and 0.0 <= sol <= 360.0, f"invalid solar longitude for manifest event {eid}")
        req(not (BLIND[0] <= sol <= BLIND[1]), f"protected event entered predecessor manifest {eid}")
        raw=cells[stat_col]; nstat=None
        if raw not in {"","...","nan","NaN","None"}:
            try:x=float(raw)
            except Exception:x=float('nan')
            if math.isfinite(x) and x.is_integer(): nstat=int(x)
        out.append((eid,sol,nstat))
    return out


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--universe-manifest',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args(); args.output.mkdir(parents=True,exist_ok=True)

    manifest_raw=args.universe_manifest.read_bytes(); manifest_sha=hashlib.sha256(manifest_raw).hexdigest(); manifest=json.loads(manifest_raw)
    req(manifest['schema']=='ORBITTRACE_EXACT_1284_SPARSE_UNIVERSE_MANIFEST_V1','wrong universe manifest schema')
    req(manifest['years']==[2022,2023] and manifest['blind_exclusion']==[20.0,55.0],'universe manifest firewall changed')
    req(manifest['num_stat_accessed'] is False and manifest['shower_label_accessed'] is False,'universe manifest accessed forbidden fields')
    subset_ids={(d,b):list(manifest['subsets'][f'd{d}_b{b}']) for d in DENOMS for b in BUCKETS}
    for key,ids in subset_ids.items(): req(len(ids)==EXPECTED[key],f'manifest subset count changed {key}')
    audited_union=list(manifest['audited_union_ids']); req(len(audited_union)==sum(EXPECTED[(128,b)] for b in BUCKETS),'manifest union count changed')
    req(len(audited_union)==len(set(audited_union)),'duplicate manifest union IDs')
    allowed_month={str(k):str(v) for k,v in manifest['audited_union_authoritative_month'].items()}
    req(set(allowed_month)==set(audited_union),'manifest month map mismatch')

    rows={}; raw_month_sha={}
    for month in MONTHS:
        print(f'[numstat] fetch {month}',flush=True)
        text=dd.get_monthly_file_content_by_date(month); raw_month_sha[month]=hashlib.sha256(text.encode()).hexdigest()
        # Require byte-identical monthly source to predecessor-universe reconstruction.
        req(raw_month_sha[month]==manifest['source_sha256'][month],f'monthly source changed between manifest and station join: {month}')
        for eid,sol,nstat in parse_month_for_manifest(text,month,allowed_month):
            req(eid not in rows,f'duplicate authoritative manifest event in station join: {eid}')
            rows[eid]=(int(eid[:4]),nstat)
    req(set(rows)==set(audited_union),f'station join coverage mismatch: got {len(rows)} of {len(audited_union)} manifest IDs')

    def usable(eid:str)->bool:
        n=rows[eid][1]; return isinstance(n,int) and not isinstance(n,bool) and n>=2

    year_stats={}
    for y in YEARS:
        ids=[eid for eid in audited_union if rows[eid][0]==y]; good=[eid for eid in ids if usable(eid)]; frac=len(good)/len(ids) if ids else 0.0
        year_stats[str(y)]={'requested':len(ids),'usable_integer_ge2':len(good),'complete_fraction':frac,'gate_at_least_0_95':bool(frac>=MIN_COMPLETE),'all_events_usable':bool(len(good)==len(ids))}
    subset_stats={}
    for d in DENOMS:
        for b in BUCKETS:
            ids=subset_ids[(d,b)]; good=[eid for eid in ids if usable(eid)]; frac=len(good)/len(ids)
            subset_stats[f'd{d}_b{b}']={'requested':len(ids),'usable_integer_ge2':len(good),'complete_fraction':frac,'gate_at_least_0_95':bool(frac>=MIN_COMPLETE),'all_events_usable':bool(len(good)==len(ids))}

    sparse_hist=Counter(rows[eid][1] for eid in audited_union if usable(eid))
    mapping={eid:(int(rows[eid][1]) if usable(eid) else None) for eid in audited_union}
    mapping_raw=(json.dumps(mapping,sort_keys=True,separators=(',',':'))+'\n').encode(); mapping_sha=hashlib.sha256(mapping_raw).hexdigest()
    gates={'exact_subset_counts':True,'year_2022_complete_ge_0_95':year_stats['2022']['gate_at_least_0_95'],'year_2023_complete_ge_0_95':year_stats['2023']['gate_at_least_0_95'],'all_eight_subsets_complete_ge_0_95':all(x['gate_at_least_0_95'] for x in subset_stats.values()),'protected_values_not_emitted':True,'exact_manifest_join':True}
    verdict='PASS_TOPOMODAL_NUMSTAT_AVAILABILITY_V1' if all(gates.values()) else 'FAIL_TOPOMODAL_NUMSTAT_AVAILABILITY_V1'
    result={'schema':'ORBITTRACE_TOPOMODAL_NUMSTAT_AVAILABILITY_V1','verdict':verdict,'years':[2022,2023],'blind_exclusion':[20.0,55.0],'minimum_complete_fraction':MIN_COMPLETE,'expected_subset_counts':{f'd{d}_b{b}':EXPECTED[(d,b)] for d in DENOMS for b in BUCKETS},'audited_union_count':len(audited_union),'year_stats':year_stats,'subset_stats':subset_stats,'audited_union_numstat_histogram_diagnostic_only':{str(k):int(v) for k,v in sorted(sparse_hist.items())},'audited_mapping_sha256':mapping_sha,'universe_manifest_sha256':manifest_sha,'monthly_raw_sha256':raw_month_sha,'gates':gates,'source':'official_GMN_monthly_trajectory_files_via_gmn_python_api_0_0_13_joined_to_exact_1284_manifest','fields_parsed':['unique_trajectory_identifier','sol_lon_deg','num_stat'],'num_stat_parsed_only_for_manifest_ids':True,'station_codes_parsed':False,'station_geography_accessed':False,'participating_station_field_parsed':False,'shower_truth_parsed':False,'meteor_geometry_parsed_in_station_join':False,'target_information_access':False,'target_region_station_count_emitted_or_used':False,'sonotaco_scientific_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'scientific_ranking_computed':False,'post_result_parameter_search':False}
    (args.output/'TOPOMODAL_NUMSTAT_AVAILABILITY_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); (args.output/'audited_union_numstat_mapping.json').write_bytes(mapping_raw)
    print(json.dumps({'verdict':verdict,'year_stats':year_stats,'subset_stats':subset_stats,'mapping_sha256':mapping_sha,'universe_manifest_sha256':manifest_sha},indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
