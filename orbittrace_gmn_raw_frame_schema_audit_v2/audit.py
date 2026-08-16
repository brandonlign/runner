#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import orbittrace_recurrent_eom_hdbscan_v1.run_development as parent

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)

TOKENS=(
    'ra','dec','radiant','vg','vgeo','velocity','speed','err','error','sd','sigma','unc',
    'qc','conv','ncam','q','peri','omega','node','ascending','inc','incl','ecc','semi','a','orbit'
)


def req(ok: bool, msg: str)->None:
    if not ok: raise RuntimeError(msg)


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
    qmod=parent.load_module(a.quality_source,'raw_frame_schema_v2_utility')
    qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime()
    support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS
    support.CORPUS='orbittrace-gmn-raw-frame-schema-audit-v2-target-excluded'
    support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'target firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json)
    _candidate,base,_scorer=support.load_sources(a)

    raw_columns:set[str]=set()
    monthly_columns:dict[str,list[str]]={}
    original=support.read_gmn_frame
    counter={'n':0}
    def wrapped(text: str):
        frame=original(text)
        cols=sorted(map(str,frame.columns))
        raw_columns.update(cols)
        counter['n']+=1
        monthly_columns[f'frame_{counter["n"]:02d}']=cols
        return frame
    support.read_gmn_frame=wrapped
    scan,_cal,_hidden,sources=support.parse_catalogue(base)
    req(sorted(scan)==list(YEARS),f'unexpected years {sorted(scan)}')
    req([x['key'] for x in sources]==list(MONTH_KEYS),'source list changed')
    req(counter['n']==24,f'expected 24 raw frames, got {counter["n"]}')

    # Column names only. No raw cell, event, or label value is serialized.
    relevant=[]
    for c in sorted(raw_columns):
        low=c.lower()
        if any(t in low for t in TOKENS): relevant.append(c)
    result={
        'verdict':'PASS_GMN_RAW_FRAME_SCHEMA_AUDIT_V2',
        'scientific_role':'PREPROJECTION_COLUMN_NAMES_ONLY_TARGET_EXCLUDED_GMN_2022_2023',
        'raw_frame_count':counter['n'],
        'raw_column_names':sorted(raw_columns),
        'relevant_raw_column_names':relevant,
        'monthly_column_names':monthly_columns,
        'normalized_scan_events_by_year':{str(y):len(scan[y]) for y in YEARS},
        'raw_cell_values_serialized':False,
        'event_values_serialized':False,
        'known_shower_labels_indexed_for_science':False,
        'known_shower_label_values_serialized':False,
        'blind_exclusion':list(BLIND),
        'target_information_access':False,
        'target_region_events_accessed':False,
        'sonotaco_2013_2014_access':False,
        'asfn_access':False,'efn_access':False,'amos_access':False,
        'maarsy_scientific_access':False,'dms_scientific_access':False,
    }
    (a.output/'GMN_RAW_FRAME_SCHEMA_AUDIT_V2.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'verdict':result['verdict'],'raw_column_count':len(raw_columns),'relevant_raw_column_names':relevant},indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
