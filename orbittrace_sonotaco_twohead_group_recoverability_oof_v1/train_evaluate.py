#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

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
VARIANT='twohead_group_recoverability_min_oof_v19_rank_sum'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def model()->ExtraTreesClassifier:
    return ExtraTreesClassifier(n_estimators=600,max_depth=4,min_samples_leaf=5,max_features=None,random_state=20260809,n_jobs=-1)


def positive_probability(m:ExtraTreesClassifier,X:np.ndarray)->np.ndarray:
    classes=list(map(int,m.classes_.tolist())); require(0 in classes and 1 in classes,'annual classifier missing a class')
    out=np.asarray(m.predict_proba(X)[:,classes.index(1)],dtype=np.float64)
    require(out.shape==(len(X),) and np.all(np.isfinite(out)) and np.all((out>=0.0)&(out<=1.0)),'invalid annual probabilities')
    return out


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--sugar-root',type=Path,required=True); p.add_argument('--hdbscan-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v23.sha(a.ranker_source)==RANKER_SOURCE_SHA,'#839 ranker source changed')
    roots={'sugar':a.sugar_root,'hdbscan':a.hdbscan_root}

    for route in ROUTES:
        for name,expected in EXPECTED_EXACT_FILE_SHA[route].items(): require(v23.sha(roots[route]/name)==expected,f'{route} {name} differs from valid v22 pretruth payload')
        X=np.load(roots[route]/'features.npy',allow_pickle=False); require(X.shape[1]==FEATURE_DIM,f'{route} feature dimension changed')
        require(v23.rounded12_sha(X)==EXPECTED_ROUNDED12_FEATURE_SHA[route],f'{route} semantic feature payload differs from valid v22')
        meta=json.loads((roots[route]/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        require(meta['feature_dimension']==FEATURE_DIM and meta['truth_accessed'] is False and meta['v19_family_sha256']==EXPECTED_V19_FAMILY_SHA[route],f'{route} invalid pretruth identity')

    truth_year={}; frozen_eval={}
    for route,year in PANELS:
        truth_year[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    ranker=v23.load_module(a.ranker_source,'frozen_839_twohead_group_recoverability')
    route_data={}; Xs=[]; fam13s=[]; fam14s=[]; groups=[]; offsets={}; cursor=0

    for route in ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
        ids=list(map(str,meta['family_ids'])); fams=fp['families']; X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require([str(f['family_id']) for f in fams]==ids and X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),'route payload alignment changed')
        require(v23.array_sha(X)==meta['feature_sha256'] and v23.array_sha(C)==meta['centroid_sha256'],'pretruth internal array hash changed')
        by_year={y:truth_year[(route,y)] for y in YEARS}; eligible=v23.eligible_from_year_truth(by_year); hidden={}; hidden.update(by_year[2013]); hidden.update(by_year[2014])
        best=[v23.combined_best_label(f,hidden,eligible) for f in fams]
        f13=[]; f14=[]; route_groups=[]
        for i,(fam,b) in enumerate(zip(fams,best)):
            label=b['best_label']
            if label is None:
                a13=a14=0; group=f'NEG/{route}/{ids[i]}'
            else:
                a13=int(v23.year_f1_for_label(fam,by_year[2013],label)>RECOVERY_F1_THRESHOLD)
                a14=int(v23.year_f1_for_label(fam,by_year[2014],label)>RECOVERY_F1_THRESHOLD)
                group='SHOWER/'+str(label)
            f13.append(a13); f14.append(a14); route_groups.append(group)
        y13=np.asarray(f13,dtype=np.int8); y14=np.asarray(f14,dtype=np.int8)
        require(np.unique(y13).size==2 and np.unique(y14).size==2,f'{route} annual family target degenerate')
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); fam13s.append(y13); fam14s.append(y14); groups.extend(route_groups)
        route_data[route]={'meta':meta,'families':fams,'ids':ids,'centroids':C,'eligible':eligible,'groups':route_groups,'family13':y13,'family14':y14}

    Xall=np.vstack(Xs); family13=np.concatenate(fam13s); family14=np.concatenate(fam14s); groups=list(map(str,groups))
    require(Xall.shape==(cursor,FEATURE_DIM) and len(groups)==len(family13)==len(family14)==cursor,'stacked shape mismatch')

    gp13={}; gp14={}
    for i,g in enumerate(groups):
        if g.startswith('SHOWER/'):
            gp13[g]=max(int(gp13.get(g,0)),int(family13[i])); gp14[g]=max(int(gp14.get(g,0)),int(family14[i]))
    y13=np.asarray([int(gp13.get(g,0)) if g.startswith('SHOWER/') else 0 for g in groups],dtype=np.int8)
    y14=np.asarray([int(gp14.get(g,0)) if g.startswith('SHOWER/') else 0 for g in groups],dtype=np.int8)
    require(np.unique(y13).size==2 and np.unique(y14).size==2,'stacked annual group target degenerate')
    for i,g in enumerate(groups):
        if int(family13[i])==1: require(int(y13[i])==1 and g.startswith('SHOWER/'),'2013 base-positive family lost in group target')
        if int(family14[i])==1: require(int(y14[i])==1 and g.startswith('SHOWER/'),'2014 base-positive family lost in group target')

    folds=np.asarray([v23.v1.deterministic_fold(g) for g in groups],dtype=int); weights=np.asarray(ranker.grouped_weights(groups),dtype=float)
    require(weights.shape==(cursor,) and np.all(np.isfinite(weights)) and np.all(weights>0),'invalid group weights')
    totals={}
    for i,g in enumerate(groups): totals[g]=float(totals.get(g,0.0)+weights[i])
    require(len({round(v,12) for v in totals.values()})==1,'group weights no longer equalize total group mass')

    oof13=np.zeros(cursor,dtype=float); oof14=np.zeros(cursor,dtype=float); fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; require(tr.any() and te.any(),f'empty fold {fold}')
        require(np.unique(y13[tr]).size==2 and np.unique(y14[tr]).size==2,f'annual training fold {fold} lacks both classes')
        m13=model(); m14=model(); m13.fit(Xall[tr],y13[tr],sample_weight=weights[tr]); m14.fit(Xall[tr],y14[tr],sample_weight=weights[tr])
        oof13[te]=positive_probability(m13,Xall[te]); oof14[te]=positive_probability(m14,Xall[te])
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),f'group leakage fold {fold}')
        fold_diag.append({'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'train_groups':len({groups[i] for i in np.where(tr)[0]}),'test_groups':len({groups[i] for i in np.where(te)[0]}),'train_positive_2013':int(np.sum(y13[tr]==1)),'test_positive_2013':int(np.sum(y13[te]==1)),'train_positive_2014':int(np.sum(y14[tr]==1)),'test_positive_2014':int(np.sum(y14[te]==1))})
    combined=np.minimum(oof13,oof14); require(np.all(np.isfinite(combined)),'combined min score nonfinite')

    variants={}; control_panels=[]; target_diag={}; order_diag={}
    for route in ROUTES:
        lo,hi=offsets[route]; rd=route_data[route]; ids=rd['ids']; scores=combined[lo:hi]
        tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
        idx=ranker.diversity_order(scores,rd['centroids'],0.8,1.0,tie); classifier_order=[ids[i] for i in idx]
        v19order=list(map(str,rd['meta']['v19_order'])); fused=list(v23.v19.fusion_orders(classifier_order,v19order)['rank_sum'])
        variants[route]={VARIANT:v23.rerank(rd['families'],fused),'v19_control':v23.rerank(rd['families'],v19order)}
        rg=groups[lo:hi]; ry13=y13[lo:hi]; ry14=y14[lo:hi]; rf13=family13[lo:hi]; rf14=family14[lo:hi]
        g13={g for i,g in enumerate(rg) if int(ry13[i])==1 and g.startswith('SHOWER/')}; g14={g for i,g in enumerate(rg) if int(ry14[i])==1 and g.startswith('SHOWER/')}
        target_diag[route]={'families':len(ids),'eligible_recurrent_showers':len(rd['eligible']),'base_positive_families_2013':int(np.sum(rf13==1)),'base_positive_families_2014':int(np.sum(rf14==1)),'densified_positive_families_2013':int(np.sum(ry13==1)),'densified_positive_families_2014':int(np.sum(ry14==1)),'added_positive_fragments_2013':int(np.sum((ry13==1)&(rf13==0))),'added_positive_fragments_2014':int(np.sum((ry14==1)&(rf14==0))),'positive_strict_shower_groups_2013':len(g13),'positive_strict_shower_groups_2014':len(g14),'target_definition':'two annual strict-group recoverability heads; group positive in year y iff any stacked route family in group has F1_y>0.5; combined score=min(p2013,p2014)'}
        order_diag[route]={'oof_probability_2013_sha256':v23.array_sha(oof13[lo:hi]),'oof_probability_2014_sha256':v23.array_sha(oof14[lo:hi]),'combined_min_score_sha256':v23.array_sha(scores),'classifier_diversity_order_sha256':hashlib.sha256('\n'.join(classifier_order).encode()).hexdigest(),'fused_order_sha256':hashlib.sha256('\n'.join(fused).encode()).hexdigest(),'head_combination':'min(p2013,p2014), frozen from v24','diversity':{'lambda':0.8,'scale':1.0},'fusion':'equal rank-sum with exact v19'}
        for year in YEARS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget']); cur=v23.evaluate(variants[route]['v19_control'],truth_year[(route,year)],budget); exp=V19_METRICS[(route,year)]
            require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'v19 control mismatch {route} {year}')
            control_panels.append({'comparator':route,'year':year,**cur})

    panels=[]
    for route,year in PANELS:
        budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget']); cur=v23.evaluate(variants[route][VARIANT],truth_year[(route,year)],budget); lit=frozen_eval[(route,year)]['comparator_summary']
        cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5'])
        panels.append({'comparator':route,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':cm/lm if lm else float('inf'),'recovery_ratio':cr/lr if lr else float('inf'),'superiority_pair_pass':bool(cm>lm and cr>=lr)})
    wins=sum(int(x['superiority_pair_pass']) for x in panels); passed=bool(wins==4)

    full={'verdict':'NOT_FROZEN_TWOHEAD_GROUP_RECOVERABILITY_OOF_FAIL','head_2013_sha256':None,'head_2014_sha256':None}
    if passed:
        m13=model(); m14=model(); m13.fit(Xall,y13,sample_weight=weights); m14.fit(Xall,y14,sample_weight=weights); m13.set_params(n_jobs=1); m14.set_params(n_jobs=1)
        p13=a.output/'sonotaco_group_recoverability_2013.joblib'; p14=a.output/'sonotaco_group_recoverability_2014.joblib'; joblib.dump(m13,p13); joblib.dump(m14,p14)
        full={'verdict':'PASS_FULL_EXPOSED_SONOTACO_TWOHEAD_GROUP_RECOVERABILITY_MODEL_FREEZE','head_2013_sha256':v23.sha(p13),'head_2014_sha256':v23.sha(p14),'feature_dimension':FEATURE_DIM,'training_examples':cursor,'training_groups':len(set(groups)),'target_2013_sha256':v23.array_sha(y13),'target_2014_sha256':v23.array_sha(y14),'group_weight_sha256':v23.array_sha(weights),'head_combination':'min positive-class probability; frozen from v24','model':{'kind':'ExtraTreesClassifier','n_estimators':600,'max_depth':4,'min_samples_leaf':5,'max_features':None,'random_state':20260809},'in_sample_full_fit_score_used_for_promotion':False}
    (a.output/'TWOHEAD_GROUP_RECOVERABILITY_FULL_MODEL_FREEZE.json').write_text(json.dumps(full,indent=2,sort_keys=True)+'\n')

    result={'scientific_stage':'EXPOSED_SONOTACO_TWOHEAD_ANNUAL_STRICT_GROUP_RECOVERABILITY_OOF_RANKING_DEVELOPMENT_V1','verdict':'PASS_TWOHEAD_GROUP_RECOVERABILITY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_TWOHEAD_GROUP_RECOVERABILITY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','sole_scientific_change_from_1004':'single conjunctive group target -> two annual group-recoverability heads combined by frozen v24 min rule','feature_dimension':FEATURE_DIM,'recovery_f1_threshold':RECOVERY_F1_THRESHOLD,'threshold_selected_from_result':False,'head_combination':'min(p2013,p2014)','head_combination_search':False,'candidate_membership_changed':False,'pretruth_feature_changed':False,'strict_whole_shower_oof':True,'shared_models_across_routes':True,'annual_group_targets_shared_across_routes':True,'classifier':{'kind':'ExtraTreesClassifier','n_estimators':600,'max_depth':4,'min_samples_leaf':5,'max_features':None,'random_state':20260809},'class_weight_used':False,'resampling_used':False,'probability_calibration_used':False,'group_weighting':'exact #839 inverse strict-group weights','diversity':{'lambda':0.8,'scale':1.0},'fusion':'equal rank-sum with exact v19','promotion_variant':VARIANT,'panel_wins':wins,'all_panel_win':passed,'panels':panels,'v19_control_panels':control_panels,'target_diagnostics':target_diag,'fold_diagnostics':fold_diag,'order_diagnostics':order_diag,'full_model_freeze':full,'feature_search':False,'target_search':False,'model_search':False,'hyperparameter_search':False,'class_weight_search':False,'resampling_search':False,'calibration_search':False,'fusion_search':False,'diversity_search':False,'source_quota_selected':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0]}
    (a.output/'SONOTACO_TWOHEAD_GROUP_RECOVERABILITY_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'target_diagnostics':target_diag,'panels':panels,'full_model_freeze':full},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
