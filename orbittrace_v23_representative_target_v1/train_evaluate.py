#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, importlib.util, json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import joblib
import numpy as np
from scipy.optimize import linear_sum_assignment

from orbittrace_unified_recurrent_catalogue_lab_v1 import run_lab as v1
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

ROUTES=('sugar','hdbscan'); YEARS=(2013,2014)
PANELS=(('sugar',2013),('sugar',2014),('hdbscan',2013),('hdbscan',2014))
FEATURE_DIM=71
RANKER_SOURCE_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
VARIANTS=('representative_oof_quality','representative_oof_v19_rank_sum')
PREFERENCE={'representative_oof_quality':2,'representative_oof_v19_rank_sum':1}
V19={('sugar',2013):(0.2813397742020527,17),('sugar',2014):(0.3328665843994243,18),('hdbscan',2013):(0.1386807102765093,9),('hdbscan',2014):(0.11367457228624304,5)}

def require(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); require(spec is not None and spec.loader is not None,f'cannot import {path}'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def arr_sha(x:np.ndarray)->str:
    a=np.ascontiguousarray(x); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes()); return h.hexdigest()

def eligible_truth(by_year:dict[int,dict[str,str]])->dict[str,Counter[int]]:
    d:dict[str,Counter[int]]=defaultdict(Counter)
    for y in YEARS:
        for lab in by_year[y].values():
            if lab!='SPORADIC': d[str(lab)][y]+=1
    return {lab:c for lab,c in d.items() if sum(c.values())>=8 and all(c.get(y,0)>=4 for y in YEARS)}
def family_truth(f:dict[str,Any],hidden:dict[str,str],eligible:dict[str,Counter[int]])->dict[str,Any]:
    ids=list(map(str,f['event_ids'])); cnt=Counter(hidden.get(e,'SPORADIC') for e in ids); rows=[]
    for lab,cy in eligible.items():
        ov=int(cnt.get(lab,0))
        if not ov: continue
        total=int(sum(cy.values())); p=ov/max(len(ids),1); r=ov/total; f1=2*p*r/(p+r) if p+r else 0.0; rows.append((f1,p,ov,str(lab),r))
    if not rows: return {'positive':False,'best_label':None,'overlap':0,'precision':0.0,'recall':0.0,'f1':0.0}
    f1,p,ov,lab,r=max(rows,key=lambda z:(z[0],z[1],z[2],z[3])); return {'positive':bool(p>=0.5 and ov>=4),'best_label':lab,'overlap':ov,'precision':float(p),'recall':float(r),'f1':float(f1)}
def representative_targets(ids:list[str],truths:list[dict[str,Any]])->tuple[np.ndarray,dict[str,str]]:
    by:dict[str,list[int]]=defaultdict(list)
    for i,t in enumerate(truths):
        if t['positive'] and t['best_label'] is not None: by[str(t['best_label'])].append(i)
    chosen:dict[str,str]={}; y=np.zeros(len(ids),dtype=np.float64)
    for lab,inds in sorted(by.items()):
        # Highest F1, precision, overlap; stable lexical family ID is final deterministic tie break.
        best=sorted(inds,key=lambda i:(-float(truths[i]['f1']),-float(truths[i]['precision']),-int(truths[i]['overlap']),ids[i]))[0]
        y[best]=float(truths[best]['f1']); chosen[lab]=ids[best]
    return y,chosen
