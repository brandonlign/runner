#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.base import clone

from orbittrace_v23_worst_year_oof_ranker_v1 import train_evaluate as v23

ROUTES=v23.ROUTES
YEARS=v23.YEARS
PANELS=v23.PANELS
FEATURE_DIM=v23.FEATURE_DIM
RANKER_SOURCE_SHA=v23.RANKER_SOURCE_SHA
V19_METRICS=v23.V19_METRICS
EXPECTED_EXACT_FILE_SHA=v23.EXPECTED_EXACT_FILE_SHA
EXPECTED_ROUNDED12_FEATURE_SHA=v23.EXPECTED_ROUNDED12_FEATURE_SHA
EXPECTED_V19_FAMILY_SHA=v23.EXPECTED_V19_FAMILY_SHA

VARIANTS=('nested_capacity_oof_quality','nested_capacity_oof_v19_rank_sum')
PREFERENCE={'nested_capacity_oof_quality':2,'nested_capacity_oof_v19_rank_sum':1}

CAPACITIES=(
    ('baseline_d4_l5', {'max_depth':4,'min_samples_leaf':5}),
    ('medium_d8_l3', {'max_depth':8,'min_samples_leaf':3}),
    ('high_unbounded_l2', {'max_depth':None,'min_samples_leaf':2}),
)
CAPACITY_TIE_PREFERENCE={'baseline_d4_l5':3,'medium_d8_l3':2,'high_unbounded_l2':1}

V24_FUSED_METRICS={
    ('sugar',2013):(0.27806630131631344,16),
    ('sugar',2014):(0.32869544907104964,17),
    ('hdbscan',2013):(0.14257102406283795,10),
    ('hdbscan',2014):(0.12833942693327394,7),
}

def require(ok: bool,msg: str)->None:
    if not ok:
        raise RuntimeError(msg)

def capacity_model(ranker: Any, name: str):
    params=dict(CAPACITIES)[name]
    model=clone(ranker.model())
    model.set_params(**params)
    return model

def stable_group_ndcg(pred: np.ndarray, y13: np.ndarray, y14: np.ndarray, groups: list[str], mask: np.ndarray)->float:
    idx=np.where(mask)[0]
    require(len(idx)>0,'empty NDCG mask')
    per: dict[str,list[int]]=defaultdict(list)
    for i in idx.tolist():
        per[str(groups[i])].append(int(i))
    group_ids=sorted(per)
    rel=[]; score=[]
    for g in group_ids:
        ii=np.asarray(per[g],dtype=int)
        rel.append(float(np.max(np.minimum(y13[ii],y14[ii]))))
        score.append(float(np.max(pred[ii])))
    rel=np.asarray(rel,dtype=np.float64); score=np.asarray(score,dtype=np.float64)
    require(np.all(np.isfinite(rel)) and np.all(np.isfinite(score)),'nonfinite NDCG inputs')
    require(np.all((rel>=0.0)&(rel<=1.0)),'invalid NDCG relevance')
    gain=np.exp2(rel)-1.0
    def dcg(order: list[int])->float:
        return float(sum(gain[i]/np.log2(rank+2.0) for rank,i in enumerate(order)))
    pred_order=sorted(range(len(group_ids)),key=lambda i:(-score[i],group_ids[i]))
    ideal_order=sorted(range(len(group_ids)),key=lambda i:(-rel[i],group_ids[i]))
    ideal=dcg(ideal_order)
    require(ideal>0.0,'zero ideal NDCG in nested selection')
    return dcg(pred_order)/ideal

def fit_predict_capacity(ranker: Any, name: str, X: np.ndarray, y: np.ndarray, w: np.ndarray, tr: np.ndarray, te: np.ndarray)->np.ndarray:
    m=capacity_model(ranker,name)
    m.fit(X[tr],y[tr],sample_weight=w[tr])
    return np.asarray(m.predict(X[te]),dtype=np.float64)

