#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy import sparse
from scipy.optimize import Bounds, LinearConstraint, linear_sum_assignment, milp

PANELS=(('sugar',2013,34),('sugar',2014,46),('hdbscan',2013,11),('hdbscan',2014,9))
TIERS=(9,11,34,46)
CATALOGUE_SHA='dd751abd4330f58b4056eb8da473ee4d19ae756211f0538c41b252ffc9fb352b'


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)
def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def hash_ids(ids:list[str])->str: return hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest()


def matrix_for_panel(families:list[dict[str,Any]],indices:list[int],truth:dict[str,str]):
    counts=Counter(v for v in truth.values() if v!='SPORADIC')
    labels=sorted(k for k,n in counts.items() if n>=4)
    truth_sets={l:{eid for eid,v in truth.items() if v==l} for l in labels}; truth_ids=set(truth)
    mat=np.zeros((len(labels),len(indices)),dtype=np.float64)
    for j,idx in enumerate(indices):
        pred=set(map(str,families[idx]['event_ids'])) & truth_ids
        if not pred: continue
        for i,label in enumerate(labels):
            actual=truth_sets[label]; ov=len(actual&pred)
            if ov:
                p=ov/len(pred); r=ov/len(actual); mat[i,j]=2*p*r/(p+r)
    return labels,mat


def evaluate(families:list[dict[str,Any]],order:list[int],truth:dict[str,str],budget:int)->dict[str,Any]:
    counts=Counter(v for v in truth.values() if v!='SPORADIC')
    labels=sorted(k for k,n in counts.items() if n>=4)
    truth_sets={l:{eid for eid,v in truth.items() if v==l} for l in labels}; truth_ids=set(truth)
    active=[]
    for absolute_rank,idx in enumerate(order,start=1):
        pred=set(map(str,families[idx]['event_ids'])) & truth_ids
        if pred: active.append((absolute_rank,idx,pred))
        if len(active)>=budget: break
    mat=np.zeros((len(labels),len(active)),dtype=np.float64)
    for i,label in enumerate(labels):
        actual=truth_sets[label]
        for j,(_rank,_idx,pred) in enumerate(active):
            ov=len(actual&pred)
            if ov:
                p=ov/len(pred); r=ov/len(actual); mat[i,j]=2*p*r/(p+r)
    n=max(len(labels),len(active)); cost=np.zeros((n,n),dtype=np.float64); cost[:len(labels),:len(active)]=-mat
    ri,cj=linear_sum_assignment(cost); vals=[]
    for i,j in zip(ri.tolist(),cj.tolist()):
        if i<len(labels): vals.append(float(mat[i,j]) if j<len(active) else 0.0)
    return {'eligible_showers':len(labels),'candidate_used':len(active),'macro_f1':float(np.mean(vals)) if vals else 0.0,'recovered_f1_gt_0_5':int(sum(v>0.5 for v in vals))}


