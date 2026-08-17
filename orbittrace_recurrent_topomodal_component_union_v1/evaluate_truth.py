#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path
from typing import Any
import numpy as np

YEARS=(2022,2023)
MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
SOURCE_PRELABEL_SHA256='bd0d28410d23bef0c5c8847ecd8d54e91b74e148ce62e8533407787d265e468f'
QUALITY_SHA256='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
V8_RESULT_SHA256='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
BUCKETS=(0,1,2,3)

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path);req(spec is not None and spec.loader is not None,f'cannot import {path}')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def compact(m:dict[str,Any])->dict[str,Any]:return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def zero_filled_mrr(m:dict[str,Any])->float:
    eligible=int(m['eligible_labels']);qualified=int(m['qualified_matches']);conditional=float(m['mrr'])
    req(eligible>=qualified>=0,'invalid eligible/qualified counts')
    if eligible==0:return 0.0
    if qualified==0:
        req(conditional==0.0,'nonzero conditional MRR with zero qualified matches');return 0.0
    return conditional*qualified/eligible
def aggregate(panels:list[dict[str,Any]],key:str)->dict[str,Any]:
    vals=[p[key] for p in panels]; eligible=sum(int(x['eligible_labels']) for x in vals); mass=sum(float(x['mrr'])*int(x['qualified_matches']) for x in vals)
    return {'qualified_total':sum(int(x['qualified_matches']) for x in vals),'conditional_mrr_mean':float(np.mean([float(x['mrr']) for x in vals])),'zero_filled_mrr_mean':float(np.mean([zero_filled_mrr(x) for x in vals])),'zero_filled_mrr_pooled':mass/eligible if eligible else 0.0,'eligible_total':eligible,'reciprocal_mass':mass,'precision_mean':float(np.mean([float(x['top100_dominant_precision']) for x in vals])),'fragmentation_mean':float(np.mean([float(x['fragmentation_median_top500']) for x in vals])),'recovered_at_25_total':sum(int(x['recovered_at_25']) for x in vals),'recovered_at_50_total':sum(int(x['recovered_at_50']) for x in vals),'recovered_at_100_total':sum(int(x['recovered_at_100']) for x in vals),'recovered_at_500_total':sum(int(x['recovered_at_500']) for x in vals)}

