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
FEATURE_DIM=71
RECOVERY=0.5
RANKER_SOURCE_SHA=v24.RANKER_SOURCE_SHA
VARIANT='v32_leaf_support_presence_v19_rank_sum'
V24_EXPECT={
    ('sugar',2013):(0.27806630131631344,16),
    ('sugar',2014):(0.32869544907104964,17),
    ('hdbscan',2013):(0.14257102406283795,10),
    ('hdbscan',2014):(0.12833942693327394,7),
}


def require(ok:bool,msg:str)->None:
    if not ok:
        raise RuntimeError(msg)


def leaf_support_fraction(model:Any,Xtr:np.ndarray,ytr:np.ndarray,Xte:np.ndarray)->np.ndarray:
    train_leaf=np.asarray(model.apply(Xtr))
    test_leaf=np.asarray(model.apply(Xte))
    require(train_leaf.ndim==2 and test_leaf.ndim==2 and train_leaf.shape[1]==test_leaf.shape[1], 'unexpected forest leaf matrices')
    require(train_leaf.shape[1]==600, f'exact v24 tree count changed: {train_leaf.shape[1]}')
    positive=np.asarray(ytr>RECOVERY,dtype=bool)
    require(positive.any(), 'OOF training fold has no annual-positive family')
    counts=np.zeros(len(Xte),dtype=np.int32)
    for t in range(train_leaf.shape[1]):
        positive_leaves=set(map(int,train_leaf[positive,t].tolist()))
        require(positive_leaves, f'tree {t} has no annual-positive training leaf')
        counts += np.fromiter((int(int(x) in positive_leaves) for x in test_leaf[:,t]),dtype=np.int8,count=len(Xte))
    out=counts.astype(np.float64)/float(train_leaf.shape[1])
    require(out.shape==(len(Xte),) and np.all(np.isfinite(out)) and np.all((out>=0)&(out<=1)), 'invalid leaf-support fraction')
    return out


