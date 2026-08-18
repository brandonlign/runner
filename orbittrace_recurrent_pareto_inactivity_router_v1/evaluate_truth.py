#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path
from typing import Any
import numpy as np

YEARS=(2022,2023); MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13)); BLIND=(20.0,55.0); SCALES=(64,128,1024); BUCKETS=(0,1,2,3)
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'; V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f'cannot import {p}'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def mem(r:dict[str,Any])->frozenset[str]:return frozenset(str(x) for x in r['event_ids'])
def compact(m:dict[str,Any])->dict[str,Any]:return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def zfmrr(m:dict[str,Any])->float:
    e=int(m['eligible_labels']); q=int(m['qualified_matches']); c=float(m['mrr']); req(e>=q>=0,'invalid eligible/qualified')
    if e==0:return 0.0
    if q==0:req(c==0.0,'conditional MRR nonzero with zero qualified');return 0.0
    return c*q/e

def aggregate(ps:list[dict[str,Any]],key:str)->dict[str,Any]:
    vals=[p[key] for p in ps]; eligible=sum(int(x['eligible_labels']) for x in vals); mass=sum(float(x['mrr'])*int(x['qualified_matches']) for x in vals)
    return {'qualified_total':sum(int(x['qualified_matches']) for x in vals),'conditional_mrr_mean':float(np.mean([float(x['mrr']) for x in vals])),'zero_filled_mrr_mean':float(np.mean([zfmrr(x) for x in vals])),'zero_filled_mrr_pooled':mass/eligible if eligible else 0.0,'precision_mean':float(np.mean([float(x['top100_dominant_precision']) for x in vals])),'fragmentation_mean':float(np.mean([float(x['fragmentation_median_top500']) for x in vals])),'recovered_at_25_total':sum(int(x['recovered_at_25']) for x in vals),'recovered_at_50_total':sum(int(x['recovered_at_50']) for x in vals),'recovered_at_100_total':sum(int(x['recovered_at_100']) for x in vals),'recovered_at_500_total':sum(int(x['recovered_at_500']) for x in vals),'eligible_total':eligible,'reciprocal_mass':mass}

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('prelabel','pretruth','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True); req(sha(a.quality_source)==QUALITY_SHA and sha(a.v8_result_json)==V8_SHA,'runtime inputs changed')
    pre=json.loads(a.prelabel.read_text()); audit=json.loads(a.pretruth.read_text()); pre_sha=sha(a.prelabel)
    req(pre['schema']=='ORBITTRACE_RECURRENT_PARETO_INACTIVITY_ROUTER_V1_PRELABEL' and pre['scientific_role']=='PRELABEL_SAMPLE_SIZE_ROUTER','prelabel role')
    req(audit['schema']=='ORBITTRACE_RECURRENT_PARETO_INACTIVITY_ROUTER_V1_PRETRUTH' and audit['verdict']=='PASS_RECURRENT_PARETO_INACTIVITY_ROUTER_V1_PRETRUTH','pretruth not pass'); req(audit['prelabel_sha256']==pre_sha and len(audit['gates'])==9 and all(audit['gates'].values()),'pretruth binding')
    for flag in ('shower_truth_used','target_information_access','target_region_events_accessed','sonotaco_scientific_access','asfn_efn_event_level_access','amos_scientific_access','maarsy_scientific_access','dms_scientific_access'):
        req(pre.get(flag) is False,f'firewall {flag}')
    panels={(int(x['denominator']),int(x['bucket'])):x for x in pre['panels']}; req(set(panels)=={(d,b) for d in SCALES for b in BUCKETS},'panel set')
    for x in panels.values():
        K=int(x['equal_budget_k']); r=list(x['recurrent_candidates']); s=list(x['routed_candidates']); req(len(r)==K and len(s)>=K,'budget/capacity'); universe=set(x['annual_event_ids']['2022'])|set(x['annual_event_ids']['2023']); req(len(universe)==int(x['event_count']),'universe count'); req(all(mem(z).issubset(universe) for z in r+s),'candidate outside universe')
        if bool(x['mechanism_active']): req(x['route']=='recurrent_eom' and [mem(z) for z in s]==[mem(z) for z in r],'active route identity')
        else:req(x['route']=='pareto_prominence','inactive route identity')

    parent=load(a.parent_runner,'router_truth_parent'); q=load(a.quality_source,'router_truth_gmn'); q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=MONTH_KEYS; q.v1.mult.TOP_K=100
    runtime=q.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-recurrent-pareto-inactivity-router-v1-truth'; support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'blind changed'); setattr(a,'fixed4_baseline_json',a.v8_result_json); _c,base,_s=support.load_sources(a); scan,_cal,hidden,sources=support.parse_catalogue(base)
    req(isinstance(hidden,dict) and sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'truth/source set')
    events=[]
    for y in YEARS:events.extend(parent.normalize_event(r,y) for r in list(scan[y]))
    req(len(events)==738682 and all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'target-excluded universe changed'); ids={str(e['id']) for e in events}; req(len(ids)==len(events),'duplicate ids')

    results=[]
    for d in SCALES:
        for b in BUCKETS:
            x=panels[(d,b)]; K=int(x['equal_budget_k']); r=list(x['recurrent_candidates']); s=list(x['routed_candidates'])[:K]
            for y in YEARS:
                annual=set(x['annual_event_ids'][str(y)]); req(annual.issubset(ids),'panel ids absent')
                rm=compact(parent.metrics(r,hidden,annual)); sm=compact(parent.metrics(s,hidden,annual)); req(int(rm['eligible_labels'])==int(sm['eligible_labels']),'eligibility changed')
                results.append({'denominator':d,'bucket':b,'year':y,'mechanism_active':bool(x['mechanism_active']),'route':x['route'],'equal_budget_k':K,'recurrent_equal_budget':rm,'router_equal_budget':sm,'recurrent_zero_filled_mrr':zfmrr(rm),'router_zero_filled_mrr':zfmrr(sm),'qualified_nonlower':int(sm['qualified_matches'])>=int(rm['qualified_matches'])})
    scales={}; gates={}
    for d in SCALES:
        ps=[p for p in results if p['denominator']==d]; req(len(ps)==8,'scale panel count'); ra=aggregate(ps,'recurrent_equal_budget'); sa=aggregate(ps,'router_equal_budget')
        scales[str(d)]={'panel_count':8,'recurrent':ra,'router':sa,'qualified_nonlower_panels':sum(bool(p['qualified_nonlower']) for p in ps),'active_annual_panels':sum(bool(p['mechanism_active']) for p in ps),'pareto_annual_panels':sum(not bool(p['mechanism_active']) for p in ps)}
        gates[f'd{d}_qualified_total_not_lower']=sa['qualified_total']>=ra['qualified_total']
        gates[f'd{d}_zero_filled_mrr_mean_not_lower']=sa['zero_filled_mrr_mean']>=ra['zero_filled_mrr_mean']
        gates[f'd{d}_precision_mean_not_lower']=sa['precision_mean']>=ra['precision_mean']
        gates[f'd{d}_fragmentation_mean_not_higher']=sa['fragmentation_mean']<=ra['fragmentation_mean']
    r64=scales['64']['recurrent']; s64=scales['64']['router']; gates['d64_strict_material_effect']=bool(s64['qualified_total']>r64['qualified_total'] or s64['zero_filled_mrr_mean']>r64['zero_filled_mrr_mean'])
    req(len(gates)==13,'gate count'); passed=sum(bool(v) for v in gates.values()); verdict='PASS_RECURRENT_PARETO_INACTIVITY_ROUTER_V1' if passed==13 else 'FAIL_RECURRENT_PARETO_INACTIVITY_ROUTER_V1'
    out={'schema':'ORBITTRACE_RECURRENT_PARETO_INACTIVITY_ROUTER_V1_TRUTH','scientific_role':'TARGET_EXCLUDED_GMN_SAMPLE_SIZE_GENERALIZATION_DEVELOPMENT','verdict':verdict,'passed_gates':passed,'total_gates':13,'prelabel_sha256':pre_sha,'pretruth_sha256':sha(a.pretruth),'ranking_metric_gate':'zero_filled_eligible_query_mrr','historical_conditional_mrr_role':'diagnostic_only','panels':results,'scale_aggregates':scales,'gates':gates,'blind_exclusion':list(BLIND),'target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'asfn_efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False,'asfn_negative_result_remains_binding':True}
    p=a.output/'RECURRENT_PARETO_INACTIVITY_ROUTER_V1_TRUTH.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':verdict,'passed_gates':passed,'scales':scales,'gates':gates,'result_sha256':sha(p)},indent=2,sort_keys=True),flush=True); return 0
if __name__=='__main__':raise SystemExit(main())
