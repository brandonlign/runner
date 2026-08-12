#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

FEATURE_DIM=71
RECOVERY=0.5
ROUTES=('sugar','hdbscan')
YEARS=(2013,2014)
PANELS=(('sugar',2013),('sugar',2014),('hdbscan',2013),('hdbscan',2014))
V31_CONTROL={
 ('sugar',2013):(0.2719801488280529,16),('sugar',2014):(0.31529041952487225,17),
 ('hdbscan',2013):(0.14888037368183737,9),('hdbscan',2014):(0.15198123772301594,9),
}


def req(x:bool,msg:str)->None:
    if not x: raise RuntimeError(msg)
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f'cannot import {path}')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def order_sha(order:list[str])->str: return hashlib.sha256('\n'.join(order).encode()).hexdigest()


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--sugar-root',type=Path,required=True); p.add_argument('--hdbscan-root',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--v31-source',type=Path,required=True); p.add_argument('--predictive-source',type=Path,required=True); p.add_argument('--pretruth-predictive-json',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    pre=json.loads(a.pretruth_predictive_json.read_text()); req(pre['verdict']=='PASS_V61_PRETRUTH_PREDICTIVE_ORDER_FREEZE' and pre['truth_accessed'] is False and pre['sonotaco_truth_access'] is False,'invalid v61 pretruth authorization')
    v31=load_module(a.v31_source,'v61_exact_v31_parent'); pred=load_module(a.predictive_source,'v61_exact_predictive_fusion')
    v22=v31.v22; v24=v31.v24; v19=v31.v19
    req(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker source changed')
    roots={'sugar':a.sugar_root,'hdbscan':a.hdbscan_root}

    # Immutable payload checks still occur before exposed truth is interpreted.
    for route in ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
        req(meta['truth_accessed'] is False and meta['feature_dimension']==FEATURE_DIM and fp['truth_accessed'] is False,f'{route} invalid pretruth payload')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        req(X.shape[1]==FEATURE_DIM and C.shape[1]==8,f'{route} array shape changed'); req(v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],f'{route} array identity changed')
        ids=list(map(str,meta['family_ids'])); po=list(map(str,pre['routes'][route]['predictive_order'])); req(len(po)==len(ids) and set(po)==set(ids),'predictive order universe mismatch')
        req(order_sha(po)==pre['routes'][route]['predictive_order_sha256'],'predictive order hash mismatch')

    # Exposed SonotaCo truth is first read here, after the complete predictive orders are frozen.
    truth={}; frozen_eval={}
    for route,year in PANELS:
        truth[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text()); frozen_eval[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    ranker=v22.load_module(a.ranker_source,'frozen_839_v61_parent_geometry'); route_data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; route_offsets={}; cursor=0
    for route in ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text()); ids=list(map(str,meta['family_ids'])); fams=fp['families']; req([str(f['family_id']) for f in fams]==ids,f'{route} family order changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False); by={y:truth[(route,y)] for y in YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014]); base=[v22.family_truth(f,hidden,eligible) for f in fams]
        y13=[]; y14=[]; rg=[]
        for i,(f,t) in enumerate(zip(fams,base)):
            label=t['best_label']; rg.append(('SHOWER/'+str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None: q13=q14=0.0
            else: q13,q14=v24.annual_f1_for_fixed_label(f,str(label),by)
            y13.append(float(q13)); y14.append(float(q14))
        route_offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); y13s.append(np.asarray(y13,float)); y14s.append(np.asarray(y14,float)); groups.extend(rg); route_data[route]={'meta':meta,'fams':fams,'ids':ids,'centroids':C}

    Xall=np.vstack(Xs); y13all=np.concatenate(y13s); y14all=np.concatenate(y14s); groups=list(map(str,groups)); req(Xall.shape==(cursor,FEATURE_DIM) and len(groups)==cursor,'stacked parent input mismatch')
    folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],dtype=int); margin13=np.zeros(cursor,float); margin14=np.zeros(cursor,float)
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; req(tr.any() and te.any(),f'empty fold {fold}'); req({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),f'group leakage fold {fold}')
        mu=np.mean(Xall[tr],axis=0); sd=np.std(Xall[tr],axis=0,ddof=0); scale=sd.copy(); scale[scale==0.0]=1.0; Ztr=(Xall[tr]-mu[None,:])/scale[None,:]; Zte=(Xall[te]-mu[None,:])/scale[None,:]; te_idx=np.where(te)[0]
        for yall,out,year in ((y13all,margin13,2013),(y14all,margin14,2014)):
            pos=yall[tr]>RECOVERY; neg=~pos; req(pos.any() and neg.any(),f'{year} fold {fold} lacks references'); P=Ztr[pos]; N=Ztr[neg]
            for j,gi in enumerate(te_idx.tolist()): out[gi]=float(np.min(np.linalg.norm(N-Zte[j][None,:],axis=1))-np.min(np.linalg.norm(P-Zte[j][None,:],axis=1)))
    combined=np.minimum(margin13,margin14); req(np.isfinite(combined).all(),'nonfinite parent margin')

    v31_orders={}; v61_orders={}; parent_controls=[]
    for route in ROUTES:
        lo,hi=route_offsets[route]; rd=route_data[route]; ids=rd['ids']; scores=combined[lo:hi]; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]; idx=ranker.diversity_order(scores,rd['centroids'],0.8,1.0,tie); local=[ids[i] for i in idx]; v19_order=list(map(str,rd['meta']['v19_order'])); parent=list(v19.fusion_orders(local,v19_order)['rank_sum']); v31_orders[route]=parent
        predictive=list(map(str,pre['routes'][route]['predictive_order'])); v61_orders[route]=pred.equal_rank_fusion(parent,predictive)
        for year in YEARS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget']); cur=v22.evaluate(v22.rerank(rd['fams'],parent),truth[(route,year)],budget); exp=V31_CONTROL[(route,year)]; req(abs(float(cur['macro_f1'])-exp[0])<1e-12 and int(cur['recovered_f1_gt_0_5'])==exp[1],f'{route} {year} exact v31 control changed'); parent_controls.append({'comparator':route,'year':year,**cur})

    panels=[]
    for route,year in PANELS:
        rd=route_data[route]; budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget']); cur=v22.evaluate(v22.rerank(rd['fams'],v61_orders[route]),truth[(route,year)],budget); lit=frozen_eval[(route,year)]['comparator_summary']; cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5']); panels.append({'comparator':route,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'superiority_pair_pass':bool(cm>lm and cr>=lr),'macro_f1_ratio':cm/lm if lm else float('inf'),'recovery_ratio':cr/lr if lr else float('inf')})
    wins=sum(int(x['superiority_pair_pass']) for x in panels); passed=wins==4; verdict='PASS_V61_GMN_AUTHORIZED_PREDICTIVE_CONSISTENCY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V61_GMN_AUTHORIZED_PREDICTIVE_CONSISTENCY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT'
    result={'scientific_stage':'EXPOSED_SONOTACO_V61_GMN_AUTHORIZED_PREDICTIVE_CONSISTENCY_V1','verdict':verdict,'panel_wins':wins,'panels':panels,'v31_control':parent_controls,'orders':{r:{'v31_order_sha256':order_sha(v31_orders[r]),'predictive_order_sha256':pre['routes'][r]['predictive_order_sha256'],'v61_order_sha256':order_sha(v61_orders[r])} for r in ROUTES},'sole_scientific_change':'equal rank-sum exact v31 parent order with externally GMN-authorized candidate-internal predictive order','fusion':'equal 1-based rank sum; tie v31 rank then family_id','parameter_search':False,'predictive_feature_search':False,'fusion_search':False,'candidate_membership_changed':False,'candidate_generation_recomputed':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0]}
    out=a.output/'V61_GMN_AUTHORIZED_PREDICTIVE_CONSISTENCY_RESULT.json'; out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':verdict,'panel_wins':wins,'panels':panels},indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
