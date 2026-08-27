#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

FEATURE_DIM=71
RECOVERY=0.5
VARIANT='local_geometry_margin_v19_rank_sum'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def order_sha(order:list[str])->str:
    return hashlib.sha256('\n'.join(map(str,order)).encode()).hexdigest()


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--sugar-root',type=Path,required=True); p.add_argument('--hdbscan-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker source changed')
    roots={'sugar':a.sugar_root,'hdbscan':a.hdbscan_root}

    # Immutable pretruth identity is checked before truth is interpreted by workflow and rechecked here.
    for route in v24.ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and meta['feature_dimension']==FEATURE_DIM and fp['truth_accessed'] is False,f'{route} invalid pretruth payload')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require(X.shape[1]==FEATURE_DIM and C.shape[1]==8,f'{route} array shape changed')
        require(v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],f'{route} array identity changed')

    truth={}; frozen_eval={}
    for route,year in v24.PANELS:
        truth[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    ranker=v22.load_module(a.ranker_source,'frozen_839_v31_geometry')
    route_data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; route_offsets={}; cursor=0
    for route in v24.ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
        ids=list(map(str,meta['family_ids'])); fams=fp['families']; require([str(f['family_id']) for f in fams]==ids,f'{route} family order changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        by={y:truth[(route,y)] for y in v24.YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014])
        base=[v22.family_truth(f,hidden,eligible) for f in fams]
        y13=[]; y14=[]; rg=[]
        for i,(f,t) in enumerate(zip(fams,base)):
            label=t['best_label']; rg.append(('SHOWER/'+str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None: q13=q14=0.0
            else: q13,q14=v24.annual_f1_for_fixed_label(f,str(label),by)
            y13.append(float(q13)); y14.append(float(q14))
        route_offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); y13s.append(np.asarray(y13,float)); y14s.append(np.asarray(y14,float)); groups.extend(rg)
        route_data[route]={'meta':meta,'fams':fams,'ids':ids,'centroids':C}

    Xall=np.vstack(Xs); y13all=np.concatenate(y13s); y14all=np.concatenate(y14s); groups=list(map(str,groups))
    require(Xall.shape==(cursor,FEATURE_DIM) and len(y13all)==len(y14all)==len(groups)==cursor,'stacked input mismatch')
    folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],dtype=int)
    margin13=np.zeros(cursor,dtype=float); margin14=np.zeros(cursor,dtype=float); fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; require(tr.any() and te.any(),f'empty fold {fold}')
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),f'group leakage fold {fold}')
        mu=np.mean(Xall[tr],axis=0); sd=np.std(Xall[tr],axis=0,ddof=0); scale=sd.copy(); scale[scale==0.0]=1.0
        Ztr=(Xall[tr]-mu[None,:])/scale[None,:]; Zte=(Xall[te]-mu[None,:])/scale[None,:]
        tr_idx=np.where(tr)[0]; te_idx=np.where(te)[0]
        annual_diag={}
        for year,yall,out in ((2013,y13all,margin13),(2014,y14all,margin14)):
            pos=yall[tr]>RECOVERY; neg=~pos; require(pos.any() and neg.any(),f'{year} fold {fold} lacks positive/nonpositive references')
            P=Ztr[pos]; N=Ztr[neg]
            # Exact k=1 ordinary Euclidean geometry from #1021.
            for j,global_i in enumerate(te_idx.tolist()):
                dpos=float(np.min(np.linalg.norm(P-Zte[j][None,:],axis=1))); dneg=float(np.min(np.linalg.norm(N-Zte[j][None,:],axis=1))); out[global_i]=dneg-dpos
            annual_diag[str(year)]={'positive_references':int(pos.sum()),'nonpositive_references':int(neg.sum())}
        fold_diag.append({'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'zero_variance_features':int(np.sum(sd==0.0)),'annual_references':annual_diag})

    combined=np.minimum(margin13,margin14); require(np.all(np.isfinite(combined)),'nonfinite combined local-geometry margin')
    variants={}; order_diag={}; control=[]
    for route in v24.ROUTES:
        lo,hi=route_offsets[route]; rd=route_data[route]; ids=rd['ids']; scores=combined[lo:hi]
        tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
        idx=ranker.diversity_order(scores,rd['centroids'],0.8,1.0,tie); local_order=[ids[i] for i in idx]
        v19_order=list(map(str,rd['meta']['v19_order'])); fused=list(v19.fusion_orders(local_order,v19_order)['rank_sum'])
        variants[route]=v22.rerank(rd['fams'],fused)
        order_diag[route]={'annual_margin_2013_sha256':v22.array_sha(margin13[lo:hi]),'annual_margin_2014_sha256':v22.array_sha(margin14[lo:hi]),'combined_margin_sha256':v22.array_sha(scores),'local_diversity_order_sha256':order_sha(local_order),'fused_order_sha256':order_sha(fused),'diversity':{'lambda':0.8,'scale':1.0},'fusion':'equal rank-sum with exact v19'}
        for year in v24.YEARS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget']); v19_ranked=v22.rerank(rd['fams'],v19_order); cur=v22.evaluate(v19_ranked,truth[(route,year)],budget); exp=v24.V19_METRICS[(route,year)]
            require(abs(float(cur['macro_f1'])-float(exp[0]))<1e-12 and int(cur['recovered_f1_gt_0_5'])==int(exp[1]),f'{route} {year} v19 control changed')
            control.append({'comparator':route,'year':year,**cur})

    panels=[]
    for route,year in v24.PANELS:
        budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget']); cur=v22.evaluate(variants[route],truth[(route,year)],budget); lit=frozen_eval[(route,year)]['comparator_summary']
        cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5'])
        panels.append({'comparator':route,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':cm/lm if lm else float('inf'),'recovery_ratio':cr/lr if lr else float('inf'),'superiority_pair_pass':bool(cm>lm and cr>=lr)})
    wins=sum(int(r['superiority_pair_pass']) for r in panels); passed=bool(wins==4)

    freeze={'verdict':'NOT_FROZEN_V31_LOCAL_GEOMETRY_OOF_FAIL','reference_sha256':None}
    if passed:
        mu=np.mean(Xall,axis=0); sd=np.std(Xall,axis=0,ddof=0); scale=sd.copy(); scale[scale==0.0]=1.0
        path=a.output/'v31_local_geometry_reference.npz'; np.savez_compressed(path,X=Xall,mean=mu,scale=scale,y13=(y13all>RECOVERY).astype(np.int8),y14=(y14all>RECOVERY).astype(np.int8),groups=np.asarray(groups,dtype=str))
        freeze={'verdict':'PASS_V31_FULL_EXPOSED_LOCAL_GEOMETRY_REFERENCE_FREEZE','reference_sha256':v22.sha(path),'training_examples':cursor,'training_groups':len(set(groups)),'feature_dimension':FEATURE_DIM,'k':1,'distance':'ordinary Euclidean after full-training z-score','annual_combiner':'min(margin_2013,margin_2014)','in_sample_reference_score_used_for_promotion':False}
    (a.output/'V31_LOCAL_GEOMETRY_MODEL_FREEZE.json').write_text(json.dumps(freeze,indent=2,sort_keys=True)+'\n')

    result={'scientific_stage':'EXPOSED_SONOTACO_V31_STRICT_OOF_LOCAL_GEOMETRY_MARGIN_V1','verdict':'PASS_V31_LOCAL_GEOMETRY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V31_LOCAL_GEOMETRY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','sole_scientific_change':'exact #1021 fold-local 1-nearest positive/nonpositive geometry margin replaces tree prediction','feature_dimension':FEATURE_DIM,'recovery_f1_threshold':RECOVERY,'nearest_k':1,'distance':'ordinary Euclidean across all 71 fold-training standardized dimensions','scaling':'fold-training mean and population std; zero std -> 1.0','annual_margin':'d_nonpositive-d_positive','annual_combiner':'min(margin_2013,margin_2014)','strict_whole_shower_oof':True,'candidate_membership_changed':False,'pretruth_feature_changed':False,'diversity':{'lambda':0.8,'scale':1.0},'fusion':'one equal rank-sum with exact v19','promotion_variant':VARIANT,'panel_wins':wins,'panels':panels,'v19_control':control,'fold_diagnostics':fold_diag,'order_diagnostics':order_diag,'full_model_freeze':freeze,'k_search':False,'metric_search':False,'scaling_search':False,'feature_search':False,'threshold_search':False,'annual_combiner_search':False,'diversity_search':False,'fusion_search':False,'source_quota_selected':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0]}
    (a.output/'V31_LOCAL_GEOMETRY_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'panels':panels,'full_model_freeze':freeze},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
