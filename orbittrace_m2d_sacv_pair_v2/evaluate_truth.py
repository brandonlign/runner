#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any
import numpy as np
from scipy.optimize import linear_sum_assignment
YEARS=(2022,2023);MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13));BLIND=(20.0,55.0);DENOMS=(128,1024);BUCKETS=(0,1,2,3)
FAIR_SHA='8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5';INTERNAL_SHA='7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd';QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990';V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
SACV_BASELINE={'sugar2017':{'precision':0.8508954378869,'f1':0.8169897091265172},'hdbscan2025':{'precision':0.9369285146156977,'f1':0.8863023728371738}}
EXPECTED_PARENT={'sugar2017':{'mean_macro_f1':0.5608353827866924,'mean_macro_precision':0.546515915964596,'mean_macro_recall':0.6006608502900602,'total_recovered_f1_gt_05':164,'total_recovered_f1_gt_08':112},'hdbscan2025':{'mean_macro_f1':0.03799360813979141,'mean_macro_precision':0.034748036963226744,'mean_macro_recall':0.04201631001380206,'total_recovered_f1_gt_05':28,'total_recovered_f1_gt_08':28}}
def req(x:bool,m:str)->None:
    if not x:raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p);req(s is not None and s.loader is not None,f'cannot import {p}');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def matrices(cands,hidden,annual):
    counts=Counter(v for k,v in hidden.items() if k in annual and v!='SPORADIC');labels=sorted(k for k,n in counts.items() if n>=4);L,C=len(labels),len(cands);f=np.zeros((L,C));p=np.zeros_like(f);r=np.zeros_like(f);nmem=np.zeros(C,dtype=int);ix={lab:i for i,lab in enumerate(labels)}
    for j,c in enumerate(cands):
        ids=[str(x) for x in c['event_ids'] if str(x) in annual];nmem[j]=len(ids)
        if not ids:continue
        cc=Counter(hidden.get(e,'SPORADIC') for e in ids)
        for lab,ov in cc.items():
            if lab not in ix:continue
            i=ix[lab];pp=ov/len(ids);rr=ov/counts[lab];ff=2*pp*rr/(pp+rr) if pp+rr else 0.;p[i,j]=pp;r[i,j]=rr;f[i,j]=ff
    return {'labels':labels,'f':f,'p':p,'r':r,'nmem':nmem}
def assigned(m):
    f,p,r=m['f'],m['p'],m['r'];L,C=f.shape;af=np.zeros(L);ap=np.zeros(L);ar=np.zeros(L);ai=np.full(L,-1,dtype=int);n=max(L,C)
    if n:
        cost=np.zeros((n,n));cost[:L,:C]=-f;ri,cj=linear_sum_assignment(cost)
        for i,j in zip(ri,cj):
            if i<L and j<C:af[i],ap[i],ar[i],ai[i]=f[i,j],p[i,j],r[i,j],int(j)
    return {'eligible_showers':L,'candidate_count':C,'macro_f1':float(np.mean(af)) if L else 0.,'macro_precision':float(np.mean(ap)) if L else 0.,'macro_recall':float(np.mean(ar)) if L else 0.,'recovered_f1_gt_05':int(np.sum(af>0.5)),'recovered_f1_gt_08':int(np.sum(af>0.8)),'assigned_f1':af,'assigned_precision':ap,'assigned_recall':ar,'candidate_by_label':ai}
def pack(a):return {k:v for k,v in a.items() if k not in {'assigned_f1','assigned_precision','assigned_recall','candidate_by_label'}}
def aggregate(rows,key):
    v=[r[key] for r in rows];return {'panels':len(v),'mean_macro_f1':mean(float(x['macro_f1']) for x in v),'mean_macro_precision':mean(float(x['macro_precision']) for x in v),'mean_macro_recall':mean(float(x['macro_recall']) for x in v),'total_recovered_f1_gt_05':sum(int(x['recovered_f1_gt_05']) for x in v),'total_recovered_f1_gt_08':sum(int(x['recovered_f1_gt_08']) for x in v)}