def evaluate(families:list[dict[str,Any]],truth:dict[str,str],budget:int)->dict[str,Any]:
    cnt=Counter(v for v in truth.values() if v!='SPORADIC'); labels=sorted(k for k,n in cnt.items() if n>=4); ts={l:{e for e,v in truth.items() if v==l} for l in labels}; tids=set(truth); active=[]
    for f in families:
        s=set(map(str,f['event_ids']))&tids
        if s: active.append((int(f['rank']),str(f['family_id']),s))
    active=sorted(active,key=lambda z:(z[0],z[1]))[:budget]; mat=np.zeros((len(labels),len(active)))
    for i,l in enumerate(labels):
        a=ts[l]
        for j,(_r,_id,pred) in enumerate(active):
            ov=len(a&pred)
            if ov:
                pr=ov/len(pred); rc=ov/len(a); mat[i,j]=2*pr*rc/(pr+rc)
    n=max(len(labels),len(active)); cost=np.zeros((n,n)); cost[:len(labels),:len(active)]=-mat; ri,cj=linear_sum_assignment(cost); vals=[float(mat[i,j]) if j<len(active) else 0.0 for i,j in zip(ri.tolist(),cj.tolist()) if i<len(labels)]
    return {'macro_f1':float(np.mean(vals)) if vals else 0.0,'recovered_f1_gt_0_5':int(sum(x>0.5 for x in vals)),'candidate_used':len(active),'eligible_showers':len(labels)}
