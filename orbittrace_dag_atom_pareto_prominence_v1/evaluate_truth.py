#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math
from pathlib import Path
from typing import Any
import numpy as np

YEARS=(2022,2023);MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13));BLIND=(20.0,55.0);BUCKETS=(0,1,2,3);DENOMS=(64,128,1024);SALT='ORBITTRACE_SCALE_STRESS_V1|'
QUALITY_SHA256='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
V8_RESULT_SHA256='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
OLD_PARETO_TRUTH_SHA256='697118cf053154d009fad5a323c92e40bdea6d187c054a58d81b9d6abb8f4b6f'

def req(x:bool,m:str)->None:
    if not x:raise RuntimeError(m)
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path);req(spec is not None and spec.loader is not None,f'cannot import {path}')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def compact(m:dict[str,Any])->dict[str,Any]:return {k:v for k,v in m.items() if k!='first_rank_by_label'}
def event_hash_u64(eid:str)->int:return int.from_bytes(hashlib.sha256((SALT+eid).encode()).digest()[:8],'big')
def uhash(ids:set[str])->str:return hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest()
def zero_mrr(m:dict[str,Any])->float:
    e=int(m['eligible_labels']);q=int(m['qualified_matches']);c=float(m['mrr']);req(e>=q>=0,'bad eligible/qualified')
    if e==0:return 0.0
    if q==0:req(c==0.0,'conditional MRR with no qualified');return 0.0
    return c*q/e
def aggregate(rows:list[dict[str,Any]],key:str)->dict[str,Any]:
    vals=[r[key] for r in rows];eligible=sum(int(x['eligible_labels']) for x in vals);mass=sum(float(x['mrr'])*int(x['qualified_matches']) for x in vals)
    return {'qualified_total':sum(int(x['qualified_matches']) for x in vals),'conditional_mrr_mean':float(np.mean([float(x['mrr']) for x in vals])),'zero_filled_mrr_mean':float(np.mean([zero_mrr(x) for x in vals])),'zero_filled_mrr_pooled':mass/eligible if eligible else 0.0,'eligible_total':eligible,'reciprocal_mass':mass,'precision_mean':float(np.mean([float(x['top100_dominant_precision']) for x in vals])),'fragmentation_mean':float(np.mean([float(x['fragmentation_median_top500']) for x in vals])),'recovered_at_25_total':sum(int(x['recovered_at_25']) for x in vals),'recovered_at_50_total':sum(int(x['recovered_at_50']) for x in vals),'recovered_at_100_total':sum(int(x['recovered_at_100']) for x in vals),'recovered_at_500_total':sum(int(x['recovered_at_500']) for x in vals)}
