#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Any

SOURCE_SHA='bd0d28410d23bef0c5c8847ecd8d54e91b74e148ce62e8533407787d265e468f'
BS=(0,1,2,3); MIN_SUPPORT=4
EXPECTED_K={(128,0):29,(128,1):35,(128,2):38,(128,3):33,(1024,0):8,(1024,1):5,(1024,2):6,(1024,3):9}

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def mem(r:dict[str,Any])->frozenset[str]:return frozenset(str(x) for x in r['event_ids'])
def disjoint(rows:list[dict[str,Any]])->bool:
    ss=[mem(r) for r in rows]
    return all(not a&b for i,a in enumerate(ss) for b in ss[i+1:])
def restrict(rows:list[dict[str,Any]],u:set[str])->list[frozenset[str]]:
    out=[];seen=set()
    for r in rows:
        s=frozenset(x for x in mem(r) if x in u)
        if len(s)>=MIN_SUPPORT and s not in seen:seen.add(s);out.append(s)
    return out
def mbj(fine:list[dict[str,Any]],coarse:list[dict[str,Any]],u:set[str])->float:
    fs=[mem(r) for r in fine];cs=restrict(coarse,u)
    if not fs:return 0.0
    vals=[]
    for a in fs:
        best=0.0
        for b in cs:
            i=len(a&b)
            if i:best=max(best,i/len(a|b))
        vals.append(best)
    return sum(vals)/len(vals)

