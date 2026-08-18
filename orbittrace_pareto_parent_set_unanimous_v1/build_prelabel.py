#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path
from typing import Any
import numpy as np

YEARS=(2022,2023); MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13)); BLIND=(20.0,55.0)
D=64; BUCKETS=(0,1,2,3); SALT='ORBITTRACE_SCALE_STRESS_V1|'
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'; V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'
POS_SCHEMA='ORBITTRACE_RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1_PRELABEL'

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(path:Path,name:str)->Any:
    s=importlib.util.spec_from_file_location(name,path);req(s is not None and s.loader is not None,f'cannot import {path}');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def h64(eid:str)->int:return int.from_bytes(hashlib.sha256((SALT+str(eid)).encode()).digest()[:8],'big')
def mem(r:dict[str,Any])->frozenset[str]:return frozenset(str(x) for x in r['event_ids'])
def disjoint(rows:list[dict[str,Any]])->bool:
    ss=[mem(x) for x in rows];return all(not a&b for i,a in enumerate(ss) for b in ss[i+1:])
def pset(r:dict[str,Any])->tuple[int,...]:
    p=tuple(int(x) for x in r['overlap_parent_ranks']);req(bool(p) and p==tuple(sorted(set(p))),'invalid parent-rank set');return p

def modal_ranks(rows:list[dict[str,Any]])->dict[str,int]:
    modal=sorted(rows,key=lambda c:(-float(c['modal_contrast']),int(c['native_support_rank']),str(c['family_hash'])))
    M={str(c['family_hash']):i+1 for i,c in enumerate(modal)}
    req(sorted(M.values())==list(range(1,len(rows)+1)),'modal rank not permutation');return M