def source_count(families:list[dict[str,Any]],indices:list[int])->dict[str,int]:
    c=Counter(str(families[i]['source']) for i in indices)
    return {k:int(c.get(k,0)) for k in ('hard','p19','p20')}


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--catalogue',type=Path,required=True); ap.add_argument('--v29-result',type=Path,required=True); ap.add_argument('--truth-root',type=Path,required=True); ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    require(sha(a.catalogue)==CATALOGUE_SHA,'fixed v29 catalogue changed')
    catalogue=json.loads(a.catalogue.read_text()); families=catalogue['families']; require(len(families)==334,'v29 family count changed')
    require([int(f['rank']) for f in families]==list(range(1,335)),'v29 order malformed')
    frozen=json.loads(a.v29_result.read_text()); require(frozen['verdict']=='FAIL_V29_CANONICAL_SONOTACO_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT','v29 verdict changed')
    require(frozen['candidate_catalogue_sha256']==CATALOGUE_SHA,'v29 result/catalogue mismatch')

    truth={}; literature={}; active_flags=[]
    for route,year,budget in PANELS:
        t=json.loads((a.truth_root/f'truth_{route}_{year}.json').read_text()); truth[(route,year)]=t
        e=json.loads((a.truth_root/f'evaluation_{route}_{year}.json').read_text()); literature[(route,year)]=(float(e['comparator_summary']['macro_f1']),int(e['comparator_summary']['recovered_f1_gt_0_5']))
        ids=set(t); active_flags.append([bool(set(map(str,f['event_ids']))&ids) for f in families])
    all_active=np.all(np.asarray(active_flags,dtype=bool),axis=0); candidate_indices=np.flatnonzero(all_active).tolist(); require(len(candidate_indices)>46,'too few all-panel-active families')
    n=len(candidate_indices); tier_index={t:i for i,t in enumerate(TIERS)}

    pdata={}
    for route,year,budget in PANELS: pdata[(route,year)]=matrix_for_panel(families,candidate_indices,truth[(route,year)])

    # Binary variables: four nested family selections plus sparse assignment edges.
    x={(ti,j):ti*n+j for ti in range(4) for j in range(n)}; cursor=4*n; y={}; edges={}
    for pi,(route,year,budget) in enumerate(PANELS):
        labels,mat=pdata[(route,year)]; ee=[]
        for i,j in zip(*np.nonzero(mat)):
            vid=cursor; cursor+=1; y[(pi,int(i),int(j))]=vid; ee.append((int(i),int(j),vid,float(mat[i,j])))
        edges[pi]=ee
    nvar=cursor; rows=[]; lbs=[]; ubs=[]
    def add(terms,lb=-np.inf,ub=np.inf): rows.append(terms); lbs.append(lb); ubs.append(ub)
    for ti,t in enumerate(TIERS): add([(x[(ti,j)],1.0) for j in range(n)],t,t)
    for ti in range(3):
        for j in range(n): add([(x[(ti,j)],1.0),(x[(ti+1,j)],-1.0)],-np.inf,0.0)
    for pi,(route,year,budget) in enumerate(PANELS):
        labels,mat=pdata[(route,year)]; by_label=defaultdict(list); by_family=defaultdict(list)
        for i,j,vid,f1 in edges[pi]: by_label[i].append((vid,1.0)); by_family[j].append((vid,1.0))
        for terms in by_label.values(): add(terms,-np.inf,1.0)
        ti=tier_index[budget]
        for j,terms in by_family.items(): add(terms+[(x[(ti,j)],-1.0)],-np.inf,0.0)
        lit_macro,lit_recovery=literature[(route,year)]
        add([(vid,f1) for _i,_j,vid,f1 in edges[pi]],lit_macro*len(labels)+1e-6,np.inf)
        add([(vid,1.0) for _i,_j,vid,f1 in edges[pi] if f1>0.5],lit_recovery,np.inf)
    rr=[]; cc=[]; vv=[]
    for r,terms in enumerate(rows):
        for col,val in terms: rr.append(r); cc.append(col); vv.append(val)
    A=sparse.csr_matrix((vv,(rr,cc)),shape=(len(rows),nvar)); constraint=LinearConstraint(A,np.asarray(lbs),np.asarray(ubs))
    objective=np.zeros(nvar,dtype=float)
    for pi,(route,year,budget) in enumerate(PANELS):
        labels,_mat=pdata[(route,year)]
        for _i,_j,vid,f1 in edges[pi]: objective[vid]=-f1/len(labels)
    # Deterministic negligible preference for lower existing v29 ranks; scientific feasibility constraints dominate.
    for ti in range(4):
        for j,idx in enumerate(candidate_indices): objective[x[(ti,j)]]+=1e-8*(idx+1)
    result=milp(objective,integrality=np.ones(nvar),bounds=Bounds(np.zeros(nvar),np.ones(nvar)),constraints=constraint,options={'time_limit':180,'mip_rel_gap':0.0})
    require(result.success,f'oracle MILP failed: {result.message}')

    selected={}
    for ti,t in enumerate(TIERS): selected[t]=[j for j in range(n) if result.x[x[(ti,j)]]>0.5]
    require(all(len(selected[t])==t for t in TIERS),'oracle cardinality changed')
    require(set(selected[9]).issubset(selected[11]) and set(selected[11]).issubset(selected[34]) and set(selected[34]).issubset(selected[46]),'oracle not nested')
    order_js=[]; previous=set()
    for t in TIERS:
        additions=set(selected[t])-previous; order_js.extend(sorted(additions,key=lambda j:candidate_indices[j])); previous=set(selected[t])
    remaining=[j for j in range(n) if j not in previous]; oracle_order=[candidate_indices[j] for j in order_js]+[candidate_indices[j] for j in sorted(remaining,key=lambda j:candidate_indices[j])]
    used=set(oracle_order); oracle_order.extend([i for i in range(len(families)) if i not in used]); require(len(oracle_order)==334 and len(set(oracle_order))==334,'oracle full order invalid')

    panel_rows=[]; all_pass=True
    for route,year,budget in PANELS:
        cur=evaluate(families,oracle_order,truth[(route,year)],budget); lm,lr=literature[(route,year)]; passed=bool(cur['macro_f1']>lm and cur['recovered_f1_gt_0_5']>=lr); all_pass &= passed
        panel_rows.append({'comparator':route,'year':year,'budget':budget,'oracle_macro_f1':cur['macro_f1'],'literature_macro_f1':lm,'oracle_recovered_f1_gt_0_5':cur['recovered_f1_gt_0_5'],'literature_recovered_f1_gt_0_5':lr,'superiority_pair_pass':passed})
    require(all_pass,'MILP assignment feasible but exact evaluator did not pass all panels')

    tiers_out={}; prev_abs=set()
    for t in TIERS:
        abs_indices=[candidate_indices[j] for j in selected[t]]; additions=sorted(set(abs_indices)-prev_abs); prev_abs=set(abs_indices)
        tiers_out[str(t)]={
            'oracle_source_composition':source_count(families,abs_indices),
            'current_v29_source_composition':source_count(families,list(range(t))),
            'oracle_current_v29_ranks':sorted(i+1 for i in abs_indices),
            'oracle_added_current_v29_ranks':sorted(i+1 for i in additions),
            'oracle_family_id_sha256':hash_ids([str(families[i]['family_id']) for i in abs_indices]),
        }
    out={
        'stage':'V29_FIXED_CANONICAL_CATALOGUE_EXPOSED_JOINT_ORACLE_DIAGNOSTIC_V1',
        'diagnostic_only':True,'deployable_reorder_defined':False,'parameter_search':False,
        'catalogue_sha256':CATALOGUE_SHA,'fixed_family_count':334,'all_panel_active_family_count':len(candidate_indices),
        'v29_actual_panels':[{k:v for k,v in p.items() if k!='matched_positive_pairs'} for p in frozen['panels']],
        'oracle_panels':panel_rows,'oracle_all_panel_pass':True,
        'nested_selection_pass':True,'solver_success':bool(result.success),'solver_status':int(result.status),'solver_message':str(result.message),'solver_objective':float(result.fun),
        'tiers':tiers_out,
        'conclusion':'RANKING_TRANSFER_FAILURE_NOT_CANDIDATE_MEMBERSHIP_CEILING',
        'truth_aware_oracle_may_not_be_used_as_deployable_rank':True,
        'maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,
    }
    (a.output/'V29_FIXED_CATALOGUE_JOINT_ORACLE_DIAGNOSTIC_V1.json').write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)); return 0

if __name__=='__main__': raise SystemExit(main())
