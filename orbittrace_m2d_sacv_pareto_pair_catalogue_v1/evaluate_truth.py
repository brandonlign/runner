#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path
from typing import Any
import numpy as np

YEARS=(2022,2023)
MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0); BUCKETS=(0,1,2,3)
QUALITY_SHA256='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
V8_RESULT_SHA256='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
FAIR_SHA='8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5'
SACV_V1_PRETRUTH_SHA='77528fbec227bf8d8d311b9054c46db43668d7f12e9460b85db680c4a6ce927b'

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load_module(path:Path,name:str)->Any:
    s=importlib.util.spec_from_file_location(name,path); req(s is not None and s.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def compact(m:dict[str,Any])->dict[str,Any]:return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def zero_filled_mrr(m:dict[str,Any])->float:
    e=int(m['eligible_labels']); q=int(m['qualified_matches']); c=float(m['mrr']); req(e>=q>=0,'invalid eligible/qualified')
    if e==0 or q==0:return 0.0
    return c*q/e
def aggregate(rows:list[dict[str,Any]],key:str)->dict[str,Any]:
    v=[r[key] for r in rows]; eligible=sum(int(x['eligible_labels']) for x in v); mass=sum(float(x['mrr'])*int(x['qualified_matches']) for x in v)
    return {'qualified_total':sum(int(x['qualified_matches']) for x in v),
            'conditional_mrr_mean':float(np.mean([float(x['mrr']) for x in v])),
            'zero_filled_mrr_mean':float(np.mean([zero_filled_mrr(x) for x in v])),
            'zero_filled_mrr_pooled':mass/eligible if eligible else 0.0,
            'eligible_total':eligible,'reciprocal_mass':mass,
            'precision_mean':float(np.mean([float(x['top100_dominant_precision']) for x in v])),
            'fragmentation_mean':float(np.mean([float(x['fragmentation_median_top500']) for x in v])),
            'recovered_at_25_total':sum(int(x['recovered_at_25']) for x in v),
            'recovered_at_50_total':sum(int(x['recovered_at_50']) for x in v),
            'recovered_at_100_total':sum(int(x['recovered_at_100']) for x in v),
            'recovered_at_500_total':sum(int(x['recovered_at_500']) for x in v)}

def main()->int:
    ap=argparse.ArgumentParser()
    for name in ('prelabel','pretruth','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'):
        ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha256(a.quality_source)==QUALITY_SHA256,'quality source changed'); req(sha256(a.v8_result_json)==V8_RESULT_SHA256,'v8 result changed')
    pre_sha=sha256(a.prelabel); audit_sha=sha256(a.pretruth); pre=json.loads(a.prelabel.read_text()); audit=json.loads(a.pretruth.read_text())
    req(pre['schema']=='ORBITTRACE_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRELABEL','prelabel schema')
    req(pre['scientific_role']=='TARGET_EXCLUDED_COMPLETE_SACV_VALIDATED_PAIR_CATALOGUE_FROZEN_BEFORE_SHOWER_TRUTH','prelabel role')
    req(pre['fair_pretruth_sha256']==FAIR_SHA and pre['sacv_v1_pretruth_sha256']==SACV_V1_PRETRUTH_SHA,'frozen source mismatch')
    req(pre['configuration']=={
        'annual_hypothesis_order':'excess_desc_parent_support_desc_contamination_asc_radius_asc_center_id_asc',
        'pair_validation':'exact_sacv_v1_reciprocal_crossyear_validation',
        'pair_membership':'exact_union_of_endpoint_sacv_balls_within_immutable_parent',
        'pareto_objectives_minimized':['immutable_m2d_parent_rank','sacv_2022_hypothesis_rank','sacv_2023_hypothesis_rank'],
        'pareto':'ordinary_nondominated_layers','final_order':'pareto_layer_asc_pair_hash_asc',
        'pair_hash':'sha256(parent_family_hash|center_2022_id|center_2023_id)',
        'duplicate_membership_policy':'retain_distinct_pair_identities_and_consume_budget',
        'equal_budget':'exact_sacv_v1_parent_candidate_count_per_panel','fallback_fill':'forbidden'},'configuration changed')
    for f in ('shower_truth_used','target_information_access','target_region_events_accessed','sonotaco_scientific_access'):req(pre.get(f) is False,f'prelabel firewall {f}')
    req(audit['schema']=='ORBITTRACE_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH' and audit['scientific_role']=='ZERO_LABEL_PRETRUTH_AUTHORIZATION','pretruth identity')
    req(audit['verdict']=='PASS_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_PRETRUTH','pretruth unauthorized')
    req(audit['prelabel_sha256']==pre_sha and len(audit['gates'])==10 and all(bool(v) for v in audit['gates'].values()),'pretruth gates')
    subset={(int(r['denominator']),int(r['bucket'])):r for r in pre['panels']}
    req(set(subset)=={(d,b) for d in (128,1024) for b in BUCKETS},'panel set')
    for row in pre['panels']:
        succ=list(row['successor_candidates']); base=list(row['sacv_v1_candidates']); K=int(row['equal_budget_k'])
        req(len(base)==K and len(succ)>=K and row['capacity_ok'] is True,'capacity')
        req([int(x['rank']) for x in base]==list(range(1,K+1)),'SACV ranks')
        req([int(x['rank']) for x in succ]==list(range(1,len(succ)+1)),'successor ranks')
        annual=set(row['annual_event_ids']['2022'])|set(row['annual_event_ids']['2023']); req(len(annual)==int(row['event_count']),'event universe')
        req(all(set(x['event_ids']).issubset(annual) for x in succ[:K]+base),'candidate outside panel')
    parent=load_module(a.parent_runner,'sacv_pareto_pair_truth_parent'); q=load_module(a.quality_source,'sacv_pareto_pair_truth_gmn')
    q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=MONTH_KEYS; q.v1.mult.TOP_K=100
    rt=q.v1.mult.load_frozen_runtime(); support=rt.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-m2d-sacv-pareto-pair-catalogue-v1'; support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'firewall changed'); setattr(a,'fixed4_baseline_json',a.v8_result_json)
    _candidate,baseline_payload,_scorer=support.load_sources(a); scan,_cal,hidden,sources=support.parse_catalogue(baseline_payload)
    req(isinstance(hidden,dict),'hidden truth unavailable'); req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'truth/source set')
    events=[]
    for y in YEARS:events.extend(parent.normalize_event(r,y) for r in list(scan[y]))
    req(len(events)==738682 and all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'event firewall')
    ids={str(e['id']) for e in events}; req(len(ids)==len(events),'event ids nonunique')
    panels=[]
    for d in (128,1024):
        for b in BUCKETS:
            frozen=subset[(d,b)]; K=int(frozen['equal_budget_k'])
            succ=[{'family_id':'PAIR-'+str(x['pair_hash']),'event_ids':list(x['event_ids'])} for x in list(frozen['successor_candidates'])[:K]]
            base=[{'family_id':str(x['family_id']),'event_ids':list(x['event_ids'])} for x in list(frozen['sacv_v1_candidates'])]
            req(len(succ)==len(base)==K,'equal budget')
            for y in YEARS:
                annual=set(frozen['annual_event_ids'][str(y)]); req(annual.issubset(ids),'panel ids absent')
                bm=compact(parent.metrics(base,hidden,annual)); sm=compact(parent.metrics(succ,hidden,annual)); req(int(bm['eligible_labels'])==int(sm['eligible_labels']),'eligibility')
                panels.append({'denominator':d,'bucket':b,'year':y,'equal_budget_k':K,'sacv_v1_equal_budget':bm,'successor_equal_budget':sm,
                               'sacv_v1_zero_filled_mrr':zero_filled_mrr(bm),'successor_zero_filled_mrr':zero_filled_mrr(sm),
                               'qualified_nonlower':int(sm['qualified_matches'])>=int(bm['qualified_matches']),
                               'qualified_strict_win':int(sm['qualified_matches'])>int(bm['qualified_matches'])})
    scales={}; gates={}
    for d in (128,1024):
        rows=[p for p in panels if p['denominator']==d]; req(len(rows)==8,'missing annual panels')
        ba=aggregate(rows,'sacv_v1_equal_budget'); sa=aggregate(rows,'successor_equal_budget'); non=sum(bool(p['qualified_nonlower']) for p in rows)
        scales[str(d)]={'panel_count':8,'sacv_v1_equal_budget':ba,'successor_equal_budget':sa,'qualified_nonlower_panels':non,'qualified_loss_panels':8-non}
        prefix='fine' if d==1024 else 'coarse'
        gates[f'{prefix}_qualified_total_not_lower']=sa['qualified_total']>=ba['qualified_total']
        gates[f'{prefix}_qualified_nonlower_at_least_6_of_8']=non>=6
        gates[f'{prefix}_zero_filled_mrr_mean_not_lower']=sa['zero_filled_mrr_mean']>=ba['zero_filled_mrr_mean']
        gates[f'{prefix}_precision_mean_not_lower']=sa['precision_mean']>=ba['precision_mean']
        gates[f'{prefix}_fragmentation_mean_not_higher']=sa['fragmentation_mean']<=ba['fragmentation_mean']
    strict=False
    for d in ('128','1024'):
        ba=scales[d]['sacv_v1_equal_budget']; sa=scales[d]['successor_equal_budget']
        strict = strict or sa['qualified_total']>ba['qualified_total'] or sa['zero_filled_mrr_mean']>ba['zero_filled_mrr_mean'] or sa['precision_mean']>ba['precision_mean']
    gates['at_least_one_strict_catalogue_gain']=bool(strict)
    verdict='PASS_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_DEVELOPMENT' if all(gates.values()) else 'FAIL_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_DEVELOPMENT'
    out={'schema':'ORBITTRACE_M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_TRUTH','scientific_role':'TARGET_EXCLUDED_GMN_2022_2023_SPARSE_CATALOGUE_DEVELOPMENT',
         'verdict':verdict,'prelabel_sha256':pre_sha,'pretruth_sha256':audit_sha,'ranking_metric_gate':'zero_filled_eligible_query_mrr_panel_mean',
         'historical_conditional_mrr_role':'diagnostic_only','panels':panels,'scale_aggregates':scales,'gates':gates,'blind_exclusion':list(BLIND),
         'target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'asfn_event_level_access':False,
         'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,
         'method_parameter_selection_from_result':False,'post_target_reveal_development':True}
    p=a.output/'M2D_SACV_PARETO_PAIR_CATALOGUE_V1_GMN_RESULT.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':verdict,'scales':scales,'gates':gates,'result_sha256':sha256(p)},indent=2,sort_keys=True),flush=True); return 0
if __name__=='__main__':raise SystemExit(main())
