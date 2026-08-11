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


def forest_support(model:Any,Xtr:np.ndarray,ytr:np.ndarray,gtr:list[str],Xte:np.ndarray)->tuple[np.ndarray,np.ndarray]:
    train_leaf=np.asarray(model.apply(Xtr)); test_leaf=np.asarray(model.apply(Xte))
    require(train_leaf.ndim==2 and test_leaf.shape[1]==train_leaf.shape[1],'unexpected forest leaf matrix')
    positive=np.asarray(ytr>RECOVERY,dtype=bool); require(positive.any(),'training fold has no high-quality annual family')
    frac=np.zeros(len(Xte),dtype=float); mean_groups=np.zeros(len(Xte),dtype=float)
    nt=train_leaf.shape[1]
    for t in range(nt):
        by_leaf:dict[int,set[str]]={}
        for i in np.where(positive)[0].tolist():
            leaf=int(train_leaf[i,t]); by_leaf.setdefault(leaf,set()).add(str(gtr[i]))
        for j in range(len(Xte)):
            n=len(by_leaf.get(int(test_leaf[j,t]),set()))
            frac[j]+=float(n>0); mean_groups[j]+=float(n)
    frac/=float(nt); mean_groups/=float(nt)
    require(np.all((frac>=0)&(frac<=1)) and np.all(mean_groups>=0),'invalid support diagnostic')
    return frac,mean_groups


