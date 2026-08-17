#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

FEATURE_DIM=71
RECOVERY=0.5
EXPECTED={2013:(0.14888037368183737,9,11),2014:(0.15198123772301594,9,9)}


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def f1_for_members(members:set[str],truth_y:dict[str,str],label:str)->float:
    actual={eid for eid,v in truth_y.items() if v==label}
    pred=members & set(truth_y)
    if not actual or not pred: return 0.0
    ov=len(actual & pred)
    if ov==0: return 0.0
    p=ov/len(pred); r=ov/len(actual)
    return float(2*p*r/(p+r))


def rank_map(order:list[str])->dict[str,int]:
    return {fid:i+1 for i,fid in enumerate(order)}


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--payload-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker source changed')

    roots={r:a.payload_root/r for r in v24.ROUTES}
    truth={}; frozen={}
    for route,year in v24.PANELS:
        truth[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    ranker=v22.load_module(a.ranker_source,'frozen_839_v31_rankgap_diag')
    data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; offsets={}; cursor=0
    for route in v24.ROUTES:
        root=roots[route]
        meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and meta['feature_dimension']==FEATURE_DIM and fp['truth_accessed'] is False,f'{route} invalid immutable pretruth payload')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']
        require([str(f['family_id']) for f in fams]==ids,f'{route} family order changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),f'{route} array shape changed')
        require(v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],f'{route} immutable arrays changed')
        by={y:truth[(route,y)] for y in v24.YEARS}
        eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014])
        base=[v22.family_truth(f,hidden,eligible) for f in fams]
        y13=[]; y14=[]; rg=[]
        for i,(f,t) in enumerate(zip(fams,base)):
            label=t['best_label']; rg.append(('SHOWER/'+str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None: q13=q14=0.0
            else: q13,q14=v24.annual_f1_for_fixed_label(f,str(label),by)
            y13.append(float(q13)); y14.append(float(q14))
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids)
        Xs.append(X); y13s.append(np.asarray(y13,dtype=np.float64)); y14s.append(np.asarray(y14,dtype=np.float64)); groups.extend(rg)
        data[route]={'meta':meta,'fams':fams,'ids':ids,'centroids':C}

    Xall=np.vstack(Xs); y13=np.concatenate(y13s); y14=np.concatenate(y14s); groups=list(map(str,groups))
    require(Xall.shape==(cursor,FEATURE_DIM) and len(y13)==len(y14)==len(groups)==cursor,'stacked v31 input mismatch')
    folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],dtype=int)
    margin13=np.zeros(cursor,dtype=np.float64); margin14=np.zeros(cursor,dtype=np.float64)
    for fold in range(5):
        tr=folds!=fold; te=folds==fold
        require(tr.any() and te.any(),f'empty fold {fold}')
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),f'group leakage fold {fold}')
        mu=np.mean(Xall[tr],axis=0); sd=np.std(Xall[tr],axis=0,ddof=0); scale=sd.copy(); scale[scale==0.0]=1.0
        Ztr=(Xall[tr]-mu[None,:])/scale[None,:]; Zte=(Xall[te]-mu[None,:])/scale[None,:]
        te_idx=np.where(te)[0]
        for yall,out in ((y13,margin13),(y14,margin14)):
            pos=yall[tr]>RECOVERY; neg=~pos
            require(pos.any() and neg.any(),'v31 fold lacks positive/nonpositive references')
            P=Ztr[pos]; N=Ztr[neg]
            for j,global_i in enumerate(te_idx.tolist()):
                dpos=float(np.min(np.linalg.norm(P-Zte[j][None,:],axis=1)))
                dneg=float(np.min(np.linalg.norm(N-Zte[j][None,:],axis=1)))
                out[global_i]=dneg-dpos
    score=np.minimum(margin13,margin14)

    lo,hi=offsets['hdbscan']; rd=data['hdbscan']; ids=rd['ids']; route_score=score[lo:hi]
    tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
    tie_by={ids[i]:(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))}
    raw_order=sorted(ids,key=lambda fid:(-float(route_score[ids.index(fid)]),tie_by[fid]))
    didx=ranker.diversity_order(route_score,rd['centroids'],0.8,1.0,tie); diversity_order=[ids[i] for i in didx]
    v19_order=list(map(str,rd['meta']['v19_order']))
    fused_order=list(v19.fusion_orders(diversity_order,v19_order)['rank_sum'])
    ranked=v22.rerank(rd['fams'],fused_order)
    ranks={'raw':rank_map(raw_order),'diversity':rank_map(diversity_order),'v19':rank_map(v19_order),'fused':rank_map(fused_order)}
    by_fid={str(f['family_id']):f for f in rd['fams']}

    annual={}
    for year in (2013,2014):
        exp_macro,exp_rec,budget=EXPECTED[year]
        cur=v22.evaluate(ranked,truth[('hdbscan',year)],budget)
        require(abs(float(cur['macro_f1'])-exp_macro)<1e-12 and int(cur['recovered_f1_gt_0_5'])==exp_rec,f'exact v31 HDB {year} reproduction failed')
        truth_y=truth[('hdbscan',year)]; truth_ids=set(truth_y)
        labels=sorted(label for label,n in Counter(v for v in truth_y.values() if v!='SPORADIC').items() if n>=4)
        active_fused=[fid for fid in fused_order if set(map(str,by_fid[fid]['event_ids'])) & truth_ids][:budget]
        rows=[]
        for label in labels:
            cand=[]
            for fid in ids:
                members=set(map(str,by_fid[fid]['event_ids']))
                f1=f1_for_members(members,truth_y,label)
                if f1>0.0:
                    cand.append((float(f1),fid))
            if cand:
                cand.sort(key=lambda x:(-x[0],ranks['fused'][x[1]],x[1])); best_f1,best_fid=cand[0]
            else:
                best_f1,best_fid=0.0,None
            recoverable=[(f1,fid) for f1,fid in cand if f1>RECOVERY]
            surfaced=any(fid in active_fused for _f1,fid in recoverable)
            if recoverable:
                best_ranked=min(recoverable,key=lambda x:(ranks['fused'][x[1]],-x[0],x[1]))
                first_rec_f1,first_rec_fid=best_ranked
            else:
                first_rec_f1,first_rec_fid=None,None
            row={'label':label,'best_fixed_candidate_f1':float(best_f1),'best_fixed_candidate_family_id':best_fid,'candidate_recoverable':bool(recoverable),'v31_surfaced_recoverable':bool(surfaced),'recoverable_but_missed':bool(recoverable and not surfaced),'first_recoverable_family_id_by_v31_fused_rank':first_rec_fid,'first_recoverable_family_f1':None if first_rec_f1 is None else float(first_rec_f1)}
            if best_fid is not None:
                for k in ('raw','diversity','v19','fused'): row[f'best_candidate_{k}_rank']=int(ranks[k][best_fid])
            if first_rec_fid is not None:
                for k in ('raw','diversity','v19','fused'): row[f'first_recoverable_{k}_rank']=int(ranks[k][first_rec_fid])
                row['recoverable_in_top_2x_budget']=bool(ranks['fused'][first_rec_fid]<=2*budget)
                row['recoverable_in_top_5x_budget']=bool(ranks['fused'][first_rec_fid]<=5*budget)
            else:
                row['recoverable_in_top_2x_budget']=False; row['recoverable_in_top_5x_budget']=False
            rows.append(row)
        recoverable_rows=[r for r in rows if r['candidate_recoverable']]; missed=[r for r in rows if r['recoverable_but_missed']]; no_candidate=[r for r in rows if not r['candidate_recoverable']]
        annual[str(year)]={
            'budget':budget,'eligible_truth_showers':len(labels),'candidate_recoverable_showers':len(recoverable_rows),'no_recoverable_fixed_candidate_showers':len(no_candidate),'v31_surfaced_recoverable_showers':sum(int(r['v31_surfaced_recoverable']) for r in rows),'recoverable_but_missed_showers':len(missed),
            'missed_with_recoverable_candidate_top_2x_budget':sum(int(r['recoverable_in_top_2x_budget']) for r in missed),'missed_with_recoverable_candidate_top_5x_budget':sum(int(r['recoverable_in_top_5x_budget']) for r in missed),
            'missed_first_recoverable_fused_rank_median':None if not missed else float(np.median([r['first_recoverable_fused_rank'] for r in missed])),
            'missed_first_recoverable_fused_rank_min':None if not missed else int(min(r['first_recoverable_fused_rank'] for r in missed)),
            'missed_first_recoverable_fused_rank_max':None if not missed else int(max(r['first_recoverable_fused_rank'] for r in missed)),
            'rows':rows,
        }

    result={
        'verdict':'PASS_V31_HDB_MISSED_LABEL_RANKGAP_DIAGNOSTIC',
        'scientific_role':'POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED',
        'v31_reproduction':{str(y):{'macro_f1':EXPECTED[y][0],'recovered_f1_gt_0_5':EXPECTED[y][1],'budget':EXPECTED[y][2]} for y in (2013,2014)},
        'annual':annual,
        'orders_described':['raw local-margin','exact #839 diversity','immutable v19','final v31 v19 rank-sum'],
        'new_rank_evaluated':False,'successor_selected':False,'cutoff_selected':False,'candidate_membership_changed':False,'feature_search':False,'model_search':False,'metric_search':False,'k_search':False,'threshold_search':False,'diversity_search':False,'fusion_search':False,'parameter_search':False,'post_result_second_search':False,
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0],
    }
    (a.output/'V31_HDB_MISSED_LABEL_RANKGAP_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    compact={y:{k:v for k,v in annual[y].items() if k!='rows'} for y in ('2013','2014')}
    print(json.dumps({'verdict':result['verdict'],'annual':compact},indent=2,sort_keys=True,allow_nan=False))
    return 0

if __name__=='__main__': raise SystemExit(main())
