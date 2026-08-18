#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path
from typing import Any
import numpy as np
YEARS=(2022,2023);MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13));BLIND=(20.0,55.0);D=64;BUCKETS=(0,1,2,3)
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990';V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
def req(x:bool,m:str)->None:
    if not x:raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p);req(s is not None and s.loader is not None,f'cannot import {p}');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def compact(m:dict[str,Any])->dict[str,Any]:return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def zmrr(m:dict[str,Any])->float:
    e=int(m['eligible_labels']);q=int(m['qualified_matches']);c=float(m['mrr']);req(e>=q>=0,'bad eligible/recovered');return 0.0 if e==0 else c*q/e
def agg(vals:list[dict[str,Any]])->dict[str,Any]:
    return {'qualified_total':sum(int(x['qualified_matches']) for x in vals),'zero_filled_mrr_mean':float(np.mean([zmrr(x) for x in vals])),'conditional_mrr_mean':float(np.mean([float(x['mrr']) for x in vals])),'precision_mean':float(np.mean([float(x['top100_dominant_precision']) for x in vals])),'fragmentation_mean':float(np.mean([float(x['fragmentation_median_top500']) for x in vals])),'recovered_at_25_total':sum(int(x['recovered_at_25']) for x in vals),'recovered_at_50_total':sum(int(x['recovered_at_50']) for x in vals),'recovered_at_100_total':sum(int(x['recovered_at_100']) for x in vals),'recovered_at_500_total':sum(int(x['recovered_at_500']) for x in vals),'eligible_total':sum(int(x['eligible_labels']) for x in vals),'reciprocal_mass':sum(float(x['mrr'])*int(x['qualified_matches']) for x in vals)}
def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('prelabel','pretruth','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True);req(sha(a.quality_source)==QUALITY_SHA,'quality source changed');req(sha(a.v8_result_json)==V8_SHA,'v8 changed')
    pre=json.loads(a.prelabel.read_text());audit=json.loads(a.pretruth.read_text());ph=sha(a.prelabel)
    req(pre['schema']=='ORBITTRACE_PARETO_PARENT_SET_UNANIMOUS_V1_PRELABEL' and pre['scientific_role']=='PRELABEL_PARETO_PARENT_SET_UNANIMOUS_V1','prelabel identity')
    req(audit['verdict']=='PASS_PARETO_PARENT_SET_UNANIMOUS_V1_PRETRUTH' and audit['prelabel_sha256']==ph and len(audit['gates'])==12 and all(audit['gates'].values()),'pretruth authorization')
    for f in ('shower_truth_used','target_information_access','target_region_events_accessed','sonotaco_2013_2014_access','amos_scientific_access','maarsy_scientific_access','dms_scientific_access'):req(pre.get(f) is False,f'firewall {f}')
    subset={int(r['bucket']):r for r in pre['subsets']};req(set(subset)==set(BUCKETS) and all(int(r['denominator'])==D for r in pre['subsets']),'panel set')
    parent=load(a.parent_runner,'uset_truth_parent');q=load(a.quality_source,'uset_truth_gmn');q.v1.mult.YEARS=YEARS;q.v1.mult.MONTH_KEYS=MONTH_KEYS;q.v1.mult.TOP_K=100
    runtime=q.v1.mult.load_frozen_runtime();support=runtime.load_support_module(a.support_source_parts);support.YEARS=YEARS;support.MONTH_KEYS=MONTH_KEYS;support.CORPUS='orbittrace-pareto-parent-set-unanimous-v1-truth';support.RANKING_VARIANTS=('persistence',);req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'firewall changed');setattr(a,'fixed4_baseline_json',a.v8_result_json)
    _c,base,_s=support.load_sources(a);scan,_cal,hidden,sources=support.parse_catalogue(base);req(isinstance(hidden,dict),'truth unavailable');req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'source set')
    events=[]
    for y in YEARS:events.extend(parent.normalize_event(r,y) for r in list(scan[y]))
    req(len(events)==738682 and all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'target-excluded universe changed');runtime_ids={str(e['id']) for e in events};req(len(runtime_ids)==738682,'duplicate ids')
    panels=[]
    for b in BUCKETS:
        r=subset[b];K=int(r['equal_budget_k']);par=list(r['recurrent_candidates']);succ=list(r['successor_candidates'])[:K];req(len(par)==len(succ)==K,'equal budget');req([int(x['rank']) for x in par]==list(range(1,K+1)),'parent rank');req([int(x['pareto_parent_set_rank']) for x in r['successor_candidates']]==list(range(1,len(r['successor_candidates'])+1)),'successor rank')
        for y in YEARS:
            annual=set(r['annual_event_ids'][str(y)]);req(annual.issubset(runtime_ids),'panel ids absent');pm=compact(parent.metrics(par,hidden,annual));sm=compact(parent.metrics(succ,hidden,annual));req(int(pm['eligible_labels'])==int(sm['eligible_labels']),'eligibility changed')
            panels.append({'denominator':D,'bucket':b,'year':y,'equal_budget_k':K,'parent':pm,'successor':sm,'parent_zero_filled_mrr':zmrr(pm),'successor_zero_filled_mrr':zmrr(sm),'qualified_nonlower':int(sm['qualified_matches'])>=int(pm['qualified_matches'])})
    req(len(panels)==8,'annual panel count');pa=agg([p['parent'] for p in panels]);sa=agg([p['successor'] for p in panels]);non=sum(bool(p['qualified_nonlower']) for p in panels)
    gates={'qualified_total_not_lower':sa['qualified_total']>=pa['qualified_total'],'qualified_nonlower_at_least_6_of_8':non>=6,'zero_filled_mrr_mean_not_lower':sa['zero_filled_mrr_mean']>=pa['zero_filled_mrr_mean'],'precision_mean_not_lower':sa['precision_mean']>=pa['precision_mean'],'fragmentation_mean_not_higher':sa['fragmentation_mean']<=pa['fragmentation_mean']}
    verdict='PASS_PARETO_PARENT_SET_UNANIMOUS_V1' if all(gates.values()) else 'FAIL_PARETO_PARENT_SET_UNANIMOUS_V1'
    out={'schema':'ORBITTRACE_PARETO_PARENT_SET_UNANIMOUS_V1_TRUTH','scientific_role':'TARGET_EXCLUDED_GMN_D64_SET_VALUED_CORRESPONDENCE_TEST','verdict':verdict,'prelabel_sha256':ph,'pretruth_sha256':sha(a.pretruth),'ranking_metric_gate':'zero_filled_eligible_query_mrr_panel_mean','historical_conditional_mrr_role':'diagnostic_only','panels':panels,'parent_aggregate':pa,'successor_aggregate':sa,'qualified_nonlower_panels':non,'gates':gates,'blind_exclusion':list(BLIND),'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False}
    p=a.output/'PARETO_PARENT_SET_UNANIMOUS_V1_TRUTH.json';p.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps({'verdict':verdict,'parent':pa,'successor':sa,'qualified_nonlower_panels':non,'gates':gates,'result_sha256':sha(p)},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
