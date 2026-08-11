#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

FEATURE_DIM=71
RECOVERY=0.5
EXPECTED_HDB={
    2013:{'macro_f1':0.14888037368183737,'recovered':9,'budget':11},
    2014:{'macro_f1':0.15198123772301594,'recovered':9,'budget':9},
}


def require(ok:bool,msg:str)->None:
    if not ok:
        raise RuntimeError(msg)


def f1_matrix(labels:list[str], families:list[tuple[int,str,set[str]]], truth_sets:dict[str,set[str]])->np.ndarray:
    mat=np.zeros((len(labels),len(families)),dtype=np.float64)
    for i,label in enumerate(labels):
        actual=truth_sets[label]
        for j,(_rank,_fid,pred) in enumerate(families):
            ov=len(actual&pred)
            if ov:
                p=ov/len(pred); r=ov/len(actual); mat[i,j]=2*p*r/(p+r)
    return mat


def hungarian_assign(labels:list[str],families:list[tuple[int,str,set[str]]],truth_sets:dict[str,set[str]])->dict[str,Any]:
    mat=f1_matrix(labels,families,truth_sets)
    n=max(len(labels),len(families)); cost=np.zeros((n,n),dtype=np.float64); cost[:len(labels),:len(families)]=-mat
    ri,cj=linear_sum_assignment(cost)
    rows=[]
    vals=[]
    for i,j in zip(ri.tolist(),cj.tolist()):
        if i>=len(labels):
            continue
        val=float(mat[i,j]) if j<len(families) else 0.0
        vals.append(val)
        if j<len(families):
            rank,fid,_members=families[j]
            rows.append({'label':labels[i],'family_id':fid,'rank':int(rank),'f1':val})
        else:
            rows.append({'label':labels[i],'family_id':None,'rank':None,'f1':0.0})
    require(len(vals)==len(labels),'Hungarian assignment omitted eligible labels')
    return {'macro_f1':float(np.mean(vals)) if vals else 0.0,'recovered_f1_gt_0_5':int(sum(v>RECOVERY for v in vals)),'rows':rows,'matrix':mat}


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--payload-root',type=Path,required=True)
    p.add_argument('--truth-root',type=Path,required=True)
    p.add_argument('--ranker-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker source changed')

    roots={route:a.payload_root/route for route in v24.ROUTES}
    # Recheck immutable #950 pretruth identity before using exposed truth.
    for route in v24.ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and meta['feature_dimension']==FEATURE_DIM and fp['truth_accessed'] is False,f'{route} invalid immutable pretruth payload')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']; require([str(f['family_id']) for f in fams]==ids,f'{route} family order changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        require(X.shape==(len(ids),FEATURE_DIM) and C.shape==(len(ids),8),f'{route} immutable array shape changed')
        require(v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],f'{route} immutable array hash changed')

    truth={}; frozen={}
    for route,year in v24.PANELS:
        truth[(route,year)]=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text())
        frozen[(route,year)]=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())

    ranker=v22.load_module(a.ranker_source,'frozen_839_v31_rep_ceiling_diag')
    route_data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; offsets={}; cursor=0
    for route in v24.ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
        ids=list(map(str,meta['family_ids'])); fams=fp['families']; X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False)
        by={y:truth[(route,y)] for y in v24.YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014])
        base=[v22.family_truth(f,hidden,eligible) for f in fams]
        y13=[]; y14=[]; rg=[]
        for i,(f,t) in enumerate(zip(fams,base)):
            label=t['best_label']; rg.append(('SHOWER/'+str(label)) if label is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or label is None:
                q13=q14=0.0
            else:
                q13,q14=v24.annual_f1_for_fixed_label(f,str(label),by)
            y13.append(float(q13)); y14.append(float(q14))
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); y13s.append(np.asarray(y13,dtype=np.float64)); y14s.append(np.asarray(y14,dtype=np.float64)); groups.extend(rg)
        route_data[route]={'meta':meta,'fams':fams,'ids':ids,'centroids':C}

    Xall=np.vstack(Xs); y13all=np.concatenate(y13s); y14all=np.concatenate(y14s); groups=list(map(str,groups))
    require(Xall.shape==(cursor,FEATURE_DIM) and len(y13all)==len(y14all)==len(groups)==cursor,'stacked v31 reproduction input mismatch')
    folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],dtype=int)
    margin13=np.zeros(cursor,dtype=np.float64); margin14=np.zeros(cursor,dtype=np.float64)
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; require(tr.any() and te.any(),f'empty fold {fold}')
        require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),f'group leakage fold {fold}')
        mu=np.mean(Xall[tr],axis=0); sd=np.std(Xall[tr],axis=0,ddof=0); scale=sd.copy(); scale[scale==0.0]=1.0
        Ztr=(Xall[tr]-mu[None,:])/scale[None,:]; Zte=(Xall[te]-mu[None,:])/scale[None,:]
        te_idx=np.where(te)[0]
        for yall,out in ((y13all,margin13),(y14all,margin14)):
            pos=yall[tr]>RECOVERY; neg=~pos; require(pos.any() and neg.any(),'v31 fold lacks annual positive/nonpositive references')
            P=Ztr[pos]; N=Ztr[neg]
            for j,global_i in enumerate(te_idx.tolist()):
                dpos=float(np.min(np.linalg.norm(P-Zte[j][None,:],axis=1))); dneg=float(np.min(np.linalg.norm(N-Zte[j][None,:],axis=1))); out[global_i]=dneg-dpos
    combined=np.minimum(margin13,margin14); require(np.all(np.isfinite(combined)),'nonfinite v31 reproduced score')

    # Only HDB route is diagnosed; Sugar is reconstructed above solely to preserve exact stacked OOF training.
    lo,hi=offsets['hdbscan']; rd=route_data['hdbscan']; ids=rd['ids']; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]
    idx=ranker.diversity_order(combined[lo:hi],rd['centroids'],0.8,1.0,tie); local_order=[ids[i] for i in idx]
    v19_order=list(map(str,rd['meta']['v19_order'])); fused=list(v19.fusion_orders(local_order,v19_order)['rank_sum']); v31_fams=v22.rerank(rd['fams'],fused)

    fixed_universe_rank={fid:i+1 for i,fid in enumerate(ids)}
    by_fid={str(f['family_id']):f for f in rd['fams']}
    annual={}
    for year in (2013,2014):
        exp=EXPECTED_HDB[year]; budget=int(exp['budget']); truth_y=truth[('hdbscan',year)]
        reproduced=v22.evaluate(v31_fams,truth_y,budget)
        require(abs(float(reproduced['macro_f1'])-float(exp['macro_f1']))<1e-12 and int(reproduced['recovered_f1_gt_0_5'])==int(exp['recovered']),f'v31 HDB {year} reproduction failed')

        counts=Counter(v for v in truth_y.values() if v!='SPORADIC'); labels=sorted(k for k,n in counts.items() if n>=4); truth_sets={l:{eid for eid,v in truth_y.items() if v==l} for l in labels}; truth_ids=set(truth_y)
        active=[]
        for f in v31_fams:
            members=set(map(str,f['event_ids'])) & truth_ids
            if members:
                active.append((int(f['rank']),str(f['family_id']),members))
        active=sorted(active,key=lambda x:(x[0],x[1]))[:budget]
        exact=hungarian_assign(labels,active,truth_sets)
        require(abs(float(exact['macro_f1'])-float(exp['macro_f1']))<1e-12 and int(exact['recovered_f1_gt_0_5'])==int(exp['recovered']),f'detailed v31 Hungarian reproduction failed {year}')
        positive_rows=[r for r in exact['rows'] if r['family_id'] is not None and float(r['f1'])>0.0]
        assigned_labels=[str(r['label']) for r in positive_rows]
        require(len(assigned_labels)==len(set(assigned_labels)) and assigned_labels,'empty/duplicate v31 assigned label set')

        all_candidates=[]
        for fid in ids:
            f=by_fid[fid]; members=set(map(str,f['event_ids'])) & truth_ids
            if members:
                all_candidates.append((fixed_universe_rank[fid],fid,members))
        oracle=hungarian_assign(assigned_labels,all_candidates,truth_sets)
        oracle_by_label={r['label']:r for r in oracle['rows']}
        v31_by_label={r['label']:r for r in positive_rows}
        per_label=[]
        active_ids={fid for _rank,fid,_members in active}
        for label in sorted(assigned_labels):
            vr=v31_by_label[label]; orow=oracle_by_label[label]
            require(orow['family_id'] is not None,'oracle assigned fixed label to padding despite available candidate universe')
            per_label.append({
                'label':label,
                'v31_family_id':vr['family_id'],'v31_rank':int(vr['rank']),'v31_f1':float(vr['f1']),
                'oracle_family_id':orow['family_id'],'oracle_fixed_universe_rank':int(orow['rank']),'oracle_f1':float(orow['f1']),
                'f1_gain':float(orow['f1'])-float(vr['f1']),
                'oracle_family_already_in_v31_top_budget':bool(orow['family_id'] in active_ids),
                'same_family':bool(orow['family_id']==vr['family_id']),
            })
        ceiling_macro=float(sum(float(r['f1']) for r in oracle['rows'])/len(labels))
        ceiling_recovered=int(sum(float(r['f1'])>RECOVERY for r in oracle['rows']))
        lit=frozen[('hdbscan',year)]['comparator_summary']; lit_macro=float(lit['macro_f1']); lit_rec=int(lit['recovered_f1_gt_0_5'])
        annual[str(year)]={
            'eligible_truth_showers':len(labels),'budget':budget,
            'v31_macro_f1':float(exact['macro_f1']),'v31_recovered_f1_gt_0_5':int(exact['recovered_f1_gt_0_5']),
            'v31_positive_overlap_assigned_labels':len(assigned_labels),'v31_assigned_label_set':sorted(assigned_labels),
            'same_label_representative_ceiling_macro_f1':ceiling_macro,
            'same_label_representative_ceiling_recovered_f1_gt_0_5':ceiling_recovered,
            'literature_macro_f1':lit_macro,'literature_recovered_f1_gt_0_5':lit_rec,
            'ceiling_clears_literature_macro_f1':bool(ceiling_macro>lit_macro),
            'ceiling_meets_literature_recovery':bool(ceiling_recovered>=lit_rec),
            'same_label_ceiling_would_clear_pair':bool(ceiling_macro>lit_macro and ceiling_recovered>=lit_rec),
            'macro_f1_gain_from_perfect_representatives':ceiling_macro-float(exact['macro_f1']),
            'labels_with_better_representative':int(sum(float(r['f1_gain'])>1e-15 for r in per_label)),
            'oracle_representatives_already_in_top_budget':int(sum(bool(r['oracle_family_already_in_v31_top_budget']) for r in per_label)),
            'per_label':per_label,
        }

    result={
        'verdict':'PASS_V31_HDB_REPRESENTATIVE_CEILING_DIAGNOSTIC',
        'scientific_role':'POST_RESULT_TRUTH_AWARE_DIAGNOSTIC_ONLY_NO_SUCCESSOR_SELECTED',
        'v31_reproduction':{str(y):{'macro_f1':EXPECTED_HDB[y]['macro_f1'],'recovered_f1_gt_0_5':EXPECTED_HDB[y]['recovered'],'budget':EXPECTED_HDB[y]['budget']} for y in (2013,2014)},
        'annual':annual,
        'assigned_label_definition':'positive-F1 labels in exact v31 top-budget Hungarian assignment',
        'representative_ceiling_definition':'one-to-one Hungarian optimum over all fixed HDB route candidates while holding exact v31 assigned label set fixed; all other eligible truth labels remain zero',
        'new_rank_evaluated':False,'representative_selector_defined':False,'successor_selected':False,'feature_search':False,'model_search':False,'threshold_search':False,'parameter_search':False,'post_result_second_search':False,
        'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0],
    }
    (a.output/'V31_HDB_REPRESENTATIVE_CEILING_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':result['verdict'],'2013':{k:v for k,v in annual['2013'].items() if k!='per_label' and k!='v31_assigned_label_set'},'2014':{k:v for k,v in annual['2014'].items() if k!='per_label' and k!='v31_assigned_label_set'}},indent=2,sort_keys=True,allow_nan=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
