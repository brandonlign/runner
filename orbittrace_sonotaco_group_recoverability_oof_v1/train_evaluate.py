#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier

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
RECOVERY_F1_THRESHOLD=0.5
VARIANT='group_recoverability_oof_v19_rank_sum'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def recovery_model()->ExtraTreesClassifier:
    return ExtraTreesClassifier(
        n_estimators=600,
        max_depth=4,
        min_samples_leaf=5,
        max_features=None,
        random_state=20260809,
        n_jobs=-1,
    )


def positive_probability(model:ExtraTreesClassifier,X:np.ndarray)->np.ndarray:
    classes=list(map(int,model.classes_.tolist()))
    require(0 in classes and 1 in classes,'group-recoverability classifier missing a class')
    j=classes.index(1)
    out=np.asarray(model.predict_proba(X)[:,j],dtype=np.float64)
    require(out.shape==(len(X),) and np.all(np.isfinite(out)) and np.all((out>=0.0)&(out<=1.0)),'invalid group-recoverability probabilities')
    return out


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

    # Exact repaired v22-v25 pretruth scientific identity before truth is interpreted.
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

    ranker=v23.load_module(a.ranker_source,'frozen_839_group_recoverability')
    route_data={}; Xs=[]; base_targets=[]; groups=[]; route_offsets={}; cursor=0

    # First derive the exact #997 family-level predicate and strict groups, but do not yet
    # assign the densified target. Group positivity is defined globally across the stacked
    # Sugar+HDBSCAN strict group, matching the shared whole-shower fold semantics.
    for route in ROUTES:
        root=roots[route]
        meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fam_payload=json.loads((root/'family_memberships.json').read_text())
        require(meta['feature_dimension']==FEATURE_DIM and meta['truth_accessed'] is False,'invalid pretruth manifest')
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

        family_target=[]; route_groups=[]; annual=[]
        for i,(f,b) in enumerate(zip(fams,best)):
            label=b['best_label']
            if label is None:
                f13=f14=0.0; target=0; group=f'NEG/{route}/{ids[i]}'
            else:
                f13=v23.year_f1_for_label(f,by_year[2013],label)
                f14=v23.year_f1_for_label(f,by_year[2014],label)
                target=int(f13>RECOVERY_F1_THRESHOLD and f14>RECOVERY_F1_THRESHOLD)
                group='SHOWER/'+str(label)
            family_target.append(target); route_groups.append(group); annual.append((float(f13),float(f14)))

        base=np.asarray(family_target,dtype=np.int8)
        require(set(np.unique(base).tolist()).issubset({0,1}) and np.unique(base).size==2,f'{route} family recoverability target degenerate')
        route_offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids)
        Xs.append(X); base_targets.append(base); groups.extend(route_groups)
        route_data[route]={'meta':meta,'families':fams,'ids':ids,'centroids':C,'best':best,'annual':annual,'eligible':eligible,'family_target':base,'groups':route_groups}

    Xall=np.vstack(Xs); base_all=np.concatenate(base_targets); groups=list(map(str,groups))
    require(Xall.shape==(cursor,FEATURE_DIM) and len(base_all)==len(groups)==cursor,'stacked training shape mismatch')

    group_positive={}
    for i,g in enumerate(groups):
        if g.startswith('SHOWER/'):
            group_positive[g]=max(int(group_positive.get(g,0)),int(base_all[i]))
    yall=np.asarray([int(group_positive.get(g,0)) if g.startswith('SHOWER/') else 0 for g in groups],dtype=np.int8)
    require(np.unique(yall).size==2,'stacked group-recoverability target degenerate')
    for i,g in enumerate(groups):
        if int(base_all[i])==1:
            require(g.startswith('SHOWER/') and int(yall[i])==1,'base-positive family not assigned positive group target')

    folds=np.asarray([v23.v1.deterministic_fold(g) for g in groups],dtype=int)
    weights=np.asarray(ranker.grouped_weights(groups),dtype=np.float64)
    require(weights.shape==(cursor,) and np.all(np.isfinite(weights)) and np.all(weights>0),'invalid exact grouped weights')

    # Confirm inverse-group weighting keeps each strict group's total training mass fixed.
    totals={}
    for i,g in enumerate(groups): totals[g]=float(totals.get(g,0.0)+weights[i])
    rounded={round(v,12) for v in totals.values()}
    require(len(rounded)==1,'exact grouped weights no longer equalize total group weight')

    oof=np.zeros(cursor,dtype=np.float64); fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold
        require(tr.any() and te.any(),f'empty grouped fold {fold}')
        require(np.unique(yall[tr]).size==2,f'training fold {fold} lacks both group-recoverability classes')
        m=recovery_model(); m.fit(Xall[tr],yall[tr],sample_weight=weights[tr]); oof[te]=positive_probability(m,Xall[te])
        train_groups={groups[i] for i in np.where(tr)[0]}; test_groups={groups[i] for i in np.where(te)[0]}
        require(train_groups.isdisjoint(test_groups),f'group leakage in fold {fold}')
        fold_diag.append({
            'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),
            'train_groups':len(train_groups),'test_groups':len(test_groups),
            'train_positive_examples':int(np.sum(yall[tr]==1)),'test_positive_examples':int(np.sum(yall[te]==1)),
            'train_positive_groups':int(len({groups[i] for i in np.where(tr & (yall==1))[0]})),
            'test_positive_groups':int(len({groups[i] for i in np.where(te & (yall==1))[0]})),
            'test_probability_mean':float(np.mean(oof[te])),'test_probability_min':float(np.min(oof[te])),'test_probability_max':float(np.max(oof[te])),
        })

    variants={}; control_panels=[]; order_diag={}; target_diag={}
    for route in ROUTES:
        lo,hi=route_offsets[route]; rd=route_data[route]; ids=rd['ids']; scores=oof[lo:hi]
        route_y=yall[lo:hi]; route_base=base_all[lo:hi]; route_groups=groups[lo:hi]
        tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
        idx=ranker.diversity_order(scores,rd['centroids'],0.8,1.0,tie)
        classifier_order=[ids[i] for i in idx]
        v19order=list(map(str,rd['meta']['v19_order']))
        fused=list(v23.v19.fusion_orders(classifier_order,v19order)['rank_sum'])
        variants[route]={VARIANT:v23.rerank(rd['families'],fused),'v19_control':v23.rerank(rd['families'],v19order)}
        positive_groups={g for i,g in enumerate(route_groups) if int(route_y[i])==1 and g.startswith('SHOWER/')}
        base_positive_groups={g for i,g in enumerate(route_groups) if int(route_base[i])==1 and g.startswith('SHOWER/')}
        require(base_positive_groups.issubset(positive_groups),f'{route} densified group target lost a base-positive group')
        target_diag[route]={
            'families':len(ids),
            'eligible_recurrent_showers':len(rd['eligible']),
            'base_balanced_recovery_positive_families':int(np.sum(route_base==1)),
            'densified_group_positive_families':int(np.sum(route_y==1)),
            'densified_added_positive_fragments':int(np.sum((route_y==1)&(route_base==0))),
            'recoverable_strict_shower_groups_present_in_route':len(positive_groups),
            'base_positive_strict_shower_groups_present_in_route':len(base_positive_groups),
            'target_definition':'all families in SHOWER/<label> are positive iff any stacked Sugar/HDBSCAN family in that strict shower group satisfies F1_2013>0.5 AND F1_2014>0.5; NEG groups remain 0',
            'threshold_source':'existing frozen literature recovered-shower criterion F1>0.5; not selected in this experiment',
        }
        order_diag[route]={
            'oof_positive_probability_sha256':v23.array_sha(scores),
            'classifier_diversity_order_sha256':hashlib.sha256('\n'.join(classifier_order).encode()).hexdigest(),
            'fused_order_sha256':hashlib.sha256('\n'.join(fused).encode()).hexdigest(),
            'diversity':{'lambda':0.8,'scale':1.0},
            'fusion':'parameter-free equal rank-sum with exact v19',
            'classifier_only_order_evaluated_as_promotion_candidate':False,
        }
        for year in YEARS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget'])
            cur=v23.evaluate(variants[route]['v19_control'],truth_year[(route,year)],budget); exp=V19_METRICS[(route,year)]
            require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'v19 fixed-membership control mismatch {route} {year}')
            control_panels.append({'comparator':route,'year':year,**cur})

    panels=[]
    for route,year in PANELS:
        budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget'])
        cur=v23.evaluate(variants[route][VARIANT],truth_year[(route,year)],budget); lit=frozen_eval[(route,year)]['comparator_summary']
        cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5'])
        panels.append({
            'comparator':route,'year':year,'budget':budget,
            'candidate_macro_f1':cm,'literature_macro_f1':lm,
            'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,
            'macro_f1_ratio':cm/lm if lm else float('inf'),'recovery_ratio':cr/lr if lr else float('inf'),
            'superiority_pair_pass':bool(cm>lm and cr>=lr),
        })
    wins=sum(int(x['superiority_pair_pass']) for x in panels); passed=bool(wins==4)

    full_freeze={'verdict':'NOT_FROZEN_GROUP_RECOVERABILITY_OOF_FAIL','model_sha256':None}
    if passed:
        full=recovery_model(); full.fit(Xall,yall,sample_weight=weights); full.set_params(n_jobs=1)
        path=a.output/'sonotaco_group_recoverability_classifier.joblib'; joblib.dump(full,path)
        full_freeze={
            'verdict':'PASS_FULL_EXPOSED_SONOTACO_GROUP_RECOVERABILITY_MODEL_FREEZE',
            'model_sha256':v23.sha(path),'feature_dimension':FEATURE_DIM,
            'training_examples':cursor,'training_groups':len(set(groups)),
            'positive_examples':int(np.sum(yall==1)),
            'positive_groups':int(len({groups[i] for i in range(len(groups)) if int(yall[i])==1})),
            'target_sha256':v23.array_sha(yall),'group_weight_sha256':v23.array_sha(weights),
            'model':{'kind':'ExtraTreesClassifier','n_estimators':600,'max_depth':4,'min_samples_leaf':5,'max_features':None,'random_state':20260809},
            'in_sample_full_fit_score_used_for_promotion':False,
        }
    (a.output/'GROUP_RECOVERABILITY_FULL_MODEL_FREEZE.json').write_text(json.dumps(full_freeze,indent=2,sort_keys=True)+'\n')

    result={
        'scientific_stage':'EXPOSED_SONOTACO_STRICT_GROUP_RECOVERABILITY_OOF_RANKING_DEVELOPMENT_V1',
        'verdict':'PASS_GROUP_RECOVERABILITY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_GROUP_RECOVERABILITY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change_from_997':'family balanced-recovery target -> strict shower-group recoverability target copied to every family in that group',
        'feature_dimension':FEATURE_DIM,'recovery_f1_threshold':RECOVERY_F1_THRESHOLD,
        'threshold_selected_from_result':False,'threshold_source':'existing literature evaluator recovered-shower criterion',
        'candidate_membership_changed':False,'pretruth_feature_changed':False,
        'strict_whole_shower_oof':True,'shared_model_across_routes':True,'group_target_shared_across_routes':True,
        'classifier':{'kind':'ExtraTreesClassifier','n_estimators':600,'max_depth':4,'min_samples_leaf':5,'max_features':None,'random_state':20260809},
        'class_weight_used':False,'resampling_used':False,'probability_calibration_used':False,
        'group_weighting':'exact #839 inverse strict-group weights; equal total weight per strict group',
        'diversity':{'lambda':0.8,'scale':1.0},'fusion':'parameter-free equal rank-sum with exact v19',
        'promotion_variant':VARIANT,'panel_wins':wins,'all_panel_win':passed,'panels':panels,
        'v19_control_panels':control_panels,'target_diagnostics':target_diag,'fold_diagnostics':fold_diag,'order_diagnostics':order_diag,
        'full_model_freeze':full_freeze,
        'feature_search':False,'target_search':False,'model_search':False,'hyperparameter_search':False,'class_weight_search':False,'resampling_search':False,'calibration_search':False,'fusion_search':False,'diversity_search':False,'source_quota_selected':False,'post_result_second_search':False,
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0],
    }
    (a.output/'SONOTACO_GROUP_RECOVERABILITY_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'target_diagnostics':target_diag,'panels':panels,'full_model_freeze':full_freeze},indent=2,sort_keys=True,allow_nan=False))
    return 0

if __name__=='__main__': raise SystemExit(main())
