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
VARIANTS=('pairwise_oof_quality','pairwise_oof_v19_rank_sum')
PREFERENCE={'pairwise_oof_quality':2,'pairwise_oof_v19_rank_sum':1}


def require(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)


def pair_model()->ExtraTreesClassifier:
    return ExtraTreesClassifier(
        n_estimators=600,max_depth=4,min_samples_leaf=5,max_features=None,
        random_state=20260809,n_jobs=-1,
    )


def training_representatives(
    train_idx: np.ndarray,
    route_names: list[str],
    groups: list[str],
    family_ids: list[str],
    quality: np.ndarray,
)->list[int]:
    units: dict[tuple[str,str],list[int]]=defaultdict(list)
    for i in np.where(train_idx)[0].tolist():
        units[(route_names[i],groups[i])].append(i)
    reps=[]
    for key in sorted(units):
        choices=units[key]
        # Highest balanced quality; stable ID is deterministic final tie-break.
        best=sorted(choices,key=lambda i:(-float(quality[i]),str(family_ids[i])))[0]
        reps.append(best)
    return reps


def build_pair_training(
    X: np.ndarray,
    quality: np.ndarray,
    groups: list[str],
    reps: list[int],
)->tuple[np.ndarray,np.ndarray,np.ndarray,dict[str,int]]:
    diffs=[]; labels=[]; weights=[]; unordered=0; skipped_same_group=0; skipped_tie=0
    for a_pos in range(len(reps)):
        i=reps[a_pos]
        for b_pos in range(a_pos+1,len(reps)):
            j=reps[b_pos]
            if groups[i]==groups[j]:
                skipped_same_group+=1; continue
            qi=float(quality[i]); qj=float(quality[j])
            if qi==qj:
                skipped_tie+=1; continue
            unordered+=1; d=np.asarray(X[i]-X[j],dtype=np.float64); w=abs(qi-qj); win=1 if qi>qj else 0
            diffs.append(d); labels.append(win); weights.append(w)
            diffs.append(-d); labels.append(1-win); weights.append(w)
    require(unordered>0,'no informative pairwise training comparisons')
    xp=np.asarray(diffs,dtype=np.float64); yp=np.asarray(labels,dtype=np.int8); wp=np.asarray(weights,dtype=np.float64)
    require(xp.ndim==2 and xp.shape[1]==FEATURE_DIM and len(xp)==len(yp)==len(wp),'bad pairwise training shape')
    require(set(yp.tolist())=={0,1} and np.all(np.isfinite(xp)) and np.all(np.isfinite(wp)) and np.all(wp>0),'invalid pairwise training data')
    return xp,yp,wp,{'representatives':len(reps),'informative_unordered_pairs':unordered,'oriented_pairs':len(yp),'skipped_same_group_pairs':skipped_same_group,'skipped_equal_quality_pairs':skipped_tie}