def set_pareto_rank(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    req(bool(rows),'empty retained catalogue');M=modal_ranks(rows)
    def dom(a:dict[str,Any],b:dict[str,Any])->bool:
        pa,pb=pset(a),pset(b);ma=M[str(a['family_hash'])];mb=M[str(b['family_hash'])]
        rec=max(pa)<=min(pb)
        return rec and ma<=mb and (max(pa)<min(pb) or ma<mb)
    rem=list(rows);layer={};L=1
    while rem:
        front=[a for a in rem if not any(dom(b,a) for b in rem if b is not a)]
        req(bool(front),'empty unanimous-set Pareto front')
        for a in front:layer[str(a['family_hash'])]=L
        gone={str(x['family_hash']) for x in front};rem=[x for x in rem if str(x['family_hash']) not in gone];L+=1
    for a in rows:
        for b in rows:
            if a is not b and dom(a,b):req(layer[str(a['family_hash'])]<layer[str(b['family_hash'])],'dominance/layer violation')
    ordered=sorted(rows,key=lambda c:(layer[str(c['family_hash'])],M[str(c['family_hash'])],pset(c),int(c['native_support_rank']),str(c['family_hash'])))
    out=[]
    for rank,c0 in enumerate(ordered,1):
        c=dict(c0);h=str(c['family_hash']);c['modal_prominence_rank']=M[h];c['pareto_layer']=layer[h];c['pareto_parent_set_rank']=rank;c['catalogue_source']='recurrent_topomodal_parent_set_unanimous_pareto';out.append(c)
    req([int(x['pareto_parent_set_rank']) for x in out]==list(range(1,len(out)+1)),'rank sequence')
    return out

def barycenter_order(rows:list[dict[str,Any]])->list[str]:
    # Exact frozen barycenter relation reconstructed only as a zero-label activity control.
    M=modal_ranks(rows)
    def rb(r:dict[str,Any])->float:
        ps=pset(r);cs=tuple(int(x) for x in r['overlap_counts']);req(len(ps)==len(cs) and all(x>0 for x in cs),'bad overlap counts');return sum(p*c for p,c in zip(ps,cs))/sum(cs)
    def dom(a:dict[str,Any],b:dict[str,Any])->bool:
        ra,rr=rb(a),rb(b);ma=M[str(a['family_hash'])];mb=M[str(b['family_hash'])];return ra<=rr and ma<=mb and (ra<rr or ma<mb)
    rem=list(rows);layer={};L=1
    while rem:
        front=[a for a in rem if not any(dom(b,a) for b in rem if b is not a)];req(bool(front),'empty bary diagnostic front')
        for a in front:layer[str(a['family_hash'])]=L
        gone={str(x['family_hash']) for x in front};rem=[x for x in rem if str(x['family_hash']) not in gone];L+=1
    ordered=sorted(rows,key=lambda c:(layer[str(c['family_hash'])],M[str(c['family_hash'])],rb(c),int(c['native_support_rank']),str(c['family_hash'])))
    return [str(x['family_hash']) for x in ordered]

def sparse_compatibility(pre:dict[str,Any])->dict[str,Any]:
    req(pre['schema']==POS_SCHEMA and pre['scientific_role']=='PRELABEL_RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1','wrong positive Pareto prelabel')
    exact=True;panels=[]
    for r in pre['subsets']:
        succ=list(r['successor_candidates']);rebuilt=[]
        for s0 in succ:
            rr=int(s0['corroborating_parent_rank']);x=dict(s0);x['native_support_rank']=int(s0['native_support_rank']);x['overlap_parent_ranks']=[rr];x['overlap_counts']=[len(mem(s0))];rebuilt.append(x)
        ranked=set_pareto_rank(rebuilt);old=[str(x['family_hash']) for x in succ];new=[str(x['family_hash']) for x in ranked];same=old==new;exact &= same
        panels.append({'denominator':int(r['denominator']),'bucket':int(r['bucket']),'candidate_count':len(succ),'exact_order_reproduced':same})
    return {'all_8_exact':exact,'panels':panels}

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('support-cut-generator','structural-runner','parent-runner','positive-pareto-prelabel','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.quality_source)==QUALITY_SHA,'quality source changed');req(sha(a.v8_result_json)==V8_SHA,'v8 source changed')
    positive=json.loads(a.positive_pareto_prelabel.read_text());compat=sparse_compatibility(positive);req(compat['all_8_exact'],'parent-set rule failed sparse-source compatibility')
    cut=load(a.support_cut_generator,'uset_cut');structural=load(a.structural_runner,'uset_structural');parent=load(a.parent_runner,'uset_parent')
    req(tuple(cut.YEARS)==YEARS and tuple(cut.BLIND)==BLIND and float(cut.RADIUS)==1.0 and int(cut.MIN_SUPPORT)==4,'support-cut constants changed')
    req(tuple(structural.BLIND)==BLIND and float(structural.RADIUS)==1.0 and int(structural.MIN_SUPPORT)==4,'structural constants changed')
    req(tuple(parent.BLIND)==BLIND and int(parent.MIN_CLUSTER_SIZE)==10 and int(parent.MIN_SAMPLES)==10,'parent constants changed')
    q=load(a.quality_source,'uset_gmn');q.v1.mult.YEARS=YEARS;q.v1.mult.MONTH_KEYS=MONTH_KEYS;q.v1.mult.TOP_K=100
    runtime=q.v1.mult.load_frozen_runtime();support=runtime.load_support_module(a.support_source_parts);support.YEARS=YEARS;support.MONTH_KEYS=MONTH_KEYS;support.CORPUS='orbittrace-pareto-parent-set-unanimous-v1-target-excluded';support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'firewall changed');setattr(a,'fixed4_baseline_json',a.v8_result_json)
    _c,base,_s=support.load_sources(a);scan,_cal,hidden_unused,sources=support.parse_catalogue(base);del hidden_unused
    req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'GMN source set changed')
    events=[]
    for y in YEARS:events.extend(parent.normalize_event(r,y) for r in list(scan[y]))
    req(len(events)==738682 and len({str(e['id']) for e in events})==738682,'target-excluded universe changed');req(all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'protected event survived')
    Xfull=parent.geo_matrix(events);years_full=np.asarray([int(e['year']) for e in events],dtype=np.int64);ids_full=[str(e['id']) for e in events];hashes=np.asarray([h64(x) for x in ids_full],dtype=np.uint64)
    subsets=[];panels=[];multi_total=0;different=False
    for b in BUCKETS:
        ix=np.flatnonzero((hashes%np.uint64(D))==np.uint64(b));sub=[events[int(i)] for i in ix];X=np.asarray(Xfull[ix],dtype=float);yrs=np.asarray(years_full[ix],dtype=np.int64);ids=[ids_full[int(i)] for i in ix]
        req(all(np.any(yrs==y) for y in YEARS),'panel lost year');print(f'[parent-set-pretruth] b={b} n={len(ids)}',flush=True)
        support_rows,_ss=cut.support_resolved_cut(structural,sub);parents,_ps=cut.recurrent_ranked(parent,X,yrs,ids)
        req(disjoint(support_rows) and disjoint(parents),'source candidates overlap');K=len(parents);req(K>0 and [int(x['rank']) for x in parents]==list(range(1,K+1)),'bad recurrent comparator')
        psets=[mem(p) for p in parents];retained=[];audit=[];multi=0
        for r0 in support_rows:
            s=mem(r0);hits=[]
            for j,ps in enumerate(psets,1):
                n=len(s&ps)
                if n:hits.append((j,n))
            ar={'family_hash':str(r0['family_hash']),'support_rank':int(r0['rank']),'overlap_parent_ranks':[r for r,_ in hits],'overlap_counts':[n for _,n in hits],'parent_overlap_count':len(hits)}
            if hits:
                ranks=[r for r,_ in hits];counts=[n for _,n in hits];req(ranks==sorted(set(ranks)) and all(n>0 for n in counts),'invalid complete parent set')
                x=dict(r0);x['native_support_rank']=int(r0['rank']);x['overlap_parent_ranks']=ranks;x['overlap_counts']=counts;retained.append(x);ar['retained']=True
                if len(hits)>1:multi+=1
            else:ar['retained']=False
            audit.append(ar)
        req(retained and disjoint(retained),'retained set empty/non-disjoint')
        ranked=set_pareto_rank(retained);req(len(ranked)>=K,f'insufficient capacity b={b}: {len(ranked)}<{K}')
        source_mem={str(x['family_hash']):mem(x) for x in retained};req(all(mem(x)==source_mem[str(x['family_hash'])] for x in ranked),'membership changed')
        bary=barycenter_order(retained);new=[str(x['family_hash']) for x in ranked];panel_diff=(new!=bary);different|=panel_diff;multi_total+=multi
        annual={str(y):[ids[int(i)] for i in np.flatnonzero(yrs==y)] for y in YEARS};req(len(set(annual['2022'])|set(annual['2023']))==len(ids),'annual universe mismatch')
        subsets.append({'denominator':D,'bucket':b,'event_count':len(ids),'events_by_year':{str(y):int(np.sum(yrs==y)) for y in YEARS},'annual_event_ids':annual,'event_universe_sha256':hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest(),'equal_budget_k':K,'support_cut_candidates':support_rows,'recurrent_candidates':parents,'overlap_audit':audit,'successor_candidates':ranked})
        panels.append({'bucket':b,'event_count':len(ids),'K':K,'support_count':len(support_rows),'retained_count':len(ranked),'multi_parent_count':multi,'capacity_at_least_k':len(ranked)>=K,'order_differs_from_barycenter':panel_diff,'topk_changed_vs_barycenter':new[:K]!=bary[:K]})
    req(multi_total>0,'multi-parent mechanism inactive');req(different,'set-valued order identical to barycenter everywhere')
    pre={'schema':'ORBITTRACE_PARETO_PARENT_SET_UNANIMOUS_V1_PRELABEL','scientific_role':'PRELABEL_PARETO_PARENT_SET_UNANIMOUS_V1','configuration':{'denominator':D,'buckets':list(BUCKETS),'salt':SALT,'candidate_extraction':'frozen_support_resolved_topomodal_cut','retain':'positive_recurrent_overlap','correspondence':'complete_sorted_parent_rank_set','pareto_objectives':['unanimous_parent_set_precedence','modal_prominence_rank_minimize'],'pareto_final_order':'layer_M_full_parent_rank_tuple_native_support_rank_family_hash','equal_budget':'recurrent_candidate_count'},'positive_sparse_compatibility':compat,'subsets':subsets,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    pp=a.output/'PARETO_PARENT_SET_UNANIMOUS_V1_PRELABEL.json';pp.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+'\n');ph=sha(pp)
    gates={'firewall_and_exact_scale':True,'support_cut_disjoint_all_4':True,'recurrent_disjoint_and_ranked_all_4':True,'positive_overlap_retained_zero_overlap_discarded':True,'retained_membership_unchanged':True,'complete_parent_sets_valid':True,'modal_rank_permutation_all':True,'unanimous_pareto_layers_and_order_valid':True,'no_scalar_parent_correspondence_used':True,'capacity_at_least_k_all_4':all(x['capacity_at_least_k'] for x in panels),'multi_parent_and_set_order_active':multi_total>0 and different,'positive_sparse_order_exact_all_8':compat['all_8_exact']}
    verdict='PASS_PARETO_PARENT_SET_UNANIMOUS_V1_PRETRUTH' if all(gates.values()) else 'FAIL_PARETO_PARENT_SET_UNANIMOUS_V1_PRETRUTH'
    out={'schema':'ORBITTRACE_PARETO_PARENT_SET_UNANIMOUS_V1_PRETRUTH','scientific_role':'ZERO_LABEL_SET_VALUED_CORRESPONDENCE_AUTHORIZATION','verdict':verdict,'prelabel_sha256':ph,'panels':panels,'multi_parent_total':multi_total,'gates':gates,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'method_parameter_selection_from_result':False}
    (a.output/'PARETO_PARENT_SET_UNANIMOUS_V1_PRETRUTH.json').write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps({'verdict':verdict,'prelabel_sha256':ph,'multi_parent_total':multi_total,'panels':panels,'gates':gates},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