def paired_summary(rows):
    ne=[x for x in rows if int(x['extraction_member_count'])>0]
    return {'count':len(rows),'nonempty_count':len(ne),'nonempty_fraction':len(ne)/len(rows) if rows else 0.,'parent_mean_precision':mean(x['parent_precision'] for x in rows) if rows else 0.,'extraction_mean_precision':mean(x['extraction_precision'] for x in rows) if rows else 0.,'parent_mean_recall':mean(x['parent_recall'] for x in rows) if rows else 0.,'extraction_mean_recall':mean(x['extraction_recall'] for x in rows) if rows else 0.,'parent_mean_f1':mean(x['parent_f1'] for x in rows) if rows else 0.,'extraction_mean_f1':mean(x['extraction_f1'] for x in rows) if rows else 0.,'nonempty_precision_nonregression_fraction':sum(x['extraction_precision']>=x['parent_precision'] for x in ne)/len(ne) if ne else 0.,'strict_refined_assignment_count':sum(x['strict_refined'] for x in rows),'precision_strict_win_count':sum(x['extraction_precision']>x['parent_precision'] for x in rows),'f1_strict_win_count':sum(x['extraction_f1']>x['parent_f1'] for x in rows),'f1_loss_count':sum(x['extraction_f1']<x['parent_f1'] for x in rows)}
