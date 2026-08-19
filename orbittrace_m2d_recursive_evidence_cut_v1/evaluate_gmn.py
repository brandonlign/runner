#!/usr/bin/env python3
from __future__ import annotations

import argparse,hashlib,importlib.util,json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any
import numpy as np
from scipy.optimize import linear_sum_assignment

YEARS=(2022,2023); MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13)); BLIND=(20.0,55.0); DENOMS=(128,1024); BUCKETS=(0,1,2,3)
BASELINE_SHA='7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd'; QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'; V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'

def req(x,m):
    if not x: raise RuntimeError(m)
def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f'cannot import {p}'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def evaluate(cands:list[dict[str,Any]], hidden:dict[str,str], annual:set[str])->dict[str,Any]:
    cnt=Counter(v for k,v in hidden.items() if k in annual and v!='SPORADIC'); labs=sorted(k for k,n in cnt.items() if n>=4); L,C=len(labs),len(cands)
    if not L: return {'eligible_showers':0,'candidate_count':C,'macro_f1':0.0,'macro_precision':0.0,'macro_recall':0.0,'recovered_f1_gt_05':0,'recovered_f1_gt_08':0}
    f=np.zeros((L,C)); p=np.zeros_like(f); r=np.zeros_like(f); li={x:i for i,x in enumerate(labs)}
    for j,c in enumerate(cands):
        ids=[str(x) for x in c['event_ids'] if str(x) in annual]; n=len(ids)
        if not n: continue
        cc=Counter(hidden.get(e,'SPORADIC') for e in ids)
        for lab,ov in cc.items():
            if lab not in li: continue
            i=li[lab]; pp=ov/n; rr=ov/cnt[lab]; ff=2*pp*rr/(pp+rr) if pp+rr else 0.; f[i,j]=ff; p[i,j]=pp; r[i,j]=rr
    if C: ri,cj=linear_sum_assignment(f,maximize=True)
    else: ri,cj=np.asarray([],int),np.asarray([],int)
    af=np.zeros(L); ap=np.zeros(L); ar=np.zeros(L)
    for i,j in zip(ri,cj): af[i]=f[i,j]; ap[i]=p[i,j]; ar[i]=r[i,j]
    return {'eligible_showers':L,'candidate_count':C,'macro_f1':float(np.mean(af)),'macro_precision':float(np.mean(ap)),'macro_recall':float(np.mean(ar)),'recovered_f1_gt_05':int(np.sum(af>.5)),'recovered_f1_gt_08':int(np.sum(af>.8))}

def agg(rows,side):
    v=[x[side] for x in rows]; return {'panels':len(v),'mean_macro_f1':mean(float(x['macro_f1']) for x in v),'mean_macro_precision':mean(float(x['macro_precision']) for x in v),'mean_macro_recall':mean(float(x['macro_recall']) for x in v),'total_recovered_f1_gt_05':sum(int(x['recovered_f1_gt_05']) for x in v),'total_recovered_f1_gt_08':sum(int(x['recovered_f1_gt_08']) for x in v)}

