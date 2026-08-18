#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np
from scipy.optimize import linear_sum_assignment
YEARS=(2022,2023); MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13)); BLIND=(20.0,55.0)
PRE_SHA='e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1'; RES_SHA='433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106'; QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'; V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'; COUNTS={2022:315024,2023:423658}
def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f'cannot import {p}'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def evaluate(cands:list[dict[str,Any]],hidden:dict[str,str],annual:set[str])->dict[str,Any]:
    cnt=Counter(v for k,v in hidden.items() if k in annual and v!='SPORADIC'); labels=sorted(k for k,n in cnt.items() if n>=4); L=len(labels); C=len(cands)
    if L==0:return {'eligible_showers':0,'candidate_count':C,'macro_f1':0.0,'macro_precision':0.0,'macro_recall':0.0,'recovered_f1_gt_05':0,'recovered_f1_gt_08':0}
    f=np.zeros((L,C),float); p=np.zeros_like(f); r=np.zeros_like(f)
    labix={lab:i for i,lab in enumerate(labels)}
    for j,c in enumerate(cands):
        ids=[str(x) for x in c['event_ids'] if str(x) in annual]; n=len(ids)
        if n==0:continue
        cc=Counter(hidden.get(eid,'SPORADIC') for eid in ids)
        for lab,ov in cc.items():
            if lab not in labix:continue
            i=labix[lab]; pp=ov/n; rr=ov/cnt[lab]; ff=2*pp*rr/(pp+rr) if pp+rr else 0.0; f[i,j]=ff; p[i,j]=pp; r[i,j]=rr
    if C:
        ri,cj=linear_sum_assignment(f,maximize=True)
    else: ri=np.asarray([],int); cj=np.asarray([],int)
    assigned=np.zeros(L,float); ap=np.zeros(L,float); ar=np.zeros(L,float)
    for i,j in zip(ri,cj): assigned[i]=f[i,j]; ap[i]=p[i,j]; ar[i]=r[i,j]
    return {'eligible_showers':L,'candidate_count':C,'macro_f1':float(np.mean(assigned)),'macro_precision':float(np.mean(ap)),'macro_recall':float(np.mean(ar)),'recovered_f1_gt_05':int(np.sum(assigned>0.5)),'recovered_f1_gt_08':int(np.sum(assigned>0.8)),'assigned_f1_by_label':{labels[i]:float(assigned[i]) for i in range(L)}}

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('pretruth','recurrent-prelabel','recurrent-result','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True); req(sha(a.recurrent_prelabel)==PRE_SHA and sha(a.recurrent_result)==RES_SHA,'recurrent artifacts changed'); req(sha(a.quality_source)==QUALITY_SHA and sha(a.v8_result_json)==V8_SHA,'runtime inputs changed')
    pre=json.loads(a.pretruth.read_text()); req(pre['scientific_role']=='TARGET_EXCLUDED_GMN_LITERATURE_COMPARATORS_FROZEN_BEFORE_TRUTH' and pre['shower_truth_used'] is False,'pretruth role/firewall'); req(pre['target_information_access'] is False and pre['target_region_events_accessed'] is False,'target firewall')
    rec=list(pre['recurrent_candidates']); sealed=json.loads(a.recurrent_result.read_text()); req(sealed['verdict']=='PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT','recurrent not pass')
    pr=load(a.parent_runner,'gmn_lit_truth_parent'); q=load(a.quality_source,'gmn_lit_truth_q'); q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=MONTH_KEYS; q.v1.mult.TOP_K=100; rt=q.v1.mult.load_frozen_runtime(); support=rt.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-recurrent-eom-gmn-literature-direct-v1-truth'; support.RANKING_VARIANTS=('persistence',); req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'blind changed'); setattr(a,'fixed4_baseline_json',a.v8_result_json); _c,base,_s=support.load_sources(a); scan,_cal,hidden,sources=support.parse_catalogue(base); req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'source set changed')
    annual={}
    for y in YEARS:
        rows=[pr.normalize_event(r,y) for r in list(scan[y])]; annual[y]={str(e['id']) for e in rows}; req(len(annual[y])==COUNTS[y],f'count {y}')
    methods={'recurrent_eom':{str(y):rec for y in YEARS},'sugar2017':{str(y):pre['panels'][str(y)]['sugar']['clusters'] for y in YEARS},'hdbscan2025':{str(y):pre['panels'][str(y)]['hdbscan2025']['clusters'] for y in YEARS}}
    metrics={m:{str(y):evaluate(methods[m][str(y)],hidden,annual[y]) for y in YEARS} for m in methods}
    gates={}; passed=0
    for comp in ('sugar2017','hdbscan2025'):
        for y in YEARS:
            r=metrics['recurrent_eom'][str(y)]; c=metrics[comp][str(y)]; ok=bool(r['macro_f1']>c['macro_f1'] and r['recovered_f1_gt_05']>=c['recovered_f1_gt_05']); gates[f'{comp}_{y}']={'passed':ok,'recurrent_macro_f1':r['macro_f1'],'comparator_macro_f1':c['macro_f1'],'recurrent_recovered_gt05':r['recovered_f1_gt_05'],'comparator_recovered_gt05':c['recovered_f1_gt_05']}; passed+=int(ok)
    verdict='PASS_RECURRENT_EOM_GMN_LITERATURE_4_OF_4' if passed==4 else 'NO_GMN_LITERATURE_4_OF_4_SUPERIORITY'
    out={'schema':'ORBITTRACE_RECURRENT_EOM_GMN_LITERATURE_DIRECT_V1_RESULT','verdict':verdict,'passed_pair_gates':passed,'total_pair_gates':4,'pretruth_sha256':sha(a.pretruth),'metrics':metrics,'pair_gates':gates,'recurrent_existing_zero_filled_mrr':{str(y):sealed['successor_metrics'][str(y)].get('zero_filled_mrr') for y in YEARS},'mrr_head_to_head_defined':False,'mrr_reason':'published literature comparators are unordered catalogues','target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':verdict,'passed_pair_gates':passed,'metrics':{m:{y:{k:v for k,v in z.items() if k!='assigned_f1_by_label'} for y,z in mm.items()} for m,mm in metrics.items()},'pair_gates':gates,'result_sha256':sha(a.output)},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
