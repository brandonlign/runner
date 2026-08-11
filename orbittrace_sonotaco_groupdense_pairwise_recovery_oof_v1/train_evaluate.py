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
VARIANT='groupdense_pairwise_recovery_v19_rank_sum'


def require(ok:bool,msg:str)->None:
    if not ok:
        raise RuntimeError(msg)


def pair_model()->ExtraTreesClassifier:
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
    require(0 in classes and 1 in classes,'pairwise classifier missing a class')
    j=classes.index(1)
    out=np.asarray(model.predict_proba(X)[:,j],dtype=np.float64)
    require(out.shape==(len(X),) and np.all(np.isfinite(out)) and np.all((out>=0.0)&(out<=1.0)),'invalid pairwise probabilities')
    return out


def build_pair_training(
    X:np.ndarray,
    y:np.ndarray,
    groups:list[str],
    base_weights:np.ndarray,
    train_mask:np.ndarray,
)->tuple[np.ndarray,np.ndarray,np.ndarray,dict]:
    pos=np.where(train_mask & (y==1))[0]
    neg=np.where(train_mask & (y==0))[0]
    require(len(pos)>0 and len(neg)>0,'pairwise fold lacks positive or negative examples')
    diffs=[]; labels=[]; weights=[]; unordered=0; skipped_same_group=0
    for i in pos.tolist():
        for j in neg.tolist():
            if groups[i]==groups[j]:
                skipped_same_group+=1
                continue
            d=np.asarray(X[i]-X[j],dtype=np.float64)
            w=float(base_weights[i]*base_weights[j])
            require(np.isfinite(w) and w>0,'invalid pair weight')
            diffs.append(d); labels.append(1); weights.append(w)
            diffs.append(-d); labels.append(0); weights.append(w)
            unordered+=1
    require(unordered>0,'no informative positive-negative group pairs')
    xp=np.asarray(diffs,dtype=np.float64)
    yp=np.asarray(labels,dtype=np.int8)
    wp=np.asarray(weights,dtype=np.float64)
    require(xp.ndim==2 and xp.shape[1]==FEATURE_DIM and len(xp)==len(yp)==len(wp),'bad pairwise training shape')
    require(set(yp.tolist())=={0,1} and np.all(np.isfinite(xp)) and np.all(np.isfinite(wp)) and np.all(wp>0),'invalid pairwise training arrays')
    # Scale is irrelevant to tree fitting but deterministic mean-one normalization keeps
    # numerical magnitudes stable without introducing a scientific parameter.
    wp=wp/float(np.mean(wp))
    return xp,yp,wp,{
        'positive_family_examples':int(len(pos)),
        'negative_family_examples':int(len(neg)),
        'informative_unordered_pairs':int(unordered),
        'oriented_pairs':int(len(yp)),
        'skipped_same_group_pairs':int(skipped_same_group),
        'pair_weight_rule':'exact inherited family_group_weight_i * family_group_weight_j; deterministic mean-one rescale only',
    }


