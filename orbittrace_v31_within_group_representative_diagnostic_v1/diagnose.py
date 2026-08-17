#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

FEATURE_DIM=71
RECOVERY=0.5
EXPECTED={2013:(0.14888037368183737,9,11),2014:(0.15198123772301594,9,9)}


def require(ok:bool,msg:str)->None:
    if not ok:
        raise RuntimeError(msg)


def order_sha(order:list[str])->str:
    return hashlib.sha256('\n'.join(map(str,order)).encode()).hexdigest()


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--payload-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker source changed')
    ranker=v22.load_module(a.ranker_source,'frozen_839_v31_repdiag')

    truth={}; frozen={}
    for route,year in v24.PANELS:
        truth[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; offsets={}; cursor=0
    for route in v24.ROUTES:
        root=a.payload_root/route
        meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and fp['truth_accessed'] is False and meta['feature_dimension']==FEATURE_DIM,f'{route} invalid pretruth payload')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']
        require([str(f['family_id']) for f in fams]==ids,f'{route} family alignment changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),f'{route} array shape changed')
        require(v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],f'{route} array identity changed')
        by={y:truth[(route,y)] for y in v24.YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014])
        base=[v22.family_truth(f,hidden,eligible) for f in fams]
        q13=[]; q14=[]; rg=[]
        for i,(fam,t) in enumerate(zip(fams,base)):
            label=t['best_label']; rg.append(('SHOWER/'+str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None: a13=a14=0.0
            else: a13,a14=v24.annual_f1_for_fixed_label(fam,str(label),by)
            q13.append(float(a13)); q14.append(float(a14))
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids)
        Xs.append(X); y13s.append(np.asarray(q13,float)); y14s.append(np.asarray(q14,float)); groups.extend(rg)
        data[route]={'meta':meta,'fams':fams,'ids':ids,'centroids':C,'groups':rg,'y13':np.asarray(q13,float),'y14':np.asarray(q14,float)}

    Xall=np.vstack(Xs); y13all=np.concatenate(y13s); y14all=np.concatenate(y14s); groups=list(map(str,groups))
    require(Xall.shape==(cursor,FEATURE_DIM) and len(groups)==len(y13all)==len(y14all)==cursor,'stacked input mismatch')
    folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],dtype=int)
    margin13=np.zeros(cursor,float); margin14=np.zeros(cursor,float)
    for fold in range(5):
        tr=folds!=fold; te=folds==fold
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),f'group leakage fold {fold}')
        mu=np.mean(Xall[tr],axis=0); sd=np.std(Xall[tr],axis=0,ddof=0); scale=sd.copy(); scale[scale==0.0]=1.0
        Ztr=(Xall[tr]-mu[None,:])/scale[None,:]; Zte=(Xall[te]-mu[None,:])/scale[None,:]; teidx=np.where(te)[0]
        for year,yall,out in ((2013,y13all,margin13),(2014,y14all,margin14)):
            pos=yall[tr]>RECOVERY; neg=~pos; require(pos.any() and neg.any(),f'{year} fold {fold} lacks references')
            P=Ztr[pos]; N=Ztr[neg]
            for j,gi in enumerate(teidx.tolist()):
                out[gi]=float(np.min(np.linalg.norm(N-Zte[j][None,:],axis=1))-np.min(np.linalg.norm(P-Zte[j][None,:],axis=1)))
    score=np.minimum(margin13,margin14); require(np.all(np.isfinite(score)),'nonfinite v31 score')

    lo,hi=offsets['hdbscan']; rd=data['hdbscan']; ids=rd['ids']; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
    idx=ranker.diversity_order(score[lo:hi],rd['centroids'],0.8,1.0,tie); local=[ids[i] for i in idx]
    v19order=list(map(str,rd['meta']['v19_order'])); v31order=list(v19.fusion_orders(local,v19order)['rank_sum']); v31ranked=v22.rerank(rd['fams'],v31order)
    require(len(v31order)==len(ids) and set(v31order)==set(ids),'v31 order universe changed')
    byid={fid:i for i,fid in enumerate(ids)}; diagnostics={}

    for year in (2013,2014):
        exp_macro,exp_rec,budget=EXPECTED[year]
        cur=v22.evaluate(v31ranked,truth[('hdbscan',year)],budget)
        require(abs(float(cur['macro_f1'])-exp_macro)<1e-12 and int(cur['recovered_f1_gt_0_5'])==exp_rec,f'v31 HDB {year} reproduction failed')
        annual=rd['y13'] if year==2013 else rd['y14']
        group_to_inds=defaultdict(list)
        for i,g in enumerate(rd['groups']):
            if g.startswith('SHOWER/'): group_to_inds[g].append(i)
        recoverable_groups={g for g,inds in group_to_inds.items() if any(float(annual[i])>RECOVERY for i in inds)}
        top=v31order[:budget]; top_groups=[rd['groups'][byid[fid]] for fid in top]
        top_recoverable={g for g in top_groups if g in recoverable_groups}
        counts=Counter(top_groups)

        oracle_top=list(top); slot_rows=[]
        for g,count in sorted(counts.items()):
            positions=[j for j,x in enumerate(top_groups) if x==g]
            if not g.startswith('SHOWER/'):
                for j in positions:
                    i=byid[top[j]]; slot_rows.append({'slot':j+1,'group':g,'selected_family_id':top[j],'selected_annual_f1':float(annual[i]),'oracle_family_id':top[j],'oracle_annual_f1':float(annual[i]),'annual_f1_gain':0.0,'annual_recoverable_group':False})
                continue
            candidates=sorted(group_to_inds[g],key=lambda i:(-float(annual[i]),ids[i]))
            require(len(candidates)>=count,f'group {g} lacks enough distinct candidates for slot-preserving oracle')
            chosen=candidates[:count]
            for j,ci in zip(positions,chosen):
                si=byid[top[j]]; oracle_top[j]=ids[ci]
                slot_rows.append({'slot':j+1,'group':g,'selected_family_id':top[j],'selected_annual_f1':float(annual[si]),'oracle_family_id':ids[ci],'oracle_annual_f1':float(annual[ci]),'annual_f1_gain':float(annual[ci]-annual[si]),'annual_recoverable_group':bool(g in recoverable_groups)})
        require(len(oracle_top)==budget and len(set(oracle_top))==budget,'oracle top contains duplicate family')
        used=set(oracle_top); oracle_order=oracle_top+[fid for fid in v31order if fid not in used]
        require(len(oracle_order)==len(v31order) and set(oracle_order)==set(v31order),'oracle full order universe changed')
        oracle_ranked=v22.rerank(rd['fams'],oracle_order); om=v22.evaluate(oracle_ranked,truth[('hdbscan',year)],budget); lit=frozen[('hdbscan',year)]['comparator_summary']
        gains=np.asarray([float(r['annual_f1_gain']) for r in slot_rows if r['group'].startswith('SHOWER/')],float)
        diagnostics[str(year)]={
            'budget':budget,
            'v31':{'macro_f1':float(cur['macro_f1']),'recovered_f1_gt_0_5':int(cur['recovered_f1_gt_0_5'])},
            'group_constrained_oracle':{'macro_f1':float(om['macro_f1']),'recovered_f1_gt_0_5':int(om['recovered_f1_gt_0_5']),'beats_literature_gate':bool(float(om['macro_f1'])>float(lit['macro_f1']) and int(om['recovered_f1_gt_0_5'])>=int(lit['recovered_f1_gt_0_5'])),'order_sha256':order_sha(oracle_order)},
            'literature':{'macro_f1':float(lit['macro_f1']),'recovered_f1_gt_0_5':int(lit['recovered_f1_gt_0_5'])},
            'top_budget_unique_strict_shower_groups':len({g for g in top_groups if g.startswith('SHOWER/')}),
            'top_budget_neg_slots':sum(g.startswith('NEG/') for g in top_groups),
            'annual_recoverable_groups_in_fixed_universe':len(recoverable_groups),
            'annual_recoverable_groups_surfaced_top_budget':len(top_recoverable),
            'comparator_recovery_count':int(lit['recovered_f1_gt_0_5']),
            'global_group_shortfall_vs_comparator':max(0,int(lit['recovered_f1_gt_0_5'])-len(top_recoverable)),
            'median_same_group_representative_f1_gain':float(np.median(gains)) if len(gains) else 0.0,
            'max_same_group_representative_f1_gain':float(np.max(gains)) if len(gains) else 0.0,
            'slots':sorted(slot_rows,key=lambda r:r['slot']),
        }

    result={
        'verdict':'PASS_V31_WITHIN_GROUP_REPRESENTATIVE_DIAGNOSTIC',
        'scientific_role':'POST_RESULT_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED',
        'v31_hdb_order_sha256':order_sha(v31order),
        'annual_diagnostics':diagnostics,
        'oracle_constraint':'top-budget strict group multiset fixed exactly to v31; only same-group fixed-family representatives may change',
        'successor_selected':False,'representative_rule_selected':False,'membership_changed':False,'new_group_introduced_by_oracle':False,'parameter_search':False,'feature_search':False,'model_search':False,'post_result_second_search':False,
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0],
    }
    (a.output/'V31_WITHIN_GROUP_REPRESENTATIVE_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    compact={'verdict':result['verdict'],'v31_hdb_order_sha256':result['v31_hdb_order_sha256'],'annual_diagnostics':{}}
    for year in ('2013','2014'):
        compact['annual_diagnostics'][year]={k:v for k,v in diagnostics[year].items() if k!='slots'}
    print(json.dumps(compact,indent=2,sort_keys=True,allow_nan=False)); return 0


if __name__=='__main__':
    raise SystemExit(main())