def preference_scores(model: ExtraTreesClassifier,Xtest: np.ndarray,Xrefs: np.ndarray)->np.ndarray:
    require(len(Xrefs)>0,'empty preference reference panel')
    out=np.zeros(len(Xtest),dtype=np.float64)
    for start in range(0,len(Xtest),64):
        xt=Xtest[start:start+64]
        d=(xt[:,None,:]-Xrefs[None,:,:]).reshape(-1,FEATURE_DIM)
        pf=model.predict_proba(d)[:,1]
        pr=model.predict_proba(-d)[:,1]
        pref=0.5*(pf + (1.0-pr))
        out[start:start+len(xt)]=pref.reshape(len(xt),len(Xrefs)).mean(axis=1)
    require(np.all(np.isfinite(out)) and np.all((out>=0.0)&(out<=1.0)),'invalid preference scores')
    return out


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--sugar-root',type=Path,required=True); p.add_argument('--hdbscan-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v23.sha(a.ranker_source)==RANKER_SOURCE_SHA,'#839 ranker source changed')
    roots={'sugar':a.sugar_root,'hdbscan':a.hdbscan_root}

    # Same repaired-v23/v24 scientific pretruth identity guard.
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

    ranker=v23.load_module(a.ranker_source,'frozen_839_v25_diversity')
    route_data={}; Xs=[]; qualities=[]; groups=[]; route_names=[]; all_ids=[]; route_offsets={}; cursor=0; target_diag={}
    for route in ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fam_payload=json.loads((root/'family_memberships.json').read_text())
        require(meta['feature_dimension']==FEATURE_DIM and meta['truth_accessed'] is False,'invalid pretruth manifest')
        require(fam_payload['truth_accessed'] is False,'membership payload already truth-bearing')
        ids=list(map(str,meta['family_ids'])); fams=fam_payload['families']; require([str(f['family_id']) for f in fams]==ids,'family alignment changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),'pretruth array shape changed')
        require(v23.array_sha(X)==meta['feature_sha256'] and v23.array_sha(C)==meta['centroid_sha256'],'pretruth internal array hash changed')

        by_year={y:truth_year[(route,y)] for y in YEARS}; eligible=v23.eligible_from_year_truth(by_year); hidden={}; hidden.update(by_year[2013]); hidden.update(by_year[2014])
        require(len(hidden)==len(by_year[2013])+len(by_year[2014]),f'{route} duplicate IDs across years')
        best=[v23.combined_best_label(f,hidden,eligible) for f in fams]
        q=[]; gs=[]; per_year=[]
        for i,(f,b) in enumerate(zip(fams,best)):
            label=b['best_label']
            if label is None:
                f13=f14=0.0; group=f'NEG/{route}/{ids[i]}'
            else:
                f13=v23.year_f1_for_label(f,by_year[2013],label); f14=v23.year_f1_for_label(f,by_year[2014],label); group='SHOWER/'+str(label)
            q.append(float(min(f13,f14))); gs.append(group); per_year.append((float(f13),float(f14)))
        qa=np.asarray(q,dtype=np.float64); require(np.all(np.isfinite(qa)) and np.all((qa>=0)&(qa<=1)),'invalid balanced quality')
        route_offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); qualities.append(qa); groups.extend(gs); route_names.extend([route]*len(ids)); all_ids.extend(ids)
        route_data[route]={'meta':meta,'families':fams,'ids':ids,'centroids':C,'best':best,'per_year':per_year,'eligible':eligible}
        target_diag[route]={'families':len(ids),'eligible_recurrent_showers':len(eligible),'families_with_best_recurrent_label':int(sum(b['best_label'] is not None for b in best)),'nonzero_balanced_quality':int(np.sum(qa>0)),'quality_mean':float(np.mean(qa)),'quality_median':float(np.median(qa)),'quality_max':float(np.max(qa)),'quality_definition':'min(F1_2013,F1_2014) for exact v22-v24 best_label'}

    Xall=np.vstack(Xs); qall=np.concatenate(qualities); groups=list(map(str,groups)); route_names=list(map(str,route_names)); all_ids=list(map(str,all_ids))
    require(Xall.shape==(cursor,FEATURE_DIM) and len(qall)==len(groups)==len(route_names)==len(all_ids)==cursor,'stacked training shape mismatch')
    folds=np.asarray([v23.v1.deterministic_fold(g) for g in groups],dtype=int); oof=np.zeros(cursor,dtype=np.float64); fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; require(tr.any() and te.any(),f'empty grouped fold {fold}')
        reps=training_representatives(tr,route_names,groups,all_ids,qall)
        xp,yp,wp,pdiag=build_pair_training(Xall,qall,groups,reps)
        m=pair_model(); m.fit(xp,yp,sample_weight=wp)
        oof[te]=preference_scores(m,Xall[te],Xall[reps])
        train_groups=set(groups[i] for i in np.where(tr)[0]); test_groups=set(groups[i] for i in np.where(te)[0]); require(train_groups.isdisjoint(test_groups),f'group leakage in fold {fold}')
        fold_diag.append({'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'train_groups':len(train_groups),'test_groups':len(test_groups),**pdiag,'test_score_mean':float(np.mean(oof[te])),'test_score_min':float(np.min(oof[te])),'test_score_max':float(np.max(oof[te]))})

    variants={}; control_panels=[]; order_diag={}
    for route in ROUTES:
        lo,hi=route_offsets[route]; rd=route_data[route]; ids=rd['ids']; scores=oof[lo:hi]
        tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
        idx=ranker.diversity_order(scores,rd['centroids'],0.8,1.0,tie); qorder=[ids[i] for i in idx]
        v19order=list(map(str,rd['meta']['v19_order'])); fused=list(v23.v19.fusion_orders(qorder,v19order)['rank_sum'])
        variants[route]={'pairwise_oof_quality':v23.rerank(rd['families'],qorder),'pairwise_oof_v19_rank_sum':v23.rerank(rd['families'],fused),'v19_control':v23.rerank(rd['families'],v19order)}
        order_diag[route]={'oof_preference_sha256':v23.array_sha(scores),'quality_order_sha256':hashlib.sha256('\n'.join(qorder).encode()).hexdigest(),'fused_order_sha256':hashlib.sha256('\n'.join(fused).encode()).hexdigest(),'preference_reference':'fold training representatives only','pairwise_antisymmetrization':True}
        for year in YEARS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget']); cur=v23.evaluate(variants[route]['v19_control'],truth_year[(route,year)],budget); exp=V19_METRICS[(route,year)]
            require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'v19 fixed-membership control mismatch {route} {year}')
            control_panels.append({'comparator':route,'year':year,**cur})

    rows=[]
    for variant in VARIANTS:
        panels=[]
        for route,year in PANELS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget']); cur=v23.evaluate(variants[route][variant],truth_year[(route,year)],budget); lit=frozen_eval[(route,year)]['comparator_summary']
            cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5']); mr=cm/lm if lm else float('inf'); rr=cr/lr if lr else float('inf'); win=bool(cm>lm and cr>=lr)
            panels.append({'comparator':route,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':mr,'recovery_ratio':rr,'superiority_pair_pass':win})
        wins=sum(int(x['superiority_pair_pass']) for x in panels); minm=min(x['macro_f1_ratio'] for x in panels); minr=min(x['recovery_ratio'] for x in panels); meanm=float(np.mean([x['macro_f1_ratio'] for x in panels])); meanr=float(np.mean([x['recovery_ratio'] for x in panels]))
        rows.append({'variant':variant,'panel_wins':wins,'all_panel_win':wins==4,'min_macro_f1_ratio':minm,'min_recovery_ratio':minr,'mean_macro_f1_ratio':meanm,'mean_recovery_ratio':meanr,'selection_key':[wins,minm,minr,meanm,meanr,PREFERENCE[variant]],'panels':panels})
    winner=max(rows,key=lambda r:tuple(r['selection_key'])); passed=bool(winner['all_panel_win'])

    full_freeze={'verdict':'NOT_FROZEN_V25_OOF_FAIL','model_sha256':None,'reference_sha256':None}
    if passed:
        all_mask=np.ones(cursor,dtype=bool); reps=training_representatives(all_mask,route_names,groups,all_ids,qall); xp,yp,wp,pdiag=build_pair_training(Xall,qall,groups,reps); full=pair_model(); full.fit(xp,yp,sample_weight=wp); full.set_params(n_jobs=1)
        mp=a.output/'v25_sonotaco_pairwise_ranker.joblib'; rp=a.output/'v25_sonotaco_reference_features.npy'; joblib.dump(full,mp); np.save(rp,Xall[reps],allow_pickle=False)
        full_freeze={'verdict':'PASS_V25_FULL_SONOTACO_PAIRWISE_MODEL_FREEZE','model_sha256':v23.sha(mp),'reference_sha256':v23.sha(rp),'feature_dimension':FEATURE_DIM,'reference_count':len(reps),'training_examples':cursor,'training_groups':len(set(groups)),'training_pair_diagnostics':pdiag,'balanced_quality_sha256':v23.array_sha(qall),'in_sample_full_fit_score_used_for_promotion':False}
    (a.output/'V25_FULL_MODEL_FREEZE.json').write_text(json.dumps(full_freeze,indent=2,sort_keys=True)+'\n')

    result={'scientific_stage':'V25_EXPOSED_SONOTACO_STRICT_GROUP_PAIRWISE_OOF_RANKING_DEVELOPMENT','sole_scientific_change_from_v24':'squared-error regression -> group-balanced pairwise preference objective','feature_dimension':FEATURE_DIM,'v22_v24_pretruth_scientific_identity_pass':True,'same_shower_all_fragments_both_routes_same_fold':True,'pairwise_quality_definition':'min(F1_2013,F1_2014) exact v23 quality','pairwise_model_search':False,'pair_threshold_search':False,'pair_weighting':'abs quality difference','folds':fold_diag,'target_diagnostics':target_diag,'order_diagnostics':order_diag,'v19_control_reproduction_pass':True,'v19_control':control_panels,'all_results':rows,'winner':winner,'verdict':'PASS_V25_EXPOSED_PAIRWISE_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V25_PAIRWISE_OOF_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','full_model_freeze':full_freeze,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','full_fit_in_sample_score_used':False,'post_result_second_search':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False}
    (a.output/'V25_EXPOSED_PAIRWISE_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'winner':winner,'full_model_freeze':full_freeze,'folds':fold_diag,'target_diagnostics':target_diag},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
