#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from collections import defaultdict
from pathlib import Path
import numpy as np
from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

FEATURE_DIM=71; RECOVERY=0.5; VARIANT='group_prototype_local_geometry_v19_rank_sum'

def require(ok,msg):
    if not ok: raise RuntimeError(msg)
def osh(x): return hashlib.sha256('\n'.join(map(str,x)).encode()).hexdigest()

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--payload-root',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True); require(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker changed')
    roots={r:a.payload_root/r for r in v24.ROUTES}; truth={}; frozen={}
    for r,y in v24.PANELS: truth[(r,y)]=json.loads((a.truth_root/f'truth_{r}_{y}.json').read_text()); frozen[(r,y)]=json.loads((a.truth_root/f'evaluation_{r}_{y}.json').read_text())
    ranker=v22.load_module(a.ranker_source,'frozen_839_v35_group_proto')
    data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; offsets={}; cursor=0
    for route in v24.ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and meta['feature_dimension']==FEATURE_DIM and fp['truth_accessed'] is False,f'{route} bad pretruth')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']; require([str(f['family_id']) for f in fams]==ids,'family order changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False); require(v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],'array identity changed')
        by={y:truth[(route,y)] for y in v24.YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014]); base=[v22.family_truth(f,hidden,eligible) for f in fams]
        y13=[]; y14=[]; rg=[]
        for i,(f,t) in enumerate(zip(fams,base)):
            lab=t['best_label']; rg.append(('SHOWER/'+str(lab)) if lab is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or lab is None: q13=q14=0.0
            else: q13,q14=v24.annual_f1_for_fixed_label(f,str(lab),by)
            y13.append(float(q13)); y14.append(float(q14))
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); y13s.append(np.asarray(y13,float)); y14s.append(np.asarray(y14,float)); groups.extend(rg); data[route]={'meta':meta,'fams':fams,'ids':ids,'centroids':C}
    X=np.vstack(Xs); y13=np.concatenate(y13s); y14=np.concatenate(y14s); groups=list(map(str,groups)); require(X.shape==(cursor,FEATURE_DIM),'stack shape')
    folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],int); m13=np.zeros(cursor); m14=np.zeros(cursor); fd=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),'group leakage')
        mu=X[tr].mean(0); sd=X[tr].std(0,ddof=0); scale=sd.copy(); scale[scale==0]=1.0; Ztr=(X[tr]-mu)/scale; Zte=(X[te]-mu)/scale; tri=np.where(tr)[0]; tei=np.where(te)[0]
        bygroup=defaultdict(list)
        for local,gi in enumerate(tri.tolist()): bygroup[groups[gi]].append(local)
        names=sorted(bygroup); prot=np.vstack([Ztr[bygroup[g]].mean(0) for g in names]); p13=np.asarray([any(y13[tri[k]]>RECOVERY for k in bygroup[g]) for g in names],bool); p14=np.asarray([any(y14[tri[k]]>RECOVERY for k in bygroup[g]) for g in names],bool)
        require(p13.any() and (~p13).any() and p14.any() and (~p14).any(),'prototype class missing')
        for parr,out in ((p13,m13),(p14,m14)):
            P=prot[parr]; N=prot[~parr]
            for j,gi in enumerate(tei.tolist()): out[gi]=float(np.min(np.linalg.norm(N-Zte[j],axis=1))-np.min(np.linalg.norm(P-Zte[j],axis=1)))
        fd.append({'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'training_groups':len(names),'positive_group_prototypes_2013':int(p13.sum()),'positive_group_prototypes_2014':int(p14.sum()),'zero_variance_features':int((sd==0).sum())})
    score=np.minimum(m13,m14); variants={}; od={}; controls=[]
    for route in v24.ROUTES:
        lo,hi=offsets[route]; rd=data[route]; ids=rd['ids']; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]; idx=ranker.diversity_order(score[lo:hi],rd['centroids'],0.8,1.0,tie); local=[ids[i] for i in idx]; vo=list(map(str,rd['meta']['v19_order'])); fused=list(v19.fusion_orders(local,vo)['rank_sum']); variants[route]=v22.rerank(rd['fams'],fused); od[route]={'margin_2013_sha256':v22.array_sha(m13[lo:hi]),'margin_2014_sha256':v22.array_sha(m14[lo:hi]),'combined_sha256':v22.array_sha(score[lo:hi]),'diversity_order_sha256':osh(local),'fused_order_sha256':osh(fused)}
        vr=v22.rerank(rd['fams'],vo)
        for year in v24.YEARS:
            b=int(frozen[(route,year)]['candidate_budget']['comparator_budget']); cur=v22.evaluate(vr,truth[(route,year)],b); exp=v24.V19_METRICS[(route,year)]; require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'v19 control {route} {year}'); controls.append({'comparator':route,'year':year,**cur})
    panels=[]
    for route,year in v24.PANELS:
        b=int(frozen[(route,year)]['candidate_budget']['comparator_budget']); cur=v22.evaluate(variants[route],truth[(route,year)],b); lit=frozen[(route,year)]['comparator_summary']; cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5']); panels.append({'comparator':route,'year':year,'budget':b,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'macro_f1_ratio':cm/lm,'recovery_ratio':cr/lr,'superiority_pair_pass':bool(cm>lm and cr>=lr)})
    wins=sum(int(x['superiority_pair_pass']) for x in panels); passed=wins==4; freeze={'verdict':'NOT_FROZEN_V35_GROUP_PROTOTYPE_FAIL','reference_sha256':None}
    if passed:
        mu=X.mean(0); sd=X.std(0,ddof=0); scale=sd.copy(); scale[scale==0]=1.; Z=(X-mu)/scale; bg=defaultdict(list)
        for i,g in enumerate(groups): bg[g].append(i)
        names=sorted(bg); prot=np.vstack([Z[bg[g]].mean(0) for g in names]); p13=np.asarray([any(y13[i]>RECOVERY for i in bg[g]) for g in names],np.int8); p14=np.asarray([any(y14[i]>RECOVERY for i in bg[g]) for g in names],np.int8); path=a.output/'v35_group_prototype_reference.npz'; np.savez_compressed(path,mean=mu,scale=scale,prototypes=prot,positive2013=p13,positive2014=p14,groups=np.asarray(names,dtype=str)); freeze={'verdict':'PASS_V35_FULL_EXPOSED_GROUP_PROTOTYPE_REFERENCE_FREEZE','reference_sha256':v22.sha(path),'training_examples':cursor,'training_groups':len(names),'feature_dimension':FEATURE_DIM,'in_sample_score_used_for_promotion':False}
    (a.output/'V35_GROUP_PROTOTYPE_MODEL_FREEZE.json').write_text(json.dumps(freeze,indent=2,sort_keys=True)+'\n')
    result={'scientific_stage':'EXPOSED_SONOTACO_V35_STRICT_GROUP_PROTOTYPE_LOCAL_GEOMETRY_V1','verdict':'PASS_V35_GROUP_PROTOTYPE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V35_GROUP_PROTOTYPE_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','sole_scientific_change_from_v31':'individual fold-training family references -> one arithmetic-mean prototype per strict fold-training group with annual group positivity=max family F1>0.5','feature_dimension':FEATURE_DIM,'nearest_k':1,'distance':'ordinary Euclidean after exact v31 fold-training-family z-score','prototype':'arithmetic mean of all standardized training-family features in each strict group across routes','group_positive_definition':'any family in strict group has annual F1>0.5','annual_combiner':'min(margin_2013,margin_2014)','strict_whole_shower_oof':True,'candidate_membership_changed':False,'pretruth_feature_changed':False,'diversity':{'lambda':0.8,'scale':1.0},'fusion':'one equal rank-sum with exact v19','panel_wins':wins,'panels':panels,'v19_control':controls,'fold_diagnostics':fd,'order_diagnostics':od,'full_model_freeze':freeze,'prototype_search':False,'prototype_weight_search':False,'group_size_threshold_search':False,'k_search':False,'metric_search':False,'feature_search':False,'threshold_search':False,'annual_combiner_search':False,'diversity_search':False,'fusion_search':False,'source_quota_selected':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0]}; (a.output/'V35_GROUP_PROTOTYPE_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'panels':panels,'full_model_freeze':freeze},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
