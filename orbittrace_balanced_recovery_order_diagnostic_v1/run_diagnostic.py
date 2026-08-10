#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from orbittrace_sonotaco_balanced_recovery_oof_v1 import train_evaluate as br


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def q(x:list[int],p:float)->float:
    return float(np.quantile(np.asarray(x,dtype=float),p)) if x else float('nan')


def order_target_summary(order:list[str],ids:list[str],y:np.ndarray,groups:list[str],budgets:dict[int,int])->dict[str,Any]:
    rank={fid:i+1 for i,fid in enumerate(order)}
    first={}
    for i,fid in enumerate(ids):
        if int(y[i])!=1: continue
        g=groups[i]; r=rank[fid]
        old=first.get(g)
        if old is None or r<old: first[g]=r
    ranks=sorted(first.values())
    budget_rows={}
    for year,budget in sorted(budgets.items()):
        top=set(order[:budget]); fam_count=int(sum(int(y[i])==1 and ids[i] in top for i in range(len(ids))))
        grp_count=int(sum(r<=budget for r in ranks))
        budget_rows[str(year)]={'budget':int(budget),'positive_families_in_top_budget':fam_count,'distinct_positive_shower_groups_in_top_budget':grp_count}
    return {
        'distinct_positive_shower_groups':len(ranks),
        'positive_families':int(np.sum(y==1)),
        'first_rank_best':int(min(ranks)) if ranks else None,
        'first_rank_median':q(ranks,0.50),
        'first_rank_q75':q(ranks,0.75),
        'first_rank_q90':q(ranks,0.90),
        'first_rank_worst':int(max(ranks)) if ranks else None,
        'budgets':budget_rows,
    }


