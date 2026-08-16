#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import orbittrace_recurrent_eom_hdbscan_v1.run_development as parent

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
FIELDS=('q_au','q_au_','e','i_deg','peri_deg','node_deg')


def req(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)


def finite(v: Any)->bool:
    try: return v is not None and math.isfinite(float(v))
    except (TypeError,ValueError): return False


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--quality-source',type=Path,required=True)
    p.add_argument('--support-source-parts',type=Path,required=True)
    p.add_argument('--candidate-payload',type=Path,required=True)
    p.add_argument('--baseline-payload',type=Path,required=True)
    p.add_argument('--scorer-parts',type=Path,required=True)
    p.add_argument('--v8-result-json',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    req(parent.sha(a.quality_source)==parent.QUALITY_SHA,'frozen GMN utility changed')
    req(parent.sha(a.v8_result_json)==parent.V8_RESULT_SHA,'frozen support result changed')
    qmod=parent.load_module(a.quality_source,'gmn_orbit_coverage_audit_v2_utility')
    qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime()
    support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS
    support.CORPUS='orbittrace-gmn-orbit-coverage-audit-v2-sol-first-target-excluded'
    support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'target firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json)
    _candidate,base,_scorer=support.load_sources(a)

    # Important firewall: inside the raw-frame hook, access ONLY ID + solar longitude
    # for all rows. Orbital columns are indexed only on rows already proven outside 20–55 deg.
    safe_orbit_by_id: dict[str, dict[str, Any]]={}
    original=support.read_gmn_frame
    frame_count=0
    raw_rows=0
    excluded_rows=0
    def wrapped(text: str):
        nonlocal frame_count,raw_rows,excluded_rows
        frame=original(text); frame_count+=1; raw_rows+=len(frame)
        req('unique_trajectory_identifier' in frame.columns,'raw GMN ID column missing')
        req('sol_lon_deg' in frame.columns,'raw GMN solar-longitude column missing')
        sol=np.asarray(frame['sol_lon_deg'],dtype=float)%360.0
        req(np.all(np.isfinite(sol)),'nonfinite raw solar longitude')
        safe_mask=~((sol>=BLIND[0])&(sol<=BLIND[1]))
        excluded_rows+=int(np.sum(~safe_mask))
        cols=['unique_trajectory_identifier']+[f for f in FIELDS if f in frame.columns]
        safe=frame.loc[safe_mask,cols]
        # Only safe rows reach any orbital-field access below.
        for row in safe.itertuples(index=False,name=None):
            eid=str(row[0])
            req(eid not in safe_orbit_by_id,f'duplicate safe raw trajectory ID: {eid}')
            safe_orbit_by_id[eid]={k:v for k,v in zip(cols[1:],row[1:])}
        return frame
    support.read_gmn_frame=wrapped
    scan,_cal,_hidden,sources=support.parse_catalogue(base)
    req(frame_count==24,f'expected 24 raw frames, got {frame_count}')
    req(sorted(scan)==list(YEARS),f'unexpected years {sorted(scan)}')
    req([x['key'] for x in sources]==list(MONTH_KEYS),'source list changed')

    by_year_ids={y:[str(row['id']) for row in scan[y]] for y in YEARS}
    accessible_ids=[eid for y in YEARS for eid in by_year_ids[y]]
    req(len(accessible_ids)==738682,f'accessible event count changed: {len(accessible_ids)}')
    req(len(set(accessible_ids))==len(accessible_ids),'duplicate accessible IDs')
    matched=[eid for eid in accessible_ids if eid in safe_orbit_by_id]
    counts={field:sum(finite(safe_orbit_by_id[eid].get(field)) for eid in matched) for field in FIELDS}
    q_selected='q_au' if counts['q_au']>=counts['q_au_'] else 'q_au_'
    required=(q_selected,'e','i_deg','peri_deg','node_deg')
    complete=sum(all(finite(safe_orbit_by_id[eid].get(f)) for f in required) for eid in matched)
    valid=0
    for eid in matched:
        row=safe_orbit_by_id[eid]
        if not all(finite(row.get(f)) for f in required): continue
        q=float(row[q_selected]); e=float(row['e']); inc=float(row['i_deg'])
        if q>0.0 and e>=0.0 and 0.0<=inc<=180.0: valid+=1
    year_complete={}
    for y in YEARS:
        ids=[eid for eid in by_year_ids[y] if eid in safe_orbit_by_id]
        year_complete[str(y)]={
            'accessible':len(by_year_ids[y]),
            'matched_safe_raw_id':len(ids),
            'complete_required_orbit':sum(all(finite(safe_orbit_by_id[eid].get(f)) for f in required) for eid in ids),
        }

    result={
        'verdict':'PASS_GMN_ORBIT_COVERAGE_AUDIT_V2',
        'scientific_role':'SOL_FIRST_TARGET_EXCLUDED_ORBIT_FIELD_COVERAGE_ONLY_NO_TRUTH',
        'firewall_order':'raw_id_and_sol_only_then_20_55_exclusion_then_orbit_fields',
        'raw_frame_count':frame_count,'raw_rows':raw_rows,'raw_rows_excluded_before_orbit_access':excluded_rows,
        'accessible_events':len(accessible_ids),'safe_raw_id_matches':len(matched),
        'finite_field_counts':counts,'selected_perihelion_distance_field':q_selected,
        'required_orbit_fields':list(required),'complete_required_orbit':complete,
        'physically_valid_required_orbit':valid,'coverage_fraction':complete/len(accessible_ids),'valid_fraction':valid/len(accessible_ids),
        'year_coverage':year_complete,
        'protected_row_orbit_fields_accessed':False,'event_values_serialized':False,
        'known_shower_labels_indexed_for_science':False,'known_shower_label_values_serialized':False,
        'blind_exclusion':list(BLIND),'target_information_access':False,'target_region_events_accessed':False,
        'sonotaco_2013_2014_access':False,'asfn_access':False,'efn_access':False,'amos_access':False,
        'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    (a.output/'GMN_ORBIT_COVERAGE_AUDIT_V2.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('verdict','raw_rows','raw_rows_excluded_before_orbit_access','accessible_events','safe_raw_id_matches','selected_perihelion_distance_field','complete_required_orbit','coverage_fraction','physically_valid_required_orbit','valid_fraction','year_coverage')},indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
