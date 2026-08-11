#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19
from orbittrace_v32_leaf_support_oof_v1 import train_evaluate as v32

ROUTES=v32.ROUTES; YEARS=v32.YEARS; PANELS=v32.PANELS
FEATURE_DIM=71; RECOVERY=0.5; V24_EXPECT=v32.V24_EXPECT

def require(ok,msg):
    if not ok: raise RuntimeError(msg)

def weighted_leaf_fraction(model,Xtr,ytr,wtr,Xte):
    a=np.asarray(model.apply(Xtr)); b=np.asarray(model.apply(Xte)); require(a.shape[1]==b.shape[1]==600,'tree count changed')
    pos=np.asarray(ytr>RECOVERY,bool); w=np.asarray(wtr,float); out=np.zeros(len(Xte),float)
    for t in range(600):
        total={}; good={}
        for leaf,ww,pp in zip(a[:,t],w,pos):
            k=int(leaf); total[k]=total.get(k,0.0)+float(ww)
            if pp: good[k]=good.get(k,0.0)+float(ww)
        vals=[]
        for leaf in b[:,t]:
            k=int(leaf); den=float(total.get(k,0.0)); require(den>0,'held-out leaf has zero training weight'); vals.append(float(good.get(k,0.0))/den)
        out += np.asarray(vals,float)
    out/=600.0; require(np.all(np.isfinite(out)) and np.all((out>=0)&(out<=1)),'invalid weighted leaf score'); return out

