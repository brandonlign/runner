#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import joblib
import numpy as np
from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

BASE_DIM=71; AUG_DIM=73
V24_EXPECT={('sugar',2013):(0.27806630131631344,16),('sugar',2014):(0.32869544907104964,17),('hdbscan',2013):(0.14257102406283795,10),('hdbscan',2014):(0.12833942693327394,7)}
def require(ok,msg):
    if not ok: raise RuntimeError(msg)
def osha(x): return hashlib.sha256('\n'.join(map(str,x)).encode()).hexdigest()

def main():
    p=argparse.ArgumentParser(); p.add_argument('--payload-root',type=Path,required=True); p.add_argument('--aug-root',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker changed'); ranker=v22.load_module(a.ranker_source,'frozen_839_v36')
    truth={}; frozen={}
    for r,y in v24.PANELS: truth[(r,y)]=json.loads((a.truth_root/f'truth_{r}_{y}.json').read_text()); frozen[(r,y)]=json.loads((a.truth_root/f'evaluation_{r}_{y}.json').read_text())
    data={}; X71s=[]; X73s=[]; A=[]; B=[]; groups=[]; offsets={}; cursor=0
    for r in v24.ROUTES:
        root=a.payload_root/r; aug=a.aug_root/r; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text()); am=json.loads((aug/'V36_PRETRUTH_MANIFEST.json').read_text())
        require(meta['truth_accessed'] is False and fp['truth_accessed'] is False and am['truth_accessed'] is False and am['verdict']=='PASS_V36_ANNUAL_ORIENTED_EXPANDED_COUNT_PRETRUTH','invalid pretruth inputs')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']; X71=np.load(root/'features.npy',allow_pickle=False); X73=np.load(aug/'features_73.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require([str(f['family_id']) for f in fams]==ids and am['family_ids']==ids,'family alignment changed'); require(X71.shape==(len(ids),BASE_DIM) and X73.shape==(len(ids),AUG_DIM) and C.shape==(len(ids),8),'array shape changed'); require(v22.array_sha(X71)==meta['feature_sha256'] and v22.array_sha(X73)==am['augmented_feature_sha256'] and np.array_equal(X73[:,:BASE_DIM],X71),'feature identity changed')
        by={y:truth[(r,y)] for y in v24.YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014]); base=[v22.family_truth(f,hidden,eligible) for f in fams]
        q13=[]; q14=[]; rg=[]
        for i,(fam,t) in enumerate(zip(fams,base)):
            lab=t['best_label']; rg.append('SHOWER/'+str(lab) if lab is not None else f'NEG/{r}/{ids[i]}'); x13,x14=(0.0,0.0) if (not t['positive'] or lab is None) else v24.annual_f1_for_fixed_label(fam,str(lab),by); q13.append(float(x13)); q14.append(float(x14))
        offsets[r]=(cursor,cursor+len(ids)); cursor+=len(ids); X71s.append(X71); X73s.append(X73); A.append(np.asarray(q13,float)); B.append(np.asarray(q14,float)); groups.extend(rg); data[r]={'meta':meta,'fams':fams,'ids':ids,'C':C}
    X71=np.vstack(X71s); X73=np.vstack(X73s); y13=np.concatenate(A); y14=np.concatenate(B); folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],int); weights=np.asarray(ranker.grouped_weights(groups),float); require(X71.shape==(cursor,BASE_DIM) and X73.shape==(cursor,AUG_DIM) and np.all(weights>0),'stacked input invalid')
    base13=np.zeros(cursor); base14=np.zeros(cursor); aug13=np.zeros(cursor); aug14=np.zeros(cursor); fold_diag=[]
    for f in range(5):
        tr=folds!=f; te=folds==f; require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),'group leakage')
        b13=ranker.model(); b14=ranker.model(); n13=ranker.model(); n14=ranker.model(); b13.fit(X71[tr],y13[tr],sample_weight=weights[tr]); b14.fit(X71[tr],y14[tr],sample_weight=weights[tr]); n13.fit(X73[tr],y13[tr],sample_weight=weights[tr]); n14.fit(X73[tr],y14[tr],sample_weight=weights[tr]); base13[te]=b13.predict(X71[te]); base14[te]=b14.predict(X71[te]); aug13[te]=n13.predict(X73[te]); aug14[te]=n14.predict(X73[te]); fold_diag.append({'fold':f,'train_examples':int(tr.sum()),'test_examples':int(te.sum())})
    base_score=np.minimum(base13,base14); aug_score=np.minimum(aug13,aug14); outputs={}; controls=[]; order_diag={}
    for r in v24.ROUTES:
        lo,hi=offsets[r]; rd=data[r]; ids=rd['ids']; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]; old=list(map(str,rd['meta']['v19_order']))
        def ranked(vals):
            idx=ranker.diversity_order(vals,rd['C'],0.8,1.0,tie); inner=[ids[i] for i in idx]; final=list(v19.fusion_orders(inner,old)['rank_sum']); return final,v22.rerank(rd['fams'],final)
        bo,bf=ranked(base_score[lo:hi]); ao,af=ranked(aug_score[lo:hi]); outputs[r]=af; order_diag[r]={'v24_control_order_sha256':osha(bo),'v36_order_sha256':osha(ao),'annual_prediction_2013_sha256':v22.array_sha(aug13[lo:hi]),'annual_prediction_2014_sha256':v22.array_sha(aug14[lo:hi])}
        for y in v24.YEARS:
            budget=int(frozen[(r,y)]['candidate_budget']['comparator_budget']); cur=v22.evaluate(bf,truth[(r,y)],budget); exp=V24_EXPECT[(r,y)]; require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'v24 control mismatch {r} {y}'); controls.append({'comparator':r,'year':y,**cur})
    panels=[]
    for r,y in v24.PANELS:
        budget=int(frozen[(r,y)]['candidate_budget']['comparator_budget']); cur=v22.evaluate(outputs[r],truth[(r,y)],budget); lit=frozen[(r,y)]['comparator_summary']; cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5']); panels.append({'comparator':r,'year':y,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'superiority_pair_pass':bool(cm>lm and cr>=lr)})
    wins=sum(int(x['superiority_pair_pass']) for x in panels); passed=wins==4; freeze={'verdict':'NOT_FROZEN_V36_OOF_FAIL'}
    if passed:
        m13=ranker.model(); m14=ranker.model(); m13.fit(X73,y13,sample_weight=weights); m14.fit(X73,y14,sample_weight=weights); m13.set_params(n_jobs=1); m14.set_params(n_jobs=1); p13=a.output/'v36_head_2013.joblib'; p14=a.output/'v36_head_2014.joblib'; joblib.dump(m13,p13); joblib.dump(m14,p14); freeze={'verdict':'PASS_FULL_EXPOSED_V36_MODEL_FREEZE','head_2013_sha256':v22.sha(p13),'head_2014_sha256':v22.sha(p14),'feature_dimension':AUG_DIM,'in_sample_score_used_for_promotion':False}
    result={'verdict':'PASS_V36_ANNUAL_ORIENTED_EXPANDED_COUNTS_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V36_ANNUAL_ORIENTED_EXPANDED_COUNTS_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','panel_wins':wins,'panels':panels,'v24_control_reproduction':controls,'fold_diagnostics':fold_diag,'order_diagnostics':order_diag,'feature_dimension':AUG_DIM,'sole_scientific_change_from_v24':'append log1p fixed expanded membership count for 2013 and 2014 as two oriented pretruth features','augmentation_feature_names':['log1p_expanded_member_count_2013','log1p_expanded_member_count_2014'],'candidate_membership_changed':False,'strict_whole_shower_oof':True,'model_changed':False,'target_changed':False,'annual_combiner':'min(pred_2013,pred_2014)','diversity':{'lambda':0.8,'scale':1.0},'fusion':'one equal rank-sum with exact v19','additional_feature_search':False,'count_transform_search':False,'ratio_or_difference_feature_used':False,'year_specific_feature_subset_search':False,'model_search':False,'target_search':False,'annual_combiner_search':False,'diversity_search':False,'fusion_search':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0],'full_model_freeze':freeze}
    (a.output/'V36_ANNUAL_ORIENTED_EXPANDED_COUNTS_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'panels':panels,'full_model_freeze':freeze},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
