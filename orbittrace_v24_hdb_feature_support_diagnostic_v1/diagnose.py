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

EXPECTED_HDB={2013:(0.14257102406283795,10,11),2014:(0.12833942693327394,7,9)}
RECOVERY=0.5
FEATURE_DIM=71


def require(ok:bool,msg:str)->None:
    if not ok:
        raise RuntimeError(msg)


def summarize(rows:list[dict[str,Any]])->dict[str,Any]:
    if not rows:
        return {
            'groups':0,'nearest_positive_distance_median':0.0,'nearest_positive_distance_q90':0.0,
            'nearest_negative_distance_median':0.0,'support_margin_median':0.0,
            'closer_to_positive_count':0,'closer_to_positive_fraction':0.0,'v24_rank_median':0.0,
        }
    dpos=np.asarray([float(r['nearest_positive_distance']) for r in rows],float)
    dneg=np.asarray([float(r['nearest_negative_distance']) for r in rows],float)
    margin=np.asarray([float(r['support_margin']) for r in rows],float)
    rank=np.asarray([int(r['v24_rank']) for r in rows],float)
    closer=sum(bool(r['closer_to_positive']) for r in rows)
    return {
        'groups':len(rows),
        'nearest_positive_distance_median':float(np.median(dpos)),
        'nearest_positive_distance_q90':float(np.quantile(dpos,0.9)),
        'nearest_negative_distance_median':float(np.median(dneg)),
        'support_margin_median':float(np.median(margin)),
        'closer_to_positive_count':int(closer),
        'closer_to_positive_fraction':float(closer/len(rows)),
        'v24_rank_median':float(np.median(rank)),
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--sugar-root',type=Path,required=True)
    p.add_argument('--hdbscan-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker source changed')

    roots={'sugar':a.sugar_root,'hdbscan':a.hdbscan_root}
    truth={}
    for route,year in v24.PANELS:
        truth[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())

    ranker=v22.load_module(a.ranker_source,'frozen_839_feature_support_diag')
    route_data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; routes=[]; ids_all=[]; offsets={}; cursor=0
    for route in v24.ROUTES:
        root=roots[route]
        meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['feature_dimension']==FEATURE_DIM and meta['truth_accessed'] is False and fp['truth_accessed'] is False,f'{route} invalid immutable pretruth payload')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']
        require([str(f['family_id']) for f in fams]==ids,f'{route} family alignment changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),f'{route} immutable array shape changed')
        require(v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],f'{route} immutable array hash changed')
        by={y:truth[(route,y)] for y in v24.YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014])
        base_truths=[v22.family_truth(f,hidden,eligible) for f in fams]
        y13=[]; y14=[]; route_groups=[]
        for i,(f,t) in enumerate(zip(fams,base_truths)):
            label=t['best_label']; route_groups.append(('SHOWER/'+str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None:
                y13.append(0.0); y14.append(0.0)
            else:
                q13,q14=v24.annual_f1_for_fixed_label(f,str(label),by); y13.append(q13); y14.append(q14)
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids)
        Xs.append(X); y13s.append(np.asarray(y13,float)); y14s.append(np.asarray(y14,float)); groups.extend(route_groups); routes.extend([route]*len(ids)); ids_all.extend(ids)
        route_data[route]={'meta':meta,'fams':fams,'ids':ids,'centroids':C,'groups':route_groups,'y13':np.asarray(y13,float),'y14':np.asarray(y14,float)}

    Xall=np.vstack(Xs); y13all=np.concatenate(y13s); y14all=np.concatenate(y14s); groups=list(map(str,groups)); routes=list(map(str,routes)); ids_all=list(map(str,ids_all))
    require(Xall.shape==(cursor,FEATURE_DIM) and len(y13all)==len(y14all)==len(groups)==len(routes)==len(ids_all)==cursor,'stacked geometry input mismatch')
    folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],dtype=int)
    weights=np.asarray(ranker.grouped_weights(groups),float)

    # Exact v24 replay; this is a gate, not a new model.
    o13=np.zeros(cursor); o14=np.zeros(cursor)
    fold_stats={}
    for fold in range(5):
        tr=folds!=fold; te=folds==fold
        require(tr.any() and te.any(),f'empty fold {fold}')
        train_groups={groups[i] for i in np.where(tr)[0]}; test_groups={groups[i] for i in np.where(te)[0]}
        require(train_groups.isdisjoint(test_groups),f'group leakage fold {fold}')
        m13=ranker.model(); m14=ranker.model(); m13.fit(Xall[tr],y13all[tr],sample_weight=weights[tr]); m14.fit(Xall[tr],y14all[tr],sample_weight=weights[tr]); o13[te]=m13.predict(Xall[te]); o14[te]=m14.predict(Xall[te])
        mu=np.mean(Xall[tr],axis=0); sd=np.std(Xall[tr],axis=0,ddof=0)
        require(mu.shape==(FEATURE_DIM,) and sd.shape==(FEATURE_DIM,) and np.all(np.isfinite(mu)) and np.all(np.isfinite(sd)),'invalid fold scaling statistics')
        zero=sd==0.0; scale=sd.copy(); scale[zero]=1.0
        fold_stats[fold]={'mean':mu,'scale':scale,'zero_variance_features':int(np.sum(zero))}
    worst=np.minimum(o13,o14)

    lo,hi=offsets['hdbscan']; rd=route_data['hdbscan']; ids=rd['ids']; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
    idx=ranker.diversity_order(worst[lo:hi],rd['centroids'],0.8,1.0,tie); quality=[ids[i] for i in idx]; v19_order=list(map(str,rd['meta']['v19_order'])); fused=list(v19.fusion_orders(quality,v19_order)['rank_sum'])
    reranked=v22.rerank(rd['fams'],fused); rank={fid:i+1 for i,fid in enumerate(fused)}
    reproduction={}
    for year in (2013,2014):
        macro,rec,budget=EXPECTED_HDB[year]; cur=v22.evaluate(reranked,truth[('hdbscan',year)],budget)
        require(abs(float(cur['macro_f1'])-macro)<1e-12 and int(cur['recovered_f1_gt_0_5'])==rec,f'v24 HDB {year} reproduction failed')
        reproduction[str(year)]={'macro_f1':float(cur['macro_f1']),'recovered_f1_gt_0_5':int(cur['recovered_f1_gt_0_5']),'budget':budget}

    annual_all={2013:y13all,2014:y14all}; annual_hdb={2013:rd['y13'],2014:rd['y14']}; per_year={}
    for year in (2013,2014):
        arr_all=annual_all[year]; arr_hdb=annual_hdb[year]; family_rows=[]; support_by_local={}
        for local_i in np.where(arr_hdb>RECOVERY)[0].tolist():
            gi=lo+local_i; fold=int(folds[gi]); tr=folds!=fold; pos=tr & (arr_all>RECOVERY); neg=tr & ~(arr_all>RECOVERY)
            require(pos.any() and neg.any(),f'{year} fold {fold} lacks positive or negative geometry reference')
            mu=fold_stats[fold]['mean']; scale=fold_stats[fold]['scale']; z=(Xall[gi]-mu)/scale; ztrain=(Xall-mu[None,:])/scale[None,:]
            pidx=np.where(pos)[0]; nidx=np.where(neg)[0]
            dp=np.linalg.norm(ztrain[pidx]-z[None,:],axis=1); dn=np.linalg.norm(ztrain[nidx]-z[None,:],axis=1)
            require(np.all(np.isfinite(dp)) and np.all(np.isfinite(dn)),'nonfinite support distance')
            jp=int(pidx[int(np.argmin(dp))]); jn=int(nidx[int(np.argmin(dn))]); dpos=float(np.min(dp)); dneg=float(np.min(dn))
            require(groups[jp]!=groups[gi],f'{year} nearest positive leaked same shower group')
            row={
                'family_id':ids[local_i],'group':rd['groups'][local_i],'annual_f1':float(arr_hdb[local_i]),'fold':fold,'v24_rank':int(rank[ids[local_i]]),
                'nearest_positive_distance':dpos,'nearest_negative_distance':dneg,'support_margin':float(dneg-dpos),'closer_to_positive':bool(dpos<dneg),
                'nearest_positive_reference':{'route':routes[jp],'family_id':ids_all[jp],'group':groups[jp],'annual_f1':float(arr_all[jp])},
                'nearest_negative_reference':{'route':routes[jn],'family_id':ids_all[jn],'group':groups[jn],'annual_f1':float(arr_all[jn])},
            }
            family_rows.append(row); support_by_local[local_i]=row

        positive_groups=sorted({rd['groups'][i] for i in np.where(arr_hdb>RECOVERY)[0] if rd['groups'][i].startswith('SHOWER/')})
        group_rows=[]; surfaced_count=0
        for g in positive_groups:
            inds=[int(i) for i in np.where(arr_hdb>RECOVERY)[0] if rd['groups'][int(i)]==g]
            require(inds,'empty positive group')
            rep=sorted(inds,key=lambda i:(rank[ids[i]],ids[i]))[0]; base=support_by_local[rep].copy(); surfaced=int(base['v24_rank'])<=EXPECTED_HDB[year][2]; surfaced_count+=int(surfaced)
            base.update({'representative_family_id':ids[rep],'annual_recoverable_families':len(inds),'surfaced':bool(surfaced)})
            group_rows.append(base)
        require(surfaced_count==EXPECTED_HDB[year][1],f'{year} surfaced support groups do not reproduce v24 recovered count')
        surfaced=[r for r in group_rows if r['surfaced']]; missed=[r for r in group_rows if not r['surfaced']]
        per_year[str(year)]={
            'budget':EXPECTED_HDB[year][2],'annual_recoverable_groups':len(group_rows),
            'surface_definition':'earliest-ranked annual-positive family at or above frozen comparator budget',
            'group_representative_definition':'annual-positive family with earliest exact v24 final rank; stable family_id tie-break',
            'surfaced_summary':summarize(surfaced),'missed_summary':summarize(missed),
            'group_representatives':group_rows,'annual_positive_family_support':family_rows,
        }

    result={
        'verdict':'PASS_V24_HDB_FEATURE_SUPPORT_DIAGNOSTIC',
        'scientific_role':'POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED',
        'v24_hdb_reproduction':reproduction,
        'geometry':{
            'features':FEATURE_DIM,'scaling':'training-fold arithmetic mean and population std (ddof=0); exactly-zero std replaced by 1.0','distance':'ordinary Euclidean across all 71 standardized dimensions',
            'positive_reference_definition':'annual F1 > 0.5 for exact v22 fixed best label among OOF training examples','negative_reference_definition':'all remaining OOF training examples',
            'same_shower_reference_allowed':False,'feature_selection':False,'distance_search':False,'nearest_k':1,
        },
        'annual_diagnostics':per_year,
        'successor_selected':False,'new_rank_or_score_evaluated':False,'distance_cutoff_selected':False,'significance_threshold_selected':False,'feature_search':False,'metric_search':False,'parameter_search':False,'post_result_second_search':False,
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0],
    }
    (a.output/'V24_HDB_FEATURE_SUPPORT_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    compact={'verdict':result['verdict'],'v24_hdb_reproduction':reproduction,'geometry':result['geometry'],'2013':{k:v for k,v in per_year['2013'].items() if k not in ('group_representatives','annual_positive_family_support')},'2014':{k:v for k,v in per_year['2014'].items() if k not in ('group_representatives','annual_positive_family_support')}}
    print(json.dumps(compact,indent=2,sort_keys=True,allow_nan=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
