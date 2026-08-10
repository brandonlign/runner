#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

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
VARIANTS=('two_head_min_oof_quality','two_head_min_oof_v19_rank_sum')
PREFERENCE={'two_head_min_oof_quality':2,'two_head_min_oof_v19_rank_sum':1}


def require(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--sugar-root',type=Path,required=True)
    p.add_argument('--hdbscan-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v23.sha(a.ranker_source)==RANKER_SOURCE_SHA,'#839 ranker source changed')
    roots={'sugar':a.sugar_root,'hdbscan':a.hdbscan_root}

    # Repeat the exact repaired-v23 scientific identity guard.
    for route in ROUTES:
        for name,expected in EXPECTED_EXACT_FILE_SHA[route].items():
            require(v23.sha(roots[route]/name)==expected,f'{route} {name} differs from valid v22 pretruth payload')
        pre_X=np.load(roots[route]/'features.npy',allow_pickle=False)
        require(pre_X.shape[1]==FEATURE_DIM,f'{route} feature dimension changed')
        require(v23.rounded12_sha(pre_X)==EXPECTED_ROUNDED12_FEATURE_SHA[route],f'{route} semantic feature payload differs from valid v22')
        pre_meta=json.loads((roots[route]/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        require(pre_meta['feature_dimension']==FEATURE_DIM and pre_meta['truth_accessed'] is False,f'{route} invalid pretruth manifest')
        require(pre_meta['v19_family_sha256']==EXPECTED_V19_FAMILY_SHA[route],f'{route} v19 family identity changed')

    truth_year={}; frozen_eval={}
    for route,year in PANELS:
        truth_year[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    ranker=v23.load_module(a.ranker_source,'frozen_839_v24_train')
    route_data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; route_offsets={}; cursor=0; target_diag={}
    for route in ROUTES:
        root=roots[route]
        meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fam_payload=json.loads((root/'family_memberships.json').read_text())
        require(meta['feature_dimension']==FEATURE_DIM and meta['truth_accessed'] is False,'invalid v22 pretruth manifest')
        require(fam_payload['truth_accessed'] is False,'membership payload already truth-bearing')
        ids=list(map(str,meta['family_ids'])); fams=fam_payload['families']
        require([str(f['family_id']) for f in fams]==ids,'family alignment changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),'pretruth array shape changed')
        require(v23.array_sha(X)==meta['feature_sha256'] and v23.array_sha(C)==meta['centroid_sha256'],'pretruth internal array hash changed')

        by_year={y:truth_year[(route,y)] for y in YEARS}
        eligible=v23.eligible_from_year_truth(by_year)
        hidden={}; hidden.update(by_year[2013]); hidden.update(by_year[2014])
        require(len(hidden)==len(by_year[2013])+len(by_year[2014]),f'{route} duplicate IDs across years')
        best=[v23.combined_best_label(f,hidden,eligible) for f in fams]
        y13=[]; y14=[]; gs=[]
        for i,(f,b) in enumerate(zip(fams,best)):
            label=b['best_label']
            if label is None:
                f13=f14=0.0; group=f'NEG/{route}/{ids[i]}'
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
            'families':len(ids),'eligible_recurrent_showers':len(eligible),
            'families_with_best_recurrent_label':int(sum(b['best_label'] is not None for b in best)),
            '2013_nonzero_targets':int(np.sum(y13a>0)),'2014_nonzero_targets':int(np.sum(y14a>0)),
            '2013_mean':float(np.mean(y13a)),'2014_mean':float(np.mean(y14a)),
            '2013_median':float(np.median(y13a)),'2014_median':float(np.median(y14a)),
            '2013_max':float(np.max(y13a)),'2014_max':float(np.max(y14a)),
            'fixed_best_label_definition':'exact v22/v23 combined recurrent best_label',
            'head_targets':['F1_2013','F1_2014'],
        }

    Xall=np.vstack(Xs); y13all=np.concatenate(y13s); y14all=np.concatenate(y14s); groups=list(map(str,groups))
    require(Xall.shape==(cursor,FEATURE_DIM) and len(y13all)==len(y14all)==len(groups)==cursor,'stacked training shape mismatch')
    folds=np.asarray([v23.v1.deterministic_fold(g) for g in groups],dtype=int)
    weights=ranker.grouped_weights(groups)
    oof13=np.zeros(cursor,dtype=np.float64); oof14=np.zeros(cursor,dtype=np.float64); fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold
        require(tr.any() and te.any(),f'empty grouped fold {fold}')
        m13=ranker.model(); m14=ranker.model()
        m13.fit(Xall[tr],y13all[tr],sample_weight=weights[tr]); m14.fit(Xall[tr],y14all[tr],sample_weight=weights[tr])
        oof13[te]=m13.predict(Xall[te]); oof14[te]=m14.predict(Xall[te])
        test_groups=set(groups[i] for i in np.where(te)[0]); train_groups=set(groups[i] for i in np.where(tr)[0])
        require(test_groups.isdisjoint(train_groups),f'group leakage in fold {fold}')
        fold_diag.append({
            'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),
            'train_groups':len(train_groups),'test_groups':len(test_groups),
            'test_nonzero_2013':int(np.sum(y13all[te]>0)),'test_nonzero_2014':int(np.sum(y14all[te]>0)),
        })
    min_oof=np.minimum(oof13,oof14)

    variants={}; control_panels=[]; order_diag={}
    for route in ROUTES:
        lo,hi=route_offsets[route]; rd=route_data[route]; ids=rd['ids']; scores=min_oof[lo:hi]
        tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
        idx=ranker.diversity_order(scores,rd['centroids'],0.8,1.0,tie); qorder=[ids[i] for i in idx]
        v19order=list(map(str,rd['meta']['v19_order']))
        fused=list(v23.v19.fusion_orders(qorder,v19order)['rank_sum'])
        variants[route]={
            'two_head_min_oof_quality':v23.rerank(rd['families'],qorder),
            'two_head_min_oof_v19_rank_sum':v23.rerank(rd['families'],fused),
            'v19_control':v23.rerank(rd['families'],v19order),
        }
        order_diag[route]={
            'oof_2013_prediction_sha256':v23.array_sha(oof13[lo:hi]),
            'oof_2014_prediction_sha256':v23.array_sha(oof14[lo:hi]),
            'min_oof_prediction_sha256':v23.array_sha(scores),
            'quality_order_sha256':hashlib.sha256('\n'.join(qorder).encode()).hexdigest(),
            'fused_order_sha256':hashlib.sha256('\n'.join(fused).encode()).hexdigest(),
            'prediction_combiner':'min(pred_2013,pred_2014)',
        }
        for year in YEARS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget'])
            cur=v23.evaluate(variants[route]['v19_control'],truth_year[(route,year)],budget); exp=V19_METRICS[(route,year)]
            require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'v19 fixed-membership control mismatch {route} {year}')
            control_panels.append({'comparator':route,'year':year,**cur})

    rows=[]
    for variant in VARIANTS:
        panels=[]
        for route,year in PANELS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget'])
            cur=v23.evaluate(variants[route][variant],truth_year[(route,year)],budget); lit=frozen_eval[(route,year)]['comparator_summary']
            cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5'])
            mr=cm/lm if lm else float('inf'); rr=cr/lr if lr else float('inf'); win=bool(cm>lm and cr>=lr)
            panels.append({'comparator':route,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':mr,'recovery_ratio':rr,'superiority_pair_pass':win})
        wins=sum(int(x['superiority_pair_pass']) for x in panels); minm=min(x['macro_f1_ratio'] for x in panels); minr=min(x['recovery_ratio'] for x in panels)
        meanm=float(np.mean([x['macro_f1_ratio'] for x in panels])); meanr=float(np.mean([x['recovery_ratio'] for x in panels]))
        rows.append({'variant':variant,'panel_wins':wins,'all_panel_win':wins==4,'min_macro_f1_ratio':minm,'min_recovery_ratio':minr,'mean_macro_f1_ratio':meanm,'mean_recovery_ratio':meanr,'selection_key':[wins,minm,minr,meanm,meanr,PREFERENCE[variant]],'panels':panels})
    winner=max(rows,key=lambda r:tuple(r['selection_key'])); passed=bool(winner['all_panel_win'])

    full_freeze={'verdict':'NOT_FROZEN_V24_OOF_FAIL','head_2013_sha256':None,'head_2014_sha256':None}
    if passed:
        full13=ranker.model(); full14=ranker.model()
        full13.fit(Xall,y13all,sample_weight=weights); full14.fit(Xall,y14all,sample_weight=weights)
        full13.set_params(n_jobs=1); full14.set_params(n_jobs=1)
        p13=a.output/'v24_sonotaco_head_2013.joblib'; p14=a.output/'v24_sonotaco_head_2014.joblib'
        joblib.dump(full13,p13); joblib.dump(full14,p14)
        full_freeze={
            'verdict':'PASS_V24_FULL_SONOTACO_TWO_HEAD_MODEL_FREEZE',
            'head_2013_sha256':v23.sha(p13),'head_2014_sha256':v23.sha(p14),'feature_dimension':FEATURE_DIM,
            'training_examples':len(groups),'training_groups':len(set(groups)),
            'training_feature_sha256':v23.array_sha(Xall),'target_2013_sha256':v23.array_sha(y13all),'target_2014_sha256':v23.array_sha(y14all),
            'prediction_combiner':'min(head_2013,head_2014)','in_sample_full_fit_score_used_for_promotion':False,
        }
    (a.output/'V24_FULL_MODEL_FREEZE.json').write_text(json.dumps(full_freeze,indent=2,sort_keys=True)+'\n')

    result={
        'scientific_stage':'V24_EXPOSED_SONOTACO_TWO_HEAD_ANNUAL_STRICT_GROUP_OOF_RANKING_DEVELOPMENT',
        'sole_scientific_change_from_v23':'fit separate 2013/2014 annual-quality heads and combine OOF predictions by fixed minimum',
        'feature_dimension':FEATURE_DIM,'v22_v23_pretruth_scientific_identity_pass':True,
        'same_shower_all_fragments_both_routes_same_fold':True,'two_head_architecture_identical_except_target':True,
        'prediction_combiner':'min(predicted_F1_2013,predicted_F1_2014)','prediction_combiner_search':False,
        'folds':fold_diag,'target_diagnostics':target_diag,'order_diagnostics':order_diag,
        'v19_control_reproduction_pass':True,'v19_control':control_panels,'all_results':rows,'winner':winner,
        'verdict':'PASS_V24_EXPOSED_TWO_HEAD_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V24_TWO_HEAD_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'full_model_freeze':full_freeze,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','full_fit_in_sample_score_used':False,'post_result_second_search':False,
        'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,
    }
    (a.output/'V24_EXPOSED_TWO_HEAD_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'winner':winner,'full_model_freeze':full_freeze,'target_diagnostics':target_diag},indent=2,sort_keys=True,allow_nan=False))
    return 0

if __name__=='__main__': raise SystemExit(main())
