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
from sklearn.ensemble import ExtraTreesClassifier

from orbittrace_unified_recurrent_catalogue_lab_v1 import run_lab as v1
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

ROUTES=('sugar','hdbscan')
YEARS=(2013,2014)
PANELS=(('sugar',2013),('sugar',2014),('hdbscan',2013),('hdbscan',2014))
FEATURE_DIM=71
RANKER_SOURCE_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
VARIANTS=('representative_classifier_oof','representative_classifier_oof_v19_rank_sum')
PREFERENCE={'representative_classifier_oof':2,'representative_classifier_oof_v19_rank_sum':1}
V19={
    ('sugar',2013):(0.2813397742020527,17),('sugar',2014):(0.3328665843994243,18),
    ('hdbscan',2013):(0.1386807102765093,9),('hdbscan',2014):(0.11367457228624304,5),
}


def require(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)

def sha(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_module(path: Path,name: str)->Any:
    spec=importlib.util.spec_from_file_location(name,path)
    require(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def array_sha(x: np.ndarray)->str:
    a=np.ascontiguousarray(x)
    h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes(order='C')); return h.hexdigest()

def classifier()->ExtraTreesClassifier:
    return ExtraTreesClassifier(
        n_estimators=600,
        max_depth=4,
        min_samples_leaf=5,
        max_features=None,
        random_state=20260809,
        n_jobs=1,
        class_weight='balanced',
    )

def eligible_truth(by_year: dict[int,dict[str,str]])->dict[str,Counter[int]]:
    d: dict[str,Counter[int]]=defaultdict(Counter)
    for year in YEARS:
        for label in by_year[year].values():
            if label!='SPORADIC': d[str(label)][year]+=1
    return {label:c for label,c in d.items() if sum(c.values())>=8 and all(c.get(y,0)>=4 for y in YEARS)}

def family_truth(family: dict[str,Any],hidden: dict[str,str],eligible: dict[str,Counter[int]])->dict[str,Any]:
    ids=list(map(str,family['event_ids'])); counts=Counter(hidden.get(eid,'SPORADIC') for eid in ids); rows=[]
    for label,year_counts in eligible.items():
        overlap=int(counts.get(label,0))
        if overlap<=0: continue
        total=int(sum(year_counts.values())); precision=overlap/max(len(ids),1); recall=overlap/total
        f1=2.0*precision*recall/(precision+recall) if precision+recall else 0.0
        rows.append((f1,precision,overlap,str(label),recall))
    if not rows:
        return {'positive':False,'best_label':None,'overlap':0,'precision':0.0,'recall':0.0,'f1':0.0}
    f1,precision,overlap,label,recall=max(rows,key=lambda z:(z[0],z[1],z[2],z[3]))
    return {'positive':bool(precision>=0.5 and overlap>=4),'best_label':label,'overlap':overlap,'precision':float(precision),'recall':float(recall),'f1':float(f1)}

def representative_labels(ids: list[str],truths: list[dict[str,Any]])->tuple[np.ndarray,dict[str,str]]:
    by: dict[str,list[int]]=defaultdict(list)
    for i,t in enumerate(truths):
        if t['positive'] and t['best_label'] is not None:
            by[str(t['best_label'])].append(i)
    y=np.zeros(len(ids),dtype=np.int8); chosen={}
    for label,inds in sorted(by.items()):
        best=sorted(inds,key=lambda i:(-float(truths[i]['f1']),-float(truths[i]['precision']),-int(truths[i]['overlap']),ids[i]))[0]
        y[best]=1; chosen[label]=ids[best]
    return y,chosen

def positive_probability(model: ExtraTreesClassifier,X: np.ndarray)->np.ndarray:
    require(set(map(int,model.classes_.tolist()))=={0,1},f'classifier classes changed: {model.classes_}')
    j=int(np.where(model.classes_==1)[0][0]); p=np.asarray(model.predict_proba(X)[:,j],dtype=np.float64)
    require(p.shape==(len(X),) and np.all(np.isfinite(p)) and np.all((p>=0)&(p<=1)),'invalid representative probabilities')
    return p

def evaluate(families: list[dict[str,Any]],truth: dict[str,str],budget: int)->dict[str,Any]:
    counts=Counter(v for v in truth.values() if v!='SPORADIC'); labels=sorted(k for k,n in counts.items() if n>=4)
    truth_sets={l:{eid for eid,v in truth.items() if v==l} for l in labels}; truth_ids=set(truth); active=[]
    for family in families:
        members=set(map(str,family['event_ids'])) & truth_ids
        if members: active.append((int(family['rank']),str(family['family_id']),members))
    active=sorted(active,key=lambda z:(z[0],z[1]))[:int(budget)]; mat=np.zeros((len(labels),len(active)),dtype=np.float64)
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
    by={str(f['family_id']):f for f in families}; require(set(order)==set(by) and len(order)==len(by),'rerank universe mismatch')
    return [{'family_id':fid,'rank':i+1,'event_ids':list(map(str,by[fid]['event_ids'])),'source':by[fid].get('source')} for i,fid in enumerate(order)]


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--sugar-root',type=Path,required=True); p.add_argument('--hdbscan-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True); require(sha(a.ranker_source)==RANKER_SOURCE_SHA,'ranker source changed')
    roots={'sugar':a.sugar_root,'hdbscan':a.hdbscan_root}; truth_year={}; frozen={}
    for route,year in PANELS:
        truth_year[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    ranker=load_module(a.ranker_source,'frozen_839_v24')
    data={}; Xs=[]; ys=[]; groups=[]; offsets={}; cursor=0; target_diag={}
    for route in ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fam_payload=json.loads((root/'family_memberships.json').read_text())
        require(meta['feature_dimension']==FEATURE_DIM and meta['truth_accessed'] is False and fam_payload['truth_accessed'] is False,'invalid pretruth payload')
        ids=list(map(str,meta['family_ids'])); fams=fam_payload['families']; require([str(f['family_id']) for f in fams]==ids,'family alignment changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False); require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),'pretruth array shape changed')
        by_year={y:truth_year[(route,y)] for y in YEARS}; eligible=eligible_truth(by_year); hidden={**by_year[2013],**by_year[2014]}; truths=[family_truth(f,hidden,eligible) for f in fams]
        y,chosen=representative_labels(ids,truths)
        gs=[('SHOWER/'+str(t['best_label'])) if t['best_label'] is not None else ('NEG/'+route+'/'+ids[i]) for i,t in enumerate(truths)]
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); ys.append(y); groups.extend(gs)
        data[route]={'ids':ids,'fams':fams,'C':C,'tie':meta['tie_rank'],'v19':list(map(str,meta['v19_order']))}
        target_diag[route]={'families':len(ids),'eligible_showers':len(eligible),'candidate_positive_fragments':int(sum(t['positive'] for t in truths)),'representative_positive_labels':int(y.sum()),'representative_labels':len(chosen)}
        require(int(y.sum())==len(chosen)<=len(eligible),'representative label count invalid')

    Xall=np.vstack(Xs); yall=np.concatenate(ys); groups=list(map(str,groups)); require(Xall.shape==(cursor,FEATURE_DIM) and len(yall)==len(groups)==cursor,'stacked training shape mismatch')
    folds=np.asarray([v1.deterministic_fold(g) for g in groups],dtype=int); group_weights=ranker.grouped_weights(groups); oof=np.zeros(cursor,dtype=np.float64); fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; require(tr.any() and te.any(),f'empty fold {fold}'); require(set(np.unique(yall[tr]).tolist())=={0,1},f'training fold {fold} lacks a class')
        test_groups=set(groups[i] for i in np.where(te)[0]); train_groups=set(groups[i] for i in np.where(tr)[0]); require(test_groups.isdisjoint(train_groups),f'group leakage fold {fold}')
        m=classifier(); m.fit(Xall[tr],yall[tr],sample_weight=group_weights[tr]); oof[te]=positive_probability(m,Xall[te])
        n0=int(np.sum(yall[tr]==0)); n1=int(np.sum(yall[tr]==1)); fold_diag.append({'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'train_class_0':n0,'train_class_1':n1,'test_representatives':int(np.sum(yall[te]==1)),'test_groups':len(test_groups),'class_weight_formula':'balanced from this training fold only'})

    variants={}; control=[]
    for route in ROUTES:
        lo,hi=offsets[route]; rd=data[route]; ids=rd['ids']; scores=oof[lo:hi]; tie=[(int(rd['tie'][i]),ids[i]) for i in range(len(ids))]
        idx=ranker.diversity_order(scores,rd['C'],0.8,1.0,tie); qorder=[ids[i] for i in idx]; fused=list(v19.fusion_orders(qorder,rd['v19'])['rank_sum'])
        variants[route]={'representative_classifier_oof':rerank(rd['fams'],qorder),'representative_classifier_oof_v19_rank_sum':rerank(rd['fams'],fused),'v19_control':rerank(rd['fams'],rd['v19'])}
        for year in YEARS:
            budget=int(frozen[(route,year)]['candidate_budget']['comparator_budget']); cur=evaluate(variants[route]['v19_control'],truth_year[(route,year)],budget); exp=V19[(route,year)]
            require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'v19 control mismatch {route} {year}'); control.append({'comparator':route,'year':year,**cur})

    rows=[]
    for variant in VARIANTS:
        panels=[]
        for route,year in PANELS:
            budget=int(frozen[(route,year)]['candidate_budget']['comparator_budget']); cur=evaluate(variants[route][variant],truth_year[(route,year)],budget); lit=frozen[(route,year)]['comparator_summary']
            cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5']); mr=cm/lm; rr=cr/lr; win=bool(cm>lm and cr>=lr)
            panels.append({'comparator':route,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':mr,'recovery_ratio':rr,'superiority_pair_pass':win})
        wins=sum(int(x['superiority_pair_pass']) for x in panels); minm=min(x['macro_f1_ratio'] for x in panels); minr=min(x['recovery_ratio'] for x in panels); meanm=float(np.mean([x['macro_f1_ratio'] for x in panels])); meanr=float(np.mean([x['recovery_ratio'] for x in panels]))
        rows.append({'variant':variant,'panel_wins':wins,'all_panel_win':wins==4,'min_macro_f1_ratio':minm,'min_recovery_ratio':minr,'mean_macro_f1_ratio':meanm,'mean_recovery_ratio':meanr,'selection_key':[wins,minm,minr,meanm,meanr,PREFERENCE[variant]],'panels':panels})
    winner=max(rows,key=lambda r:tuple(r['selection_key'])); passed=bool(winner['all_panel_win']); model_freeze={'verdict':'NOT_FROZEN_V24_OOF_FAIL','model_sha256':None}
    if passed:
        full=classifier(); full.fit(Xall,yall,sample_weight=group_weights); path=a.output/'v24_sonotaco_representative_classifier.joblib'; joblib.dump(full,path)
        model_freeze={'verdict':'PASS_V24_FULL_SONOTACO_REPRESENTATIVE_CLASSIFIER_FREEZE','model_sha256':sha(path),'feature_dimension':FEATURE_DIM,'training_examples':len(yall),'positive_representatives':int(yall.sum()),'training_label_sha256':array_sha(yall),'training_feature_sha256':array_sha(Xall),'class_weight':'balanced','in_sample_full_fit_score_used_for_promotion':False}
    (a.output/'V24_FULL_MODEL_FREEZE.json').write_text(json.dumps(model_freeze,indent=2,sort_keys=True)+'\n')
    result={'scientific_stage':'V24_EXPOSED_SONOTACO_REPRESENTATIVE_CLASSIFIER_STRICT_GROUP_OOF','classifier':'ExtraTreesClassifier(n_estimators=600,max_depth=4,min_samples_leaf=5,max_features=None,class_weight=balanced,random_state=20260809,n_jobs=1)','representative_target_rule':'exact v23 one representative per eligible shower per route','same_shower_all_fragments_both_routes_same_fold':True,'target_diagnostics':target_diag,'folds':fold_diag,'v19_control_reproduction_pass':True,'v19_control':control,'all_results':rows,'winner':winner,'verdict':'PASS_V24_EXPOSED_REPRESENTATIVE_CLASSIFIER_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V24_REPRESENTATIVE_CLASSIFIER_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','full_model_freeze':model_freeze,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','probability_calibration':False,'probability_thresholding':False,'post_result_second_search':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False}
    (a.output/'V24_EXPOSED_REPRESENTATIVE_CLASSIFIER_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':result['verdict'],'winner':winner,'target_diagnostics':target_diag,'full_model_freeze':model_freeze},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
