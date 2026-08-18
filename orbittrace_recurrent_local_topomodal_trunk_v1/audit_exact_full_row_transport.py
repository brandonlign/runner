#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, importlib.util, json
from pathlib import Path
from typing import Any

EXPECTED_PROTOCOL_BLOB='de8d040a1f9d3b0825ce56532efd5950acefc689'
EXPECTED_BUILDER_BLOB='cd3fb15263fd4b2e38e4b413ece9b347b64816d5'
EXPECTED_PARENT_SHA='efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993'
EXPECTED_PARENT_COUNT=2094
EXPECTED_SMALL_COUNT=2027
SMALL_MAX=256
STRESS_RANK=13


def req(x:bool,m:str)->None:
    if not x:raise RuntimeError(m)
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def git_blob(p:Path)->str:
    b=p.read_bytes();return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p);req(s is not None and s.loader is not None,f'cannot import {p}');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('protocol','frozen-builder','exact-transport','geometry','parent-prelabel','output'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
    req(git_blob(a.protocol)==EXPECTED_PROTOCOL_BLOB,'protocol changed');req(git_blob(a.frozen_builder)==EXPECTED_BUILDER_BLOB,'builder changed');req(sha256(a.parent_prelabel)==EXPECTED_PARENT_SHA,'parent prelabel changed')
    frozen=load(a.frozen_builder,'exact_row_audit_frozen');exact=load(a.exact_transport,'exact_row_audit_transport')
    g=json.loads(a.geometry.read_text());p=json.loads(a.parent_prelabel.read_text());parents=list(p['successor_candidates'])
    req(len(parents)==EXPECTED_PARENT_COUNT,'parent count changed');req(g['events_total']==738682 and g['events_by_year']=={'2022':315024,'2023':423658},'geometry counts changed');req(g['blind_exclusion']==[20.0,55.0] and g['shower_truth_exported'] is False,'geometry firewall')
    event_by_id={str(e['id']):e for e in g['events']};req(len(event_by_id)==738682,'geometry IDs')
    small=[i+1 for i,r in enumerate(parents) if len(r['event_ids'])<=SMALL_MAX];req(len(small)==EXPECTED_SMALL_COUNT,f'small count {len(small)}')
    selected=sorted(set(small)|{STRESS_RANK});rows=[]
    for j,rank in enumerate(selected,1):
        ids=[str(x) for x in parents[rank-1]['event_ids']]
        print(f'[exact-row-audit] {j}/{len(selected)} rank={rank} n={len(ids)}',flush=True)
        oi,os=frozen.local_trunk(ids,event_by_id);ei,es=exact.local_trunk_exact_full_row(ids,event_by_id)
        req(oi==ei,f'final membership mismatch rank={rank}');req(os==es,f'complete summary mismatch rank={rank}')
        rows.append({'rank':rank,'parent_member_count':len(ids),'final_member_count':len(oi),'decision':os['decision'],'final_membership_sha256':os['final_membership_sha256'],'exact_equivalence':True})
    out={'schema':'ORBITTRACE_LOCAL_TRUNK_EXACT_FULL_ROW_TRANSPORT_AUDIT_V1','scientific_role':'ZERO_LABEL_ENGINEERING_EQUIVALENCE_ONLY','verdict':'PASS_LOCAL_TRUNK_EXACT_ROW_TRANSPORT_AUDIT','selection':{'small_member_count_max':SMALL_MAX,'small_parent_count':len(small),'stress_rank':STRESS_RANK,'stress_member_count':len(parents[STRESS_RANK-1]['event_ids']),'audited_unique_parent_count':len(selected)},'all_exact':True,'rows':rows,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'external_scientific_access':False,'post_result_parameter_search':False}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps({'verdict':out['verdict'],'selection':out['selection']},indent=2,sort_keys=True),flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
