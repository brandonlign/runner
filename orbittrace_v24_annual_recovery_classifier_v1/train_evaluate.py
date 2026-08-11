#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier

from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as two

ROUTES=('sugar','hdbscan')
YEARS=(2013,2014)
PANELS=(('sugar',2013),('sugar',2014),('hdbscan',2013),('hdbscan',2014))
FEATURE_DIM=71
RANKER_SOURCE_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'
RECOVERY_F1_THRESHOLD=0.5
VARIANT='annual_recovery_classifier_v19_rank_sum'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def classifier()->ExtraTreesClassifier:
    return ExtraTreesClassifier(n_estimators=600,max_depth=4,min_samples_leaf=5,max_features=None,random_state=20260809,n_jobs=1,class_weight='balanced')


def positive_probability(model:ExtraTreesClassifier,X:np.ndarray)->np.ndarray:
    require(set(map(int,model.classes_.tolist()))=={0,1},f'classifier classes changed: {model.classes_}')
    j=int(np.where(model.classes_==1)[0][0]); out=np.asarray(model.predict_proba(X)[:,j],dtype=np.float64)
    require(out.shape==(len(X),) and np.all(np.isfinite(out)) and np.all((out>=0)&(out<=1)),'invalid classifier probabilities')
    return out


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--payload-root',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(two.v22.sha(a.ranker_source)==RANKER_SOURCE_SHA,'#839 ranker source changed')
    truth_year={}; frozen={}
    for route,year in PANELS:
        truth_year[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text()); frozen[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())
    ranker=two.v22.load_module(a.ranker_source,'frozen_839_annual_recovery_classifier')

    data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; offsets={}; cursor=0; target_diag={}
    for route in ROUTES:
        root=a.payload_root/route; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['feature_dimension']==FEATURE_DIM and meta['truth_accessed'] is False and fp['truth_accessed'] is False,f'{route} invalid immutable pretruth payload')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']; require([str(f['family_id']) for f in fams]==ids,f'{route} family alignment changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False); require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),f'{route} pretruth array shape changed')
        require(two.v22.array_sha(X)==meta['feature_sha256'] and two.v22.array_sha(C)==meta['centroid_sha256'],f'{route} immutable array hash changed')
        by_year={y:truth_year[(route,y)] for y in YEARS}; eligible=two.v22.eligible_from_year_truth(by_year); hidden={**by_year[2013],**by_year[2014]}; truths=[two.v22.family_truth(f,hidden,eligible) for f in fams]
        y13=[]; y14=[]; gs=[]
        for i,(f,t) in enumerate(zip(fams,truths)):
            label=t['best_label']; gs.append(('SHOWER/'+str(label)) if label is not None else ('NEG/'+route+'/'+ids[i]))
            if not t['positive'] or label is None: q13=q14=0.0
            else: q13,q14=two.annual_f1_for_fixed_label(f,str(label),by_year)
            y13.append(int(q13>RECOVERY_F1_THRESHOLD)); y14.append(int(q14>RECOVERY_F1_THRESHOLD))
        a13=np.asarray(y13,dtype=np.int8); a14=np.asarray(y14,dtype=np.int8); require(set(np.unique(a13).tolist())=={0,1} and set(np.unique(a14).tolist())=={0,1},f'{route} annual target degenerate')
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); y13s.append(a13); y14s.append(a14); groups.extend(gs)
        data[route]={'ids':ids,'fams':fams,'C':C,'tie':list(map(int,meta['tie_rank'])),'v19':list(map(str,meta['v19_order']))}
        target_diag[route]={'families':len(ids),'eligible_recurrent_showers':len(eligible),'positive_2013_families':int(a13.sum()),'positive_2014_families':int(a14.sum()),'threshold':RECOVERY_F1_THRESHOLD,'group_assignment_changed_from_v22':False}

    X=np.vstack(Xs); y13=np.concatenate(y13s); y14=np.concatenate(y14s); groups=list(map(str,groups)); require(X.shape==(cursor,FEATURE_DIM) and len(y13)==len(y14)==len(groups)==cursor,'stacked shape mismatch')
    folds=np.asarray([two.v22.v1.deterministic_fold(g) for g in groups],dtype=int); weights=np.asarray(ranker.grouped_weights(groups),dtype=np.float64); p13=np.zeros(cursor); p14=np.zeros(cursor); fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; require(tr.any() and te.any(),f'empty fold {fold}'); require(set(np.unique(y13[tr]).tolist())=={0,1} and set(np.unique(y14[tr]).tolist())=={0,1},f'training fold {fold} lacks annual class')
        train_groups={groups[i] for i in np.where(tr)[0]}; test_groups={groups[i] for i in np.where(te)[0]}; require(train_groups.isdisjoint(test_groups),f'group leakage fold {fold}')
        m13=classifier(); m14=classifier(); m13.fit(X[tr],y13[tr],sample_weight=weights[tr]); m14.fit(X[tr],y14[tr],sample_weight=weights[tr]); p13[te]=positive_probability(m13,X[te]); p14[te]=positive_probability(m14,X[te])
        fold_diag.append({'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'train_groups':len(train_groups),'test_groups':len(test_groups),'train_positive_2013':int(y13[tr].sum()),'train_positive_2014':int(y14[tr].sum()),'test_positive_2013':int(y13[te].sum()),'test_positive_2014':int(y14[te].sum())})
    score=np.minimum(p13,p14); require(np.all(np.isfinite(score)),'nonfinite annual recovery OOF score')

    variants={}; v19_controls=[]; order_diag={}
    for route in ROUTES:
        lo,hi=offsets[route]; rd=data[route]; ids=rd['ids']; tie=[(rd['tie'][i],ids[i]) for i in range(len(ids))]; idx=ranker.diversity_order(score[lo:hi],rd['C'],0.8,1.0,tie); qorder=[ids[i] for i in idx]; fused=list(two.v19.fusion_orders(qorder,rd['v19'])['rank_sum'])
        variants[route]={VARIANT:two.v22.rerank(rd['fams'],fused),'v19':two.v22.rerank(rd['fams'],rd['v19'])}; order_diag[route]={'annual_recovery_diversity_order_sha256':hashlib.sha256('\n'.join(qorder).encode()).hexdigest(),'fused_order_sha256':hashlib.sha256('\n'.join(fused).encode()).hexdigest()}
        for year in YEARS:
            budget=int(frozen[(route,year)]['candidate_budget']['comparator_budget']); cur=two.v22.evaluate(variants[route]['v19'],truth_year[(route,year)],budget); exp=two.V19_METRICS[(route,year)]
            require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'v19 control mismatch {route} {year}'); v19_controls.append({'comparator':route,'year':year,**cur})

    panels=[]
    for route,year in PANELS:
        budget=int(frozen[(route,year)]['candidate_budget']['comparator_budget']); cur=two.v22.evaluate(variants[route][VARIANT],truth_year[(route,year)],budget); lit=frozen[(route,year)]['comparator_summary']; cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5'])
        panels.append({'comparator':route,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':cm/lm,'recovery_ratio':cr/lr,'superiority_pair_pass':bool(cm>lm and cr>=lr)})
    wins=sum(int(x['superiority_pair_pass']) for x in panels); passed=wins==4
    freeze={'verdict':'NOT_FROZEN_ANNUAL_RECOVERY_CLASSIFIER_OOF_FAIL'}
    if passed:
        f13=classifier(); f14=classifier(); f13.fit(X,y13,sample_weight=weights); f14.fit(X,y14,sample_weight=weights); pth13=a.output/'annual_recovery_2013.joblib'; pth14=a.output/'annual_recovery_2014.joblib'; joblib.dump(f13,pth13); joblib.dump(f14,pth14)
        freeze={'verdict':'PASS_FULL_EXPOSED_ANNUAL_RECOVERY_CLASSIFIER_FREEZE','head_2013_sha256':two.v22.sha(pth13),'head_2014_sha256':two.v22.sha(pth14),'feature_dimension':FEATURE_DIM,'training_examples':cursor,'in_sample_score_used_for_promotion':False}
    (a.output/'ANNUAL_RECOVERY_CLASSIFIER_FULL_MODEL_FREEZE.json').write_text(json.dumps(freeze,indent=2,sort_keys=True)+'\n')
    result={'scientific_stage':'V24_ANNUAL_FAMILY_RECOVERY_CLASSIFIER_STRICT_GROUP_OOF_V1','verdict':'PASS_ANNUAL_RECOVERY_CLASSIFIER_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_ANNUAL_RECOVERY_CLASSIFIER_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','promotion_variant':VARIANT,'panel_wins':wins,'all_panel_win':passed,'panels':panels,'target_diagnostics':target_diag,'fold_diagnostics':fold_diag,'order_diagnostics':order_diag,'v19_control_reproduction_pass':True,'v19_controls':v19_controls,'feature_dimension':FEATURE_DIM,'recovery_f1_threshold':RECOVERY_F1_THRESHOLD,'threshold_selected_from_result':False,'annual_combiner':'min(p2013,p2014)','class_weight':'balanced within each OOF training fold','candidate_membership_changed':False,'pretruth_feature_changed':False,'strict_whole_shower_oof':True,'diversity':{'lambda':0.8,'scale':1.0},'feature_search':False,'target_search':False,'threshold_search':False,'model_search':False,'hyperparameter_search':False,'class_weight_search':False,'calibration_search':False,'resampling_search':False,'annual_combiner_search':False,'fusion_search':False,'diversity_search':False,'source_quota_selected':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0],'full_model_freeze':freeze}
    (a.output/'ANNUAL_RECOVERY_CLASSIFIER_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'target_diagnostics':target_diag,'panels':panels,'full_model_freeze':freeze},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
