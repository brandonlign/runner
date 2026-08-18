#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Any

DAG_PRELABEL_SHA256='65ead5f26026dbed74a098cc1df17d000c28705cd8fcd3af5134fd98151a0573'
DAG_RESULT_SHA256='b7b4a4355a488108f4107e86e98bfc872f67c176d63eac1e56772a78f0708721'
PARETO_PRELABEL_SHA256='5752ef8b36a5d317455e649723c26692fe2636262dc6d74befbe2ffb95945310'
DENOMS=(64,128,1024);BUCKETS=(0,1,2,3);BLIND=(20.0,55.0)

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha256(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def mem(x:dict[str,Any])->tuple[str,...]:return tuple(sorted(str(z) for z in x['event_ids']))
def mhash(x:dict[str,Any])->str:return hashlib.sha256('|'.join(mem(x)).encode()).hexdigest()
def uhash(ids:set[str])->str:return hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest()
def disjoint(rows:list[dict[str,Any]])->bool:
    seen:set[str]=set()
    for r in rows:
        s=set(mem(r))
        if seen&s:return False
        seen|=s
    return True

def nondominated_layers(rows:list[dict[str,Any]])->dict[str,int]:
    remaining=set(range(len(rows))); layer=1; out:dict[str,int]={}
    while remaining:
        front=[]
        for i in sorted(remaining):
            a=rows[i]; ar=int(a['recurrence_rank']); am=int(a['modal_prominence_rank'])
            dominated=False
            for j in remaining:
                if i==j:continue
                b=rows[j]; br=int(b['recurrence_rank']); bm=int(b['modal_prominence_rank'])
                if br<=ar and bm<=am and (br<ar or bm<am):dominated=True;break
            if not dominated:front.append(i)
        req(front,'empty Pareto frontier')
        for i in front:out[str(rows[i]['atom_hash'])]=layer
        remaining.difference_update(front);layer+=1
    return out

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('dag-prelabel','dag-result','pareto-prelabel','output'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(sha256(a.dag_prelabel)==DAG_PRELABEL_SHA256,'DAG prelabel changed')
    req(sha256(a.dag_result)==DAG_RESULT_SHA256,'DAG result changed')
    req(sha256(a.pareto_prelabel)==PARETO_PRELABEL_SHA256,'Pareto prelabel changed')
    dag=json.loads(a.dag_prelabel.read_text());dr=json.loads(a.dag_result.read_text());old=json.loads(a.pareto_prelabel.read_text())
    req(dr['verdict']=='SUPPORTS_CROSSHIERARCHY_REFINEMENT_DAG_V1','DAG prerequisite did not pass')
    req(dr['prelabel_sha256']==DAG_PRELABEL_SHA256,'DAG result/prelabel mismatch')
    for flag in ('shower_truth_used','target_information_access','target_region_events_accessed','sonotaco_scientific_access','asfn_efn_event_level_access','amos_scientific_access','maarsy_scientific_access','dms_scientific_access','post_result_parameter_search'):
        req(dag.get(flag) is False,f'DAG firewall {flag}')
    dp={(int(x['denominator']),int(x['bucket'])):x for x in dag['panels']};req(set(dp)=={(d,b) for d in DENOMS for b in BUCKETS},'DAG panel set')
    op={(int(x['denominator']),int(x['bucket'])):x for x in old['subsets']};req(set(op)=={(d,b) for d in (128,1024) for b in BUCKETS},'old Pareto panel set')
    panels=[];gate_identity=True;gate_members=True;gate_union=True;gate_rank=True;gate_modal=True;gate_layers=True;gate_order=True;gate_capacity=True;gate_dense=False;gate_sparse_comp=True
    for d in DENOMS:
      for b in BUCKETS:
        src=dp[(d,b)];topo=list(src['topomodal_candidates']);rec=list(src['recurrent_candidates']);atoms=list(src['atoms']);K=len(rec)
        req(K==int(src['dag_audit']['recurrent_candidate_count']),'recurrent count audit')
        req(len(atoms)==int(src['dag_audit']['atom_count']),'atom count audit')
        topo_by={i:r for i,r in enumerate(topo)};rec_by={i:r for i,r in enumerate(rec)}
        req(all(int(r['rank'])==i+1 for i,r in enumerate(rec)),'recurrent order/rank mismatch')
        if d==64 and any(int(r['topomodal_degree'])>1 for r in atoms):gate_dense=True
        contrib=sorted({int(a0['topomodal_index']) for a0 in atoms})
        req(all(i in topo_by for i in contrib),'bad TopoModal index')
        modal_order=sorted(contrib,key=lambda i:(-float(topo_by[i]['modal_contrast']),int(topo_by[i]['rank']),str(topo_by[i]['family_hash'])))
        M={i:j+1 for j,i in enumerate(modal_order)};req(sorted(M.values())==list(range(1,len(M)+1)),'modal rank not permutation')
        succ=[]
        for a0 in atoms:
            ti=int(a0['topomodal_index']);ri=int(a0['recurrent_index']);req(ti in topo_by and ri in rec_by,'bad atom parent index')
            t=topo_by[ti];r=rec_by[ri]
            exact_hash=hashlib.sha256('|'.join(mem(a0)).encode()).hexdigest();req(exact_hash==str(a0['atom_hash']),'atom hash mismatch')
            req(str(a0['topomodal_family_hash'])==str(t['family_hash']),'atom TopoModal hash mismatch');req(str(a0['recurrent_family_hash'])==str(r['family_hash']),'atom recurrent hash mismatch')
            contrast=float(t['modal_contrast']);peak=float(t['active_mode_peak']);outside=float(t['outside_merge_level'])
            req(math.isfinite(contrast) and contrast>=-1e-12 and math.isfinite(peak) and math.isfinite(outside),'bad modal provenance')
            req(abs(contrast-(peak-outside))<=1e-12,'modal contrast identity')
            row=dict(a0)
            row.update({'catalogue_source':'crosshierarchy_dag_atom_pareto_prominence','recurrence_rank':int(r['rank']),'modal_prominence_rank':int(M[ti]),'native_support_rank':int(t['rank']),'modal_contrast':max(0.0,contrast),'active_mode_peak':peak,'outside_merge_level':outside,'topomodal_family_id':str(t['family_id']),'recurrent_family_id':str(r['family_id'])})
            succ.append(row)
        layers=nondominated_layers(succ)
        for r in succ:r['pareto_layer']=int(layers[str(r['atom_hash'])])
        succ.sort(key=lambda r:(int(r['pareto_layer']),int(r['modal_prominence_rank']),int(r['recurrence_rank']),int(r['native_support_rank']),str(r['atom_hash'])))
        for rank,r in enumerate(succ,1):r['dag_atom_pareto_rank']=rank;r['rank']=rank
        gate_layers=gate_layers and len(layers)==len(succ) and set(layers)=={str(x['atom_hash']) for x in succ}
        gate_identity=gate_identity and sorted(str(x['atom_hash']) for x in succ)==sorted(str(x['atom_hash']) for x in atoms)
        gate_members=gate_members and {str(x['atom_hash']):mem(x) for x in succ}=={str(x['atom_hash']):mem(x) for x in atoms}
        gate_union=gate_union and disjoint(succ) and set().union(*(set(mem(x)) for x in succ))==set().union(*(set(mem(x)) for x in atoms))
        gate_rank=gate_rank and all(int(x['recurrence_rank'])==int(rec_by[int(x['recurrent_index'])]['rank']) for x in succ)
        gate_modal=gate_modal and sorted({int(x['modal_prominence_rank']) for x in succ})==list(range(1,len(M)+1))
        gate_order=gate_order and [int(x['rank']) for x in succ]==list(range(1,len(succ)+1))
        gate_capacity=gate_capacity and len(succ)>=K
        if d==64:
            comparator_kind='recurrent_eom';comp=[dict(x) for x in rec]
        else:
            o=op[(d,b)];ids=set(o['annual_event_ids']['2022'])|set(o['annual_event_ids']['2023'])
            req(len(ids)==int(src['event_count']) and uhash(ids)==str(src['event_universe_sha256']),'old Pareto universe differs from DAG')
            req(int(o['equal_budget_k'])==K,'old Pareto K differs')
            comp=[dict(x) for x in o['successor_candidates']];comprec=list(o['recurrent_candidates'])
            req(len(comprec)==K,'old Pareto recurrent K')
            gate_sparse_comp=gate_sparse_comp and [mem(x) for x in comp]==[mem(x) for x in o['successor_candidates']]
            comparator_kind='recurrent_topomodal_pareto_prominence_v1'
        panels.append({'denominator':d,'bucket':b,'event_count':int(src['event_count']),'annual_event_count':src['annual_event_count'],'event_universe_sha256':str(src['event_universe_sha256']),'equal_budget_k':K,'successor_candidates':succ,'comparator_kind':comparator_kind,'comparator_candidates':comp,'dag_audit':src['dag_audit']})
    gates={'dag_source_and_pass_exact':True,'exact_12_panel_identity_counts_and_firewall':len(panels)==12,'complete_atom_identity_exact':gate_identity,'atom_memberships_byte_equivalent':gate_members,'atom_disjoint_union_exact':gate_union,'recurrent_parent_rank_exact':gate_rank,'topomodal_modal_provenance_and_rank_exact':gate_modal,'pareto_layers_valid_complete':gate_layers,'final_order_complete_deterministic':gate_order,'atom_capacity_at_least_k_all_panels':gate_capacity,'d64_many_to_many_mechanism_active':gate_dense,'no_truth_target_or_external_access':True}
    verdict='PASS_DAG_ATOM_PARETO_PROMINENCE_V1_PRETRUTH' if all(gates.values()) and gate_sparse_comp else 'FAIL_DAG_ATOM_PARETO_PROMINENCE_V1_PRETRUTH'
    pre={'schema':'ORBITTRACE_DAG_ATOM_PARETO_PROMINENCE_V1_PRELABEL','scientific_role':'PRELABEL_DAG_ATOM_PARETO_PROMINENCE_V1','source_dag_prelabel_sha256':DAG_PRELABEL_SHA256,'source_dag_result_sha256':DAG_RESULT_SHA256,'source_pareto_prelabel_sha256':PARETO_PRELABEL_SHA256,'configuration':{'candidate_membership':'exact_nonempty_topomodal_intersection_recurrent_atom','atom_filter':None,'objectives':['recurrent_parent_rank_minimize','contributing_topomodal_modal_prominence_rank_minimize'],'modal_prominence_order':'modal_contrast_desc_native_support_rank_asc_family_hash_asc','pareto':'ordinary_nondominated_layers','final_order':'pareto_layer_modal_prominence_rank_recurrence_rank_native_support_rank_atom_hash','equal_budget':'exact_recurrent_parent_count_per_panel','d64_comparator':'exact_recurrent_eom','d128_d1024_comparator':'exact_recurrent_topomodal_pareto_prominence_v1'},'panels':panels,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'asfn_efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False}
    pp=a.output/'DAG_ATOM_PARETO_PROMINENCE_V1_PRELABEL.json';pp.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+'\n');ph=sha256(pp)
    audit={'schema':'ORBITTRACE_DAG_ATOM_PARETO_PROMINENCE_V1_PRETRUTH','scientific_role':'ZERO_LABEL_PRETRUTH_AUTHORIZATION','verdict':verdict,'prelabel_sha256':ph,'gates':gates,'sparse_comparator_rebind_exact':gate_sparse_comp,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'external_scientific_access':False,'post_result_parameter_search':False}
    rp=a.output/'DAG_ATOM_PARETO_PROMINENCE_V1_PRETRUTH.json';rp.write_text(json.dumps(audit,indent=2,sort_keys=True,allow_nan=False)+'\n')
    (a.output/'PRELABEL_SHA256.txt').write_text(ph+'\n');(a.output/'PRETRUTH_SHA256.txt').write_text(sha256(rp)+'\n')
    print(json.dumps({'verdict':verdict,'gates':gates,'sparse_comparator_rebind_exact':gate_sparse_comp,'counts':[(p['denominator'],p['bucket'],p['equal_budget_k'],len(p['successor_candidates']),len(p['comparator_candidates'])) for p in panels]},indent=2),flush=True)
    return 0
if __name__=='__main__':raise SystemExit(main())
