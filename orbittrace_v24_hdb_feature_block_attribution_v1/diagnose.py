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

FEATURE_DIM=71
RECOVERY=0.5
EXPECTED_HDB={2013:(0.14257102406283795,10,11),2014:(0.12833942693327394,7,9)}
EXPECTED_PARENT_DPOS={
    2013:{'surfaced':4.179654955965411,'missed':5.360340816398479},
    2014:{'surfaced':3.6639341298550545,'missed':5.87364761526218},
}
BLOCKS={
    'raw_839':(0,34),
    'relative_noncat_839':(34,64),
    'rank_percentiles':(64,67),
    'consensus_graph':(67,71),
}


def require(ok:bool,msg:str)->None:
    if not ok:
        raise RuntimeError(msg)


def summarize_block(rows:list[dict[str,Any]],block:str)->dict[str,Any]:
    if not rows:
        return {'groups':0,'median_squared_contribution':0.0,'median_fraction_total':0.0,'median_rms':0.0,'q90_rms':0.0}
    b=[r['blocks'][block] for r in rows]
    sq=np.asarray([float(x['squared_contribution']) for x in b],float)
    frac=np.asarray([float(x['fraction_total']) for x in b],float)
    rms=np.asarray([float(x['rms_standardized_difference']) for x in b],float)
    return {
        'groups':len(rows),
        'median_squared_contribution':float(np.median(sq)),
        'median_fraction_total':float(np.median(frac)),
        'median_rms':float(np.median(rms)),
        'q90_rms':float(np.quantile(rms,0.9)),
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
    require(sum(b-a0 for a0,b in BLOCKS.values())==FEATURE_DIM,'feature block dimensions changed')
    require(sorted([x for bounds in BLOCKS.values() for x in bounds]) is not None,'invalid block declaration')

    roots={'sugar':a.sugar_root,'hdbscan':a.hdbscan_root}
    truth={}
    for route,year in v24.PANELS:
        truth[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())

    ranker=v22.load_module(a.ranker_source,'frozen_839_feature_block_attribution')
    route_data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; routes=[]; ids_all=[]; offsets={}; cursor=0
    for route in v24.ROUTES:
        root=roots[route]
        meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['feature_dimension']==FEATURE_DIM and meta['truth_accessed'] is False and fp['truth_accessed'] is False,f'{route} invalid immutable pretruth payload')
        require(meta['feature_blocks']=={'raw_839':34,'relative_noncat_839':30,'rank_percentiles':3,'consensus_graph':4},f'{route} feature-block manifest changed')
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
    require(Xall.shape==(cursor,FEATURE_DIM) and len(y13all)==len(y14all)==len(groups)==len(routes)==len(ids_all)==cursor,'stacked input mismatch')
    folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],dtype=int)
    weights=np.asarray(ranker.grouped_weights(groups),float)

    o13=np.zeros(cursor); o14=np.zeros(cursor); fold_stats={}
    for fold in range(5):
        tr=folds!=fold; te=folds==fold
        require(tr.any() and te.any(),f'empty fold {fold}')
        train_groups={groups[i] for i in np.where(tr)[0]}; test_groups={groups[i] for i in np.where(te)[0]}
        require(train_groups.isdisjoint(test_groups),f'group leakage fold {fold}')
        m13=ranker.model(); m14=ranker.model(); m13.fit(Xall[tr],y13all[tr],sample_weight=weights[tr]); m14.fit(Xall[tr],y14all[tr],sample_weight=weights[tr]); o13[te]=m13.predict(Xall[te]); o14[te]=m14.predict(Xall[te])
        mu=np.mean(Xall[tr],axis=0); sd=np.std(Xall[tr],axis=0,ddof=0); scale=sd.copy(); scale[scale==0.0]=1.0
        require(mu.shape==(FEATURE_DIM,) and scale.shape==(FEATURE_DIM,) and np.all(np.isfinite(mu)) and np.all(np.isfinite(scale)),'invalid fold scaling')
        fold_stats[fold]=(mu,scale)
    worst=np.minimum(o13,o14)

    lo,hi=offsets['hdbscan']; rd=route_data['hdbscan']; ids=rd['ids']; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
    idx=ranker.diversity_order(worst[lo:hi],rd['centroids'],0.8,1.0,tie); quality=[ids[i] for i in idx]
    v19_order=list(map(str,rd['meta']['v19_order'])); fused=list(v19.fusion_orders(quality,v19_order)['rank_sum'])
    reranked=v22.rerank(rd['fams'],fused); rank={fid:i+1 for i,fid in enumerate(fused)}
    reproduction={}
    for year in (2013,2014):
        macro,rec,budget=EXPECTED_HDB[year]; cur=v22.evaluate(reranked,truth[('hdbscan',year)],budget)
        require(abs(float(cur['macro_f1'])-macro)<1e-12 and int(cur['recovered_f1_gt_0_5'])==rec,f'v24 HDB {year} reproduction failed')
        reproduction[str(year)]={'macro_f1':float(cur['macro_f1']),'recovered_f1_gt_0_5':int(cur['recovered_f1_gt_0_5']),'budget':budget}

    annual_all={2013:y13all,2014:y14all}; annual_hdb={2013:rd['y13'],2014:rd['y14']}; diagnostics={}
    for year in (2013,2014):
        arr_all=annual_all[year]; arr_hdb=annual_hdb[year]; family_rows=[]; by_local={}
        for local_i in np.where(arr_hdb>RECOVERY)[0].tolist():
            gi=lo+local_i; fold=int(folds[gi]); tr=folds!=fold; pos=tr & (arr_all>RECOVERY)
            require(pos.any(),f'{year} fold {fold} lacks positive reference')
            mu,scale=fold_stats[fold]; z=(Xall[gi]-mu)/scale; ztrain=(Xall-mu[None,:])/scale[None,:]
            pidx=np.where(pos)[0]; dp=np.linalg.norm(ztrain[pidx]-z[None,:],axis=1); require(np.all(np.isfinite(dp)),'nonfinite positive support distance')
            jp=int(pidx[int(np.argmin(dp))]); require(groups[jp]!=groups[gi],f'{year} nearest positive leaked same shower group')
            diff2=np.square(ztrain[jp]-z); total=float(np.sum(diff2)); require(total>0.0 and np.isfinite(total),'invalid nearest-positive squared distance')
            blocks={}
            for name,(start,stop) in BLOCKS.items():
                sq=float(np.sum(diff2[start:stop])); dim=stop-start
                blocks[name]={
                    'dimension':dim,
                    'squared_contribution':sq,
                    'fraction_total':float(sq/total),
                    'rms_standardized_difference':float(np.sqrt(sq/dim)),
                }
            require(abs(sum(x['fraction_total'] for x in blocks.values())-1.0)<1e-12,'block contribution fractions do not sum to one')
            row={
                'family_id':ids[local_i],'group':rd['groups'][local_i],'annual_f1':float(arr_hdb[local_i]),'fold':fold,'v24_rank':int(rank[ids[local_i]]),
                'nearest_positive_distance':float(np.sqrt(total)),
                'nearest_positive_reference':{'route':routes[jp],'family_id':ids_all[jp],'group':groups[jp],'annual_f1':float(arr_all[jp])},
                'blocks':blocks,
            }
            family_rows.append(row); by_local[local_i]=row

        positive_groups=sorted({rd['groups'][i] for i in np.where(arr_hdb>RECOVERY)[0] if rd['groups'][i].startswith('SHOWER/')})
        group_rows=[]; surfaced_count=0
        for g in positive_groups:
            inds=[int(i) for i in np.where(arr_hdb>RECOVERY)[0] if rd['groups'][int(i)]==g]
            rep=sorted(inds,key=lambda i:(rank[ids[i]],ids[i]))[0]; base=dict(by_local[rep]); surfaced=int(base['v24_rank'])<=EXPECTED_HDB[year][2]; surfaced_count+=int(surfaced)
            base.update({'representative_family_id':ids[rep],'annual_recoverable_families':len(inds),'surfaced':bool(surfaced)}); group_rows.append(base)
        require(surfaced_count==EXPECTED_HDB[year][1],f'{year} surfaced group count does not reproduce v24')
        surfaced=[r for r in group_rows if r['surfaced']]; missed=[r for r in group_rows if not r['surfaced']]
        parent_s=float(np.median([r['nearest_positive_distance'] for r in surfaced])); parent_m=float(np.median([r['nearest_positive_distance'] for r in missed]))
        require(abs(parent_s-EXPECTED_PARENT_DPOS[year]['surfaced'])<1e-12 and abs(parent_m-EXPECTED_PARENT_DPOS[year]['missed'])<1e-12,f'{year} parent #1021 nearest-positive geometry reproduction failed')
        diagnostics[str(year)]={
            'budget':EXPECTED_HDB[year][2],'annual_recoverable_groups':len(group_rows),
            'parent_nearest_positive_distance_median':{'surfaced':parent_s,'missed':parent_m},
            'surfaced_block_summary':{b:summarize_block(surfaced,b) for b in BLOCKS},
            'missed_block_summary':{b:summarize_block(missed,b) for b in BLOCKS},
            'group_representatives':group_rows,'annual_positive_family_attribution':family_rows,
        }

    result={
        'verdict':'PASS_V24_HDB_FEATURE_BLOCK_ATTRIBUTION_DIAGNOSTIC',
        'scientific_role':'POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED',
        'v24_hdb_reproduction':reproduction,
        'parent_1021_geometry_reproduced':True,
        'feature_blocks':{k:{'start':v[0],'stop':v[1],'dimension':v[1]-v[0]} for k,v in BLOCKS.items()},
        'attribution_rule':'decompose squared standardized difference to the single full-71D nearest annual-positive OOF training reference; no block-specific nearest-reference recomputation',
        'annual_diagnostics':diagnostics,
        'successor_selected':False,'feature_subset_selected':False,'block_weight_selected':False,'new_rank_or_score_evaluated':False,'feature_search':False,'metric_search':False,'parameter_search':False,'post_result_second_search':False,
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0],
    }
    (a.output/'V24_HDB_FEATURE_BLOCK_ATTRIBUTION_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    compact={'verdict':result['verdict'],'v24_hdb_reproduction':reproduction,'parent_1021_geometry_reproduced':True}
    for year in ('2013','2014'):
        compact[year]={k:v for k,v in diagnostics[year].items() if k not in ('group_representatives','annual_positive_family_attribution')}
    print(json.dumps(compact,indent=2,sort_keys=True,allow_nan=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
