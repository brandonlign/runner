#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import types
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{year}-{month:02d}" for year in YEARS for month in range(1,13))
REPAIRED_V6_SHA256="257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24"
STAGE_A_SCHEMA="orbittrace-final-stage-a-ranked-families-v2"
METHOD_ID="v6-LF-all-event-Mondrian-null"


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def sha256_path(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path:Path,name:str)->types.ModuleType:
    spec=importlib.util.spec_from_file_location(name,path); require(spec is not None and spec.loader is not None,f"cannot import {path}")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def parse_args()->argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument('--repaired-v6-source',required=True,type=Path); p.add_argument('--base-runner',required=True,type=Path)
    p.add_argument('--support-source-parts',required=True,type=Path); p.add_argument('--candidate-payload',required=True,type=Path)
    p.add_argument('--baseline-payload',required=True,type=Path); p.add_argument('--scorer-parts',required=True,type=Path)
    p.add_argument('--parallel-exact-wrapper',required=True,type=Path); p.add_argument('--output',required=True,type=Path)
    return p.parse_args()


def geometry_arrays(frame:pd.DataFrame,columns:dict[str,str]):
    ids=frame[columns['id']].astype(str).to_numpy()
    sol=pd.to_numeric(frame[columns['sol']],errors='coerce').to_numpy(dtype=np.float64)
    lam=pd.to_numeric(frame[columns['lam']],errors='coerce').to_numpy(dtype=np.float64)
    bet=pd.to_numeric(frame[columns['bet']],errors='coerce').to_numpy(dtype=np.float64)
    vg=pd.to_numeric(frame[columns['vg']],errors='coerce').to_numpy(dtype=np.float64)
    return ids,sol,lam,bet,vg


def valid_full_region(sol,lam,bet,vg):
    valid=np.isfinite(sol)&np.isfinite(lam)&np.isfinite(bet)&np.isfinite(vg)
    valid &= (sol>=0.0)&(sol<=360.0)&(lam>=0.0)&(lam<=360.0)
    valid &= (bet>=-90.0)&(bet<=90.0)&(vg>=5.0)&(vg<=75.0)
    return valid


def parse_full_geometry(support,base):
    scan={year:[] for year in YEARS}; calibration={year:[] for year in YEARS}; seen=set(); sources=[]
    for key in MONTH_KEYS:
        year=int(key[:4]); text=support.dd.get_monthly_file_content_by_date(key); raw=text.encode('utf-8')
        frame=support.read_gmn_frame(text); columns=support.column_map(frame)
        # The label-column name may be discovered by generic schema validation; no label value is indexed/read.
        ids,sol,lam,bet,vg=geometry_arrays(frame,columns); keep=valid_full_region(sol,lam,bet,vg)
        accepted=duplicates=0
        for index in np.flatnonzero(keep):
            event_id=str(ids[int(index)])
            if not event_id or event_id in seen:
                duplicates+=int(bool(event_id)); continue
            seen.add(event_id); s=float(sol[int(index)])
            event={'id':event_id,'year':year,'sol':s,'sun_lon':float(base.wrap180(float(lam[int(index)])-s)),'ecl_lat':float(bet[int(index)]),'vg':float(vg[int(index)]),'iau':0,'complex_key':'HIDDEN'}
            scan[year].append(event); calibration[year].append(dict(event,complex_key='SPORADIC')); accepted+=1
        sources.append({'key':key,'bytes':len(raw),'sha256':support.sha256_bytes(raw),'raw_rows':int(len(frame)),'accepted_rows':accepted,'duplicates_removed':duplicates,'label_column_name_present_but_values_unread':columns['label']})
        print(f'STAGE_A_GEOMETRY {key} raw={len(frame):,} accepted={accepted:,}',flush=True)
    for year in YEARS:
        require(len(scan[year])==len(calibration[year]),f'all-event calibration count mismatch {year}')
        require([e['id'] for e in scan[year]]==[e['id'] for e in calibration[year]],f'all-event calibration ID mismatch {year}')
        require(len(scan[year])>=1000,f'insufficient Stage-A rows {year}')
    return scan,calibration,sources