def main()->int:
    ap=argparse.ArgumentParser()
    for name in ('prelabel','pretruth','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'):
        ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(sha256(a.quality_source)==QUALITY_SHA256,'quality source changed');req(sha256(a.v8_result_json)==V8_RESULT_SHA256,'v8 result changed')
    pre_sha=sha256(a.prelabel); audit_sha=sha256(a.pretruth); pre=json.loads(a.prelabel.read_text()); audit=json.loads(a.pretruth.read_text())
    req(pre['schema']=='ORBITTRACE_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1_PRELABEL','wrong prelabel schema')
    req(pre['scientific_role']=='PRELABEL_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1','wrong prelabel role')
    req(pre['source_prelabel_sha256']==SOURCE_PRELABEL_SHA256,'wrong source prelabel')
    req(pre['configuration']=={'rule':'one_recurrent_parent_plus_union_of_all_overlap_confirmed_topomodal_children','ranking':'exact_recurrent_parent_rank','equal_budget':'exact_recurrent_parent_count_per_panel'},'configuration changed')
    for flag in ('shower_truth_used','target_information_access','target_region_events_accessed','sonotaco_2013_2014_access','amos_scientific_access','maarsy_scientific_access','dms_scientific_access'):
        req(pre.get(flag) is False,f'prelabel firewall {flag}')
    req(audit['schema']=='ORBITTRACE_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1_PRETRUTH','wrong pretruth schema')
    req(audit['scientific_role']=='ZERO_LABEL_PRETRUTH_AUTHORIZATION','wrong pretruth role')
    req(audit['verdict']=='PASS_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1_PRETRUTH','pretruth did not pass')
    req(audit['prelabel_sha256']==pre_sha,'pretruth/prelabel mismatch');req(len(audit['gates'])==12 and all(bool(v) for v in audit['gates'].values()),'pretruth gates')
    subset={(int(r['denominator']),int(r['bucket'])):r for r in pre['subsets']};req(set(subset)=={(d,b) for d in (128,1024) for b in BUCKETS},'panel set')
    for row in pre['subsets']:
        s=list(row['successor_candidates']);p=list(row['recurrent_candidates']);K=int(row['equal_budget_k'])
        req(len(s)==len(p)==K and K>=1,'budget/count changed');req([int(x['rank']) for x in p]==list(range(1,K+1)),'parent rank')
        req([int(x['component_union_rank']) for x in s]==list(range(1,K+1)),'successor rank')
        for i,(x,parent) in enumerate(zip(s,p),1):
            req(x['catalogue_source']=='recurrent_topomodal_component_union','wrong source');req(str(x['parent_family_hash'])==str(parent['family_hash']),'parent identity changed')
            req(set(parent['event_ids']).issubset(set(x['event_ids'])),'parent not contained');req(int(x['component_union_rank'])==i,'rank mismatch')
        annual=set(row['annual_event_ids']['2022'])|set(row['annual_event_ids']['2023']);req(len(annual)==int(row['event_count']),'universe count')
        req(all(set(x['event_ids']).issubset(annual) for x in s+p),'candidate outside panel')
    parent=load_module(a.parent_runner,'component_union_truth_parent');q=load_module(a.quality_source,'component_union_truth_gmn')
    q.v1.mult.YEARS=YEARS;q.v1.mult.MONTH_KEYS=MONTH_KEYS;q.v1.mult.TOP_K=100
    runtime=q.v1.mult.load_frozen_runtime();support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS;support.MONTH_KEYS=MONTH_KEYS;support.CORPUS='orbittrace-recurrent-topomodal-component-union-v1';support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json);_candidate,baseline,_scorer=support.load_sources(a);scan,_cal,hidden,sources=support.parse_catalogue(baseline)
    req(isinstance(hidden,dict),'hidden truth unavailable');req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'truth/source set changed')
    events=[]
    for year in YEARS:events.extend(parent.normalize_event(r,year) for r in list(scan[year]))
    req(len(events)==738682,'target-excluded event universe changed');req(all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'protected region entered truth runtime')
    ids={str(e['id']) for e in events};req(len(ids)==len(events),'event ids nonunique')
    for row in pre['subsets']:
        for year in YEARS:req(set(row['annual_event_ids'][str(year)]).issubset(ids),'panel ids absent from runtime')
    panels=[]
    for d in (128,1024):
      for b in BUCKETS:
        frozen=subset[(d,b)];K=int(frozen['equal_budget_k']);succ=list(frozen['successor_candidates']);par=list(frozen['recurrent_candidates']);req(len(succ)==K,'successor count drift')
        for year in YEARS:
          annual=set(frozen['annual_event_ids'][str(year)])
          pm=compact(parent.metrics(par,hidden,annual));sm=compact(parent.metrics(succ,hidden,annual));req(int(pm['eligible_labels'])==int(sm['eligible_labels']),'eligibility changed')
          panels.append({'denominator':d,'bucket':b,'year':year,'equal_budget_k':K,'parent_equal_budget':pm,'successor_equal_budget':sm,'parent_zero_filled_mrr':zero_filled_mrr(pm),'successor_zero_filled_mrr':zero_filled_mrr(sm),'qualified_nonlower':int(sm['qualified_matches'])>=int(pm['qualified_matches']),'qualified_strict_win':int(sm['qualified_matches'])>int(pm['qualified_matches'])})
    scales={}
    for d in (128,1024):
      ps=[p for p in panels if p['denominator']==d];req(len(ps)==8,'missing annual panels');pa=aggregate(ps,'parent_equal_budget');sa=aggregate(ps,'successor_equal_budget');non=sum(bool(p['qualified_nonlower']) for p in ps);strict=sum(bool(p['qualified_strict_win']) for p in ps)
      scales[str(d)]={'panel_count':8,'parent_equal_budget':pa,'successor_equal_budget':sa,'qualified_nonlower_panels':non,'qualified_strict_win_panels':strict,'qualified_loss_panels':8-non}
    fp=scales['1024']['parent_equal_budget'];fs=scales['1024']['successor_equal_budget'];cp=scales['128']['parent_equal_budget'];cs=scales['128']['successor_equal_budget']
    gates={'fine_qualified_total_strictly_greater':fs['qualified_total']>fp['qualified_total'],'fine_qualified_nonlower_at_least_6_of_8':scales['1024']['qualified_nonlower_panels']>=6,'fine_zero_filled_mrr_mean_not_lower':fs['zero_filled_mrr_mean']>=fp['zero_filled_mrr_mean'],'fine_precision_mean_not_lower':fs['precision_mean']>=fp['precision_mean'],'fine_fragmentation_mean_not_higher':fs['fragmentation_mean']<=fp['fragmentation_mean'],'coarse_qualified_total_not_lower':cs['qualified_total']>=cp['qualified_total'],'coarse_qualified_nonlower_at_least_6_of_8':scales['128']['qualified_nonlower_panels']>=6,'coarse_zero_filled_mrr_mean_not_lower':cs['zero_filled_mrr_mean']>=cp['zero_filled_mrr_mean'],'coarse_precision_mean_not_lower':cs['precision_mean']>=cp['precision_mean'],'coarse_fragmentation_mean_not_higher':cs['fragmentation_mean']<=cp['fragmentation_mean']}
    verdict='PASS_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1' if all(gates.values()) else 'FAIL_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1'
    out={'schema':'ORBITTRACE_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1_TRUTH','scientific_role':'TARGET_EXCLUDED_GMN_2022_2023_SPARSE_RECOVERY_DEVELOPMENT','verdict':verdict,'source_stage1_run_id':32072681272,'source_stage1_artifact_id':9302288262,'source_prelabel_sha256':SOURCE_PRELABEL_SHA256,'prelabel_sha256':pre_sha,'pretruth_sha256':audit_sha,'ranking_metric_gate':'zero_filled_eligible_query_mrr_panel_mean','historical_conditional_mrr_role':'diagnostic_only','panels':panels,'scale_aggregates':scales,'gates':gates,'blind_exclusion':list(BLIND),'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False,'retroactive_previous_result_change':False}
    (a.output/'RECURRENT_TOPOMODAL_COMPONENT_UNION_V1_TRUTH.json').write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':verdict,'scales':scales,'gates':gates},indent=2,sort_keys=True),flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
