#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, importlib.util, json
from pathlib import Path
from typing import Any

FROZEN_PROTOCOL_BLOB='de8d040a1f9d3b0825ce56532efd5950acefc689'
FROZEN_BUILDER_BLOB='cd3fb15263fd4b2e38e4b413ece9b347b64816d5'
LAZY_HELPER_BLOB='79cc2e51929fd60f8e17faec4c1b04c19e43010e'
PARENT_PRELABEL_SHA256='efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993'
EXPECTED_PARENT_COUNT=2094
SMALL_MAX=256
STRESS_RANKS=(1,2,4,6,10,13)
EXPECTED_SMALL_COUNT=2027


def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)

def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git_blob(p:Path)->str:
    b=p.read_bytes();return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def load(path:Path,name:str)->Any:
    s=importlib.util.spec_from_file_location(name,path);req(s is not None and s.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--protocol',type=Path,required=True)
    ap.add_argument('--frozen-builder',type=Path,required=True)
    ap.add_argument('--lazy-helper',type=Path,required=True)
    ap.add_argument('--geometry',type=Path,required=True)
    ap.add_argument('--parent-prelabel',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    req(git_blob(a.protocol)==FROZEN_PROTOCOL_BLOB,'protocol changed')
    req(git_blob(a.frozen_builder)==FROZEN_BUILDER_BLOB,'frozen builder changed')
    req(git_blob(a.lazy_helper)==LAZY_HELPER_BLOB,'lazy helper changed')
    req(sha256(a.parent_prelabel)==PARENT_PRELABEL_SHA256,'parent prelabel changed')
    frozen=load(a.frozen_builder,'audit_frozen_local_trunk')
    lazy=load(a.lazy_helper,'audit_lazy_local_trunk')
    g=json.loads(a.geometry.read_text());p=json.loads(a.parent_prelabel.read_text())
    req(g['schema']=='ORBITTRACE_RECURRENT_LOCAL_TOPOMODAL_TRUNK_V1_GEOMETRY','wrong geometry schema')
    req(g['scientific_role']=='LABEL_FREE_TARGET_EXCLUDED_GMN_GEOMETRY_ONLY','geometry not label-free')
    req(g['events_total']==738682 and g['events_by_year']=={'2022':315024,'2023':423658},'geometry counts changed')
    req(g['blind_exclusion']==[20.0,55.0] and g['shower_truth_exported'] is False,'geometry firewall changed')
    for k in ('target_information_access','target_region_events_accessed','sonotaco_2013_2014_access','asfn_event_level_access','efn_event_level_access','amos_scientific_access','maarsy_scientific_access','dms_scientific_access','orbital_information_access','station_metadata_access','uncertainty_metadata_access'):
        req(g.get(k) is False,f'forbidden geometry flag {k}')
    parents=list(p['successor_candidates']);req(len(parents)==EXPECTED_PARENT_COUNT,'parent count changed')
    event_by_id={str(e['id']):e for e in g['events']};req(len(event_by_id)==738682,'geometry ID count')
    small=[i+1 for i,r in enumerate(parents) if len(r['event_ids'])<=SMALL_MAX]
    req(len(small)==EXPECTED_SMALL_COUNT,f'expected {EXPECTED_SMALL_COUNT} small parents, got {len(small)}')
    selected=sorted(set(small)|set(STRESS_RANKS));req(all(1<=r<=EXPECTED_PARENT_COUNT for r in selected),'bad audit rank')
    stress_sizes={str(r):len(parents[r-1]['event_ids']) for r in STRESS_RANKS}
    rows=[]
    for j,rank in enumerate(selected,1):
        parent_ids=[str(x) for x in parents[rank-1]['event_ids']]
        print(f'[lazy-audit] {j}/{len(selected)} rank={rank} n={len(parent_ids)}',flush=True)
        orig_ids,orig_summary=frozen.local_trunk(parent_ids,event_by_id)
        lazy_ids,lazy_summary=lazy.local_trunk_lazy(parent_ids,event_by_id)
        req(orig_ids==lazy_ids,f'final membership mismatch rank={rank}')
        req(orig_summary==lazy_summary,f'complete summary mismatch rank={rank}')
        rows.append({'rank':rank,'parent_member_count':len(parent_ids),'final_member_count':len(orig_ids),'decision':orig_summary['decision'],'final_membership_sha256':orig_summary['final_membership_sha256'],'exact_original_equivalence':True})
    out={'schema':'ORBITTRACE_LOCAL_TRUNK_LAZY_EQUIVALENCE_AUDIT_V1','scientific_role':'ZERO_LABEL_ENGINEERING_EQUIVALENCE_ONLY','verdict':'PASS_LOCAL_TRUNK_LAZY_EQUIVALENCE_AUDIT','frozen_protocol_blob':FROZEN_PROTOCOL_BLOB,'frozen_builder_blob':FROZEN_BUILDER_BLOB,'lazy_helper_blob':LAZY_HELPER_BLOB,'parent_prelabel_sha256':PARENT_PRELABEL_SHA256,'selection':{'small_member_count_max':SMALL_MAX,'small_parent_count':len(small),'stress_ranks':list(STRESS_RANKS),'stress_sizes':stress_sizes,'audited_unique_parent_count':len(selected)},'all_exact':True,'rows':rows,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'external_scientific_access':False,'post_result_parameter_search':False}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':out['verdict'],'audited_unique_parent_count':len(selected),'stress_sizes':stress_sizes},indent=2,sort_keys=True),flush=True)
    return 0
if __name__=='__main__':raise SystemExit(main())