def inner_select_capacity(
    ranker: Any,
    X: np.ndarray,
    y13: np.ndarray,
    y14: np.ndarray,
    groups: list[str],
    folds: np.ndarray,
    weights: np.ndarray,
    outer_fold: int,
)->tuple[str,list[dict[str,Any]]]:
    outer_train=folds!=outer_fold
    diagnostics=[]
    for name,_params in CAPACITIES:
        p13=np.full(len(groups),np.nan,dtype=np.float64)
        p14=np.full(len(groups),np.nan,dtype=np.float64)
        inner_rows=[]
        for inner_fold in range(5):
            if inner_fold==outer_fold:
                continue
            itr=outer_train & (folds!=inner_fold)
            ite=outer_train & (folds==inner_fold)
            require(itr.any() and ite.any(),f'empty inner fold outer={outer_fold} inner={inner_fold}')
            train_groups={groups[i] for i in np.where(itr)[0]}
            test_groups={groups[i] for i in np.where(ite)[0]}
            require(train_groups.isdisjoint(test_groups),f'inner group leakage outer={outer_fold} inner={inner_fold}')
            p13[ite]=fit_predict_capacity(ranker,name,X,y13,weights,itr,ite)
            p14[ite]=fit_predict_capacity(ranker,name,X,y14,weights,itr,ite)
            inner_rows.append({
                'inner_fold':inner_fold,
                'train_examples':int(itr.sum()),
                'test_examples':int(ite.sum()),
                'train_groups':len(train_groups),
                'test_groups':len(test_groups),
            })
        require(np.all(np.isfinite(p13[outer_train])) and np.all(np.isfinite(p14[outer_train])),f'incomplete inner OOF {name} outer={outer_fold}')
        require(np.all(np.isnan(p13[~outer_train])) and np.all(np.isnan(p14[~outer_train])),f'outer test populated during inner selection {name} outer={outer_fold}')
        combined=np.minimum(p13,p14)
        score=stable_group_ndcg(combined,y13,y14,groups,outer_train)
        diagnostics.append({
            'capacity':name,
            'params':dict(dict(CAPACITIES)[name]),
            'inner_group_ndcg':float(score),
            'inner_prediction_2013_sha256':v23.array_sha(p13[outer_train]),
            'inner_prediction_2014_sha256':v23.array_sha(p14[outer_train]),
            'inner_folds':inner_rows,
            'tie_preference':CAPACITY_TIE_PREFERENCE[name],
        })
    winner=max(diagnostics,key=lambda d:(d['inner_group_ndcg'],d['tie_preference']))
    return str(winner['capacity']),diagnostics

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--sugar-root',type=Path,required=True)
    p.add_argument('--hdbscan-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    require(v23.sha(a.ranker_source)==RANKER_SOURCE_SHA,'#839 ranker source changed')
    roots={'sugar':a.sugar_root,'hdbscan':a.hdbscan_root}

    for route in ROUTES:
        for name,expected in EXPECTED_EXACT_FILE_SHA[route].items():
            require(v23.sha(roots[route]/name)==expected,f'{route} {name} differs from valid v22 pretruth payload')
        X=np.load(roots[route]/'features.npy',allow_pickle=False)
        require(X.shape[1]==FEATURE_DIM,f'{route} feature dimension changed')
        require(v23.rounded12_sha(X)==EXPECTED_ROUNDED12_FEATURE_SHA[route],f'{route} semantic features changed')
        m=json.loads((roots[route]/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        require(m['feature_dimension']==FEATURE_DIM and m['truth_accessed'] is False,f'{route} invalid pretruth manifest')
        require(m['v19_family_sha256']==EXPECTED_V19_FAMILY_SHA[route],f'{route} v19 family identity changed')

    truth_year={}; frozen_eval={}
    for route,year in PANELS:
        truth_year[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    ranker=v23.load_module(a.ranker_source,'frozen_839_v29_nested_capacity')
    base_params=ranker.model().get_params()
    require(base_params.get('max_depth')==4 and base_params.get('min_samples_leaf')==5,'#839 baseline capacity changed')
    require(base_params.get('n_estimators')==600,'#839 tree count changed')

    route_data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; route_offsets={}; cursor=0; target_diag={}
    for route in ROUTES:
        root=roots[route]
        meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fam_payload=json.loads((root/'family_memberships.json').read_text())
        require(meta['feature_dimension']==FEATURE_DIM and meta['truth_accessed'] is False,'invalid v22 pretruth manifest')
        require(fam_payload['truth_accessed'] is False,'membership payload already truth-bearing')
        ids=list(map(str,meta['family_ids']))
        fams=fam_payload['families']
        require([str(f['family_id']) for f in fams]==ids,'family alignment changed')
        X=np.load(root/'features.npy',allow_pickle=False)
        C=np.load(root/'centroids.npy',allow_pickle=False)
        require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),'pretruth shape changed')
        require(v23.array_sha(X)==meta['feature_sha256'] and v23.array_sha(C)==meta['centroid_sha256'],'pretruth internal hash changed')

        by_year={y:truth_year[(route,y)] for y in YEARS}
        eligible=v23.eligible_from_year_truth(by_year)
        hidden={}
        hidden.update(by_year[2013]); hidden.update(by_year[2014])
        require(len(hidden)==len(by_year[2013])+len(by_year[2014]),f'{route} duplicate IDs across years')
        best=[v23.combined_best_label(f,hidden,eligible) for f in fams]
        y13=[]; y14=[]; gs=[]
        for i,(f,b) in enumerate(zip(fams,best)):
            label=b['best_label']
            if label is None:
                f13=f14=0.0
                group=f'NEG/{route}/{ids[i]}'
            else:
                f13=v23.year_f1_for_label(f,by_year[2013],label)
                f14=v23.year_f1_for_label(f,by_year[2014],label)
                group='SHOWER/'+str(label)
            y13.append(float(f13)); y14.append(float(f14)); gs.append(group)
        y13a=np.asarray(y13,dtype=np.float64); y14a=np.asarray(y14,dtype=np.float64)
        for name,yarr in [('2013',y13a),('2014',y14a)]:
            require(np.all(np.isfinite(yarr)) and np.all((yarr>=0.0)&(yarr<=1.0)),f'invalid {name} annual target')
        route_offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids)
        Xs.append(X); y13s.append(y13a); y14s.append(y14a); groups.extend(gs)
        route_data[route]={'meta':meta,'families':fams,'ids':ids,'centroids':C,'best':best,'eligible':eligible}
        target_diag[route]={
            'families':len(ids),
            'eligible_recurrent_showers':len(eligible),
            'families_with_best_recurrent_label':int(sum(b['best_label'] is not None for b in best)),
            '2013_nonzero_targets':int(np.sum(y13a>0)),
            '2014_nonzero_targets':int(np.sum(y14a>0)),
            'balanced_nonzero_targets':int(np.sum(np.minimum(y13a,y14a)>0)),
            'balanced_target_mean':float(np.mean(np.minimum(y13a,y14a))),
            'balanced_target_max':float(np.max(np.minimum(y13a,y14a))),
        }

    Xall=np.vstack(Xs); y13all=np.concatenate(y13s); y14all=np.concatenate(y14s); groups=list(map(str,groups))
    require(Xall.shape==(cursor,FEATURE_DIM) and len(y13all)==len(y14all)==len(groups)==cursor,'stacked shape mismatch')
    folds=np.asarray([v23.v1.deterministic_fold(g) for g in groups],dtype=int)
    weights=ranker.grouped_weights(groups)

    v24_oof13=np.zeros(cursor,dtype=np.float64); v24_oof14=np.zeros(cursor,dtype=np.float64)
    oof13=np.zeros(cursor,dtype=np.float64); oof14=np.zeros(cursor,dtype=np.float64)
    fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold
        require(tr.any() and te.any(),f'empty outer fold {fold}')
        train_groups={groups[i] for i in np.where(tr)[0]}
        test_groups={groups[i] for i in np.where(te)[0]}
        require(train_groups.isdisjoint(test_groups),f'outer group leakage {fold}')

        b13=capacity_model(ranker,'baseline_d4_l5'); b14=capacity_model(ranker,'baseline_d4_l5')
        b13.fit(Xall[tr],y13all[tr],sample_weight=weights[tr]); b14.fit(Xall[tr],y14all[tr],sample_weight=weights[tr])
        v24_oof13[te]=b13.predict(Xall[te]); v24_oof14[te]=b14.predict(Xall[te])

        chosen,inner_diag=inner_select_capacity(ranker,Xall,y13all,y14all,groups,folds,weights,fold)
        m13=capacity_model(ranker,chosen); m14=capacity_model(ranker,chosen)
        m13.fit(Xall[tr],y13all[tr],sample_weight=weights[tr]); m14.fit(Xall[tr],y14all[tr],sample_weight=weights[tr])
        oof13[te]=m13.predict(Xall[te]); oof14[te]=m14.predict(Xall[te])
        fold_diag.append({
            'outer_fold':fold,
            'train_examples':int(tr.sum()),
            'test_examples':int(te.sum()),
            'train_groups':len(train_groups),
            'test_groups':len(test_groups),
            'selected_capacity':chosen,
            'inner_capacity_diagnostics':inner_diag,
            'outer_test_nonzero_2013':int(np.sum(y13all[te]>0)),
            'outer_test_nonzero_2014':int(np.sum(y14all[te]>0)),
        })

    require(np.all(np.isfinite(oof13)) and np.all(np.isfinite(oof14)),'nonfinite v29 OOF')
    require(np.all(np.isfinite(v24_oof13)) and np.all(np.isfinite(v24_oof14)),'nonfinite v24 control OOF')
    nested_min=np.minimum(oof13,oof14); v24_min=np.minimum(v24_oof13,v24_oof14)

    variants={}; control_panels=[]; v24_control_panels=[]; order_diag={}
    for route in ROUTES:
        lo,hi=route_offsets[route]; rd=route_data[route]; ids=rd['ids']
        tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
        idx=ranker.diversity_order(nested_min[lo:hi],rd['centroids'],0.8,1.0,tie)
        qorder=[ids[i] for i in idx]
        v19order=list(map(str,rd['meta']['v19_order']))
        fused=list(v23.v19.fusion_orders(qorder,v19order)['rank_sum'])

        bidx=ranker.diversity_order(v24_min[lo:hi],rd['centroids'],0.8,1.0,tie)
        bq=[ids[i] for i in bidx]
        bfused=list(v23.v19.fusion_orders(bq,v19order)['rank_sum'])

        variants[route]={
            'nested_capacity_oof_quality':v23.rerank(rd['families'],qorder),
            'nested_capacity_oof_v19_rank_sum':v23.rerank(rd['families'],fused),
            'v19_control':v23.rerank(rd['families'],v19order),
            'v24_fixed_capacity_control':v23.rerank(rd['families'],bfused),
        }
        order_diag[route]={
            'nested_oof_2013_sha256':v23.array_sha(oof13[lo:hi]),
            'nested_oof_2014_sha256':v23.array_sha(oof14[lo:hi]),
            'nested_min_sha256':v23.array_sha(nested_min[lo:hi]),
            'nested_quality_order_sha256':hashlib.sha256('\n'.join(qorder).encode()).hexdigest(),
            'nested_fused_order_sha256':hashlib.sha256('\n'.join(fused).encode()).hexdigest(),
            'v24_control_fused_order_sha256':hashlib.sha256('\n'.join(bfused).encode()).hexdigest(),
        }
        for year in YEARS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget'])
            cur=v23.evaluate(variants[route]['v19_control'],truth_year[(route,year)],budget)
            exp=V19_METRICS[(route,year)]
            require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'v19 control mismatch {route} {year}')
            control_panels.append({'comparator':route,'year':year,**cur})

            bcur=v23.evaluate(variants[route]['v24_fixed_capacity_control'],truth_year[(route,year)],budget)
            bexp=V24_FUSED_METRICS[(route,year)]
            require(abs(bcur['macro_f1']-bexp[0])<1e-12 and bcur['recovered_f1_gt_0_5']==bexp[1],f'v24 fixed-capacity control mismatch {route} {year}')
            v24_control_panels.append({'comparator':route,'year':year,**bcur})

    rows=[]
    for variant in VARIANTS:
        panels=[]
        for route,year in PANELS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget'])
            cur=v23.evaluate(variants[route][variant],truth_year[(route,year)],budget)
            lit=frozen_eval[(route,year)]['comparator_summary']
            cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5'])
            lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5'])
            mr=cm/lm if lm else float('inf'); rr=cr/lr if lr else float('inf')
            win=bool(cm>lm and cr>=lr)
            panels.append({
                'comparator':route,'year':year,'budget':budget,
                'candidate_macro_f1':cm,'literature_macro_f1':lm,
                'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,
                'macro_f1_ratio':mr,'recovery_ratio':rr,'superiority_pair_pass':win,
            })
        wins=sum(int(x['superiority_pair_pass']) for x in panels)
        minm=min(x['macro_f1_ratio'] for x in panels); minr=min(x['recovery_ratio'] for x in panels)
        meanm=float(np.mean([x['macro_f1_ratio'] for x in panels])); meanr=float(np.mean([x['recovery_ratio'] for x in panels]))
        rows.append({
            'variant':variant,'panel_wins':wins,'all_panel_win':wins==4,
            'min_macro_f1_ratio':minm,'min_recovery_ratio':minr,
            'mean_macro_f1_ratio':meanm,'mean_recovery_ratio':meanr,
            'selection_key':[wins,minm,minr,meanm,meanr,PREFERENCE[variant]],
            'panels':panels,
        })
    winner=max(rows,key=lambda r:tuple(r['selection_key']))
    passed=bool(winner['all_panel_win'])

    full_freeze={'verdict':'NOT_FROZEN_V29_OOF_FAIL','selected_capacity':None,'head_2013_sha256':None,'head_2014_sha256':None}
    if passed:
        full_diags=[]
        for name,_params in CAPACITIES:
            p13=np.zeros(cursor,dtype=np.float64); p14=np.zeros(cursor,dtype=np.float64)
            for fold in range(5):
                tr=folds!=fold; te=folds==fold
                p13[te]=fit_predict_capacity(ranker,name,Xall,y13all,weights,tr,te)
                p14[te]=fit_predict_capacity(ranker,name,Xall,y14all,weights,tr,te)
            score=stable_group_ndcg(np.minimum(p13,p14),y13all,y14all,groups,np.ones(cursor,dtype=bool))
            full_diags.append({'capacity':name,'group_ndcg':float(score),'tie_preference':CAPACITY_TIE_PREFERENCE[name]})
        selected=max(full_diags,key=lambda d:(d['group_ndcg'],d['tie_preference']))['capacity']
        full13=capacity_model(ranker,selected); full14=capacity_model(ranker,selected)
        full13.fit(Xall,y13all,sample_weight=weights); full14.fit(Xall,y14all,sample_weight=weights)
        full13.set_params(n_jobs=1); full14.set_params(n_jobs=1)
        p13=a.output/'v29_sonotaco_head_2013.joblib'; p14=a.output/'v29_sonotaco_head_2014.joblib'
        joblib.dump(full13,p13); joblib.dump(full14,p14)
        full_freeze={
            'verdict':'PASS_V29_FULL_SONOTACO_NESTED_CAPACITY_MODEL_FREEZE',
            'selected_capacity':selected,
            'capacity_selection_diagnostics':full_diags,
            'head_2013_sha256':v23.sha(p13),'head_2014_sha256':v23.sha(p14),
            'feature_dimension':FEATURE_DIM,'training_examples':cursor,'training_groups':len(set(groups)),
            'training_feature_sha256':v23.array_sha(Xall),
            'target_2013_sha256':v23.array_sha(y13all),'target_2014_sha256':v23.array_sha(y14all),
            'prediction_combiner':'min(head_2013,head_2014)',
            'in_sample_full_fit_score_used_for_promotion':False,
        }
    (a.output/'V29_FULL_MODEL_FREEZE.json').write_text(json.dumps(full_freeze,indent=2,sort_keys=True)+'\n')

    result={
        'scientific_stage':'V29_EXPOSED_SONOTACO_NESTED_WHOLE_SHOWER_TREE_CAPACITY_OOF_RANKING_DEVELOPMENT',
        'sole_scientific_change_from_v24':'select ExtraTrees capacity inside each outer-training split using inner whole-shower OOF full-list group NDCG',
        'feature_dimension':FEATURE_DIM,
        'capacity_library':[{'name':n,**p} for n,p in CAPACITIES],
        'capacity_library_search':False,
        'inner_selection_metric':'full-list group NDCG on max family min(pred13,pred14), relevance=max family min(F1_2013,F1_2014)',
        'inner_selection_has_top_k':False,
        'outer_heldout_group_used_for_capacity_selection':False,
        'same_shower_all_fragments_both_routes_same_outer_fold':True,
        'prediction_combiner':'min(predicted_F1_2013,predicted_F1_2014)',
        'prediction_combiner_search':False,
        'folds':fold_diag,
        'target_diagnostics':target_diag,
        'order_diagnostics':order_diag,
        'v19_control_reproduction_pass':True,
        'v19_control':control_panels,
        'v24_fixed_capacity_control_reproduction_pass':True,
        'v24_fixed_capacity_control':v24_control_panels,
        'all_results':rows,
        'winner':winner,
        'verdict':'PASS_V29_EXPOSED_NESTED_CAPACITY_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V29_NESTED_CAPACITY_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'full_model_freeze':full_freeze,
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY',
        'full_fit_in_sample_score_used':False,
        'post_result_second_search':False,
        'oracle_order_used':False,
        'maarsy_scientific_access':False,
        'dms_scientific_access':False,
        'target_information_access':False,
    }
    (a.output/'V29_EXPOSED_NESTED_CAPACITY_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'winner':winner,'selected_outer_capacities':[x['selected_capacity'] for x in fold_diag],'full_model_freeze':full_freeze},indent=2,sort_keys=True,allow_nan=False))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