def full_positive_leaf_sets(model:Any,X:np.ndarray,y:np.ndarray)->list[list[int]]:
    leaf=np.asarray(model.apply(X))
    require(leaf.ndim==2 and leaf.shape[1]==600,'unexpected full forest leaf matrix')
    positive=np.asarray(y>RECOVERY,dtype=bool)
    require(positive.any(),'full fit has no annual-positive family')
    return [sorted(set(map(int,leaf[positive,t].tolist()))) for t in range(leaf.shape[1])]


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--payload-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v22.sha(a.ranker_source)==RANKER_SOURCE_SHA,'#839 ranker source changed')

    truth={}; frozen={}
    for route,year in PANELS:
        truth[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())
    ranker=v22.load_module(a.ranker_source,'frozen_839_v32_leaf_support')

    data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; offsets={}; cursor=0
    for route in ROUTES:
        root=a.payload_root/route
        meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and meta['feature_dimension']==FEATURE_DIM and fp['truth_accessed'] is False,f'{route} invalid immutable v24 pretruth payload')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']
        require([str(f['family_id']) for f in fams]==ids,f'{route} family alignment changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),f'{route} immutable array shape changed')
        require(v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],f'{route} immutable array hash changed')
        by={y:truth[(route,y)] for y in YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014])
        base=[v22.family_truth(f,hidden,eligible) for f in fams]
        y13=[]; y14=[]; rg=[]
        for i,(f,t) in enumerate(zip(fams,base)):
            label=t['best_label']; rg.append(('SHOWER/'+str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None:
                q13=q14=0.0
            else:
                q13,q14=v24.annual_f1_for_fixed_label(f,str(label),by)
            y13.append(float(q13)); y14.append(float(q14))
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids)
        Xs.append(X); y13s.append(np.asarray(y13,dtype=np.float64)); y14s.append(np.asarray(y14,dtype=np.float64)); groups.extend(rg)
        data[route]={'meta':meta,'fams':fams,'ids':ids,'centroids':C,'y13':np.asarray(y13,float),'y14':np.asarray(y14,float)}

    Xall=np.vstack(Xs); y13=np.concatenate(y13s); y14=np.concatenate(y14s); groups=list(map(str,groups))
    require(Xall.shape==(cursor,FEATURE_DIM) and len(y13)==len(y14)==len(groups)==cursor,'stacked v32 input mismatch')
    folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],dtype=int)
    weights=np.asarray(ranker.grouped_weights(groups),dtype=np.float64)
    require(weights.shape==(cursor,) and np.all(np.isfinite(weights)) and np.all(weights>0),'invalid inherited #839 weights')

    pred13=np.zeros(cursor); pred14=np.zeros(cursor); sup13=np.zeros(cursor); sup14=np.zeros(cursor); fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold
        require(tr.any() and te.any(),f'empty fold {fold}')
        train_groups={groups[i] for i in np.where(tr)[0]}; test_groups={groups[i] for i in np.where(te)[0]}
        require(train_groups.isdisjoint(test_groups),f'whole-shower leakage fold {fold}')
        require(np.any(y13[tr]>RECOVERY) and np.any(y14[tr]>RECOVERY),f'fold {fold} lacks annual-positive training support')
        m13=ranker.model(); m14=ranker.model()
        m13.fit(Xall[tr],y13[tr],sample_weight=weights[tr]); m14.fit(Xall[tr],y14[tr],sample_weight=weights[tr])
        pred13[te]=m13.predict(Xall[te]); pred14[te]=m14.predict(Xall[te])
        sup13[te]=leaf_support_fraction(m13,Xall[tr],y13[tr],Xall[te]); sup14[te]=leaf_support_fraction(m14,Xall[tr],y14[tr],Xall[te])
        fold_diag.append({
            'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),
            'train_groups':len(train_groups),'test_groups':len(test_groups),
            'annual_positive_training_families_2013':int(np.sum(y13[tr]>RECOVERY)),
            'annual_positive_training_families_2014':int(np.sum(y14[tr]>RECOVERY)),
            'support_2013_mean':float(np.mean(sup13[te])),'support_2014_mean':float(np.mean(sup14[te])),
        })

    require(np.all(np.isfinite(pred13)) and np.all(np.isfinite(pred14)) and np.all(np.isfinite(sup13)) and np.all(np.isfinite(sup14)),'nonfinite OOF values')
    v24_score=np.minimum(pred13,pred14); v32_score=np.minimum(sup13,sup14)
    routes_out={}; controls=[]; order_diag={}
    for route in ROUTES:
        lo,hi=offsets[route]; rd=data[route]; ids=rd['ids']; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]; v19_order=list(map(str,rd['meta']['v19_order']))
        cidx=ranker.diversity_order(v24_score[lo:hi],rd['centroids'],0.8,1.0,tie); corder=[ids[i] for i in cidx]; cfused=list(v19.fusion_orders(corder,v19_order)['rank_sum']); control_fams=v22.rerank(rd['fams'],cfused)
        sidx=ranker.diversity_order(v32_score[lo:hi],rd['centroids'],0.8,1.0,tie); sorder=[ids[i] for i in sidx]; sfused=list(v19.fusion_orders(sorder,v19_order)['rank_sum']); successor_fams=v22.rerank(rd['fams'],sfused)
        routes_out[route]={'control':control_fams,'successor':successor_fams}
        order_diag[route]={
            'support_2013_sha256':v22.array_sha(sup13[lo:hi]),'support_2014_sha256':v22.array_sha(sup14[lo:hi]),'combined_support_sha256':v22.array_sha(v32_score[lo:hi]),
            'leaf_support_diversity_order_sha256':hashlib.sha256('\n'.join(sorder).encode()).hexdigest(),'fused_order_sha256':hashlib.sha256('\n'.join(sfused).encode()).hexdigest(),
        }
        for year in YEARS:
            budget=int(frozen[(route,year)]['candidate_budget']['comparator_budget']); cur=v22.evaluate(control_fams,truth[(route,year)],budget); exp=V24_EXPECT[(route,year)]
            require(abs(float(cur['macro_f1'])-exp[0])<1e-12 and int(cur['recovered_f1_gt_0_5'])==exp[1],f'exact v24 control mismatch {route} {year}')
            controls.append({'comparator':route,'year':year,'macro_f1':float(cur['macro_f1']),'recovered_f1_gt_0_5':int(cur['recovered_f1_gt_0_5']),'budget':budget})

    panels=[]
    for route,year in PANELS:
        budget=int(frozen[(route,year)]['candidate_budget']['comparator_budget']); cur=v22.evaluate(routes_out[route]['successor'],truth[(route,year)],budget); lit=frozen[(route,year)]['comparator_summary']; cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5'])
        panels.append({'comparator':route,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':cm/lm,'recovery_ratio':cr/lr,'superiority_pair_pass':bool(cm>lm and cr>=lr)})
    wins=sum(int(x['superiority_pair_pass']) for x in panels); passed=bool(wins==4)

    freeze={'verdict':'NOT_FROZEN_V32_LEAF_SUPPORT_OOF_FAIL','head_2013_sha256':None,'head_2014_sha256':None,'positive_leaf_sets_2013_sha256':None,'positive_leaf_sets_2014_sha256':None}
    if passed:
        f13=ranker.model(); f14=ranker.model(); f13.fit(Xall,y13,sample_weight=weights); f14.fit(Xall,y14,sample_weight=weights); f13.set_params(n_jobs=1); f14.set_params(n_jobs=1)
        p13=a.output/'v32_leaf_support_head_2013.joblib'; p14=a.output/'v32_leaf_support_head_2014.joblib'; joblib.dump(f13,p13); joblib.dump(f14,p14)
        l13=a.output/'v32_positive_leaf_sets_2013.json'; l14=a.output/'v32_positive_leaf_sets_2014.json'; l13.write_text(json.dumps(full_positive_leaf_sets(f13,Xall,y13),separators=(',',':'))+'\n'); l14.write_text(json.dumps(full_positive_leaf_sets(f14,Xall,y14),separators=(',',':'))+'\n')
        freeze={'verdict':'PASS_FULL_EXPOSED_V32_LEAF_SUPPORT_MODEL_FREEZE','head_2013_sha256':v22.sha(p13),'head_2014_sha256':v22.sha(p14),'positive_leaf_sets_2013_sha256':v22.sha(l13),'positive_leaf_sets_2014_sha256':v22.sha(l14),'feature_dimension':FEATURE_DIM,'training_examples':cursor,'in_sample_score_used_for_promotion':False}
    (a.output/'V32_LEAF_SUPPORT_MODEL_FREEZE.json').write_text(json.dumps(freeze,indent=2,sort_keys=True)+'\n')

    result={
        'scientific_stage':'EXPOSED_SONOTACO_V32_EXACT_V24_LEAF_SUPPORT_PRESENCE_OOF_V1',
        'verdict':'PASS_V32_LEAF_SUPPORT_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V32_LEAF_SUPPORT_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT',
        'promotion_variant':VARIANT,'panel_wins':wins,'all_panel_win':passed,'panels':panels,'v24_control_reproduction':controls,'fold_diagnostics':fold_diag,'order_diagnostics':order_diag,
        'feature_dimension':FEATURE_DIM,'recovery_f1_threshold':RECOVERY,'score_definition':'fraction of exact v24 trees whose held-out leaf contains >=1 fold-training family with annual F1>0.5','positive_weight_fraction_used':False,'regression_prediction_used_in_successor_score':False,'geometry_margin_used':False,'annual_combiner':'min(support_2013,support_2014)','tree_count':600,
        'candidate_membership_changed':False,'pretruth_feature_changed':False,'strict_whole_shower_oof':True,'diversity':{'lambda':0.8,'scale':1.0},'fusion':'one equal rank-sum with exact v19',
        'support_threshold_search':False,'positive_count_search':False,'tree_subset_search':False,'target_threshold_search':False,'model_search':False,'feature_search':False,'annual_combiner_search':False,'diversity_search':False,'fusion_search':False,'source_quota_selected':False,'post_result_second_search':False,
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0],'full_model_freeze':freeze,
    }
    (a.output/'V32_LEAF_SUPPORT_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'panels':panels,'full_model_freeze':freeze},indent=2,sort_keys=True,allow_nan=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
