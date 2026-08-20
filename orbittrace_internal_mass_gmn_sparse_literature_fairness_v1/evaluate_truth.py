#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any
import numpy as np
from scipy.optimize import linear_sum_assignment

YEARS=(2022,2023); MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13)); BLIND=(20.0,55.0); DENOMS=(128,1024); BUCKETS=(0,1,2,3)
INTERNAL_PRE_SHA='7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd'
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'; V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f'cannot import {p}'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def evaluate(cands:list[dict[str,Any]],hidden:dict[str,str],annual:set[str])->dict[str,Any]:
    cnt=Counter(v for k,v in hidden.items() if k in annual and v!='SPORADIC'); labels=sorted(k for k,n in cnt.items() if n>=4); L=len(labels); C=len(cands)
    if L==0:return {'eligible_showers':0,'candidate_count':C,'macro_f1':0.0,'macro_precision':0.0,'macro_recall':0.0,'recovered_f1_gt_05':0,'recovered_f1_gt_08':0,'assigned_f1_by_label':{}}
    f=np.zeros((L,C),float); p=np.zeros_like(f); r=np.zeros_like(f); labix={lab:i for i,lab in enumerate(labels)}
    for j,c in enumerate(cands):
        ids=[str(x) for x in c['event_ids'] if str(x) in annual]; n=len(ids)
        if n==0:continue
        cc=Counter(hidden.get(eid,'SPORADIC') for eid in ids)
        for lab,ov in cc.items():
            if lab not in labix:continue
            i=labix[lab]; pp=ov/n; rr=ov/cnt[lab]; ff=2*pp*rr/(pp+rr) if pp+rr else 0.0; f[i,j]=ff; p[i,j]=pp; r[i,j]=rr
    if C: ri,cj=linear_sum_assignment(f,maximize=True)
    else: ri=np.asarray([],int); cj=np.asarray([],int)
    assigned=np.zeros(L,float); ap=np.zeros(L,float); ar=np.zeros(L,float)
    for i,j in zip(ri,cj): assigned[i]=f[i,j]; ap[i]=p[i,j]; ar[i]=r[i,j]
    return {'eligible_showers':L,'candidate_count':C,'macro_f1':float(np.mean(assigned)),'macro_precision':float(np.mean(ap)),'macro_recall':float(np.mean(ar)),'recovered_f1_gt_05':int(np.sum(assigned>0.5)),'recovered_f1_gt_08':int(np.sum(assigned>0.8)),'assigned_f1_by_label':{labels[i]:float(assigned[i]) for i in range(L)}}

