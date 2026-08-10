#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

ROUTES=('sugar','hdbscan')
YEARS=(2013,2014)
PANELS=(('sugar',2013),('sugar',2014),('hdbscan',2013),('hdbscan',2014))
FEATURE_DIM=87
TOP_K=100
RANKER_SOURCE_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
V19_METRICS={
    ('sugar',2013):(0.2813397742020527,17),('sugar',2014):(0.3328665843994243,18),
    ('hdbscan',2013):(0.1386807102765093,9),('hdbscan',2014):(0.11367457228624304,5),
}


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)

def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()

def array_sha(x:np.ndarray)->str:
    a=np.ascontiguousarray(x); h=hashlib.sha256(); h.update(str(a.dtype).encode()); h.update(json.dumps(list(a.shape),separators=(',',':')).encode()); h.update(a.tobytes(order='C')); return h.hexdigest()

def order_sha(order:list[str])->str: return hashlib.sha256('\n'.join(order).encode()).hexdigest()


def family_for_truth(row:dict[str,Any])->dict[str,Any]:
    return {'family_id':str(row['family_id']),'rank':int(row['v19_rank']),'event_ids':list(map(str,row['final_event_ids']))}


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--v27-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(sha(a.ranker_source)==RANKER_SOURCE_SHA,'#839 ranker source changed')

    truth_year={}; frozen_eval={}
    for route,year in PANELS:
        truth_year[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    ranker=v22.load_module(a.ranker_source,'frozen_839_v28_train')
    route_data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; offsets={}; cursor=0; input_diag={}
    for route in ROUTES:
        postroot=a.v27_root/f'v27-{route}'
        baseroot=a.v27_root/f'base-{route}'
        m=json.loads((postroot/'V27_POSTMEMBERSHIP_FEATURE_MANIFEST.json').read_text())
        require(m['verdict']=='PASS_V27_POSTMEMBERSHIP_FEATURE_PRETRUTH_FREEZE','v27 feature freeze not passed')
        require((m['base_feature_dimension'],m['post_membership_feature_dimension'],m['combined_feature_dimension'])==(71,16,87),'v27 feature interface changed')
        require(m['successor_model_trained'] is False and m['literature_evaluation_performed'] is False,'v27 pretruth role changed')
        require(m['truth_accessed'] is False and m['target_information_access'] is False and m['maarsy_scientific_access'] is False and m['dms_scientific_access'] is False,'v27 firewall changed')
        ids=list(map(str,m['stage1_top100_family_ids'])); require(len(ids)==TOP_K and len(set(ids))==TOP_K,'v27 top100 identity invalid')
        X=np.load(postroot/'combined_features_top100.npy',allow_pickle=False); require(X.shape==(TOP_K,FEATURE_DIM),'v27 feature matrix shape changed'); require(array_sha(X)==m['combined_features_top100_sha256'],'v27 feature matrix hash changed')
        payload=json.loads((postroot/'expanded_top100_families.json').read_text()); require(payload['truth_accessed'] is False,'v27 expanded payload became truth-bearing')
        rows=payload['families']; require([str(r['family_id']) for r in rows]==ids,'v27 expanded top100 order/ID changed')

        base_meta=json.loads((baseroot/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); base_ids=list(map(str,base_meta['family_ids'])); require(set(ids).issubset(set(base_ids)),'v27 top100 absent from stage1 base')
        cent=np.load(baseroot/'centroids.npy',allow_pickle=False); require(cent.shape==(len(base_ids),8),'base centroid matrix shape changed'); require(array_sha(cent)==base_meta['centroid_sha256'],'base centroid hash changed')
        tie_all=list(map(int,base_meta['tie_rank'])); require(len(tie_all)==len(base_ids),'base tie vector changed'); base_index={fid:i for i,fid in enumerate(base_ids)}
        cent_top=np.asarray([cent[base_index[fid]] for fid in ids],dtype=np.float64); tie=[(tie_all[base_index[fid]],fid) for fid in ids]
        v19_top=list(map(str,base_meta['v19_order']))[:TOP_K]; require(v19_top==ids,'v27 stage1 top100 differs from exact v19')

        by_year={year:truth_year[(route,year)] for year in YEARS}; eligible=v22.eligible_from_year_truth(by_year); hidden=dict(by_year[2013]); hidden.update(by_year[2014])
        fams=[family_for_truth(r) for r in rows]; truths=[v22.family_truth(f,hidden,eligible) for f in fams]
        yy13=[]; yy14=[]; route_groups=[]
        for i,(f,t) in enumerate(zip(fams,truths)):
            lab=t['best_label']; route_groups.append(('SHOWER/'+str(lab)) if lab is not None else (f'NEG/{route}/'+ids[i]))
            if not t['positive'] or lab is None: yy13.append(0.0); yy14.append(0.0)
            else:
                f13,f14=v24.annual_f1_for_fixed_label(f,str(lab),by_year); yy13.append(float(f13)); yy14.append(float(f14))
        arr13=np.asarray(yy13,dtype=np.float64); arr14=np.asarray(yy14,dtype=np.float64)
        offsets[route]=(cursor,cursor+TOP_K); cursor+=TOP_K; Xs.append(X); y13s.append(arr13); y14s.append(arr14); groups.extend(route_groups)
        route_data[route]={'ids':ids,'fams':fams,'centroids':cent_top,'tie':tie,'v19_top':v19_top,'base_meta':base_meta}
        input_diag[route]={'families':TOP_K,'eligible_recurrent_showers':len(eligible),'positive_families':int(sum(t['positive'] for t in truths)),'nonzero_2013_targets':int(np.sum(arr13>0)),'nonzero_2014_targets':int(np.sum(arr14>0)),'combined_feature_sha256':m['combined_features_top100_sha256']}

    Xall=np.vstack(Xs); y13all=np.concatenate(y13s); y14all=np.concatenate(y14s); groups=list(map(str,groups))
    require(Xall.shape==(200,FEATURE_DIM) and len(y13all)==len(y14all)==len(groups)==200,'v28 stacked table changed')
    folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],dtype=int); weights=ranker.grouped_weights(groups); oof13=np.zeros(200); oof14=np.zeros(200); fold_diag=[]
    for fold in range(5):
        train=folds!=fold; test=folds==fold; require(train.any() and test.any(),f'empty fold {fold}')
        m13=ranker.model(); m14=ranker.model(); m13.fit(Xall[train],y13all[train],sample_weight=weights[train]); m14.fit(Xall[train],y14all[train],sample_weight=weights[train]); oof13[test]=m13.predict(Xall[test]); oof14[test]=m14.predict(Xall[test])
        tg={groups[i] for i in np.where(test)[0]}; rg={groups[i] for i in np.where(train)[0]}; require(tg.isdisjoint(rg),f'group leakage fold {fold}')
        fold_diag.append({'fold':fold,'train_examples':int(train.sum()),'test_examples':int(test.sum()),'train_groups':len(rg),'test_groups':len(tg)})

    v19_control=[]; candidate={}; order_diag={}
    for route in ROUTES:
        rd=route_data[route]; lo,hi=offsets[route]
        # Exact fixed-membership v19 top100 control.
        v19_ranked=[]
        for rank,f in enumerate(rd['fams'],start=1):
            g=dict(f); g['rank']=rank; v19_ranked.append(g)
        for year in YEARS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget']); cur=v22.evaluate(v19_ranked,truth_year[(route,year)],budget); exp=V19_METRICS[(route,year)]
            require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'v19 control mismatch {route} {year}'); v19_control.append({'comparator':route,'year':year,**cur})

        q=np.minimum(oof13[lo:hi],oof14[lo:hi]); idx=ranker.diversity_order(q,rd['centroids'],0.8,1.0,rd['tie']); quality=[rd['ids'][i] for i in idx]; final_top=list(v19.fusion_orders(quality,rd['v19_top'])['rank_sum'])
        by={str(f['family_id']):f for f in rd['fams']}; ranked=[]
        for rank,fid in enumerate(final_top,start=1):
            f=dict(by[fid]); f['rank']=rank; ranked.append(f)
        candidate[route]=ranked; order_diag[route]={'oof_2013_sha256':array_sha(oof13[lo:hi]),'oof_2014_sha256':array_sha(oof14[lo:hi]),'quality_score_sha256':array_sha(q),'postmembership_quality_order_sha256':order_sha(quality),'v19_top100_order_sha256':order_sha(rd['v19_top']),'v28_top100_order_sha256':order_sha(final_top),'stage2_family_set_exact_v19_top100':set(final_top)==set(rd['v19_top']),'diversity_lambda':0.8,'diversity_scale':1.0,'final_fusion':'equal rank_sum with exact v19 top100'}
        require(order_diag[route]['stage2_family_set_exact_v19_top100'],'v28 stage2 family set changed')

    panels=[]
    for route,year in PANELS:
        budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget']); cur=v22.evaluate(candidate[route],truth_year[(route,year)],budget); lit=frozen_eval[(route,year)]['comparator_summary']; cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5'])
        panels.append({'comparator':route,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':cm/lm if lm else float('inf'),'recovery_ratio':cr/lr if lr else float('inf'),'superiority_pair_pass':bool(cm>lm and cr>=lr)})
    wins=sum(int(x['superiority_pair_pass']) for x in panels); passed=wins==4
    full={'verdict':'NOT_FROZEN_V28_OOF_FAIL','model_2013_sha256':None,'model_2014_sha256':None}
    if passed:
        m13=ranker.model(); m14=ranker.model(); m13.fit(Xall,y13all,sample_weight=weights); m14.fit(Xall,y14all,sample_weight=weights); m13.set_params(n_jobs=1); m14.set_params(n_jobs=1); p13=a.output/'v28_sonotaco_postmembership_2013_head.joblib'; p14=a.output/'v28_sonotaco_postmembership_2014_head.joblib'; joblib.dump(m13,p13); joblib.dump(m14,p14)
        full={'verdict':'PASS_V28_FULL_SONOTACO_POSTMEMBERSHIP_TWOHEAD_MODEL_FREEZE','model_2013_sha256':sha(p13),'model_2014_sha256':sha(p14),'feature_dimension':FEATURE_DIM,'training_examples':200,'training_groups':len(set(groups)),'deployment_stage2_scope':'exact v19 top100 only','deployment_quality_combiner':'min(predicted_F1_2013,predicted_F1_2014)','deployment_diversity':{'lambda':0.8,'scale':1.0},'deployment_final_fusion':'equal rank_sum with exact v19 top100','in_sample_full_fit_score_used_for_promotion':False}
    (a.output/'V28_FULL_MODEL_FREEZE.json').write_text(json.dumps(full,indent=2,sort_keys=True)+'\n')
    result={'scientific_stage':'V28_EXPOSED_SONOTACO_POSTMEMBERSHIP_TWOHEAD_STRICT_GROUP_OOF_DEVELOPMENT','feature_dimension':FEATURE_DIM,'stage2_scope':'exact v19 top100 expanded families only','ranks_101_plus_changed':False,'input_diagnostics':input_diag,'folds':fold_diag,'v19_control_reproduction_pass':True,'v19_control':v19_control,'order_diagnostics':order_diag,'single_deployable_successor':'postmembership_twohead_v19_top100_rank_sum','panels':panels,'panel_wins':wins,'verdict':'PASS_V28_EXPOSED_POSTMEMBERSHIP_TWOHEAD_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V28_POSTMEMBERSHIP_TWOHEAD_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','full_model_freeze':full,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','full_fit_in_sample_score_used':False,'parameter_search':False,'post_result_second_search':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False}
    (a.output/'V28_EXPOSED_POSTMEMBERSHIP_TWOHEAD_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'panels':panels,'full_model_freeze':full},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
