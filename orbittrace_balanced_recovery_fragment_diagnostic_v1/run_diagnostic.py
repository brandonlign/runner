#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from orbittrace_sonotaco_balanced_recovery_oof_v1 import train_evaluate as br


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)

def quant(values:list[int],p:float)->float:
    return float(np.quantile(np.asarray(values,dtype=float),p)) if values else float('nan')

def order_sha(order:list[str])->str:
    return hashlib.sha256('\n'.join(order).encode()).hexdigest()


def fragment_summary(order:list[str],ids:list[str],y:np.ndarray,groups:list[str],budgets:dict[int,int])->dict[str,Any]:
    rank={fid:i+1 for i,fid in enumerate(order)}
    members=defaultdict(list)
    for i,g in enumerate(groups):
        if g.startswith('SHOWER/'): members[g].append(i)
    positive_groups=[g for g,idx in members.items() if any(int(y[i])==1 for i in idx)]
    rows=[]
    for g in sorted(positive_groups):
        idx=members[g]; pos=[i for i in idx if int(y[i])==1]; req(pos,f'positive group lacks positive family: {g}')
        first_any=min(rank[ids[i]] for i in idx); first_pos=min(rank[ids[i]] for i in pos)
        rows.append({'group':g,'family_count':len(idx),'target_positive_family_count':len(pos),'first_any_member_rank':int(first_any),'first_target_positive_rank':int(first_pos),'selection_gap':int(first_pos-first_any),'first_group_member_is_target_positive':bool(first_any==first_pos)})
    gaps=[int(r['selection_gap']) for r in rows]; wins=sum(int(r['first_group_member_is_target_positive']) for r in rows)
    budget_rows={}
    for year,budget in sorted(budgets.items()):
        any_count=sum(int(r['first_any_member_rank']<=budget) for r in rows)
        pos_count=sum(int(r['first_target_positive_rank']<=budget) for r in rows)
        budget_rows[str(year)]={'budget':int(budget),'positive_groups_with_any_member_in_budget':int(any_count),'positive_groups_with_target_positive_member_in_budget':int(pos_count),'fragment_only_groups':int(any_count-pos_count)}
    return {
        'positive_shower_groups':len(rows),
        'first_group_member_target_positive_count':int(wins),
        'first_group_member_target_positive_fraction':float(wins/len(rows)) if rows else 0.0,
        'selection_gap_median':quant(gaps,0.50),
        'selection_gap_q75':quant(gaps,0.75),
        'selection_gap_q90':quant(gaps,0.90),
        'selection_gap_max':int(max(gaps)) if gaps else None,
        'budgets':budget_rows,
        'group_rows':rows,
    }


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--sugar-root',type=Path,required=True)
    p.add_argument('--hdbscan-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True)
    p.add_argument('--reference-result',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(br.v23.sha(a.ranker_source)==br.RANKER_SOURCE_SHA,'#839 ranker source changed')
    reference=json.loads(a.reference_result.read_text())
    req(reference['verdict']=='FAIL_BALANCED_RECOVERY_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','reference is not authoritative #997 no-go')
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

    ranker=br.v23.load_module(a.ranker_source,'frozen_839_balanced_recovery_fragment_diag')
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
        req(int(np.sum(yarr==1))==int(reference['target_diagnostics'][route]['balanced_recovery_positive_families']),f'{route} target-positive count mismatch')
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); ys.append(yarr); all_groups.extend(groups)
        route_data[route]={'ids':ids,'C':C,'meta':meta,'y':yarr,'groups':groups}

    Xall=np.vstack(Xs); yall=np.concatenate(ys); all_groups=list(map(str,all_groups)); folds=np.asarray([br.v23.v1.deterministic_fold(g) for g in all_groups],dtype=int); weights=np.asarray(ranker.grouped_weights(all_groups),dtype=float)
    req(Xall.shape==(cursor,br.FEATURE_DIM) and len(yall)==len(all_groups)==cursor,'stacked replay alignment changed')
    oof=np.zeros(cursor,dtype=float)
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; req(tr.any() and te.any() and np.unique(yall[tr]).size==2,f'invalid replay fold {fold}')
        m=br.recovery_model(); m.fit(Xall[tr],yall[tr],sample_weight=weights[tr]); oof[te]=br.positive_probability(m,Xall[te])
        req({all_groups[i] for i in np.where(tr)[0]}.isdisjoint({all_groups[i] for i in np.where(te)[0]}),f'group leakage in replay fold {fold}')

    routes={}
    for route in br.ROUTES:
        lo,hi=offsets[route]; rd=route_data[route]; ids=rd['ids']; y=rd['y']; groups=rd['groups']; scores=np.asarray(oof[lo:hi],dtype=float)
        tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
        raw_order=[ids[i] for i in sorted(range(len(ids)),key=lambda i:(-float(scores[i]),tie[i][0],ids[i]))]
        didx=ranker.diversity_order(scores,rd['C'],0.8,1.0,tie); div_order=[ids[i] for i in didx]
        v19_order=list(map(str,rd['meta']['v19_order'])); fused=list(br.v23.v19.fusion_orders(div_order,v19_order)['rank_sum'])
        ref=reference['order_diagnostics'][route]
        req(order_sha(div_order)==ref['classifier_diversity_order_sha256'],f'{route} classifier-diversity order mismatch')
        req(order_sha(fused)==ref['fused_order_sha256'],f'{route} fused order mismatch')
        routes[route]={
            'oof_probability_sha256':br.v23.array_sha(scores),
            'reference_probability_sha256':ref['oof_positive_probability_sha256'],
            'byte_exact_probability_hash_match':bool(br.v23.array_sha(scores)==ref['oof_positive_probability_sha256']),
            'orders':{
                'raw_probability':fragment_summary(raw_order,ids,y,groups,budgets[route]),
                'probability_plus_diversity':fragment_summary(div_order,ids,y,groups,budgets[route]),
                'v19_control':fragment_summary(v19_order,ids,y,groups,budgets[route]),
                'final_v19_rank_sum':fragment_summary(fused,ids,y,groups,budgets[route]),
            },
        }

    result={
        'stage':'POST_RESULT_BALANCED_RECOVERY_FRAGMENT_VS_GROUP_DIAGNOSTIC_V1',
        'verdict':'PASS_BALANCED_RECOVERY_FRAGMENT_DIAGNOSTIC_COMPLETE',
        'replayed_scientific_source':'exact PR #997; no new ranker or order',
        'feature_dimension':br.FEATURE_DIM,'target':'F1_2013>0.5 AND F1_2014>0.5 for unchanged best recurrent label',
        'routes':routes,
        'new_literature_promotion_evaluation_performed':False,'successor_defined':False,'alternate_order_selected':False,'candidate_membership_changed':False,'feature_search':False,'target_search':False,'model_search':False,'class_weight_selected':False,'probability_calibration_selected':False,'diversity_selected':False,'fusion_weight_selected':False,'parameter_search':False,
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0],
    }
    (a.output/'BALANCED_RECOVERY_FRAGMENT_DIAGNOSTIC_V1.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
