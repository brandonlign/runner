#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

RECOVERY=0.5
EXPECTED_HDB={2013:(0.14257102406283795,10,11),2014:(0.12833942693327394,7,9)}


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def leaf_dilution(model:Any,Xtr:np.ndarray,ytr:np.ndarray,wtr:np.ndarray,Xte:np.ndarray)->dict[str,np.ndarray]:
    train_leaf=np.asarray(model.apply(Xtr)); test_leaf=np.asarray(model.apply(Xte))
    require(train_leaf.ndim==2 and test_leaf.shape[1]==train_leaf.shape[1],'unexpected forest leaf matrix')
    require(wtr.shape==(len(Xtr),) and np.all(np.isfinite(wtr)) and np.all(wtr>0),'invalid inherited training weights')
    positive=np.asarray(ytr>RECOVERY,dtype=bool); require(positive.any(),'training fold has no high-quality annual family')
    nt=train_leaf.shape[1]; nte=len(Xte)
    support=np.zeros(nte,float); posfrac=np.zeros(nte,float); posfrac_supported_sum=np.zeros(nte,float); supported_count=np.zeros(nte,int); target_mean=np.zeros(nte,float)
    for t in range(nt):
        stats:dict[int,tuple[float,float,float]]={}
        for leaf in np.unique(train_leaf[:,t]).tolist():
            mask=train_leaf[:,t]==leaf; tw=float(np.sum(wtr[mask])); require(np.isfinite(tw) and tw>0,'invalid leaf total weight')
            pw=float(np.sum(wtr[mask & positive])); ym=float(np.sum(wtr[mask]*ytr[mask])/tw)
            require(np.isfinite(pw) and pw>=0 and np.isfinite(ym),'invalid leaf diagnostic statistic')
            stats[int(leaf)]=(tw,pw,ym)
        for j in range(nte):
            tw,pw,ym=stats[int(test_leaf[j,t])]; pf=float(pw/tw); has=pw>0.0
            support[j]+=float(has); posfrac[j]+=pf; target_mean[j]+=ym
            if has:
                posfrac_supported_sum[j]+=pf; supported_count[j]+=1
    support/=float(nt); posfrac/=float(nt); target_mean/=float(nt)
    conditional=np.zeros(nte,float); nz=supported_count>0; conditional[nz]=posfrac_supported_sum[nz]/supported_count[nz]
    pred=np.asarray(model.predict(Xte),float)
    require(np.allclose(target_mean,pred,rtol=0.0,atol=1e-12),'leaf weighted target means do not reproduce exact forest prediction')
    dilution=support-posfrac
    require(np.all((support>=0)&(support<=1)) and np.all((posfrac>=0)&(posfrac<=1)) and np.all((conditional>=0)&(conditional<=1)) and np.all(dilution>=-1e-15),'invalid leaf dilution outputs')
    return {'positive_leaf_support_fraction':support,'positive_weight_fraction_mean':posfrac,'positive_weight_fraction_given_supported_leaf_mean':conditional,'leaf_target_mean':target_mean,'dilution_gap':dilution}