def rerank(fams:list[dict[str,Any]],order:list[str])->list[dict[str,Any]]:
    by={str(f['family_id']):f for f in fams}; require(set(order)==set(by) and len(order)==len(by),'rerank universe mismatch'); return [{'family_id':fid,'rank':i+1,'event_ids':list(map(str,by[fid]['event_ids'])),'source':by[fid].get('source')} for i,fid in enumerate(order)]

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--sugar-root',type=Path,required=True); p.add_argument('--hdbscan-root',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True); require(sha(a.ranker_source)==RANKER_SOURCE_SHA,'ranker changed')
    roots={'sugar':a.sugar_root,'hdbscan':a.hdbscan_root}; truths_year={}; frozen={}
    for route,year in PANELS:
        truths_year[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text()); frozen[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())
    ranker=load_module(a.ranker_source,'frozen_839_v23'); data={}; Xs=[]; ys=[]; groups=[]; offsets={}; cursor=0; diag={}
    for route in ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text()); ids=list(map(str,meta['family_ids'])); fams=fp['families']; require(fp['truth_accessed'] is False and meta['truth_accessed'] is False,'pretruth payload invalid')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False); require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),'shape changed')
        byy={y:truths_year[(route,y)] for y in YEARS}; eligible=eligible_truth(byy); hidden={**byy[2013],**byy[2014]}; tr=[family_truth(f,hidden,eligible) for f in fams]; y,chosen=representative_targets(ids,tr)
        gs=[('SHOWER/'+str(t['best_label'])) if t['best_label'] is not None else ('NEG/'+route+'/'+ids[i]) for i,t in enumerate(tr)]
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); ys.append(y); groups.extend(gs); data[route]={'ids':ids,'fams':fams,'C':C,'tie':meta['tie_rank'],'v19':list(map(str,meta['v19_order']))}
        diag[route]={'families':len(ids),'eligible_showers':len(eligible),'candidate_positive_fragments':sum(int(t['positive']) for t in tr),'representative_positive_targets':int(np.sum(y>0)),'representative_labels':len(chosen),'representative_target_mean':float(np.mean(y))}
        require(int(np.sum(y>0))==len(chosen)<=len(eligible),'representative count invalid')
    Xall=np.vstack(Xs); yall=np.concatenate(ys); folds=np.asarray([v1.deterministic_fold(str(g)) for g in groups],int); weights=ranker.grouped_weights(list(map(str,groups))); oof=np.zeros(cursor); fold_diag=[]
    for fold in range(5):
        trm=folds!=fold; tem=folds==fold; tg=set(groups[i] for i in np.where(tem)[0]); rg=set(groups[i] for i in np.where(trm)[0]); require(tg.isdisjoint(rg),f'group leakage fold {fold}'); m=ranker.model(); m.fit(Xall[trm],yall[trm],sample_weight=weights[trm]); oof[tem]=m.predict(Xall[tem]); fold_diag.append({'fold':fold,'train_examples':int(trm.sum()),'test_examples':int(tem.sum()),'test_groups':len(tg),'test_representative_targets':int(np.sum(yall[tem]>0))})
    variants={}; control=[]
    for route in ROUTES:
        lo,hi=offsets[route]; rd=data[route]; ids=rd['ids']; tie=[(int(rd['tie'][i]),ids[i]) for i in range(len(ids))]; idx=ranker.diversity_order(oof[lo:hi],rd['C'],0.8,1.0,tie); q=[ids[i] for i in idx]; fused=list(v19.fusion_orders(q,rd['v19'])['rank_sum']); variants[route]={'representative_oof_quality':rerank(rd['fams'],q),'representative_oof_v19_rank_sum':rerank(rd['fams'],fused),'v19_control':rerank(rd['fams'],rd['v19'])}
        for year in YEARS:
            b=int(frozen[(route,year)]['candidate_budget']['comparator_budget']); cur=evaluate(variants[route]['v19_control'],truths_year[(route,year)],b); exp=V19[(route,year)]; require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'v19 control mismatch {route} {year}'); control.append({'comparator':route,'year':year,**cur})
    rows=[]
    for variant in VARIANTS:
        panels=[]
        for route,year in PANELS:
            b=int(frozen[(route,year)]['candidate_budget']['comparator_budget']); cur=evaluate(variants[route][variant],truths_year[(route,year)],b); lit=frozen[(route,year)]['comparator_summary']; cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5']); panels.append({'comparator':route,'year':year,'budget':b,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':cm/lm,'recovery_ratio':cr/lr,'superiority_pair_pass':bool(cm>lm and cr>=lr)})
        wins=sum(int(x['superiority_pair_pass']) for x in panels); minm=min(x['macro_f1_ratio'] for x in panels); minr=min(x['recovery_ratio'] for x in panels); meanm=float(np.mean([x['macro_f1_ratio'] for x in panels])); meanr=float(np.mean([x['recovery_ratio'] for x in panels])); rows.append({'variant':variant,'panel_wins':wins,'all_panel_win':wins==4,'min_macro_f1_ratio':minm,'min_recovery_ratio':minr,'mean_macro_f1_ratio':meanm,'mean_recovery_ratio':meanr,'selection_key':[wins,minm,minr,meanm,meanr,PREFERENCE[variant]],'panels':panels})
    winner=max(rows,key=lambda r:tuple(r['selection_key'])); passed=bool(winner['all_panel_win']); freeze={'verdict':'NOT_FROZEN_V23_OOF_FAIL','model_sha256':None}
    if passed:
        full=ranker.model(); full.fit(Xall,yall,sample_weight=weights); full.set_params(n_jobs=1); path=a.output/'v23_sonotaco_representative_ranker.joblib'; joblib.dump(full,path); freeze={'verdict':'PASS_V23_FULL_SONOTACO_REPRESENTATIVE_MODEL_FREEZE','model_sha256':sha(path),'feature_dimension':FEATURE_DIM,'training_examples':len(yall),'representative_targets':int(np.sum(yall>0)),'training_target_sha256':arr_sha(yall),'training_feature_sha256':arr_sha(Xall),'in_sample_full_fit_score_used_for_promotion':False}
    (a.output/'V23_FULL_MODEL_FREEZE.json').write_text(json.dumps(freeze,indent=2,sort_keys=True)+'\n')
    result={'scientific_stage':'V23_EXPOSED_SONOTACO_REPRESENTATIVE_TARGET_STRICT_GROUP_OOF','target_rule':'one deterministic best fixed-membership representative per eligible shower per route','same_shower_all_fragments_both_routes_same_fold':True,'target_diagnostics':diag,'folds':fold_diag,'v19_control_reproduction_pass':True,'v19_control':control,'all_results':rows,'winner':winner,'verdict':'PASS_V23_EXPOSED_REPRESENTATIVE_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V23_REPRESENTATIVE_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','full_model_freeze':freeze,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','post_result_second_search':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False}
    (a.output/'V23_EXPOSED_REPRESENTATIVE_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':result['verdict'],'winner':winner,'target_diagnostics':diag,'full_model_freeze':freeze},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