def build(children:list[dict[str,Any]]):
    req(children and disjoint(children),'source children empty or non-disjoint')
    hashes=[str(c['family_hash']) for c in children];req(len(hashes)==len(set(hashes)),'family_hash collision')
    for c in children:
        mc=float(c['modal_contrast']);peak=float(c['active_mode_peak']);outside=float(c['outside_merge_level'])
        req(math.isfinite(mc) and mc>=0.0,'bad modal_contrast')
        req(math.isfinite(peak) and math.isfinite(outside),'bad mode density values')
        req(math.isclose(mc,peak-outside,rel_tol=1e-12,abs_tol=1e-12),'modal_contrast provenance mismatch')
        req(int(c['corroborating_parent_rank'])>=1,'invalid parent rank')
    prom=sorted(children,key=lambda c:(-float(c['modal_contrast']),int(c['native_support_rank']),str(c['family_hash'])))
    M={str(c['family_hash']):i+1 for i,c in enumerate(prom)}
    req(sorted(M.values())==list(range(1,len(children)+1)),'modal rank not permutation')
    def dominates(a:dict[str,Any],b:dict[str,Any])->bool:
        ra=int(a['corroborating_parent_rank']);rb=int(b['corroborating_parent_rank']);ma=M[str(a['family_hash'])];mb=M[str(b['family_hash'])]
        return ra<=rb and ma<=mb and (ra<rb or ma<mb)
    remaining=list(children);layer={};L=1
    while remaining:
        front=[a for a in remaining if not any(dominates(b,a) for b in remaining if b is not a)]
        req(bool(front),'empty Pareto front')
        for a in front:layer[str(a['family_hash'])]=L
        remove={str(x['family_hash']) for x in front};remaining=[x for x in remaining if str(x['family_hash']) not in remove];L+=1
    req(len(layer)==len(children),'layer assignment incomplete')
    for a in children:
        for b in children:
            if a is not b and dominates(a,b):req(layer[str(a['family_hash'])]<layer[str(b['family_hash'])],'dominance/layer violation')
    out=[]
    ordered=sorted(children,key=lambda c:(layer[str(c['family_hash'])],M[str(c['family_hash'])],int(c['corroborating_parent_rank']),int(c['native_support_rank']),str(c['family_hash'])))
    for rank,c0 in enumerate(ordered,1):
        c=dict(c0);h=str(c['family_hash']);c['modal_prominence_rank']=M[h];c['pareto_layer']=layer[h];c['pareto_prominence_rank']=rank;c['catalogue_source']='recurrent_topomodal_pareto_prominence';out.append(c)
    return out,M,layer

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--source-prelabel',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.source_prelabel)==SOURCE_SHA,'source prelabel changed');src=json.loads(a.source_prelabel.read_text())
    req(src['schema']=='ORBITTRACE_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRELABEL','wrong source schema');req(src['scientific_role']=='PRELABEL_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1','wrong source role')
    for flag in ('shower_truth_used','target_information_access','target_region_events_accessed','sonotaco_2013_2014_access','amos_scientific_access','maarsy_scientific_access','dms_scientific_access'):
        req(src.get(flag) is False,f'firewall flag {flag}')
    sm={(int(x['denominator']),int(x['bucket'])):x for x in src['subsets']};keys=set(EXPECTED_K);req(set(sm)==keys,'panel set')
    orders={};parents={};universes={};panels=[];frozen=[]
    identity_all=True;membership_all=True;modal_all=True;layer_all=True;order_all=True;disjoint_all=True;capacity_all=True;coarse_cover_all=True;fine_cover_all=True
    for key in sorted(keys):
        row=sm[key];K=EXPECTED_K[key];req(int(row['equal_budget_k'])==K,'K changed')
        children=list(row['successor_candidates']);parent=list(row['recurrent_candidates']);req(len(parent)==K,'parent count changed')
        out,M,L=build(children)
        identity=set(str(x['family_hash']) for x in out)==set(str(x['family_hash']) for x in children) and len(out)==len(children)
        smem={str(x['family_hash']):mem(x) for x in children};membership=all(mem(x)==smem[str(x['family_hash'])] for x in out)
        modal_ok=all(math.isfinite(float(x['modal_contrast'])) and float(x['modal_contrast'])>=0 and math.isclose(float(x['modal_contrast']),float(x['active_mode_peak'])-float(x['outside_merge_level']),rel_tol=1e-12,abs_tol=1e-12) for x in children)
        layer_ok=sorted(int(x['pareto_prominence_rank']) for x in out)==list(range(1,len(out)+1)) and all(int(x['pareto_layer'])>=1 for x in out)
        order_ok=[int(x['pareto_prominence_rank']) for x in out]==list(range(1,len(out)+1))
        dj=disjoint(out);cap=len(out)>=K
        old_distinct=len({int(x['corroborating_parent_rank']) for x in children[:K]});new_distinct=len({int(x['corroborating_parent_rank']) for x in out[:K]})
        cover_ok=new_distinct>old_distinct if key[0]==128 else new_distinct>=old_distinct
        if key[0]==128:coarse_cover_all &= cover_ok
        else:fine_cover_all &= cover_ok
        identity_all&=identity;membership_all&=membership;modal_all&=modal_ok;layer_all&=layer_ok;order_all&=order_ok;disjoint_all&=dj;capacity_all&=cap
        universe=set(row['annual_event_ids']['2022'])|set(row['annual_event_ids']['2023']);req(len(universe)==int(row['event_count']),'event universe changed');req(all(mem(x).issubset(universe) for x in out+parent),'candidate outside universe')
        panels.append({'denominator':key[0],'bucket':key[1],'K':K,'candidate_count':len(out),'max_pareto_layer':max(int(x['pareto_layer']) for x in out),'source_topk_distinct_parent_count':old_distinct,'successor_topk_distinct_parent_count':new_distinct,'distinct_parent_gate':cover_ok,'candidate_identity_exact':identity,'membership_unchanged':membership,'modal_provenance_valid':modal_ok,'pareto_layers_valid':layer_ok,'deterministic_order':order_ok,'pairwise_disjoint':dj,'capacity_at_least_k':cap})
        frozen.append({'denominator':key[0],'bucket':key[1],'event_count':len(universe),'annual_event_ids':row['annual_event_ids'],'equal_budget_k':K,'successor_candidates':out,'recurrent_candidates':parent,'source_overlap_consensus_candidates':children})
        orders[key]=out;parents[key]=parent;universes[key]=universe
    cross=[]
    for b in BS:
        fk=(1024,b);ck=(128,b);fu=universes[fk];req(fu.issubset(universes[ck]),'fine not nested')
        sj=mbj(orders[fk][:EXPECTED_K[fk]],orders[ck][:EXPECTED_K[ck]],fu);rj=mbj(parents[fk][:EXPECTED_K[fk]],parents[ck][:EXPECTED_K[ck]],fu)
        cross.append({'bucket':b,'successor_mean_best_jaccard':sj,'recurrent_mean_best_jaccard':rj,'nonlower':sj>=rj})
    smn=sum(x['successor_mean_best_jaccard'] for x in cross)/4;rmn=sum(x['recurrent_mean_best_jaccard'] for x in cross)/4;cross_all=all(x['nonlower'] for x in cross)
    gates={'immutable_source_and_firewall':True,'candidate_identity_exact_all_8':identity_all,'membership_byte_equivalent_all_8':membership_all,'modal_contrast_provenance_all_8':modal_all,'modal_prominence_rank_permutation_all_8':True,'pareto_layers_valid_all_8':layer_all,'deterministic_permutation_all_8':order_all,'pairwise_disjoint_all_8':disjoint_all,'capacity_at_least_k_all_8':capacity_all,'coarse_distinct_parent_strict_gain_4_of_4':coarse_cover_all,'fine_distinct_parent_nonlower_4_of_4':fine_cover_all,'cross_scale_nonlower_4_of_4_and_aggregate':cross_all and smn>=rmn}
    req(len(gates)==12,'gate count')
    verdict='PASS_RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1_PRETRUTH' if all(gates.values()) else 'FAIL_RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1_PRETRUTH'
    pre={'schema':'ORBITTRACE_RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1_PRELABEL','scientific_role':'PRELABEL_RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1','source_prelabel_sha256':SOURCE_SHA,'configuration':{'objectives':['corroborating_parent_rank_minimize','modal_prominence_rank_minimize'],'modal_prominence_order':'modal_contrast_desc_native_support_rank_asc_family_hash_asc','pareto':'ordinary_nondominated_layers','final_order':'pareto_layer_modal_prominence_rank_parent_rank_native_support_rank_family_hash','equal_budget':'exact_recurrent_parent_count_per_panel'},'subsets':frozen,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    pp=a.output/'RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1_PRELABEL.json';pp.write_text(json.dumps(pre,indent=2,sort_keys=True)+'\n');ps=sha(pp)
    res={'schema':'ORBITTRACE_RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1_PRETRUTH','scientific_role':'ZERO_LABEL_PRETRUTH_AUTHORIZATION','verdict':verdict,'prelabel_sha256':ps,'panels':panels,'cross_scale':cross,'aggregate':{'successor_cross_scale_mean':smn,'recurrent_cross_scale_mean':rmn,'nonlower_buckets':sum(x['nonlower'] for x in cross)},'gates':gates,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    (a.output/'RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1_PRETRUTH.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'verdict':verdict,'prelabel_sha256':ps,'aggregate':res['aggregate'],'gates':gates,'panels':panels,'cross_scale':cross},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