def metrics_match(a:dict[str,Any],b:dict[str,Any])->bool:
    keys=('eligible_labels','qualified_matches','recovered_at_25','recovered_at_50','recovered_at_100','recovered_at_500','top100_dominant_precision','mrr','fragmentation_median_top500')
    for k in keys:
        if k not in a or k not in b:return False
        if isinstance(a[k],(int,np.integer)) and isinstance(b[k],(int,np.integer)):
            if int(a[k])!=int(b[k]):return False
        else:
            if not math.isclose(float(a[k]),float(b[k]),rel_tol=0.0,abs_tol=1e-12):return False
    return True

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('prelabel','pretruth','old-pareto-truth','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(sha256(a.quality_source)==QUALITY_SHA256,'quality source changed');req(sha256(a.v8_result_json)==V8_RESULT_SHA256,'v8 result changed');req(sha256(a.old_pareto_truth)==OLD_PARETO_TRUTH_SHA256,'old Pareto truth changed')
    pre_sha=sha256(a.prelabel);audit_sha=sha256(a.pretruth);pre=json.loads(a.prelabel.read_text());audit=json.loads(a.pretruth.read_text());oldtruth=json.loads(a.old_pareto_truth.read_text())
    req(pre['schema']=='ORBITTRACE_DAG_ATOM_PARETO_PROMINENCE_V1_PRELABEL','wrong prelabel schema');req(pre['scientific_role']=='PRELABEL_DAG_ATOM_PARETO_PROMINENCE_V1','wrong prelabel role')
    expected_cfg={'candidate_membership':'exact_nonempty_topomodal_intersection_recurrent_atom','atom_filter':None,'objectives':['recurrent_parent_rank_minimize','contributing_topomodal_modal_prominence_rank_minimize'],'modal_prominence_order':'modal_contrast_desc_native_support_rank_asc_family_hash_asc','pareto':'ordinary_nondominated_layers','final_order':'pareto_layer_modal_prominence_rank_recurrence_rank_native_support_rank_atom_hash','equal_budget':'exact_recurrent_parent_count_per_panel','d64_comparator':'exact_recurrent_eom','d128_d1024_comparator':'exact_recurrent_topomodal_pareto_prominence_v1'}
    req(pre['configuration']==expected_cfg,'configuration changed')
    for flag in ('shower_truth_used','target_information_access','target_region_events_accessed','sonotaco_scientific_access','asfn_efn_event_level_access','amos_scientific_access','maarsy_scientific_access','dms_scientific_access','post_result_parameter_search'):req(pre.get(flag) is False,f'prelabel firewall {flag}')
    req(audit['schema']=='ORBITTRACE_DAG_ATOM_PARETO_PROMINENCE_V1_PRETRUTH','wrong pretruth schema');req(audit['verdict']=='PASS_DAG_ATOM_PARETO_PROMINENCE_V1_PRETRUTH','pretruth did not pass');req(audit['prelabel_sha256']==pre_sha,'pretruth/prelabel mismatch');req(len(audit['gates'])==12 and all(bool(v) for v in audit['gates'].values()) and audit['sparse_comparator_rebind_exact'] is True,'pretruth gates')
    panels={(int(x['denominator']),int(x['bucket'])):x for x in pre['panels']};req(set(panels)=={(d,b) for d in DENOMS for b in BUCKETS},'panel set')
    for p in pre['panels']:
        K=int(p['equal_budget_k']);s=list(p['successor_candidates']);c=list(p['comparator_candidates']);req(len(s)>=K and len(c)>=K,'candidate capacity');req([int(x['rank']) for x in s]==list(range(1,len(s)+1)),'successor rank')
        if int(p['denominator'])==64:req(p['comparator_kind']=='recurrent_eom' and len(c)==K,'d64 comparator changed')
        else:req(p['comparator_kind']=='recurrent_topomodal_pareto_prominence_v1','sparse comparator changed')
    req(oldtruth['verdict']=='PASS_RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1','old Pareto truth prerequisite')
    old_panel={(int(x['denominator']),int(x['bucket']),int(x['year'])):x for x in oldtruth['panels']};req(set(old_panel)=={(d,b,y) for d in (128,1024) for b in BUCKETS for y in YEARS},'old Pareto truth panels')

    parent=load_module(a.parent_runner,'dag_atom_truth_parent');q=load_module(a.quality_source,'dag_atom_truth_gmn');q.v1.mult.YEARS=YEARS;q.v1.mult.MONTH_KEYS=MONTH_KEYS;q.v1.mult.TOP_K=100
    runtime=q.v1.mult.load_frozen_runtime();support=runtime.load_support_module(a.support_source_parts);support.YEARS=YEARS;support.MONTH_KEYS=MONTH_KEYS;support.CORPUS='orbittrace-dag-atom-pareto-prominence-v1';support.RANKING_VARIANTS=('persistence',);req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'firewall changed')
    setattr(a,'fixed4_baseline_json',a.v8_result_json);_candidate,baseline,_scorer=support.load_sources(a);scan,_cal,hidden,sources=support.parse_catalogue(baseline);req(isinstance(hidden,dict),'hidden truth unavailable');req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'source set changed')
    events=[]
    for y in YEARS:events.extend(parent.normalize_event(r,y) for r in list(scan[y]))
    req(len(events)==738682 and len({str(e['id']) for e in events})==738682,'target-excluded universe changed');req(all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'protected region entered truth runtime')
    ids=np.asarray([str(e['id']) for e in events],dtype=object);yrs=np.asarray([int(e['year']) for e in events],dtype=np.int64);hashes=np.asarray([event_hash_u64(str(x)) for x in ids],dtype=np.uint64)

    outpan=[];old_rebind=True
    for d in DENOMS:
      for b in BUCKETS:
        p=panels[(d,b)];ix=np.flatnonzero((hashes%np.uint64(d))==np.uint64(b));panel_ids=set(str(ids[int(i)]) for i in ix);req(len(panel_ids)==int(p['event_count']) and uhash(panel_ids)==p['event_universe_sha256'],f'panel universe mismatch {d}/{b}')
        K=int(p['equal_budget_k']);succ=list(p['successor_candidates'])[:K];comp=list(p['comparator_candidates'])[:K];req(len(succ)==len(comp)==K,'equal budget drift')
        for y in YEARS:
          annual=set(str(ids[int(i)]) for i in ix if int(yrs[int(i)])==y);req(len(annual)==int(p['annual_event_count'][str(y)]),f'annual count mismatch {d}/{b}/{y}')
          cm=compact(parent.metrics(comp,hidden,annual));sm=compact(parent.metrics(succ,hidden,annual));req(int(cm['eligible_labels'])==int(sm['eligible_labels']),'eligibility differs')
          if d in (128,1024):
              oldm=old_panel[(d,b,y)]['successor_equal_budget'];ok=metrics_match(cm,oldm);old_rebind=old_rebind and ok;req(ok,f'old Pareto comparator truth failed to reproduce {d}/{b}/{y}')
          outpan.append({'denominator':d,'bucket':b,'year':y,'equal_budget_k':K,'comparator_kind':p['comparator_kind'],'comparator_equal_budget':cm,'successor_equal_budget':sm,'comparator_zero_filled_mrr':zero_mrr(cm),'successor_zero_filled_mrr':zero_mrr(sm),'qualified_nonlower':int(sm['qualified_matches'])>=int(cm['qualified_matches']),'qualified_strict_win':int(sm['qualified_matches'])>int(cm['qualified_matches'])})
    scales={}
    for d in DENOMS:
        rows=[x for x in outpan if int(x['denominator'])==d];req(len(rows)==8,'annual panel count');ca=aggregate(rows,'comparator_equal_budget');sa=aggregate(rows,'successor_equal_budget');non=sum(bool(x['qualified_nonlower']) for x in rows);strict=sum(bool(x['qualified_strict_win']) for x in rows)
        scales[str(d)]={'panel_count':8,'comparator_kind':rows[0]['comparator_kind'],'comparator_equal_budget':ca,'successor_equal_budget':sa,'qualified_nonlower_panels':non,'qualified_strict_win_panels':strict,'qualified_loss_panels':8-non}
    d64c=scales['64']['comparator_equal_budget'];d64s=scales['64']['successor_equal_budget'];d128c=scales['128']['comparator_equal_budget'];d128s=scales['128']['successor_equal_budget'];d1024c=scales['1024']['comparator_equal_budget'];d1024s=scales['1024']['successor_equal_budget']
    gates={
      'd64_qualified_total_not_lower':d64s['qualified_total']>=d64c['qualified_total'],
      'd64_qualified_nonlower_at_least_6_of_8':scales['64']['qualified_nonlower_panels']>=6,
      'd64_zero_filled_mrr_mean_not_lower':d64s['zero_filled_mrr_mean']>=d64c['zero_filled_mrr_mean'],
      'd64_precision_mean_not_lower':d64s['precision_mean']>=d64c['precision_mean'],
      'd64_fragmentation_mean_not_higher':d64s['fragmentation_mean']<=d64c['fragmentation_mean'],
      'd64_strict_material_effect':d64s['qualified_total']>d64c['qualified_total'] or d64s['zero_filled_mrr_mean']>d64c['zero_filled_mrr_mean'],
      'd128_qualified_total_not_lower':d128s['qualified_total']>=d128c['qualified_total'],
      'd128_qualified_nonlower_at_least_6_of_8':scales['128']['qualified_nonlower_panels']>=6,
      'd128_zero_filled_mrr_mean_not_lower':d128s['zero_filled_mrr_mean']>=d128c['zero_filled_mrr_mean'],
      'd128_precision_mean_not_lower':d128s['precision_mean']>=d128c['precision_mean'],
      'd128_fragmentation_mean_not_higher':d128s['fragmentation_mean']<=d128c['fragmentation_mean'],
      'd1024_qualified_total_not_lower':d1024s['qualified_total']>=d1024c['qualified_total'],
      'd1024_qualified_nonlower_at_least_6_of_8':scales['1024']['qualified_nonlower_panels']>=6,
      'd1024_zero_filled_mrr_mean_not_lower':d1024s['zero_filled_mrr_mean']>=d1024c['zero_filled_mrr_mean'],
      'd1024_precision_mean_not_lower':d1024s['precision_mean']>=d1024c['precision_mean'],
      'd1024_fragmentation_mean_not_higher':d1024s['fragmentation_mean']<=d1024c['fragmentation_mean'],
      'sparse_added_value_strict':(d128s['qualified_total']>d128c['qualified_total'] or d128s['zero_filled_mrr_mean']>d128c['zero_filled_mrr_mean'] or d1024s['qualified_total']>d1024c['qualified_total'] or d1024s['zero_filled_mrr_mean']>d1024c['zero_filled_mrr_mean'])
    }
    req(old_rebind,'old sparse comparator reproduction failed')
    verdict='PASS_DAG_ATOM_PARETO_PROMINENCE_V1' if all(gates.values()) else 'FAIL_DAG_ATOM_PARETO_PROMINENCE_V1'
    out={'schema':'ORBITTRACE_DAG_ATOM_PARETO_PROMINENCE_V1_TRUTH','scientific_role':'TARGET_EXCLUDED_GMN_2022_2023_DENSE_AND_SPARSE_DEVELOPMENT','verdict':verdict,'prelabel_sha256':pre_sha,'pretruth_sha256':audit_sha,'old_pareto_truth_sha256':OLD_PARETO_TRUTH_SHA256,'old_pareto_comparator_reproduced_exactly':old_rebind,'ranking_metric_gate':'zero_filled_eligible_query_mrr_panel_mean','historical_conditional_mrr_role':'diagnostic_only','panels':outpan,'scale_aggregates':scales,'gates':gates,'blind_exclusion':list(BLIND),'target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False,'post_result_parameter_search':False,'retroactive_previous_result_change':False}
    rp=a.output/'DAG_ATOM_PARETO_PROMINENCE_V1_TRUTH.json';rp.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n');(a.output/'RESULT_SHA256.txt').write_text(sha256(rp)+'\n')
    print(json.dumps({'verdict':verdict,'scales':scales,'gates':gates,'old_pareto_comparator_reproduced_exactly':old_rebind},indent=2,sort_keys=True),flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