def group_score_metrics(scores:np.ndarray,y:np.ndarray,groups:list[str])->dict[str,float]:
    by=defaultdict(list)
    for i,g in enumerate(groups): by[g].append(i)
    gy=[]; gs=[]
    for g,idx in sorted(by.items()):
        gy.append(int(np.any(y[idx]==1))); gs.append(float(np.max(scores[idx])))
    gyarr=np.asarray(gy,dtype=int); gsarr=np.asarray(gs,dtype=float)
    req(np.unique(gyarr).size==2,'group target degenerate')
    return {'groups':len(gy),'positive_groups':int(np.sum(gyarr==1)),'roc_auc':float(roc_auc_score(gyarr,gsarr)),'average_precision':float(average_precision_score(gyarr,gsarr))}


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--sugar-root',type=Path,required=True)
    p.add_argument('--hdbscan-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True)
    p.add_argument('--reference-result',type=Path,required=False)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(br.v23.sha(a.ranker_source)==br.RANKER_SOURCE_SHA,'#839 ranker source changed')
    roots={'sugar':a.sugar_root,'hdbscan':a.hdbscan_root}

    for route in br.ROUTES:
        for name,expected in br.EXPECTED_EXACT_FILE_SHA[route].items():
            req(br.v23.sha(roots[route]/name)==expected,f'{route} {name} differs from valid v22 pretruth payload')
        X=np.load(roots[route]/'features.npy',allow_pickle=False)
        req(X.shape[1]==br.FEATURE_DIM and br.v23.rounded12_sha(X)==br.EXPECTED_ROUNDED12_FEATURE_SHA[route],f'{route} semantic 71D feature identity changed')
        meta=json.loads((roots[route]/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text())
        req(meta['truth_accessed'] is False and meta['feature_dimension']==br.FEATURE_DIM and meta['v19_family_sha256']==br.EXPECTED_V19_FAMILY_SHA[route],f'{route} invalid pretruth identity')

    truth_year={}; budgets={route:{} for route in br.ROUTES}
    for route,year in br.PANELS:
        truth_year[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())
        budgets[route][year]=int(frozen['candidate_budget']['comparator_budget'])

    ranker=br.v23.load_module(a.ranker_source,'frozen_839_balanced_recovery_order_diag')
    route_data={}; Xs=[]; ys=[]; all_groups=[]; offsets={}; cursor=0
    for route in br.ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fam_payload=json.loads((root/'family_memberships.json').read_text())
        ids=list(map(str,meta['family_ids'])); fams=fam_payload['families']; X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        req([str(f['family_id']) for f in fams]==ids and X.shape==(len(ids),br.FEATURE_DIM) and C.shape==(len(ids),8),'route payload alignment changed')
        by_year={y:truth_year[(route,y)] for y in br.YEARS}; eligible=br.v23.eligible_from_year_truth(by_year); hidden={}; hidden.update(by_year[2013]); hidden.update(by_year[2014])
        best=[br.v23.combined_best_label(f,hidden,eligible) for f in fams]
        y=[]; groups=[]
        for i,(f,b) in enumerate(zip(fams,best)):
            label=b['best_label']
            if label is None:
                target=0; group=f'NEG/{route}/{ids[i]}'
            else:
                f13=br.v23.year_f1_for_label(f,by_year[2013],label); f14=br.v23.year_f1_for_label(f,by_year[2014],label)
                target=int(f13>br.RECOVERY_F1_THRESHOLD and f14>br.RECOVERY_F1_THRESHOLD); group='SHOWER/'+str(label)
            y.append(target); groups.append(group)
        yarr=np.asarray(y,dtype=np.int8); req(np.unique(yarr).size==2,f'{route} target degenerate')
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); ys.append(yarr); all_groups.extend(groups)
        route_data[route]={'ids':ids,'X':X,'C':C,'meta':meta,'families':fams,'y':yarr,'groups':groups}

    Xall=np.vstack(Xs); yall=np.concatenate(ys); all_groups=list(map(str,all_groups)); folds=np.asarray([br.v23.v1.deterministic_fold(g) for g in all_groups],dtype=int); weights=np.asarray(ranker.grouped_weights(all_groups),dtype=float)
    req(Xall.shape==(cursor,br.FEATURE_DIM) and len(yall)==len(all_groups)==cursor,'stacked replay alignment changed')
    oof=np.zeros(cursor,dtype=float)
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; req(tr.any() and te.any() and np.unique(yall[tr]).size==2,f'invalid replay fold {fold}')
        m=br.recovery_model(); m.fit(Xall[tr],yall[tr],sample_weight=weights[tr]); oof[te]=br.positive_probability(m,Xall[te])
        req({all_groups[i] for i in np.where(tr)[0]}.isdisjoint({all_groups[i] for i in np.where(te)[0]}),f'group leakage in replay fold {fold}')

    reference=None
    if a.reference_result is not None:
        reference=json.loads(a.reference_result.read_text()); req(reference['verdict']=='FAIL_BALANCED_RECOVERY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','reference is not authoritative #997 no-go')

    routes={}
    for route in br.ROUTES:
        lo,hi=offsets[route]; rd=route_data[route]; ids=rd['ids']; y=rd['y']; groups=rd['groups']; scores=np.asarray(oof[lo:hi],dtype=float)
        tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
        raw_order=[ids[i] for i in sorted(range(len(ids)),key=lambda i:(-float(scores[i]),tie[i][0],ids[i]))]
        didx=ranker.diversity_order(scores,rd['C'],0.8,1.0,tie); div_order=[ids[i] for i in didx]
        v19_order=list(map(str,rd['meta']['v19_order'])); fused=list(br.v23.v19.fusion_orders(div_order,v19_order)['rank_sum'])
        score_sha=br.v23.array_sha(scores); fused_sha=hashlib.sha256('\n'.join(fused).encode()).hexdigest(); div_sha=hashlib.sha256('\n'.join(div_order).encode()).hexdigest()
        reference_diag=None
        if reference is not None:
            ref=reference['order_diagnostics'][route]; t_ref=reference['target_diagnostics'][route]
            req(int(np.sum(y==1))==int(t_ref['balanced_recovery_positive_families']),f'{route} #997 target-positive count mismatch')
            req(div_sha==ref['classifier_diversity_order_sha256'],f'{route} #997 classifier-diversity order hash mismatch')
            req(fused_sha==ref['fused_order_sha256'],f'{route} #997 fused order hash mismatch')
            reference_diag={
                'reference_oof_probability_sha256':ref['oof_positive_probability_sha256'],
                'replay_oof_probability_sha256':score_sha,
                'byte_exact_probability_hash_match':bool(score_sha==ref['oof_positive_probability_sha256']),
                'classifier_diversity_order_hash_match':True,
                'fused_order_hash_match':True,
            }
        routes[route]={
            'family_score_metrics':{'families':len(ids),'positive_families':int(np.sum(y==1)),'roc_auc':float(roc_auc_score(y,scores)),'average_precision':float(average_precision_score(y,scores))},
            'strict_group_score_metrics':group_score_metrics(scores,y,groups),
            'oof_probability_sha256':score_sha,
            'diversity_order_sha256':div_sha,
            'fused_order_sha256':fused_sha,
            'reference_replay':reference_diag,
            'orders':{
                'raw_probability':order_target_summary(raw_order,ids,y,groups,budgets[route]),
                'probability_plus_diversity':order_target_summary(div_order,ids,y,groups,budgets[route]),
                'v19_control':order_target_summary(v19_order,ids,y,groups,budgets[route]),
                'final_v19_rank_sum':order_target_summary(fused,ids,y,groups,budgets[route]),
            },
        }

    result={
        'stage':'POST_RESULT_BALANCED_RECOVERY_ORDER_STAGE_DIAGNOSTIC_V1',
        'verdict':'PASS_BALANCED_RECOVERY_ORDER_DIAGNOSTIC_COMPLETE',
        'replayed_scientific_source':'exact PR #997 balanced-recovery classifier; no new ranker',
        'replay_guard':'exact target-positive count + exact classifier-diversity order hash + exact fused-order hash; raw floating probability hash recorded but nonbinding after cross-host byte-fingerprint no-result',
        'feature_dimension':br.FEATURE_DIM,'target':'F1_2013>0.5 AND F1_2014>0.5 for unchanged best recurrent label',
        'routes':routes,
        'new_literature_promotion_evaluation_performed':False,'successor_defined':False,'alternate_order_selected':False,'class_weight_selected':False,'probability_calibration_selected':False,'feature_subset_selected':False,'model_capacity_selected':False,'fusion_weight_selected':False,'diversity_selected':False,'parameter_search':False,
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0],
    }
    (a.output/'BALANCED_RECOVERY_ORDER_DIAGNOSTIC_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