def summarize(rows:list[dict[str,Any]])->dict[str,Any]:
    if not rows: return {'groups':0}
    return {
        'groups':len(rows),
        'positive_leaf_support_fraction_median':float(np.median([r['positive_leaf_support_fraction'] for r in rows])),
        'positive_weight_fraction_mean_median':float(np.median([r['positive_weight_fraction_mean'] for r in rows])),
        'positive_weight_fraction_given_supported_leaf_mean_median':float(np.median([r['positive_weight_fraction_given_supported_leaf_mean'] for r in rows])),
        'dilution_gap_median':float(np.median([r['dilution_gap'] for r in rows])),
        'leaf_target_mean_median':float(np.median([r['leaf_target_mean'] for r in rows])),
        'first_positive_rank_median':float(np.median([r['first_positive_rank'] for r in rows])),
    }


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--payload-root',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True); require(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker source changed')
    roots={r:a.payload_root/r for r in v24.ROUTES}
    truth={}; frozen_eval={}
    for route,year in v24.PANELS:
        truth[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text()); frozen_eval[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())
    ranker=v22.load_module(a.ranker_source,'frozen_839_leaf_dilution_diag')
    route_data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; offsets={}; cursor=0
    for route in v24.ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and meta['feature_dimension']==71 and fp['truth_accessed'] is False,'invalid immutable v24 pretruth payload')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']; require([str(f['family_id']) for f in fams]==ids,'family alignment changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False); require(v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],'immutable arrays changed')
        by={y:truth[(route,y)] for y in v24.YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014]); base=[v22.family_truth(f,hidden,eligible) for f in fams]
        y13=[]; y14=[]; rg=[]
        for i,(f,t) in enumerate(zip(fams,base)):
            label=t['best_label']; rg.append(('SHOWER/'+str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None: q13=q14=0.0
            else: q13,q14=v24.annual_f1_for_fixed_label(f,str(label),by)
            y13.append(float(q13)); y14.append(float(q14))
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); y13s.append(np.asarray(y13,float)); y14s.append(np.asarray(y14,float)); groups.extend(rg)
        route_data[route]={'meta':meta,'fams':fams,'ids':ids,'centroids':C,'groups':rg,'y13':np.asarray(y13,float),'y14':np.asarray(y14,float)}
    Xall=np.vstack(Xs); y13all=np.concatenate(y13s); y14all=np.concatenate(y14s); groups=list(map(str,groups)); folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],dtype=int); weights=np.asarray(ranker.grouped_weights(groups),float)
    o13=np.zeros(cursor); o14=np.zeros(cursor); metrics13={k:np.zeros(cursor) for k in ('positive_leaf_support_fraction','positive_weight_fraction_mean','positive_weight_fraction_given_supported_leaf_mean','leaf_target_mean','dilution_gap')}; metrics14={k:np.zeros(cursor) for k in metrics13}; fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; require(tr.any() and te.any(),f'empty fold {fold}')
        m13=ranker.model(); m14=ranker.model(); m13.fit(Xall[tr],y13all[tr],sample_weight=weights[tr]); m14.fit(Xall[tr],y14all[tr],sample_weight=weights[tr]); o13[te]=m13.predict(Xall[te]); o14[te]=m14.predict(Xall[te])
        d13=leaf_dilution(m13,Xall[tr],y13all[tr],weights[tr],Xall[te]); d14=leaf_dilution(m14,Xall[tr],y14all[tr],weights[tr],Xall[te])
        for k in metrics13: metrics13[k][te]=d13[k]; metrics14[k][te]=d14[k]
        tg={groups[i] for i in np.where(te)[0]}; rg={groups[i] for i in np.where(tr)[0]}; require(tg.isdisjoint(rg),f'group leakage fold {fold}')
        fold_diag.append({'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'train_high_quality_2013_families':int(np.sum(y13all[tr]>RECOVERY)),'train_high_quality_2014_families':int(np.sum(y14all[tr]>RECOVERY))})
    require(np.allclose(metrics13['leaf_target_mean'],o13,rtol=0,atol=1e-12) and np.allclose(metrics14['leaf_target_mean'],o14,rtol=0,atol=1e-12),'diagnostic leaf means do not match exact OOF predictions')
    worst=np.minimum(o13,o14); lo,hi=offsets['hdbscan']; rd=route_data['hdbscan']; ids=rd['ids']; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]; idx=ranker.diversity_order(worst[lo:hi],rd['centroids'],0.8,1.0,tie); quality=[ids[i] for i in idx]; fused=list(v19.fusion_orders(quality,list(map(str,rd['meta']['v19_order'])))['rank_sum']); rank={fid:i+1 for i,fid in enumerate(fused)}; reranked=v22.rerank(rd['fams'],fused)
    reproduction={}
    for year,(macro,rec,budget) in EXPECTED_HDB.items():
        cur=v22.evaluate(reranked,truth[('hdbscan',year)],budget); require(abs(float(cur['macro_f1'])-macro)<1e-12 and int(cur['recovered_f1_gt_0_5'])==rec,f'v24 HDB {year} reproduction failed'); reproduction[str(year)]={'macro_f1':float(cur['macro_f1']),'recovered_f1_gt_0_5':int(cur['recovered_f1_gt_0_5']),'budget':budget}
    annual={}
    for year,arr,md in ((2013,rd['y13'],metrics13),(2014,rd['y14'],metrics14)):
        budget=EXPECTED_HDB[year][2]; rg=list(map(str,rd['groups'])); posgroups=sorted({rg[i] for i in range(len(ids)) if rg[i].startswith('SHOWER/') and float(arr[i])>RECOVERY}); rows=[]
        for g in posgroups:
            pos=[i for i in range(len(ids)) if rg[i]==g and float(arr[i])>RECOVERY]; best=min(pos,key=lambda i:(rank[ids[i]],ids[i])); gi=lo+best; r=rank[ids[best]]
            rows.append({'group':g,'family_id':ids[best],'first_positive_rank':r,'surfaced':bool(r<=budget),'annual_f1':float(arr[best]),'fold':int(folds[gi]),'positive_leaf_support_fraction':float(md['positive_leaf_support_fraction'][gi]),'positive_weight_fraction_mean':float(md['positive_weight_fraction_mean'][gi]),'positive_weight_fraction_given_supported_leaf_mean':float(md['positive_weight_fraction_given_supported_leaf_mean'][gi]),'leaf_target_mean':float(md['leaf_target_mean'][gi]),'dilution_gap':float(md['dilution_gap'][gi])})
        surfaced=[x for x in rows if x['surfaced']]; missed=[x for x in rows if not x['surfaced']]; require(len(surfaced)==EXPECTED_HDB[year][1],f'{year} surfaced count mismatch')
        annual[str(year)]={'budget':budget,'recoverable_groups':len(rows),'surfaced':summarize(surfaced),'missed':summarize(missed),'groups':rows}
    result={'verdict':'PASS_V24_HDB_LEAF_DILUTION_DIAGNOSTIC','scientific_role':'POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED','v24_hdb_reproduction':reproduction,'leaf_measurement':'exact v24 regression leaves; inherited #839 sample-weight fraction above annual F1>0.5 and exact weighted target mean','annual_group_diagnostics':annual,'fold_diagnostics':fold_diag,'new_rank_evaluated':False,'leaf_purity_score_evaluated':False,'support_threshold_search':False,'tree_subset_search':False,'target_transform_search':False,'weight_transform_search':False,'feature_transform_used':False,'successor_selected':False,'parameter_search':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0]}
    (a.output/'V24_HDB_LEAF_DILUTION_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'); print(json.dumps({'verdict':result['verdict'],'2013':annual['2013']|{'groups':'omitted'},'2014':annual['2014']|{'groups':'omitted'}},indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