def main():
    ap=argparse.ArgumentParser()
    for n in ('refined-pretruth','literature-pretruth','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'): ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--expected-pretruth-sha',required=True); a=ap.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    req(sha(a.refined_pretruth)==a.expected_pretruth_sha,'sealed pretruth SHA mismatch'); req(sha(a.quality_source)==QUALITY_SHA and sha(a.v8_result_json)==V8_SHA,'runtime input changed')
    pre=json.loads(a.refined_pretruth.read_text()); lit=json.loads(a.literature_pretruth.read_text()); req(pre['schema']=='ORBITTRACE_M2D_RECURSIVE_EVIDENCE_CUT_V1_PRETRUTH','schema'); req(pre['scientific_role']=='TARGET_EXCLUDED_GMN_RECURSIVE_M2D_EVIDENCE_CUT_FROZEN_BEFORE_TRUTH','role'); req(pre['baseline_m2d_prelabel_sha256']==BASELINE_SHA,'baseline'); req(pre['shower_truth_used'] is False and pre['target_information_access'] is False and pre['target_region_events_accessed'] is False and pre['orbittrace_reveal_access'] is False and pre['sonotaco_scientific_access'] is False,'firewall'); req(pre['configuration']['new_tuned_parameters']==[] and pre['post_result_parameter_search'] is False,'post-result search'); req(lit['scientific_role']=='TARGET_EXCLUDED_GMN_SPARSE_LITERATURE_COMPARATORS_FROZEN_BEFORE_TRUTH' and lit['internal_prelabel_sha256']==BASELINE_SHA,'literature pretruth')
    sm={(int(s['denominator']),int(s['bucket'])):s for s in pre['subsets']}; req(set(sm)=={(d,b) for d in DENOMS for b in BUCKETS},'panel set')
    q=load(a.quality_source,'rec_truth_q'); q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=MONTH_KEYS; q.v1.mult.TOP_K=100; rt=q.v1.mult.load_frozen_runtime(); support=rt.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-m2d-recursive-evidence-cut-v1-truth'; support.RANKING_VARIANTS=('persistence',); req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'blind'); setattr(a,'fixed4_baseline_json',a.v8_result_json); _c,base,_s=support.load_sources(a); scan,_cal,hidden,sources=support.parse_catalogue(base); req(isinstance(hidden,dict) and sorted(scan)==list(YEARS),'truth load')
    comps=[]
    for d in DENOMS:
      for b in BUCKETS:
        s=sm[(d,b)]; ref=list(s['refined_candidates']); bas=list(s['baseline_candidates'])
        for y in YEARS:
          annual=set(map(str,s['annual_event_ids'][str(y)])); pp=lit['panels'][f'd{d}_b{b}_y{y}']; req(int(pp['event_count'])==len(annual),'universe')
          for name in ('sugar2017','hdbscan2025'):
            other=list(pp[name]['clusters']); k=len(other); rc=ref[:k]; bc=bas[:k]; comps.append({'denominator':d,'bucket':b,'year':y,'comparator':name,'capacity_k':k,'refined':evaluate(rc,hidden,annual),'baseline_m2d':evaluate(bc,hidden,annual),'literature':evaluate(other,hidden,annual),'refined_shortfall':max(0,k-len(ref)),'baseline_shortfall':max(0,k-len(bas))})
    routes={}
    for name in ('sugar2017','hdbscan2025'):
        rr=[x for x in comps if x['comparator']==name]; routes[name]={'refined':agg(rr,'refined'),'baseline_m2d':agg(rr,'baseline_m2d'),'literature':agg(rr,'literature'),'refined_shortfall_panels':sum(x['refined_shortfall']>0 for x in rr),'baseline_shortfall_panels':sum(x['baseline_shortfall']>0 for x in rr)}
    scales={}
    for d in DENOMS:
        rr=[x for x in comps if x['denominator']==d]; scales[str(d)]={'refined':agg(rr,'refined'),'baseline_m2d':agg(rr,'baseline_m2d')}
    rs=pre['global_size_summary']['refined']; bs=pre['global_size_summary']['baseline']
    g={'mechanism_active':int(pre['total_evidence_split_count'])>0,'sugar_f1_not_lower':routes['sugar2017']['refined']['mean_macro_f1']>=routes['sugar2017']['baseline_m2d']['mean_macro_f1'],'sugar_recovery_not_lower':routes['sugar2017']['refined']['total_recovered_f1_gt_05']>=routes['sugar2017']['baseline_m2d']['total_recovered_f1_gt_05'],'hdb_f1_not_lower':routes['hdbscan2025']['refined']['mean_macro_f1']>=routes['hdbscan2025']['baseline_m2d']['mean_macro_f1'],'hdb_recovery_not_lower':routes['hdbscan2025']['refined']['total_recovered_f1_gt_05']>=routes['hdbscan2025']['baseline_m2d']['total_recovered_f1_gt_05'],'still_beats_sugar':routes['sugar2017']['refined']['mean_macro_f1']>routes['sugar2017']['literature']['mean_macro_f1'] and routes['sugar2017']['refined']['total_recovered_f1_gt_05']>=routes['sugar2017']['literature']['total_recovered_f1_gt_05'],'still_beats_hdb_published':routes['hdbscan2025']['refined']['mean_macro_f1']>routes['hdbscan2025']['literature']['mean_macro_f1'] and routes['hdbscan2025']['refined']['total_recovered_f1_gt_05']>=routes['hdbscan2025']['literature']['total_recovered_f1_gt_05'],'coarse_f1_not_lower':scales['128']['refined']['mean_macro_f1']>=scales['128']['baseline_m2d']['mean_macro_f1'],'coarse_recovery_not_lower':scales['128']['refined']['total_recovered_f1_gt_05']>=scales['128']['baseline_m2d']['total_recovered_f1_gt_05'],'fine_f1_not_lower':scales['1024']['refined']['mean_macro_f1']>=scales['1024']['baseline_m2d']['mean_macro_f1'],'fine_recovery_not_lower':scales['1024']['refined']['total_recovered_f1_gt_05']>=scales['1024']['baseline_m2d']['total_recovered_f1_gt_05'],'mean_size_strictly_lower':float(rs['mean_member_count'])<float(bs['mean_member_count']),'p90_size_strictly_lower':float(rs['p90_member_count'])<float(bs['p90_member_count']),'max_size_strictly_lower':int(rs['max_member_count'])<int(bs['max_member_count'])}
    verdict='PASS_M2D_RECURSIVE_EVIDENCE_CUT_V1_GMN_DEVELOPMENT' if all(g.values()) else 'FAIL_M2D_RECURSIVE_EVIDENCE_CUT_V1_GMN_DEVELOPMENT'; out={'schema':'ORBITTRACE_M2D_RECURSIVE_EVIDENCE_CUT_V1_GMN_RESULT','verdict':verdict,'pretruth_sha256':sha(a.refined_pretruth),'routes':routes,'scales':scales,'size_summary':pre['global_size_summary'],'total_evidence_split_count':pre['total_evidence_split_count'],'gates':g,'comparisons':comps,'method_changed_after_truth':False,'post_result_parameter_search':False,'orbittrace_reveal_access':False,'sonotaco_scientific_access':False}; a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps({'verdict':verdict,'routes':routes,'scales':scales,'sizes':out['size_summary'],'splits':out['total_evidence_split_count'],'gates':g,'sha256':sha(a.output)},indent=2,sort_keys=True))
if __name__=='__main__': main()