def preference_scores(
    model:ExtraTreesClassifier,
    Xtest:np.ndarray,
    Xrefs:np.ndarray,
    ref_weights:np.ndarray,
)->np.ndarray:
    require(len(Xrefs)>0 and Xrefs.shape[1]==FEATURE_DIM,'empty/bad reference panel')
    rw=np.asarray(ref_weights,dtype=np.float64)
    require(rw.shape==(len(Xrefs),) and np.all(np.isfinite(rw)) and np.all(rw>0),'invalid reference weights')
    rw=rw/float(np.sum(rw))
    out=np.zeros(len(Xtest),dtype=np.float64)
    for start in range(0,len(Xtest),64):
        xt=Xtest[start:start+64]
        d=(xt[:,None,:]-Xrefs[None,:,:]).reshape(-1,FEATURE_DIM)
        pf=positive_probability(model,d)
        pr=positive_probability(model,-d)
        pref=0.5*(pf+(1.0-pr))
        pref=pref.reshape(len(xt),len(Xrefs))
        out[start:start+len(xt)]=np.sum(pref*rw[None,:],axis=1)
    require(np.all(np.isfinite(out)) and np.all((out>=0.0)&(out<=1.0)),'invalid pairwise preference scores')
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

    # Exact repaired v22-v25 scientific pretruth identity must hold before truth is read.
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

    ranker=v23.load_module(a.ranker_source,'frozen_839_groupdense_pairwise_recovery')
    route_data={}; Xs=[]; base_targets=[]; groups=[]; route_offsets={}; cursor=0

    # Reproduce the exact #1004 family predicate and strict group identity first.
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
    base_weights=np.asarray(ranker.grouped_weights(groups),dtype=np.float64)
    require(base_weights.shape==(cursor,) and np.all(np.isfinite(base_weights)) and np.all(base_weights>0),'invalid exact grouped weights')
    totals={}
    for i,g in enumerate(groups): totals[g]=float(totals.get(g,0.0)+base_weights[i])
    require(len({round(v,12) for v in totals.values()})==1,'exact grouped weights no longer equalize group mass')

    oof=np.zeros(cursor,dtype=np.float64); fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold
        require(tr.any() and te.any(),f'empty grouped fold {fold}')
        require(np.unique(yall[tr]).size==2,f'training fold {fold} lacks both classes')
        xp,yp,wp,pdiag=build_pair_training(Xall,yall,groups,base_weights,tr)
        model=pair_model(); model.fit(xp,yp,sample_weight=wp)
        refs=np.where(tr)[0]
        oof[te]=preference_scores(model,Xall[te],Xall[refs],base_weights[refs])
        train_groups={groups[i] for i in np.where(tr)[0]}; test_groups={groups[i] for i in np.where(te)[0]}
        require(train_groups.isdisjoint(test_groups),f'group leakage in fold {fold}')
        fold_diag.append({
            'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),
            'train_groups':len(train_groups),'test_groups':len(test_groups),
            'train_positive_groups':len({groups[i] for i in np.where(tr & (yall==1))[0]}),
            'test_positive_groups':len({groups[i] for i in np.where(te & (yall==1))[0]}),
            'reference_examples':int(len(refs)),'reference_weighting':'exact #839 inverse strict-group weights',
            'test_score_mean':float(np.mean(oof[te])),'test_score_min':float(np.min(oof[te])),'test_score_max':float(np.max(oof[te])),
            **pdiag,
        })

    variants={}; control_panels=[]; order_diag={}; target_diag={}
    for route in ROUTES:
        lo,hi=route_offsets[route]; rd=route_data[route]; ids=rd['ids']; scores=oof[lo:hi]
        route_y=yall[lo:hi]; route_base=base_all[lo:hi]; route_groups=groups[lo:hi]
        tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
        idx=ranker.diversity_order(scores,rd['centroids'],0.8,1.0,tie)
        pair_order=[ids[i] for i in idx]
        v19order=list(map(str,rd['meta']['v19_order']))
        fused=list(v23.v19.fusion_orders(pair_order,v19order)['rank_sum'])
        variants[route]={VARIANT:v23.rerank(rd['families'],fused),'v19_control':v23.rerank(rd['families'],v19order)}
        positive_groups={g for i,g in enumerate(route_groups) if int(route_y[i])==1 and g.startswith('SHOWER/')}
        base_positive_groups={g for i,g in enumerate(route_groups) if int(route_base[i])==1 and g.startswith('SHOWER/')}
        require(base_positive_groups.issubset(positive_groups),f'{route} densified target lost a base-positive group')
        target_diag[route]={
            'families':len(ids),'eligible_recurrent_showers':len(rd['eligible']),
            'base_balanced_recovery_positive_families':int(np.sum(route_base==1)),
            'densified_group_positive_families':int(np.sum(route_y==1)),
            'densified_added_positive_fragments':int(np.sum((route_y==1)&(route_base==0))),
            'recoverable_strict_shower_groups_present_in_route':len(positive_groups),
            'base_positive_strict_shower_groups_present_in_route':len(base_positive_groups),
            'target_definition':'exact #1004 group-dense two-year recoverability target',
        }
        order_diag[route]={
            'oof_pairwise_preference_sha256':v23.array_sha(scores),
            'pairwise_diversity_order_sha256':hashlib.sha256('\n'.join(pair_order).encode()).hexdigest(),
            'fused_order_sha256':hashlib.sha256('\n'.join(fused).encode()).hexdigest(),
            'diversity':{'lambda':0.8,'scale':1.0},
            'fusion':'parameter-free equal rank-sum with exact v19',
            'pairwise_only_order_evaluated_as_promotion_candidate':False,
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

    full_freeze={'verdict':'NOT_FROZEN_GROUPDENSE_PAIRWISE_RECOVERY_OOF_FAIL','model_sha256':None,'reference_features_sha256':None,'reference_weights_sha256':None}
    if passed:
        full_mask=np.ones(cursor,dtype=bool)
        xp,yp,wp,pdiag=build_pair_training(Xall,yall,groups,base_weights,full_mask)
        full=pair_model(); full.fit(xp,yp,sample_weight=wp); full.set_params(n_jobs=1)
        mp=a.output/'sonotaco_groupdense_pairwise_recovery_classifier.joblib'
        rp=a.output/'sonotaco_groupdense_pairwise_reference_features.npy'
        rw=a.output/'sonotaco_groupdense_pairwise_reference_weights.npy'
        joblib.dump(full,mp); np.save(rp,Xall,allow_pickle=False); np.save(rw,base_weights,allow_pickle=False)
        full_freeze={
            'verdict':'PASS_FULL_EXPOSED_SONOTACO_GROUPDENSE_PAIRWISE_RECOVERY_MODEL_FREEZE',
            'model_sha256':v23.sha(mp),'reference_features_sha256':v23.sha(rp),'reference_weights_sha256':v23.sha(rw),
            'feature_dimension':FEATURE_DIM,'training_examples':cursor,'training_groups':len(set(groups)),
            'positive_examples':int(np.sum(yall==1)),'positive_groups':len({groups[i] for i in range(cursor) if int(yall[i])==1}),
            'target_sha256':v23.array_sha(yall),'group_weight_sha256':v23.array_sha(base_weights),
            'training_pair_diagnostics':pdiag,
            'model':{'kind':'ExtraTreesClassifier','n_estimators':600,'max_depth':4,'min_samples_leaf':5,'max_features':None,'random_state':20260809},
            'in_sample_full_fit_score_used_for_promotion':False,
        }
    (a.output/'GROUPDENSE_PAIRWISE_RECOVERY_FULL_MODEL_FREEZE.json').write_text(json.dumps(full_freeze,indent=2,sort_keys=True)+'\n')

    result={
        'scientific_stage':'EXPOSED_SONOTACO_GROUPDENSE_PAIRWISE_RECOVERY_OOF_RANKING_DEVELOPMENT_V1',
        'verdict':'PASS_GROUPDENSE_PAIRWISE_RECOVERY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_GROUPDENSE_PAIRWISE_RECOVERY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'sole_scientific_change_from_1004':'pointwise ExtraTrees group-recoverability classification -> all positive-vs-negative strict-group pairwise preference objective using the same group-dense target',
        'feature_dimension':FEATURE_DIM,'recovery_f1_threshold':RECOVERY_F1_THRESHOLD,
        'threshold_selected_from_result':False,'candidate_membership_changed':False,'pretruth_feature_changed':False,
        'strict_whole_shower_oof':True,'shared_model_across_routes':True,'group_target_shared_across_routes':True,
        'pairwise_model':{'kind':'ExtraTreesClassifier','n_estimators':600,'max_depth':4,'min_samples_leaf':5,'max_features':None,'random_state':20260809},
        'pair_training':'all positive-family vs negative-family pairs from OOF training groups, both orientations',
        'pair_weighting':'product of exact #839 inverse-group family weights; deterministic mean-one normalization only',
        'reference_scoring':'antisymmetrized pairwise win probability against all fold-training families, weighted by exact #839 inverse-group weights',
        'class_weight_used':False,'resampling_used':False,'probability_calibration_used':False,'pair_subsampling_used':False,
        'diversity':{'lambda':0.8,'scale':1.0},'fusion':'parameter-free equal rank-sum with exact v19',
        'promotion_variant':VARIANT,'panel_wins':wins,'all_panel_win':passed,'panels':panels,
        'v19_control_panels':control_panels,'target_diagnostics':target_diag,'fold_diagnostics':fold_diag,'order_diagnostics':order_diag,
        'full_model_freeze':full_freeze,
        'feature_search':False,'target_search':False,'model_search':False,'hyperparameter_search':False,'pair_weight_search':False,'pair_threshold_search':False,'reference_search':False,'class_weight_search':False,'resampling_search':False,'calibration_search':False,'fusion_search':False,'diversity_search':False,'source_quota_selected':False,'post_result_second_search':False,
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0],
    }
    (a.output/'SONOTACO_GROUPDENSE_PAIRWISE_RECOVERY_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'target_diagnostics':target_diag,'panels':panels,'full_model_freeze':full_freeze},indent=2,sort_keys=True,allow_nan=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
