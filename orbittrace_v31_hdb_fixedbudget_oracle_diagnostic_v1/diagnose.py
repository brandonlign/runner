#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from orbittrace_v22_sonotaco_grouped_oof_ranker_v1 import train_evaluate as v22
from orbittrace_v24_twohead_worst_prediction_v1 import train_evaluate as v24
from orbittrace_v19_quality_consensus_fusion_v1 import run_variants_pretruth as v19

FEATURE_DIM=71
RECOVERY=0.5
EXPECTED_V31={2013:(0.14888037368183737,9,11),2014:(0.15198123772301594,9,9)}
EXPECTED_HDB={2013:(0.16813025050497152,10,11),2014:(0.15689595582646423,9,9)}


def require(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def edge_f1(members:set[str],truth_y:dict[str,str],label:str)->float:
    actual={eid for eid,v in truth_y.items() if v==label}; pred=members & set(truth_y)
    if not actual or not pred: return 0.0
    ov=len(actual&pred)
    if ov==0: return 0.0
    p=ov/len(pred); r=ov/len(actual)
    return float(2*p*r/(p+r))


def solve_matching(labels:list[str],candidate_ids:list[str],f1:np.ndarray,budget:int,recovery_min:int|None,objective:str)->dict:
    edges=[]
    for i in range(len(labels)):
        for j in range(len(candidate_ids)):
            val=float(f1[i,j])
            if val>0.0:
                edges.append((i,j,val,int(val>RECOVERY)))
    require(edges,'no positive-F1 oracle edges')
    n=len(edges)
    # label constraints + candidate constraints + total budget + optional recovery minimum
    rows=len(labels)+len(candidate_ids)+1+(1 if recovery_min is not None else 0)
    A=lil_matrix((rows,n),dtype=np.float64); lb=np.full(rows,-np.inf); ub=np.full(rows,np.inf)
    for k,(i,j,_f,_r) in enumerate(edges):
        A[i,k]=1.0; A[len(labels)+j,k]=1.0; A[len(labels)+len(candidate_ids),k]=1.0
    ub[:len(labels)]=1.0; ub[len(labels):len(labels)+len(candidate_ids)]=1.0; ub[len(labels)+len(candidate_ids)]=float(budget)
    if recovery_min is not None:
        rr=rows-1
        for k,(_i,_j,_f,r) in enumerate(edges): A[rr,k]=float(r)
        lb[rr]=float(recovery_min)
    if objective=='recovery': c=-np.asarray([r for _i,_j,_f,r in edges],dtype=np.float64)
    elif objective=='f1': c=-np.asarray([f for _i,_j,f,_r in edges],dtype=np.float64)
    else: raise ValueError(objective)
    res=milp(c=c,integrality=np.ones(n,dtype=np.int8),bounds=Bounds(np.zeros(n),np.ones(n)),constraints=LinearConstraint(A.tocsr(),lb,ub))
    if not bool(res.success):
        return {'feasible':False,'status':int(res.status),'message':str(res.message),'selected':[]}
    x=np.asarray(res.x); chosen=[edges[k] for k in range(n) if x[k]>0.5]
    rows_out=[{'label':labels[i],'family_id':candidate_ids[j],'f1':float(f),'recovered_f1_gt_0_5':bool(r)} for i,j,f,r in chosen]
    return {'feasible':True,'status':int(res.status),'message':str(res.message),'selected':sorted(rows_out,key=lambda r:(r['label'],r['family_id'])),'selected_count':len(chosen),'recovered_f1_gt_0_5':int(sum(r for _i,_j,_f,r in chosen)),'total_f1':float(sum(f for _i,_j,f,_r in chosen))}


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--payload-root',type=Path,required=True); p.add_argument('--truth-root',type=Path,required=True); p.add_argument('--ranker-source',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True); require(v22.sha(a.ranker_source)==v24.RANKER_SOURCE_SHA,'#839 ranker changed')
    roots={r:a.payload_root/r for r in v24.ROUTES}; truth={}; frozen={}
    for r,y in v24.PANELS: truth[(r,y)]=json.loads((a.truth_root/f'truth_{r}_{y}.json').read_text()); frozen[(r,y)]=json.loads((a.truth_root/f'evaluation_{r}_{y}.json').read_text())
    ranker=v22.load_module(a.ranker_source,'frozen_839_fixedbudget_oracle_diag')

    # Reproduce exact v31 fused HDB order only for descriptive rank-overlap diagnostics.
    data={}; Xs=[]; y13s=[]; y14s=[]; groups=[]; offsets={}; cursor=0
    for route in v24.ROUTES:
        root=roots[route]; meta=json.loads((root/'V22_PRETRUTH_FEATURE_MANIFEST.json').read_text()); fp=json.loads((root/'family_memberships.json').read_text())
        require(meta['truth_accessed'] is False and meta['feature_dimension']==FEATURE_DIM and fp['truth_accessed'] is False,f'{route} bad pretruth')
        ids=list(map(str,meta['family_ids'])); fams=fp['families']; require([str(f['family_id']) for f in fams]==ids,'family order changed')
        X=np.load(root/'features.npy',allow_pickle=False); C=np.load(root/'centroids.npy',allow_pickle=False); require(v22.array_sha(X)==meta['feature_sha256'] and v22.array_sha(C)==meta['centroid_sha256'],'array identity changed')
        by={y:truth[(route,y)] for y in v24.YEARS}; eligible=v22.eligible_from_year_truth(by); hidden={}; hidden.update(by[2013]); hidden.update(by[2014]); base=[v22.family_truth(f,hidden,eligible) for f in fams]
        q13=[]; q14=[]; rg=[]
        for i,(f,t) in enumerate(zip(fams,base)):
            lab=t['best_label']; rg.append(('SHOWER/'+str(lab)) if lab is not None else f'NEG/{route}/{ids[i]}')
            if not t['positive'] or lab is None: a13=a14=0.0
            else: a13,a14=v24.annual_f1_for_fixed_label(f,str(lab),by)
            q13.append(float(a13)); q14.append(float(a14))
        offsets[route]=(cursor,cursor+len(ids)); cursor+=len(ids); Xs.append(X); y13s.append(np.asarray(q13)); y14s.append(np.asarray(q14)); groups.extend(rg); data[route]={'meta':meta,'fams':fams,'ids':ids,'centroids':C}
    X=np.vstack(Xs); y13=np.concatenate(y13s); y14=np.concatenate(y14s); groups=list(map(str,groups)); folds=np.asarray([v22.v1.deterministic_fold(g) for g in groups],int); m13=np.zeros(cursor); m14=np.zeros(cursor)
    for fold in range(5):
        tr=folds!=fold; te=folds==fold; require({groups[i] for i in np.where(tr)[0]}.isdisjoint({groups[i] for i in np.where(te)[0]}),'group leakage')
        mu=X[tr].mean(0); sd=X[tr].std(0,ddof=0); scale=sd.copy(); scale[scale==0]=1.; Ztr=(X[tr]-mu)/scale; Zte=(X[te]-mu)/scale; tei=np.where(te)[0]
        for yy,out in ((y13,m13),(y14,m14)):
            pos=yy[tr]>RECOVERY; neg=~pos; P=Ztr[pos]; N=Ztr[neg]; require(len(P)>0 and len(N)>0,'empty v31 reference class')
            for j,gi in enumerate(tei.tolist()): out[gi]=float(np.min(np.linalg.norm(N-Zte[j],axis=1))-np.min(np.linalg.norm(P-Zte[j],axis=1)))
    score=np.minimum(m13,m14); lo,hi=offsets['hdbscan']; rd=data['hdbscan']; ids=rd['ids']; tie=[(int(rd['meta']['tie_rank'][i]),ids[i]) for i in range(len(ids))]; idx=ranker.diversity_order(score[lo:hi],rd['centroids'],0.8,1.0,tie); div=[ids[i] for i in idx]; fused=list(v19.fusion_orders(div,list(map(str,rd['meta']['v19_order'])))['rank_sum']); fused_rank={fid:i+1 for i,fid in enumerate(fused)}; v31_ranked=v22.rerank(rd['fams'],fused)

    by_fid={str(f['family_id']):f for f in rd['fams']}; annual={}
    for year in (2013,2014):
        vm,vr,budget=EXPECTED_V31[year]; hm,hr,hbudget=EXPECTED_HDB[year]; require(budget==hbudget,'budget mismatch')
        cur=v22.evaluate(v31_ranked,truth[('hdbscan',year)],budget); require(abs(cur['macro_f1']-vm)<1e-12 and cur['recovered_f1_gt_0_5']==vr,f'v31 reproduction {year}')
        ev=frozen[('hdbscan',year)]['comparator_summary']; require(abs(float(ev['macro_f1'])-hm)<1e-12 and int(ev['recovered_f1_gt_0_5'])==hr,'HDB literature summary changed')
        ty=truth[('hdbscan',year)]; truth_ids=set(ty); labels=sorted(l for l,n in Counter(v for v in ty.values() if v!='SPORADIC').items() if n>=4); candidate_ids=[fid for fid in ids if set(map(str,by_fid[fid]['event_ids'])) & truth_ids]
        mat=np.zeros((len(labels),len(candidate_ids)),dtype=np.float64)
        for i,l in enumerate(labels):
            for j,fid in enumerate(candidate_ids): mat[i,j]=edge_f1(set(map(str,by_fid[fid]['event_ids'])),ty,l)
        maxrec=solve_matching(labels,candidate_ids,mat,budget,None,'recovery')
        constrained=solve_matching(labels,candidate_ids,mat,budget,hr,'f1')
        require(maxrec['feasible'],'max-recovery oracle infeasible unexpectedly')
        if constrained['feasible']:
            macro=float(constrained['total_f1']/len(labels)); selected=constrained['selected']
            for row in selected: row['v31_fused_rank']=int(fused_rank[row['family_id']]); row['inside_v31_top_budget']=bool(row['v31_fused_rank']<=budget); row['inside_v31_top_2x_budget']=bool(row['v31_fused_rank']<=2*budget); row['inside_v31_top_5x_budget']=bool(row['v31_fused_rank']<=5*budget)
            clear=bool(macro>hm and constrained['recovered_f1_gt_0_5']>=hr)
        else: macro=None; selected=[]; clear=False
        annual[str(year)]={'budget':budget,'eligible_truth_showers':len(labels),'active_fixed_candidates':len(candidate_ids),'literature_macro_f1':hm,'literature_recovered_f1_gt_0_5':hr,'v31_macro_f1':vm,'v31_recovered_f1_gt_0_5':vr,'max_recovery_oracle':maxrec,'recovery_constrained_macro_oracle_feasible':bool(constrained['feasible']),'recovery_constrained_macro_oracle_macro_f1':macro,'recovery_constrained_macro_oracle_recovered_f1_gt_0_5':None if not constrained['feasible'] else int(constrained['recovered_f1_gt_0_5']),'fixed_universe_can_clear_hdb_pair_gate':clear,'selected_pairs':selected,'selected_inside_v31_top_budget':sum(int(r['inside_v31_top_budget']) for r in selected),'selected_inside_v31_top_2x_budget':sum(int(r['inside_v31_top_2x_budget']) for r in selected),'selected_inside_v31_top_5x_budget':sum(int(r['inside_v31_top_5x_budget']) for r in selected)}

    result={'verdict':'PASS_CURRENT_HDB_FIXEDBUDGET_ORACLE_DIAGNOSTIC','scientific_role':'POST_RESULT_TRUTH_AWARE_ORACLE_ONLY_NO_SUCCESSOR_SELECTED','annual':annual,'optimizer':'scipy.optimize.milp binary one-to-one matching; no solver parameter search','new_rank_evaluated':False,'oracle_promotable':False,'successor_selected':False,'candidate_membership_changed':False,'budget_search':False,'threshold_search':False,'objective_weight_search':False,'solver_parameter_search':False,'feature_search':False,'model_search':False,'parameter_search':False,'post_result_second_search':False,'sonotaco_role':'EXPOSED_DEVELOPMENT_ONLY','maarsy_scientific_access':False,'dms_scientific_access':False,'target_information_access':False,'target_region_events_accessed':False,'blind_exclusion':[20.0,55.0]}
    (a.output/'CURRENT_HDB_FIXEDBUDGET_ORACLE_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    compact={y:{k:v for k,v in annual[y].items() if k not in ('selected_pairs','max_recovery_oracle')}|{'max_recovery':annual[y]['max_recovery_oracle']['recovered_f1_gt_0_5']} for y in ('2013','2014')}; print(json.dumps({'verdict':result['verdict'],'annual':compact},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
