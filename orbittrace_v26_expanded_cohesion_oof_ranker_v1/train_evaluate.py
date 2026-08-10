#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np

from orbittrace_v23_worst_year_oof_ranker_v1 import train_evaluate as v23

ROUTES=v23.ROUTES
YEARS=v23.YEARS
PANELS=v23.PANELS
FEATURE_DIM=78
RANKER_SOURCE_SHA=v23.RANKER_SOURCE_SHA
V19_METRICS=v23.V19_METRICS
EXPECTED_V19_FAMILY_SHA=v23.EXPECTED_V19_FAMILY_SHA
VARIANTS=('expanded_cohesion_two_head_quality','expanded_cohesion_two_head_v19_rank_sum')
PREFERENCE={'expanded_cohesion_two_head_quality':2,'expanded_cohesion_two_head_v19_rank_sum':1}


def require(ok: bool,msg: str)->None:
    if not ok: raise RuntimeError(msg)


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--sugar-v22-root',type=Path,required=True); p.add_argument('--hdbscan-v22-root',type=Path,required=True)
    p.add_argument('--sugar-v26-root',type=Path,required=True); p.add_argument('--hdbscan-v26-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v23.sha(a.ranker_source)==RANKER_SOURCE_SHA,'#839 ranker source changed')
    v22roots={'sugar':a.sugar_v22_root,'hdbscan':a.hdbscan_v22_root}; v26roots={'sugar':a.sugar_v26_root,'hdbscan':a.hdbscan_v26_root}

    # All v26 feature bytes were frozen before truth; fail closed on their own manifests.
    for route in ROUTES:
        m=json.loads((v26roots[route]/'V26_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        require(m['scientific_stage']=='V26_EXPANDED_MEMBERSHIP_COHESION_PRETRUTH_FEATURE_FREEZE' and m['comparator']==route,'wrong v26 pretruth route')
        require(m['feature_dimension']==FEATURE_DIM and m['base_feature_dimension']==71 and m['expanded_cohesion_dimension']==7,'v26 feature definition changed')
        require(m['truth_accessed'] is False and m['target_information_access'] is False and m['maarsy_scientific_access'] is False and m['dms_scientific_access'] is False,'v26 pretruth firewall violation')
        x=np.load(v26roots[route]/'features_v26.npy',allow_pickle=False)
        require(x.shape==(len(m['family_ids']),FEATURE_DIM) and v23.array_sha(x)==m['feature_sha256'],'v26 feature payload identity failed')

    truth_year={}; frozen_eval={}
    for route,year in PANELS:
        truth_year[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    ranker=v23.load_module(a.ranker_source,'frozen_839_v26_train')
    route_data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; route_offsets={}; cursor=0; target_diag={}
    for route in ROUTES:
        base=json.loads((v22roots[route]/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fam_payload=json.loads((v22roots[route]/'family_memberships.json').read_text()); aug=json.loads((v26roots[route]/'V26_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        ids=list(map(str,base['family_ids'])); fams=fam_payload['families']; require([str(f['family_id']) for f in fams]==ids and list(map(str,aug['family_ids']))==ids,'family alignment changed')
        require(base['v19_family_sha256']==EXPECTED_V19_FAMILY_SHA[route] and fam_payload['truth_accessed'] is False,'v19 family identity changed')
        X=np.load(v26roots[route]/'features_v26.npy',allow_pickle=False); C=np.load(v22roots[route]/'centroids.npy',allow_pickle=False)
        require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),'v26 training array shape changed')

        by_year={y:truth_year[(route,y)] for y in YEARS}; eligible=v23.eligible_from_year_truth(by_year); hidden={}; hidden.update(by_year[2013]); hidden.update(by_year[2014]); require(len(hidden)==len(by_year[2013])+len(by_year[2014]),f'{route} duplicate IDs across years')
        best=[v23.combined_best_label(f,hidden,eligible) for f in fams]
        y13=[]; y14=[]; gs=[]
        for i,(f,b) in enumerate(zip(fams,best)):
            label=b['best_label']
            if label is None:
                f13=f14=0.0; group=f'NEG/{route}/{ids[i]}'
            else:
                f13=v23.year_f1_for_label(f,by_year[2013],label); f14=v23.year_f1_for_label(f,by_year[2014],label); group='SHOWER/'+str(label)
            y13.append(float(f13)); y14.append(float(f14)); gs.append(group)
        y13a=np.asarray(y13,dtype=np.float64); y14a=np.asarray(y14,dtype=np.float64)
        for name,y in [('2013',y13a),('2014',y14a)]: require(np.all(np.isfinite(y)) and np.all((y>=0)&(y<=1)),f'invalid {name} target')
        route_offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); y13s.append(y13a); y14s.append(y14a); groups.extend(gs)
        route_data[route]={'base':base,'families':fams,'ids':ids,'centroids':C,'eligible':eligible}
        target_diag[route]={'families':len(ids),'eligible_recurrent_showers':len(eligible),'families_with_best_recurrent_label':int(sum(b['best_label'] is not None for b in best)),'2013_nonzero_targets':int(np.sum(y13a>0)),'2014_nonzero_targets':int(np.sum(y14a>0)),'2013_mean':float(np.mean(y13a)),'2014_mean':float(np.mean(y14a))}

    Xall=np.vstack(Xs); y13all=np.concatenate(y13s); y14all=np.concatenate(y14s); groups=list(map(str,groups)); require(Xall.shape==(cursor,FEATURE_DIM) and len(groups)==cursor,'stacked v26 shape mismatch')
    folds=np.asarray([v23.v1.deterministic_fold(g) for g in groups],dtype=int); weights=ranker.grouped_weights(groups); oof13=np.zeros(cursor); oof14=np.zeros(cursor); fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; require(tr.any() and te.any(),f'empty grouped fold {fold}')
        m13=ranker.model(); m14=ranker.model(); m13.fit(Xall[tr],y13all[tr],sample_weight=weights[tr]); m14.fit(Xall[tr],y14all[tr],sample_weight=weights[tr]); oof13[te]=m13.predict(Xall[te]); oof14[te]=m14.predict(Xall[te])
        tg=set(groups[i] for i in np.where(tr)[0]); eg=set(groups[i] for i in np.where(te)[0]); require(tg.isdisjoint(eg),f'group leakage fold {fold}')
        fold_diag.append({'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'train_groups':len(tg),'test_groups':len(eg)})
    score=np.minimum(oof13,oof14)

    variants={}; control=[]; order_diag={}
    for route in ROUTES:
        lo,hi=route_offsets[route]; rd=route_data[route]; ids=rd['ids']; s=score[lo:hi]; tie=[(int(rd['base']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
        idx=ranker.diversity_order(s,rd['centroids'],0.8,1.0,tie); qorder=[ids[i] for i in idx]; v19order=list(map(str,rd['base']['v19_order'])); fused=list(v23.v19.fusion_orders(qorder,v19order)['rank_sum'])
        variants[route]={'expanded_cohesion_two_head_quality':v23.rerank(rd['families'],qorder),'expanded_cohesion_two_head_v19_rank_sum':v23.rerank(rd['families'],fused),'v19_control':v23.rerank(rd['families'],v19order)}
        order_diag[route]={'oof_2013_prediction_sha256':v23.array_sha(oof13[lo:hi]),'oof_2014_prediction_sha256':v23.array_sha(oof14[lo:hi]),'min_oof_prediction_sha256':v23.array_sha(s),'quality_order_sha256':hashlib.sha256('\n'.join(qorder).encode()).hexdigest(),'fused_order_sha256':hashlib.sha256('\n'.join(fused).encode()).hexdigest()}
        for year in YEARS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget']); cur=v23.evaluate(variants[route]['v19_control'],truth_year[(route,year)],budget); exp=V19_METRICS[(route,year)]; require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'v19 control mismatch {route} {year}'); control.append({'comparator':route,'year':year,**cur})

    rows=[]
    for variant in VARIANTS:
        panels=[]
        for route,year in PANELS:
            budget=int(frozen_eval[(route,year)]['candidate_budget']['comparator_budget']); cur=v23.evaluate(variants[route][variant],truth_year[(route,year)],budget); lit=frozen_eval[(route,year)]['comparator_summary']; cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5']); mr=cm/lm if lm else float('inf'); rr=cr/lr if lr else float('inf'); win=bool(cm>lm and cr>=lr); panels.append({'comparator':route,'year':year,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':mr,'recovery_ratio':rr,'superiority_pair_pass':win})
        wins=sum(int(x['superiority_pair_pass']) for x in panels); minm=min(x['macro_f1_ratio'] for x in panels); minr=min(x['recovery_ratio'] for x in panels); meanm=float(np.mean([x['macro_f1_ratio'] for x in panels])); meanr=float(np.mean([x['recovery_ratio'] for x in panels])); rows.append({'variant':variant,'panel_wins':wins,'all_panel_win':wins==4,'min_macro_f1_ratio':minm,'min_recovery_ratio':minr,'mean_macro_f1_ratio':meanm,'mean_recovery_ratio':meanr,'selection_key':[wins,minm,minr,meanm,meanr,PREFERENCE[variant]],'panels':panels})
    winner=max(rows,key=lambda r:tuple(r['selection_key'])); passed=bool(winner['all_panel_win'])

    freeze={'verdict':'NOT_FROZEN_V26_OOF_FAIL','head_2013_sha256':None,'head_2014_sha256':None}
    if passed:
        h13=ranker.model(); h14=ranker.model(); h13.fit(Xall,y13all,sample_weight=weights); h14.fit(Xall,y14all,sample_weight=weights); h13.set_params(n_jobs=1); h14.set_params(n_jobs=1); p13=a.output/'v26_sonotaco_head_2013.joblib'; p14=a.output/'v26_sonotaco_head_2014.joblib'; joblib.dump(h13,p13); joblib.dump(h14,p14); freeze={'verdict':'PASS_V26_FULL_SONOTACO_TWO_HEAD_MODEL_FREEZE','head_2013_sha256':v23.sha(p13),'head_2014_sha256':v23.sha(p14),'feature_dimension':FEATURE_DIM,'training_examples':cursor,'training_groups':len(set(groups)),'training_feature_sha256':v23.array_sha(Xall),'target_2013_sha256':v23.array_sha(y13all),'target_2014_sha256':v23.array_sha(y14all),'in_sample_full_fit_score_used_for_promotion':False}
    (a.output/'V26_FULL_MODEL_FREEZE.json').write_text(json.dumps(freeze,indent=2,sort_keys=True)+'\n')
    result={'scientific_stage':'V26_EXPOSED_SONOTACO_EXPANDED_MEMBERSHIP_COHESION_TWO_HEAD_OOF_RANKING_DEVELOPMENT','sole_scientific_change_from_v24':'append exact #839 7-d cohesion features computed on frozen expanded membership','feature_dimension':FEATURE_DIM,'expanded_cohesion_feature_search':False,'v24_two_head_objective_unchanged':True,'folds':fold_diag,'target_diagnostics':target_diag,'order_diagnostics':order_diag,'v19_control_reproduction_pass':True,'v19_control':control,'all_results':rows,'winner':winner,'verdict':'PASS_V26_EXPOSED_EXPANDED_COHESION_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V26_EXPANDED_COHESION_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','full_model_freeze':freeze,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','full_fit_in_sample_score_used':False,'post_result_second_search':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False}
    (a.output/'V26_EXPOSED_EXPANDED_COHESION_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':result['verdict'],'winner':winner,'full_model_freeze':freeze},indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