def agg(rows:list[dict[str,Any]],side:str)->dict[str,Any]:
    vals=[r[side] for r in rows]
    return {'panels':len(vals),'mean_macro_f1':mean(float(v['macro_f1']) for v in vals),'mean_macro_precision':mean(float(v['macro_precision']) for v in vals),'mean_macro_recall':mean(float(v['macro_recall']) for v in vals),'total_recovered_f1_gt_05':sum(int(v['recovered_f1_gt_05']) for v in vals),'total_recovered_f1_gt_08':sum(int(v['recovered_f1_gt_08']) for v in vals)}

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('pretruth','internal-prelabel','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'): ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    req(sha(a.internal_prelabel)==INTERNAL_PRE_SHA,'internal prelabel changed'); req(sha(a.quality_source)==QUALITY_SHA and sha(a.v8_result_json)==V8_SHA,'runtime inputs changed')
    pre=json.loads(a.pretruth.read_text()); req(pre['scientific_role']=='TARGET_EXCLUDED_GMN_SPARSE_LITERATURE_COMPARATORS_FROZEN_BEFORE_TRUTH' and pre['shower_truth_used'] is False,'pretruth role/firewall')
    req(pre['internal_prelabel_sha256']==INTERNAL_PRE_SHA,'pretruth internal hash'); req(pre['target_information_access'] is False and pre['target_region_events_accessed'] is False,'target firewall')
    ip=json.loads(a.internal_prelabel.read_text()); subsets={(int(s['denominator']),int(s['bucket'])):s for s in ip['subsets']}; req(set(subsets)=={(d,b) for d in DENOMS for b in BUCKETS},'panel set changed')
    pr=load(a.parent_runner,'gmn_sparse_lit_parent'); q=load(a.quality_source,'gmn_sparse_lit_q'); q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=MONTH_KEYS; q.v1.mult.TOP_K=100; rt=q.v1.mult.load_frozen_runtime(); support=rt.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-internal-mass-gmn-sparse-literature-fairness-v1-truth'; support.RANKING_VARIANTS=('persistence',); req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'blind changed'); setattr(a,'fixed4_baseline_json',a.v8_result_json); _c,base,_s=support.load_sources(a); scan,_cal,hidden,sources=support.parse_catalogue(base); req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'source set changed')
    all_eval=set()
    for s in subsets.values():
        for y in YEARS: all_eval.update(str(x) for x in s['annual_event_ids'][str(y)])
    req(all(eid in hidden for eid in all_eval),'panel event missing truth')
    comparisons=[]
    for d in DENOMS:
      for b in BUCKETS:
        s=subsets[(d,b)]; succ=list(s['successor_candidates'])
        for y in YEARS:
            key=f'd{d}_b{b}_y{y}'; pp=pre['panels'][key]; annual=set(str(x) for x in s['annual_event_ids'][str(y)])
            req(int(pp['event_count'])==len(annual),'panel event count drift')
            for comp in ('sugar2017','hdbscan2025'):
                cc=list(pp[comp]['clusters']); k=len(cc); sc=succ[:k]
                sm=evaluate(sc,hidden,annual); cm=evaluate(cc,hidden,annual)
                comparisons.append({'denominator':d,'bucket':b,'year':y,'comparator':comp,'comparator_capacity_k':k,'successor_available_candidates':len(succ),'successor_capacity_shortfall':max(0,k-len(succ)),'successor':sm,'comparator_metrics':cm,'macro_f1_relation':'win' if sm['macro_f1']>cm['macro_f1'] else ('tie' if sm['macro_f1']==cm['macro_f1'] else 'loss')})
    req(len(comparisons)==32,'comparison count')
    aggregates={}; gates={}
    for comp in ('sugar2017','hdbscan2025'):
        rs=[r for r in comparisons if r['comparator']==comp]; sa=agg(rs,'successor'); ca=agg(rs,'comparator_metrics')
        rel={'wins':sum(r['macro_f1_relation']=='win' for r in rs),'ties':sum(r['macro_f1_relation']=='tie' for r in rs),'losses':sum(r['macro_f1_relation']=='loss' for r in rs),'capacity_shortfall_panels':sum(r['successor_capacity_shortfall']>0 for r in rs),'total_capacity_shortfall':sum(int(r['successor_capacity_shortfall']) for r in rs)}
        scales={}
        for d in DENOMS:
            dr=[r for r in rs if r['denominator']==d]; scales[str(d)]={'successor':agg(dr,'successor'),'comparator':agg(dr,'comparator_metrics'),'wins':sum(r['macro_f1_relation']=='win' for r in dr),'ties':sum(r['macro_f1_relation']=='tie' for r in dr),'losses':sum(r['macro_f1_relation']=='loss' for r in dr)}
        passed=bool(sa['mean_macro_f1']>ca['mean_macro_f1'] and sa['total_recovered_f1_gt_05']>=ca['total_recovered_f1_gt_05'])
        aggregates[comp]={'successor':sa,'comparator':ca,'panel_relations':rel,'scale_aggregates':scales}
        gates[comp]={'passed':passed,'successor_mean_macro_f1':sa['mean_macro_f1'],'comparator_mean_macro_f1':ca['mean_macro_f1'],'successor_total_recovered_f1_gt_05':sa['total_recovered_f1_gt_05'],'comparator_total_recovered_f1_gt_05':ca['total_recovered_f1_gt_05']}
    verdict='PASS_INTERNAL_MASS_GMN_SPARSE_LITERATURE_FAIRNESS_V1' if all(x['passed'] for x in gates.values()) else 'NO_INTERNAL_MASS_GMN_SPARSE_LITERATURE_SUPERIORITY_V1'
    out={'schema':'ORBITTRACE_INTERNAL_MASS_GMN_SPARSE_LITERATURE_FAIRNESS_V1_RESULT','scientific_role':'TARGET_EXCLUDED_GMN_2022_2023_SPARSE_PAPER_FAIRNESS_BENCHMARK','verdict':verdict,'pretruth_sha256':sha(a.pretruth),'internal_prelabel_sha256':INTERNAL_PRE_SHA,'comparisons':comparisons,'aggregates':aggregates,'gates':gates,'interpretation_boundary':'GMN 2022/2023 is development-exposed; this is a same-universe published-config fairness benchmark, not untouched external validation or tuned-HDBSCAN-family superiority.','target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':verdict,'gates':gates,'aggregates':aggregates,'result_sha256':sha(a.output)},indent=2,sort_keys=True),flush=True); return 0
if __name__=='__main__': raise SystemExit(main())