def exact_parent(comp,got):return all(got[k]==v for k,v in EXPECTED_PARENT[comp].items())
def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('fair-pretruth','pair-pretruth','internal-prelabel','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);req(sha(a.fair_pretruth)==FAIR_SHA,'fair changed');req(sha(a.internal_prelabel)==INTERNAL_SHA,'internal changed');req(sha(a.quality_source)==QUALITY_SHA and sha(a.v8_result_json)==V8_SHA,'runtime changed')
    fair=json.loads(a.fair_pretruth.read_text());pv=json.loads(a.pair_pretruth.read_text());req(pv['scientific_role']=='TARGET_EXCLUDED_SACV_RECURRENCE_PAIR_MEMBERSHIPS_FROZEN_BEFORE_SHOWER_TRUTH','wrong pair role');req(pv['fair_pretruth_sha256']==FAIR_SHA,'pair parent changed');req(pv['shower_truth_used'] is False and pv['target_information_access'] is False and pv['target_region_events_accessed'] is False and pv['post_result_parameter_search'] is False,'pair firewall')
    fs={(int(s['denominator']),int(s['bucket'])):s for s in fair['subsets']};xs={(int(s['denominator']),int(s['bucket'])):s for s in pv['subsets']};req(set(fs)==set(xs)=={(d,b) for d in DENOMS for b in BUCKETS},'panel mismatch')
    for key in fs:
        pp=list(fs[key]['successor_candidates']);xx=list(xs[key]['extractions']);req(len(pp)==len(xx),'candidate count changed')
        for pos,(p,x) in enumerate(zip(pp,xx),1):
            req(int(p['internal_mass_rank'])==int(x['rank'])==pos,f'rank mismatch {key}/{pos}');req(str(p['family_id'])==str(x['family_id']) and str(p['family_hash'])==str(x['family_hash']),f'identity {key}/{pos}');ps=set(map(str,p['event_ids']));req(set(map(str,x['output_ids'])).issubset(ps),f'extraction escaped {key}/{pos}')
    q=load(a.quality_source,'pair_truth_q');q.v1.mult.YEARS=YEARS;q.v1.mult.MONTH_KEYS=MONTH_KEYS;q.v1.mult.TOP_K=100;rt=q.v1.mult.load_frozen_runtime();support=rt.load_support_module(a.support_source_parts);support.YEARS=YEARS;support.MONTH_KEYS=MONTH_KEYS;support.CORPUS='orbittrace-m2d-sacv-pair-v2-gmn-truth';support.RANKING_VARIANTS=('persistence',);req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'blind changed');setattr(a,'fixed4_baseline_json',a.v8_result_json);_c,base,_s=support.load_sources(a);scan,_cal,hidden,sources=support.parse_catalogue(base);req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'source set changed')
    comparisons=[];paired={c:[] for c in ('sugar2017','hdbscan2025')}
    for d in DENOMS:
      for b in BUCKETS:
        fsub,xsub=fs[(d,b)],xs[(d,b)];parents=list(fsub['successor_candidates']);outs=[{'family_id':x['family_id'],'event_ids':x['output_ids']} for x in xsub['extractions']]
        for y in YEARS:
          key=f'd{d}_b{b}_y{y}';annual=set(map(str,fsub['annual_event_ids'][str(y)]));panel=fair['panels'][key]
          for comp in ('sugar2017','hdbscan2025'):
            k=len(panel[comp]['clusters']);pm=matrices(parents[:k],hidden,annual);xm=matrices(outs[:k],hidden,annual);req(pm['labels']==xm['labels'],'truth labels');pa=assigned(pm);xa=assigned(xm);local=[]
            for i,label in enumerate(pm['labels']):
              j=int(pa['candidate_by_label'][i])
              if j<0 or float(pa['assigned_f1'][i])<=0.5:continue
              pN=int(pm['nmem'][j]);xN=int(xm['nmem'][j]);row={'denominator':d,'bucket':b,'year':y,'label':label,'candidate_index':j,'candidate_rank':j+1,'parent_member_count':pN,'extraction_member_count':xN,'parent_precision':float(pm['p'][i,j]),'parent_recall':float(pm['r'][i,j]),'parent_f1':float(pm['f'][i,j]),'extraction_precision':float(xm['p'][i,j]),'extraction_recall':float(xm['r'][i,j]),'extraction_f1':float(xm['f'][i,j]),'strict_refined':xN<pN};local.append(row);paired[comp].append(row)
            comparisons.append({'denominator':d,'bucket':b,'year':y,'comparator':comp,'capacity_k':k,'parent':pack(pa),'rematched_extraction_diagnostic':pack(xa),'paired_parent_recovered':local})
    gates={};aggregates={}
    for comp in ('sugar2017','hdbscan2025'):
      cr=[r for r in comparisons if r['comparator']==comp];pa=aggregate(cr,'parent');req(exact_parent(comp,pa),f'parent reproduction {comp}: {pa}');ps=paired_summary(paired[comp]);rg={'paired_count_at_least_20':ps['count']>=20,'nonempty_fraction_at_least_075':ps['nonempty_fraction']>=0.75,'mean_extraction_precision_at_least_080':ps['extraction_mean_precision']>=0.80,'mean_extraction_precision_strictly_higher_than_parent':ps['extraction_mean_precision']>ps['parent_mean_precision'],'mean_extraction_f1_retains_at_least_075_parent':ps['extraction_mean_f1']>=0.75*ps['parent_mean_f1'],'nonempty_precision_nonregression_fraction_at_least_050':ps['nonempty_precision_nonregression_fraction']>=0.50,'at_least_one_parent_recovered_assignment_strictly_refined':ps['strict_refined_assignment_count']>=1,'precision_nonlower_than_sacv_v1':ps['extraction_mean_precision']>=SACV_BASELINE[comp]['precision'],'f1_retains_at_least_095_sacv_v1':ps['extraction_mean_f1']>=0.95*SACV_BASELINE[comp]['f1']}
      for k,v in rg.items():gates[f'{comp}_{k}']=bool(v)
      aggregates[comp]={'parent':pa,'sacv_v1_baseline':SACV_BASELINE[comp],'rematched_extraction_diagnostic':aggregate(cr,'rematched_extraction_diagnostic'),'paired_same_discovery':ps,'gates':rg}
    gates['at_least_one_strict_successor_gain_over_sacv_v1']=any(aggregates[c]['paired_same_discovery']['extraction_mean_precision']>SACV_BASELINE[c]['precision'] or aggregates[c]['paired_same_discovery']['extraction_mean_f1']>SACV_BASELINE[c]['f1'] for c in ('sugar2017','hdbscan2025'))
    verdict='PASS_M2D_SACV_PAIR_V2_GMN_DEVELOPMENT' if all(gates.values()) else 'FAIL_M2D_SACV_PAIR_V2_GMN_DEVELOPMENT';out={'schema':'ORBITTRACE_M2D_SACV_PAIR_V2_GMN_RESULT','verdict':verdict,'fair_pretruth_sha256':FAIR_SHA,'pair_pretruth_sha256':sha(a.pair_pretruth),'aggregates':aggregates,'gates':gates,'primary_discovery_membership_changed':False,'primary_discovery_rank_changed':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'post_result_parameter_search':False};a.output.write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps({'verdict':verdict,'aggregates':aggregates,'gates':gates,'result_sha256':sha(a.output)},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
