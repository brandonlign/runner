#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linear_sum_assignment, milp
from scipy.sparse import lil_matrix

PANELS=(('sugar',2013),('sugar',2014),('hdbscan',2013),('hdbscan',2014))
CATALOGUE_SHA='dd751abd4330f58b4056eb8da473ee4d19ae756211f0538c41b252ffc9fb352b'
EXPECTED_FAIL='FAIL_V29_CANONICAL_SONOTACO_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p:Path,obj:Any)->None: p.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+'\n')


def evaluate_exact(families:list[dict[str,Any]],truth:dict[str,str],budget:int)->dict[str,Any]:
    """Exact inline transport of PR #973 evaluate(); no diagnostic rule enters here."""
    counts=Counter(v for v in truth.values() if v!='SPORADIC')
    labels=sorted(k for k,n in counts.items() if n>=4)
    truth_sets={l:{eid for eid,v in truth.items() if v==l} for l in labels}; truth_ids=set(truth)
    active=[]
    for family in families:
        members=set(map(str,family['event_ids'])) & truth_ids
        if members: active.append((int(family['rank']),str(family['family_id']),members))
    active=sorted(active,key=lambda x:(x[0],x[1]))[:int(budget)]
    mat=np.zeros((len(labels),len(active)),dtype=np.float64)
    for i,label in enumerate(labels):
        actual=truth_sets[label]
        for j,(_r,_fid,pred) in enumerate(active):
            ov=len(actual&pred)
            if ov:
                precision=ov/len(pred); recall=ov/len(actual); mat[i,j]=2*precision*recall/(precision+recall)
    n=max(len(labels),len(active)); cost=np.zeros((n,n),dtype=np.float64); cost[:len(labels),:len(active)]=-mat
    ri,cj=linear_sum_assignment(cost)
    vals=[]; matches=[]
    for i,j in zip(ri.tolist(),cj.tolist()):
        if i>=len(labels): continue
        val=float(mat[i,j]) if j<len(active) else 0.0; vals.append(val)
        if j<len(active) and val>0:
            rank,fid,pred=active[j]; actual=truth_sets[labels[i]]; ov=len(actual&pred); precision=ov/len(pred); recall=ov/len(actual)
            matches.append({'label':labels[i],'family_id':fid,'rank':rank,'f1':val,'overlap':ov,'precision':precision,'recall':recall})
    return {'eligible_showers':len(labels),'macro_f1':float(np.mean(vals)) if vals else 0.0,'recovered_f1_gt_0_5':int(sum(x>0.5 for x in vals)),'candidate_used':len(active),'matched_positive_pairs':matches}


def f1_matrix(families:list[dict[str,Any]],truth:dict[str,str]):
    counts=Counter(v for v in truth.values() if v!='SPORADIC')
    labels=sorted(k for k,n in counts.items() if n>=4)
    truth_sets={l:{eid for eid,v in truth.items() if v==l} for l in labels}; truth_ids=set(truth)
    active=[]
    for family in families:
        members=set(map(str,family['event_ids'])) & truth_ids
        if members:
            active.append({'rank':int(family['rank']),'family_id':str(family['family_id']),'source':str(family['source']),'members':members})
    mat=np.zeros((len(labels),len(active)),dtype=np.float64)
    for i,label in enumerate(labels):
        actual=truth_sets[label]
        for j,f in enumerate(active):
            pred=f['members']; ov=len(actual&pred)
            if ov:
                precision=ov/len(pred); recall=ov/len(actual); mat[i,j]=2*precision*recall/(precision+recall)
    return labels,active,mat


def solve_assignment(mat:np.ndarray,budget:int,objective:str):
    nz=np.argwhere(mat>0.0)
    if len(nz)==0: return []
    vals=mat[nz[:,0],nz[:,1]]
    n=len(nz); rows=mat.shape[0]; cols=mat.shape[1]
    A=lil_matrix((rows+cols+1,n),dtype=np.float64)
    for k,(i,j) in enumerate(nz.tolist()):
        A[i,k]=1.0; A[rows+j,k]=1.0; A[-1,k]=1.0
    upper=np.r_[np.ones(rows+cols,dtype=np.float64),float(budget)]
    con=LinearConstraint(A.tocsr(),-np.inf,upper)
    score=vals if objective=='f1' else (vals>0.5).astype(np.float64)
    # Deterministic microscopic F1 secondary objective only breaks equal recovery-count optima.
    if objective=='recovery': score=score+vals*1e-9
    res=milp(c=-score,integrality=np.ones(n,dtype=np.int8),bounds=Bounds(0.0,1.0),constraints=con,options={'time_limit':60.0})
    require(res.x is not None and bool(res.success),f'MILP failed: {res.message}')
    out=[]
    for k,x in enumerate(res.x.tolist()):
        if x>0.5:
            i,j=nz[k]; out.append((float(mat[i,j]),int(i),int(j)))
    require(len(out)<=budget,'oracle exceeded budget')
    return out