def main():
    p=argparse.ArgumentParser(); p.add_argument('--payload-root',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker changed')
    truth={}; frozen={}
    for r,y in PANELS:
        truth[(r,y)]=json.loads((a.truth_root/f'truth_{r}_{y}.json').read_text()); frozen[(r,y)]=json.loads((a.truth_root/f'evaluation_{r}_{y}.json').read_text())
    ranker=v22.load_module(a.ranker_source,'frozen_839_v33_leaf_weight')
    data={}; Xs=[]; A=[]; B=[]; groups=[]; offsets={}; cursor=0
    for r in ROUTES:
        root=a.payload_root/r; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and meta['feature_dimension']==71 and fp['truth_accessed'] is False,'invalid pretruth payload')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']; X=np.load(root/'features.npy'); C=np.load(root/'centroids.npy'); require([str(f['family_id']) for f in fams]==ids and v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],'payload identity changed')
        by={y:truth[(r,y)] for y in YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014]); base=[v22.family_truth(f,hidden,eligible) for f in fams]
        q13=[]; q14=[]; rg=[]
        for i,(f,t) in enumerate(zip(fams,base)):
            label=t['best_label']; rg.append('SHOWER/'+str(label) if label is not None else f'NEG/{r}/{ids[i]}')
            x13,x14=(0.0,0.0) if (not t['positive'] or label is None) else v24.annual_f1_for_fixed_label(f,str(label),by); q13.append(x13); q14.append(x14)
        offsets[r]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); A.append(np.asarray(q13,float)); B.append(np.asarray(q14,float)); groups.extend(rg); data[r]=(meta,fams,ids,C)
    X=np.vstack(Xs); y13=np.concatenate(A); y14=np.concatenate(B); folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups]); weights=np.asarray(ranker.grouped_weights(groups),float)
    require(X.shape==(cursor,71) and np.all(weights>0),'stacked input invalid')
    p13=np.zeros(cursor); p14=np.zeros(cursor); s13=np.zeros(cursor); s14=np.zeros(cursor); fold_diag=[]
    for f in range(5):
        tr=folds!=f; te=folds==f; require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),'group leakage')
        m13=ranker.model(); m14=ranker.model(); m13.fit(X[tr],y13[tr],sample_weight=weights[tr]); m14.fit(X[tr],y14[tr],sample_weight=weights[tr]); p13[te]=m13.predict(X[te]); p14[te]=m14.predict(X[te]); s13[te]=weighted_leaf_fraction(m13,X[tr],y13[tr],weights[tr],X[te]); s14[te]=weighted_leaf_fraction(m14,X[tr],y14[tr],weights[tr],X[te]); fold_diag.append({'fold':f,'train':int(tr.sum()),'test':int(te.sum()),'mean_2013':float(np.mean(s13[te])),'mean_2014':float(np.mean(s14[te]))})
    control_score=np.minimum(p13,p14); score=np.minimum(s13,s14); outputs={}; controls=[]; hashes={}
    for r in ROUTES:
        lo,hi=offsets[r]; meta,fams,ids,C=data[r]; tie=[(int(meta['tie_rank'][i]),ids[i]) for i in range(len(ids))]; old=list(map(str,meta['v19_order']))
        def ranked(vals):
            idx=ranker.diversity_order(vals,C,0.8,1.0,tie); order=[ids[i] for i in idx]; fused=list(v19.fusion_orders(order,old)['rank_sum']); return v22.rerank(fams,fused),fused
        ctl,_=ranked(control_score[lo:hi]); cand,fused=ranked(score[lo:hi]); outputs[r]=cand; hashes[r]={'score_2013':v22.array_sha(s13[lo:hi]),'score_2014':v22.array_sha(s14[lo:hi]),'combined':v22.array_sha(score[lo:hi]),'fused':hashlib.sha256('\n'.join(fused).encode()).hexdigest()}
        for y in YEARS:
            budget=int(frozen[(r,y)]['candidate_budget']['comparator_budget']); cur=v22.evaluate(ctl,truth[(r,y)],budget); exp=V24_EXPECT[(r,y)]; require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'v24 control mismatch {r} {y}'); controls.append({'comparator':r,'year':y,**cur})
    panels=[]
    for r,y in PANELS:
        budget=int(frozen[(r,y)]['candidate_budget']['comparator_budget']); cur=v22.evaluate(outputs[r],truth[(r,y)],budget); lit=frozen[(r,y)]['comparator_summary']; cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5']); panels.append({'comparator':r,'year':y,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'superiority_pair_pass':bool(cm>lm and cr>=lr)})
    wins=sum(int(x['superiority_pair_pass']) for x in panels); passed=wins==4
    result={'verdict':'PASS_V33_LEAF_POSITIVE_WEIGHT_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V33_LEAF_POSITIVE_WEIGHT_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','panel_wins':wins,'panels':panels,'v24_control_reproduction':controls,'fold_diagnostics':fold_diag,'order_diagnostics':hashes,'feature_dimension':71,'tree_count':600,'recovery_f1_threshold':0.5,'score_definition':'mean across all exact v24 trees of inherited #839 training-weight fraction in held-out leaf carried by fold-training families with annual F1>0.5','annual_combiner':'min(weight_fraction_2013,weight_fraction_2014)','binary_leaf_presence_used':False,'conditional_positive_fraction_used':False,'regression_prediction_used_in_successor_score':False,'geometry_margin_used':False,'candidate_membership_changed':False,'pretruth_feature_changed':False,'strict_whole_shower_oof':True,'diversity':{'lambda':0.8,'scale':1.0},'fusion':'one equal rank-sum with exact v19','support_threshold_search':False,'weight_transform_search':False,'conditioning_search':False,'tree_subset_search':False,'target_threshold_search':False,'model_search':False,'feature_search':False,'annual_combiner_search':False,'diversity_search':False,'fusion_search':False,'source_quota_selected':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','full_model_freeze':{'verdict':'AUTHORIZED_SEPARATE_FULL_FREEZE_AFTER_OOF_PASS' if passed else 'NOT_FROZEN_V33_LEAF_POSITIVE_WEIGHT_OOF_FAIL'},'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0]}
    (a.output/'V33_LEAF_POSITIVE_WEIGHT_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'panels':panels},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