def family_record(family:dict[str,Any],event_year:dict[str,int])->dict[str,Any]:
    by_year={str(year):[] for year in YEARS}
    for event_id in sorted(str(x) for x in family['event_ids']):
        require(event_id in event_year,f'family event absent from Stage-A geometry universe: {event_id}')
        by_year[str(event_year[event_id])].append(event_id)
    require(all(by_year[str(year)] for year in YEARS),f"family {family['family_id']} lacks exact two-year support")
    return {'family_id':str(family['family_id']),'rank':int(family['rank']),'years':[int(y) for y in family['years']],'event_ids_by_year':by_year}


def main()->int:
    args=parse_args(); args.output.parent.mkdir(parents=True,exist_ok=True)
    require(sha256_path(args.repaired_v6_source)==REPAIRED_V6_SHA256,'repaired v6 source identity changed')
    v6=load_module(args.repaired_v6_source,'orbittrace_final_stage_a_v6_lf')
    old=v6.load_base_runner(args.base_runner); support=old.load_support_module(args.support_source_parts); candidate,base,scorer=support.load_sources(args)
    require(list(old.YEARS)==[2022,2023] and int(old.MAX_COMPONENTS_PER_BIN)==128,'frozen v6 base constants changed')
    require(float(support.BLIND_LOW)==20.0 and float(support.BLIND_HIGH)==55.0,'development blind-boundary identity changed')
    wrapper=load_module(args.parallel_exact_wrapper,'orbittrace_final_stage_a_parallel_exact'); execution=wrapper.install(v6,workers=4,min_parallel_records=256)
    scan,calibration,sources=parse_full_geometry(support,base)
    event_year={str(e['id']):int(year) for year in YEARS for e in scan[year]}
    require(len(event_year)==sum(len(scan[y]) for y in YEARS),'Stage-A stable IDs not globally unique')

    components=[]; audits=[]
    for year in YEARS:
        audit,_anchors,year_components=v6.scan_year_v6(old,year,scan[year],calibration[year],candidate,base,scorer,support)
        require(int(audit['scan_events'])==len(scan[year])==int(audit['calibration_events']),'Stage-A scan/calibration count changed')
        require(int(audit['proposal_cap_per_window'])==512 and int(audit['max_primary_proposals_per_year'])==36864,'Stage-A proposal budget changed')
        require(len(audit['supported_bins'])>=30,f'insufficient Stage-A supported bins {year}')
        audits.append(audit); components.extend(year_components)
    primary=v6.build_family_track_v6(old,components,base,'v3')
    rescue=v6.build_family_track_v6(old,components,base,'fixed4_rescue')
    require(primary,'Stage-A produced no primary families')
    records=[family_record(f,event_year) for f in primary]
    require([r['rank'] for r in records]==list(range(1,len(records)+1)),'Stage-A primary ranks not contiguous')

    stage={'schema':STAGE_A_SCHEMA,'method_id':METHOD_ID,'years':list(YEARS),'target_reference_accessed':False,'catalogue_shower_labels_used':False,'scientific_source':{'repaired_v6_sha256':REPAIRED_V6_SHA256,'all_event_null':True,'parameter_search':False,'null_trimming':False},'input_sources':sources,'execution':execution,'year_audits':audits,'primary_family_count':len(primary),'rescue_family_count_diagnostic_only':len(rescue),'primary_families':records}
    raw=json.dumps(stage,indent=2,sort_keys=True).encode(); args.output.write_bytes(raw+b'\n')
    digest=hashlib.sha256(json.dumps(stage,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    args.output.with_suffix(args.output.suffix+'.sha256').write_text(digest+'\n')
    print(json.dumps({'schema':STAGE_A_SCHEMA,'method_id':METHOD_ID,'primary_family_count':len(primary),'stage_a_sha256':digest,'target_reference_accessed':False,'catalogue_shower_labels_used':False},indent=2),flush=True)
    return 0


if __name__=='__main__': raise SystemExit(main())