def summarize(rows:list[dict[str,Any]])->dict[str,Any]:
    if not rows: return {'groups':0}
    return {
        'groups':len(rows),
        'positive_leaf_support_fraction_median':float(np.median([r['positive_leaf_support_fraction'] for r in rows])),
        'positive_leaf_support_fraction_mean':float(np.mean([r['positive_leaf_support_fraction'] for r in rows])),
        'positive_leaf_support_fraction_min':float(np.min([r['positive_leaf_support_fraction'] for r in rows])),
        'mean_positive_groups_in_leaf_median':float(np.median([r['mean_positive_groups_in_leaf'] for r in rows])),
        'first_positive_rank_median':float(np.median([r['first_positive_rank'] for r in rows])),
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--payload-root',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker source changed')
    roots={r:a.payload_root/r for r in v24.ROUTES}

    truth={}; frozen_eval={}
    for route,year in v24.PANELS:
        truth[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen_eval[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    ranker=v22.load_module(a.ranker_source,'frozen_839_oof_support_diag')
    route_data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; offsets={}; cursor=0
    for route in v24.ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and meta['feature_dimension']==71 and fp['truth_accessed'] is False,'invalid immutable v24 pretruth payload')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']; require([str(f['family_id']) for f in fams]==ids,'family alignment changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require(v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],'immutable arrays changed')
        by={y:truth[(route,y)] for y in v24.YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014])
        base=[v22.family_truth(f,hidden,eligible) for f in fams]; y13=[]; y14=[]; rg=[]
        for i,(f,t) in enumerate(zip(fams,base)):
            label=t['best_label']; rg.append(('SHOWER/'+str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None: q13=q14=0.0
            else: q13,q14=v24.annual_f1_for_fixed_label(f,str(label),by)
            y13.append(float(q13)); y14.append(float(q14))
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); y13s.append(np.asarray(y13,float)); y14s.append(np.asarray(y14,float)); groups.extend(rg)
        route_data[route]={'meta':meta,'fams':fams,'ids':ids,'centroids':C,'groups':rg,'y13':np.asarray(y13,float),'y14':np.asarray(y14,float)}

    Xall=np.vstack(Xs); y13all=np.concatenate(y13s); y14all=np.concatenate(y14s); groups=list(map(str,groups))
    folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],dtype=int); weights=np.asarray(ranker.grouped_weights(groups),float)
    o13=np.zeros(cursor); o14=np.zeros(cursor); s13=np.zeros(cursor); s14=np.zeros(cursor); n13=np.zeros(cursor); n14=np.zeros(cursor); fold_diag=[]
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; require(tr.any() and te.any(),f'empty fold {fold}')
        m13=ranker.model(); m14=ranker.model(); m13.fit(Xall[tr],y13all[tr],sample_weight=weights[tr]); m14.fit(Xall[tr],y14all[tr],sample_weight=weights[tr])
        o13[te]=m13.predict(Xall[te]); o14[te]=m14.predict(Xall[te])
        gtr=[groups[i] for i in np.where(tr)[0]]
        s13[te],n13[te]=forest_support(m13,Xall[tr],y13all[tr],gtr,Xall[te]); s14[te],n14[te]=forest_support(m14,Xall[tr],y14all[tr],gtr,Xall[te])
        tg={groups[i] for i in np.where(te)[0]}; rg={groups[i] for i in np.where(tr)[0]}; require(tg.isdisjoint(rg),f'group leakage fold {fold}')
        fold_diag.append({'fold':fold,'train_examples':int(tr.sum()),'test_examples':int(te.sum()),'train_high_quality_2013_families':int(np.sum(y13all[tr]>RECOVERY)),'train_high_quality_2014_families':int(np.sum(y14all[tr]>RECOVERY)),'train_high_quality_2013_groups':len({groups[i] for i in np.where(tr & (y13all>RECOVERY))[0]}),'train_high_quality_2014_groups':len({groups[i] for i in np.where(tr & (y14all>RECOVERY))[0]})})

    worst=np.minimum(o13,o14); lo,hi=offsets['hdbscan']; rd=route_data['hdbscan']; ids=rd['ids']; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
    idx=ranker.diversity_order(worst[lo:hi],rd['centroids'],0.8,1.0,tie); quality=[ids[i] for i in idx]; fused=list(v19.fusion_orders(quality,list(map(str,rd['meta']['v19_order'])))['rank_sum']); rank={fid:i+1 for i,fid in enumerate(fused)}
    reranked=v22.rerank(rd['fams'],fused); reproduction={}
    for year,(macro,rec,budget) in EXPECTED_HDB.items():
        cur=v22.evaluate(reranked,truth[('hdbscan',year)],budget); require(abs(float(cur['macro_f1'])-macro)<1e-12 and int(cur['recovered_f1_gt_0_5'])==rec,f'v24 HDB {year} reproduction failed')
        reproduction[str(year)]={'macro_f1':float(cur['macro_f1']),'recovered_f1_gt_0_5':int(cur['recovered_f1_gt_0_5']),'budget':budget}

    annual={}
    for year,arr,supp,ng in ((2013,rd['y13'],s13[lo:hi],n13[lo:hi]),(2014,rd['y14'],s14[lo:hi],n14[lo:hi])):
        budget=EXPECTED_HDB[year][2]; rg=list(map(str,rd['groups'])); positive_groups=sorted({rg[i] for i in range(len(ids)) if rg[i].startswith('SHOWER/') and float(arr[i])>RECOVERY}); rows=[]
        for g in positive_groups:
            pos=[i for i in range(len(ids)) if rg[i]==g and float(arr[i])>RECOVERY]; best=min(pos,key=lambda i:rank[ids[i]]); r=rank[ids[best]]
            rows.append({'group':g,'family_id':ids[best],'first_positive_rank':r,'surfaced':bool(r<=budget),'annual_f1':float(arr[best]),'positive_leaf_support_fraction':float(supp[best]),'mean_positive_groups_in_leaf':float(ng[best]),'fold':int(folds[lo+best])})
        surfaced=[x for x in rows if x['surfaced']]; missed=[x for x in rows if not x['surfaced']]; require(len(surfaced)==EXPECTED_HDB[year][1],f'{year} surfaced recoverable-group count mismatch')
        annual[str(year)]={'budget':budget,'recoverable_groups':len(rows),'surfaced':summarize(surfaced),'missed':summarize(missed),'groups':rows}

    result={'verdict':'PASS_V24_HDB_OOF_TRAINING_SUPPORT_DIAGNOSTIC','scientific_role':'POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED','v24_hdb_reproduction':reproduction,'support_definition':'fraction of exact v24 forest trees where held-out family leaf contains >=1 fold-training family with annual F1>0.5; plus mean distinct positive strict groups in leaf','fold_diagnostics':fold_diag,'annual_group_diagnostics':annual,'support_threshold_search':False,'distance_metric_used':False,'feature_transform_used':False,'new_rank_evaluated':False,'successor_selected':False,'parameter_search':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0]}
    (a.output/'V24_HDB_OOF_TRAINING_SUPPORT_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'2013':annual['2013']|{'groups':'omitted'},'2014':annual['2014']|{'groups':'omitted'},'folds':fold_diag},indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
