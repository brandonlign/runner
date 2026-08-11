#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

FEATURE_DIM=71; RECOVERY=0.5
V24_EXPECT={('sugar',2013):(0.27806630131631344,16),('sugar',2014):(0.32869544907104964,17),('hdbscan',2013):(0.14257102406283795,10),('hdbscan',2014):(0.12833942693327394,7)}
V31_EXPECT={('sugar',2013):(0.2719801488280529,16),('sugar',2014):(0.31529041952487225,17),('hdbscan',2013):(0.14888037368183737,9),('hdbscan',2014):(0.15198123772301594,9)}

def require(ok,msg):
    if not ok: raise RuntimeError(msg)
def osha(x): return hashlib.sha256('\n'.join(map(str,x)).encode()).hexdigest()
def equal_fuse(a,b):
    require(len(a)==len(b) and set(a)==set(b),'parent order universe mismatch'); ra={x:i+1 for i,x in enumerate(a)}; rb={x:i+1 for i,x in enumerate(b)}
    return sorted(a,key=lambda x:(ra[x]+rb[x],ra[x],rb[x],x))

def main():
    p=argparse.ArgumentParser(); p.add_argument('--payload-root',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker changed'); ranker=v22.load_module(a.ranker_source,'frozen_839_v34')
    truth={}; frozen={}
    for r,y in v24.PANELS: truth[(r,y)]=json.loads((a.truth_root/f'truth_{r}_{y}.json').read_text()); frozen[(r,y)]=json.loads((a.truth_root/f'evaluation_{r}_{y}.json').read_text())
    data={}; Xs=[]; A=[]; B=[]; groups=[]; offsets={}; cursor=0
    for r in v24.ROUTES:
        root=a.payload_root/r; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text()); require(meta['truth_accessed'] is False and fp['truth_accessed'] is False and meta['feature_dimension']==71,'invalid pretruth')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']; X=np.load(root/'features.npy'); C=np.load(root/'centroids.npy'); require([str(f['family_id']) for f in fams]==ids and X.shape==(len(ids),71) and C.shape==(len(ids),8) and v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],'payload identity changed')
        by={y:truth[(r,y)] for y in v24.YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014]); base=[v22.family_truth(f,hidden,eligible) for f in fams]
        q13=[]; q14=[]; rg=[]
        for i,(fam,t) in enumerate(zip(fams,base)):
            lab=t['best_label']; rg.append('SHOWER/'+str(lab) if lab is not None else f'NEG/{r}/{ids[i]}'); x13,x14=(0.0,0.0) if (not t['positive'] or lab is None) else v24.annual_f1_for_fixed_label(fam,str(lab),by); q13.append(x13); q14.append(x14)
        offsets[r]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); A.append(np.asarray(q13,float)); B.append(np.asarray(q14,float)); groups.extend(rg); data[r]=(meta,fams,ids,C)
    X=np.vstack(Xs); y13=np.concatenate(A); y14=np.concatenate(B); folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups]); weights=np.asarray(ranker.grouped_weights(groups),float); require(X.shape==(cursor,71),'stack mismatch')
    p13=np.zeros(cursor); p14=np.zeros(cursor); m13=np.zeros(cursor); m14=np.zeros(cursor)
    for f in range(5):
        tr=folds!=f; te=folds==f; require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),'group leakage')
        e13=ranker.model(); e14=ranker.model(); e13.fit(X[tr],y13[tr],sample_weight=weights[tr]); e14.fit(X[tr],y14[tr],sample_weight=weights[tr]); p13[te]=e13.predict(X[te]); p14[te]=e14.predict(X[te])
        mu=X[tr].mean(0); sd=X[tr].std(0,ddof=0); scale=sd.copy(); scale[scale==0]=1.0; Ztr=(X[tr]-mu)/scale; Zte=(X[te]-mu)/scale; tidx=np.where(te)[0]
        for y,yy,out in ((2013,y13,m13),(2014,y14,m14)):
            pos=yy[tr]>RECOVERY; neg=~pos; P=Ztr[pos]; N=Ztr[neg]; require(len(P)>0 and len(N)>0,'missing geometry references')
            for j,gidx in enumerate(tidx): out[gidx]=float(np.min(np.linalg.norm(N-Zte[j],axis=1))-np.min(np.linalg.norm(P-Zte[j],axis=1)))
    v24score=np.minimum(p13,p14); v31score=np.minimum(m13,m14); parent_metrics=[]; panels=[]; diag={}
    for r in v24.ROUTES:
        lo,hi=offsets[r]; meta,fams,ids,C=data[r]; tie=[(int(meta['tie_rank'][i]),ids[i]) for i in range(len(ids))]; base19=list(map(str,meta['v19_order']))
        def parent(vals):
            idx=ranker.diversity_order(vals,C,0.8,1.0,tie); inner=[ids[i] for i in idx]; final=list(v19.fusion_orders(inner,base19)['rank_sum']); return final,v22.rerank(fams,final)
        o24,f24=parent(v24score[lo:hi]); o31,f31=parent(v31score[lo:hi]); o34=equal_fuse(o24,o31); f34=v22.rerank(fams,o34); diag[r]={'v24_order_sha256':osha(o24),'v31_order_sha256':osha(o31),'v34_order_sha256':osha(o34)}
        for y in v24.YEARS:
            budget=int(frozen[(r,y)]['candidate_budget']['comparator_budget'])
            for name,ff,exp in [('v24',f24,V24_EXPECT[(r,y)]),('v31',f31,V31_EXPECT[(r,y)])]:
                cur=v22.evaluate(ff,truth[(r,y)],budget); require(abs(cur['macro_f1']-exp[0])<1e-12 and cur['recovered_f1_gt_0_5']==exp[1],f'{name} parent mismatch {r} {y}'); parent_metrics.append({'parent':name,'comparator':r,'year':y,**cur})
            cur=v22.evaluate(f34,truth[(r,y)],budget); lit=frozen[(r,y)]['comparator_summary']; cm=float(cur['macro_f1']); cr=int(cur['recovered_f1_gt_0_5']); lm=float(lit['macro_f1']); lr=int(lit['recovered_f1_gt_0_5']); panels.append({'comparator':r,'year':y,'budget':budget,'candidate_macro_f1':cm,'literature_macro_f1':lm,'candidate_recovered_f1_gt_0_5':cr,'literature_recovered_f1_gt_0_5':lr,'superiority_pair_pass':bool(cm>lm and cr>=lr)})
    wins=sum(int(x['superiority_pair_pass']) for x in panels); passed=wins==4
    result={'verdict':'PASS_V34_V24_V31_EQUAL_FUSION_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT' if passed else 'FAIL_V34_V24_V31_EQUAL_FUSION_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','panel_wins':wins,'panels':panels,'parent_reproduction':parent_metrics,'order_diagnostics':diag,'fusion':'equal rank-sum of complete final v24 and v31 orders; tie v24 rank, then v31 rank, then family id','third_order_used':False,'additional_diversity_after_parent_fusion':False,'candidate_membership_changed':False,'pretruth_feature_changed':False,'strict_whole_shower_oof':True,'fusion_weight_search':False,'rank_algebra_search':False,'route_year_switch_search':False,'parent_search':False,'feature_search':False,'model_search':False,'membership_search':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0]}
    (a.output/'V34_V24_V31_EQUAL_FUSION_OOF_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':result['verdict'],'panel_wins':wins,'panels':panels},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