def source_counts(active,indices): return dict(sorted(Counter(active[j]['source'] for j in indices).items()))


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--v29-root',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    cat_path=a.v29_root/'pretruth/V29_CANONICAL_PRETRUTH_CATALOGUE.json'; final_path=a.v29_root/'final/V29_CANONICAL_SONOTACO_EXPOSED_RESULT.json'
    require(sha(cat_path)==CATALOGUE_SHA,'#973 pretruth catalogue changed')
    catalogue=json.loads(cat_path.read_text()); require(catalogue['family_count']==334 and catalogue['candidate_counts']=={'hard':25,'p19':84,'p20':225,'union':334},'#973 catalogue universe changed')
    require(catalogue['truth_accessed'] is False and catalogue['matched_comparator_rows_accessed'] is False,'pretruth boundary changed')
    frozen=json.loads(final_path.read_text()); require(frozen['verdict']==EXPECTED_FAIL and frozen['panel_wins']==0,'#973 scientific result changed')
    families=catalogue['families']; panels=[]
    frozen_by={(x['comparator'],int(x['year'])):x for x in frozen['panels']}
    all_headroom=True
    for route,year in PANELS:
        truth=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text()); ev=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text())
        budget=int(ev['candidate_budget']['comparator_budget']); lit=ev['comparator_summary']; cur=evaluate_exact(families,truth,budget); prior=frozen_by[(route,year)]
        require(abs(float(cur['macro_f1'])-float(prior['candidate_macro_f1']))<1e-12 and int(cur['recovered_f1_gt_0_5'])==int(prior['candidate_recovered_f1_gt_0_5']),'#973 panel reproduction failed')
        labels,active,mat=f1_matrix(families,truth); require(len(labels)==int(cur['eligible_showers']),'eligible shower semantics changed')
        top=sorted(range(len(active)),key=lambda j:(active[j]['rank'],active[j]['family_id']))[:budget]
        best=mat.max(axis=0) if mat.shape[0] else np.zeros(len(active))
        top_strong=int(sum(float(best[j])>0.5 for j in top))
        all_strong=[j for j in range(len(active)) if float(best[j])>0.5]
        opt=solve_assignment(mat,budget,'f1'); opt_rec=solve_assignment(mat,budget,'recovery')
        oracle_macro=float(sum(v for v,_i,_j in opt)/len(labels)) if labels else 0.0
        oracle_recovered=int(sum(v>0.5 for v,_i,_j in opt))
        max_recovered=int(sum(v>0.5 for v,_i,_j in opt_rec))
        opt_js=[j for _v,_i,j in opt]; ranks=sorted(active[j]['rank'] for j in opt_js)
        panel_headroom=bool(oracle_macro>float(lit['macro_f1']) and max_recovered>=int(lit['recovered_f1_gt_0_5']))
        all_headroom=all_headroom and panel_headroom
        panels.append({
            'comparator':route,'year':year,'budget':budget,
            'candidate_macro_f1':float(cur['macro_f1']),'candidate_recovered_f1_gt_0_5':int(cur['recovered_f1_gt_0_5']),
            'literature_macro_f1':float(lit['macro_f1']),'literature_recovered_f1_gt_0_5':int(lit['recovered_f1_gt_0_5']),
            'actual_prefix_source_counts':source_counts(active,top),'actual_prefix_intrinsic_f1_gt_0_5_families':top_strong,
            'complete_catalogue_intrinsic_f1_gt_0_5_families':len(all_strong),'complete_catalogue_strong_source_counts':source_counts(active,all_strong),
            'oracle_max_total_f1_macro_f1':oracle_macro,'oracle_max_total_f1_recovered_f1_gt_0_5':oracle_recovered,'oracle_max_recovered_f1_gt_0_5':max_recovered,
            'oracle_source_counts':source_counts(active,opt_js),'oracle_rank_min':int(min(ranks)) if ranks else None,'oracle_rank_median':float(np.median(ranks)) if ranks else None,'oracle_rank_max':int(max(ranks)) if ranks else None,
            'ranking_headroom_panel_pass':panel_headroom,
        })
    result={
        'stage':'V29_CANONICAL_POSTRESULT_FIXED_CATALOGUE_CEILING_DIAGNOSTIC_V1','catalogue_sha256':CATALOGUE_SHA,'panels':panels,
        'conclusion':'RANK_PLACEMENT_HEADROOM_REMAINS' if all_headroom else 'FIXED_CATALOGUE_CEILING_LIMITS_SUPERIORITY',
        'deployable_order_defined':False,'successor_defined':False,'parameter_search':False,'source_quota_selected':False,'oracle_family_ids_published':False,
        'sonotaco_role':'EXPOSED_POSTRESULT_DIAGNOSTIC_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,
    }
    dump(a.output/'V29_CANONICAL_POSTRESULT_CEILING_DIAGNOSTIC_V1.json',result)
    print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
