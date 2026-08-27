#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from scipy.optimize import linear_sum_assignment

from orbittrace_unified_recurrent_catalogue_lab_v1 import run_lab as v1
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

ROUTES=('sugar','hdbscan')
YEARS=(2013,2014)
PANELS=(('sugar',2013),('sugar',2014),('hdbscan',2013),('hdbscan',2014))
FEATURE_DIM=71
RANKER_SOURCE_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
VARIANTS=('sonotaco_oof_quality','sonotaco_oof_v19_rank_sum')
PREFERENCE={'sonotaco_oof_quality':2,'sonotaco_oof_v19_rank_sum':1}
V19_METRICS={
    ('sugar',2013):(0.2813397742020527,17),('sugar',2014):(0.3328665843994243,18),
    ('hdbscan',2013):(0.1386807102765093,9),('hdbscan',2014):(0.11367457228624304,5),
}


def require(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)
def sha(path: Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def load_module(path: Path,name: str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); require(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def canonical_sha(obj: Any)->str: return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def array_sha(x: np.ndarray)->str:
    a=np.ascontiguousarray(x); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes(order='C')); return h.hexdigest()


def eligible_from_year_truth(by_year: dict[int,dict[str,str]])->dict[str,Counter[int]]:
    counts: dict[str,Counter[int]]=defaultdict(Counter)
    for year in YEARS:
        for label in by_year[year].values():
            if label!='SPORADIC': counts[str(label)][year]+=1
    return {label:c for label,c in counts.items() if sum(c.values())>=8 and all(c.get(y,0)>=4 for y in YEARS)}

def family_truth(family: dict[str,Any],hidden: dict[str,str],eligible: dict[str,Counter[int]])->dict[str,Any]:
    ids=list(map(str,family['event_ids'])); counts=Counter(hidden.get(eid,'SPORADIC') for eid in ids); rows=[]
    for label,per_year in eligible.items():
        ov=int(counts.get(label,0))
        if ov<=0: continue
        total=int(sum(per_year.values())); precision=ov/max(len(ids),1); recall=ov/total; f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
        rows.append((f1,precision,ov,label,recall))
    if not rows: return {'positive':False,'best_label':None,'overlap':0,'precision':0.0,'recall':0.0,'f1':0.0}
    f1,precision,ov,label,recall=max(rows,key=lambda r:(r[0],r[1],r[2],r[3]))
    return {'positive':bool(precision>=0.5 and ov>=4),'best_label':str(label),'overlap':ov,'precision':float(precision),'recall':float(recall),'f1':float(f1)}

def evaluate(families: list[dict[str,Any]],truth: dict[str,str],budget: int)->dict[str,Any]:
    counts=Counter(v for v in truth.values() if v!='SPORADIC'); labels=sorted(k for k,n in counts.items() if n>=4); truth_sets={l:{eid for eid,v in truth.items() if v==l} for l in labels}; truth_ids=set(truth)
    active=[]
    for family in families:
        members=set(map(str,family['event_ids'])) & truth_ids
        if members: active.append((int(family['rank']),str(family['family_id']),members))
    active=sorted(active,key=lambda x:(x[0],x[1]))[:int(budget)]; mat=np.zeros((len(labels),len(active)),dtype=np.float64)
    for i,label in enumerate(labels):
        actual=truth_sets[label]
        for j,(_r,_fid,pred) in enumerate(active):
            ov=len(actual&pred)
            if ov:
                p=ov/len(pred); r=ov/len(actual); mat[i,j]=2*p*r/(p+r)
    n=max(len(labels),len(active)); cost=np.zeros((n,n),dtype=np.float64); cost[:len(labels),:len(active)]=-mat
    ri,cj=linear_sum_assignment(cost); vals=[float(mat[i,j]) if j<len(active) else 0.0 for i,j in zip(ri.tolist(),cj.tolist()) if i<len(labels)]
    return {'eligible_showers':len(labels),'macro_f1':float(np.mean(vals)) if vals else 0.0,'recovered_f1_gt_0_5':int(sum(x>0.5 for x in vals)),'candidate_used':len(active)}
def rerank(families: list[dict[str,Any]],order: list[str])->list[dict[str,Any]]:
    by={str(f['family_id']):f for f in families}; require(set(order)==set(by) and len(order)==len(by),'rerank universe mismatch'); out=[]
    for rank,fid in enumerate(order,start=1):
        f=by[fid]; out.append({'family_id':fid,'rank':rank,'event_ids':list(map(str,f['event_ids'])),'source':f.get('source')})
    return out


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--sugar-root',type=Path,required=True); p.add_argument('--hdbscan-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True); require(sha(a.ranker_source)==RANKER_SOURCE_SHA,'#839 ranker source changed')
    roots={'sugar':a.sugar_root,'hdbscan':a.hdbscan_root}; truth_year={}; frozen_eval={}
    for route,year in PANELS:
        truth_year[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text()); frozen_eval[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    ranker=load_module(a.ranker_source,'frozen_839_v22_train'); route_data={}; Xs=[]; targets=[]; groups=[]; route_offsets={}; cursor=0; target_diag={}
    for route in ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fam_payload=json.loads((root/'family_memberships.json').read_text())
        require(meta['feature_dimension']==FEATURE_DIM and meta['truth_accessed'] is False,'invalid v22 pretruth manifest'); require(fam_payload['truth_accessed'] is False,'membership payload already truth-bearing')
        ids=list(map(str,meta['family_ids'])); fams=fam_payload['families']; require([str(f['family_id']) for f in fams]==ids,'family alignment changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False); require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),'pretruth array shape changed'); require(array_sha(X)==meta['feature_sha256'] and array_sha(C)==meta['centroid_sha256'],'pretruth array hash changed')
        by_year={y:truth_year[(route,y)] for y in YEARS}; eligible=eligible_from_year_truth(by_year); hidden={}; hidden.update(by_year[2013]); hidden.update(by_year[2014]); require(len(hidden)==len(by_year[2013])+len(by_year[2014]),f'{route} duplicate IDs across years')
        truths=[family_truth(f,hidden,eligible) for f in fams]
        y=np.asarray([t['f1'] if t['positive'] else 0.0 for t in truths],dtype=np.float64)
        gs=[('SHOWER/'+str(t['best_label'])) if t['best_label'] is not None else (f'NEG/{route}/'+ids[i]) for i,t in enumerate(truths)]
        route_offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); targets.append(y); groups.extend(gs)
        route_data[route]={'meta':meta,'families':fams,'ids':ids,'centroids':C,'truths':truths,'eligible':eligible}
        target_diag[route]={'families':len(ids),'eligible_recurrent_showers':len(eligible),'positive_families':int(sum(t['positive'] for t in truths)),'nonzero_targets':int(np.sum(y>0)),'target_mean':float(np.mean(y))}

    Xall=np.vstack(Xs); yall=np.concatenate(targets); groups=list(map(str,groups)); require(Xall.shape==(cursor,FEATURE_DIM) and len(yall)==len(groups)==cursor,'stacked training shape mismatch')
    folds=np.asarray([v1.deterministic_fold(g) for g in groups],dtype=int); weights=ranker.grouped_weights(groups); oof=np.zeros(cursor,dtype=np.float64); fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; require(tr.any() and te.any(),f'empty grouped fold {fold}')
        m=ranker.model(); m.fit(Xall[tr],yall[tr],sample_weight=weights[tr]); oof[te]=m.predict(Xall[te])
        test_groups=set(groups[i] for i in np.where(te)[0]); train_groups=set(groups[i] for i in np.where(tr)[0]); require(test_groups.isdisjoint(train_groups),f'group leakage in fold {fold}')
        fold_diag.append({'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'train_groups':len(train_groups),'test_groups':len(test_groups),'test_positive_targets':int(np.sum(yall[te]>0))})

    variants={}; control_panels=[]
    for route in ROUTES:
        lo,hi=route_offsets[route]; rd=route_data[route]; ids=rd['ids']; scores=oof[lo:hi]; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
        idx=ranker.diversity_order(scores,rd['centroids'],0.8,1.0,tie); qorder=[ids[i] for i in idx]; v19order=list(map(str,rd['meta']['v19_order'])); fused=list(v19.fusion_orders(qorder,v19order)['rank_sum'])
        variants[route]={'sonotaco_oof_quality':rerank(rd['families'],qorder),'sonotaco_oof_v19_rank_sum':rerank(rd['families'],fused),'v19_control':rerank(rd['families'],v19order)}
        for year in YEARS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget']); cur=evaluate(variants[route]['v19_control'],truth_year[(route,year)],budget); exp=V19_METRICS[(route,year)]
            require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'v19 fixed-membership control mismatch {route} {year}')
            control_panels.append({'comparator':route,'year':year,**cur})

    rows=[]
    for variant in VARIANTS:
        panels=[]
        for route,year in PANELS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget']); cur=evaluate(variants[route][variant],truth_year[(route,year)],budget); lit=frozen_eval[(route,year)]['comparator_summary']
            cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5']); mr=cm/lm if lm else float('inf'); rr=cr/lr if lr else float('inf'); win=bool(cm>lm and cr>=lr)
            panels.append({'comparator':route,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':mr,'recovery_ratio':rr,'superiority_pair_pass':win})
        wins=sum(int(x['superiority_pair_pass']) for x in panels); minm=min(x['macro_f1_ratio'] for x in panels); minr=min(x['recovery_ratio'] for x in panels); meanm=float(np.mean([x['macro_f1_ratio'] for x in panels])); meanr=float(np.mean([x['recovery_ratio'] for x in panels]))
        rows.append({'variant':variant,'panel_wins':wins,'all_panel_win':wins==4,'min_macro_f1_ratio':minm,'min_recovery_ratio':minr,'mean_macro_f1_ratio':meanm,'mean_recovery_ratio':meanr,'selection_key':[wins,minm,minr,meanm,meanr,PREFERENCE[variant]],'panels':panels})
    winner=max(rows,key=lambda r:tuple(r['selection_key'])); passed=bool(winner['all_panel_win'])

    full_freeze={'verdict':'NOT_FROZEN_V22_OOF_FAIL','model_sha256':None}
    if passed:
        full=ranker.model(); full.fit(Xall,yall,sample_weight=weights); full.set_params(n_jobs=1); model_path=a.output/'v22_sonotaco_full_ranker.joblib'; joblib.dump(full,model_path)
        full_freeze={'verdict':'PASS_V22_FULL_SONOTACO_MODEL_FREEZE','model_sha256':sha(model_path),'feature_dimension':FEATURE_DIM,'training_examples':len(yall),'training_groups':len(set(groups)),'training_target_sha256':array_sha(yall),'training_feature_sha256':array_sha(Xall),'in_sample_full_fit_score_used_for_promotion':False}
    (a.output/'V22_FULL_MODEL_FREEZE.json').write_text(json.dumps(full_freeze,indent=2,sort_keys=True)+'\n')

    result={'scientific_stage':'V22_EXPOSED_SONOTACO_STRICT_GROUP_OOF_RANKING_DEVELOPMENT','feature_dimension':FEATURE_DIM,'target_definition':'exact #839 recurrent combined-two-year F1 target on fixed v19-expanded memberships','same_shower_all_fragments_both_routes_same_fold':True,'folds':fold_diag,'target_diagnostics':target_diag,'v19_control_reproduction_pass':True,'v19_control':control_panels,'all_results':rows,'winner':winner,'verdict':'PASS_V22_EXPOSED_STRICT_GROUP_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V22_STRICT_GROUP_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','full_model_freeze':full_freeze,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','full_fit_in_sample_score_used':False,'post_result_second_search':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False}
    (a.output/'V22_EXPOSED_STRICT_GROUP_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':result['verdict'],'winner':winner,'full_model_freeze':full_freeze,'target_diagnostics':target_diag},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
