#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path
from typing import Any
import numpy as np

YEARS=(2022,2023); MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13)); BLIND=(20.0,55.0)
D=64; BUCKETS=(0,1,2,3); SALT='ORBITTRACE_SCALE_STRESS_V1|'
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'; V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(path:Path,name:str)->Any:
    s=importlib.util.spec_from_file_location(name,path);req(s is not None and s.loader is not None,f'cannot import {path}');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def h64(eid:str)->int:return int.from_bytes(hashlib.sha256((SALT+str(eid)).encode()).digest()[:8],'big')
def mem(r:dict[str,Any])->frozenset[str]:return frozenset(str(x) for x in r['event_ids'])
def disjoint(rows:list[dict[str,Any]])->bool:
    ss=[mem(x) for x in rows];return all(not a&b for i,a in enumerate(ss) for b in ss[i+1:])

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('support-cut-generator','structural-runner','pareto-builder','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.quality_source)==QUALITY_SHA,'quality source changed');req(sha(a.v8_result_json)==V8_SHA,'v8 source changed')
    cut=load(a.support_cut_generator,'scale64_cut');structural=load(a.structural_runner,'scale64_structural');pareto=load(a.pareto_builder,'scale64_pareto');parent=load(a.parent_runner,'scale64_parent')
    req(tuple(cut.YEARS)==YEARS and tuple(cut.BLIND)==BLIND and float(cut.RADIUS)==1.0 and int(cut.MIN_SUPPORT)==4,'support-cut scientific constants changed')
    req(tuple(structural.BLIND)==BLIND and float(structural.RADIUS)==1.0 and int(structural.MIN_SUPPORT)==4,'structural constants changed')
    req(tuple(parent.BLIND)==BLIND and int(parent.MIN_CLUSTER_SIZE)==10 and int(parent.MIN_SAMPLES)==10,'parent constants changed')
    q=load(a.quality_source,'scale64_gmn');q.v1.mult.YEARS=YEARS;q.v1.mult.MONTH_KEYS=MONTH_KEYS;q.v1.mult.TOP_K=100
    runtime=q.v1.mult.load_frozen_runtime();support=runtime.load_support_module(a.support_source_parts);support.YEARS=YEARS;support.MONTH_KEYS=MONTH_KEYS;support.CORPUS='orbittrace-pareto-prominence-scale64-v1-target-excluded';support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'firewall changed');setattr(a,'fixed4_baseline_json',a.v8_result_json)
    _c,base,_s=support.load_sources(a);scan,_cal,hidden_unused,sources=support.parse_catalogue(base);del hidden_unused
    req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'GMN source set changed')
    events=[]
    for y in YEARS:events.extend(parent.normalize_event(r,y) for r in list(scan[y]))
    req(len(events)==738682 and len({str(e['id']) for e in events})==738682,'target-excluded universe changed');req(all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'protected event survived')
    Xfull=parent.geo_matrix(events);years_full=np.asarray([int(e['year']) for e in events],dtype=np.int64);ids_full=[str(e['id']) for e in events];hashes=np.asarray([h64(x) for x in ids_full],dtype=np.uint64)
    subsets=[];panels=[];active=False
    for b in BUCKETS:
        ix=np.flatnonzero((hashes%np.uint64(D))==np.uint64(b));sub=[events[int(i)] for i in ix];X=np.asarray(Xfull[ix],dtype=float);yrs=np.asarray(years_full[ix],dtype=np.int64);ids=[ids_full[int(i)] for i in ix]
        req(all(np.any(yrs==y) for y in YEARS),'panel lost year');print(f'[scale64-pretruth] b={b} n={len(ids)}',flush=True)
        support_rows,ss=cut.support_resolved_cut(structural,sub);parents,ps=cut.recurrent_ranked(parent,X,yrs,ids)
        req(disjoint(support_rows) and disjoint(parents),'source candidates overlap');K=len(parents);req(K>0,'empty recurrent comparator');req([int(x['rank']) for x in parents]==list(range(1,K+1)),'parent rank discontinuity')
        retained=[];audit=[]
        for r0 in support_rows:
            s=mem(r0);hits=[i+1 for i,p in enumerate(parents) if s&mem(p)];req(len(hits)<=1,'support child overlaps multiple recurrent parents')
            ar={'family_hash':str(r0['family_hash']),'support_rank':int(r0['rank']),'parent_overlap_count':len(hits),'corroborating_parent_rank':hits[0] if hits else None}
            if hits:
                r=dict(r0);r['native_support_rank']=int(r0['rank']);r['corroborating_parent_rank']=hits[0];r['catalogue_source']='recurrent_overlap_confirmed_topomodal';retained.append(r);ar['retained']=True
            else: ar['retained']=False
            audit.append(ar)
        req(retained and disjoint(retained),'retained set empty/non-disjoint');inherited=sorted(retained,key=lambda r:(int(r['corroborating_parent_rank']),int(r['native_support_rank']),str(r['family_hash'])))
        ranked,_M,_L=pareto.build(retained);req(len(ranked)>=K,f'insufficient Pareto capacity b={b}: {len(ranked)}<{K}');req(disjoint(ranked),'Pareto memberships overlap')
        source_mem={str(x['family_hash']):mem(x) for x in retained};req(all(mem(x)==source_mem[str(x['family_hash'])] for x in ranked),'Pareto changed membership')
        top_in=[str(x['family_hash']) for x in inherited[:K]];top_new=[str(x['family_hash']) for x in ranked[:K]];panel_active=top_in!=top_new;active|=panel_active
        annual={str(y):[ids[int(i)] for i in np.flatnonzero(yrs==y)] for y in YEARS};universe=set(annual['2022'])|set(annual['2023']);req(len(universe)==len(ids),'annual universe mismatch')
        subsets.append({'denominator':D,'bucket':b,'event_count':len(ids),'events_by_year':{str(y):int(np.sum(yrs==y)) for y in YEARS},'annual_event_ids':annual,'event_universe_sha256':hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest(),'equal_budget_k':K,'support_cut_candidates':support_rows,'recurrent_candidates':parents,'overlap_audit':audit,'successor_candidates':ranked})
        panels.append({'bucket':b,'event_count':len(ids),'K':K,'support_count':len(support_rows),'overlap_confirmed_count':len(retained),'pareto_capacity_at_least_k':len(ranked)>=K,'pareto_order_active':panel_active,'support_pairwise_disjoint':True,'recurrent_pairwise_disjoint':True})
    req(active,'Pareto ordering inactive in all d64 panels')
    pre={'schema':'ORBITTRACE_PARETO_PROMINENCE_SCALE64_V1_PRELABEL','scientific_role':'PRELABEL_PARETO_PROMINENCE_SCALE64_V1','configuration':{'denominator':D,'buckets':list(BUCKETS),'salt':SALT,'candidate_extraction':'exact_frozen_support_resolved_topomodal_cut','corroboration':'retain_iff_exactly_one_recurrent_parent_overlap','pareto_objectives':['corroborating_parent_rank_minimize','modal_prominence_rank_minimize'],'pareto_final_order':'layer_M_R_native_support_rank_family_hash','equal_budget':'recurrent_candidate_count'},'subsets':subsets,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'asfn_event_level_access':False,'efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'method_parameter_selection_from_result':False}
    pp=a.output/'PARETO_PROMINENCE_SCALE64_V1_PRELABEL.json';pp.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+'\n');ph=sha(pp)
    gates={'firewall_and_exact_scale':True,'support_cut_disjoint_all_4':all(x['support_pairwise_disjoint'] for x in panels),'recurrent_disjoint_and_ranked_all_4':all(x['recurrent_pairwise_disjoint'] for x in panels),'unique_parent_corroboration':True,'retained_membership_unchanged':True,'pareto_rank_and_layers_valid':True,'capacity_at_least_k_all_4':all(x['pareto_capacity_at_least_k'] for x in panels),'pareto_order_active_any_panel':active}
    verdict='PASS_PARETO_PROMINENCE_SCALE64_V1_PRETRUTH' if all(gates.values()) else 'FAIL_PARETO_PROMINENCE_SCALE64_V1_PRETRUTH'
    out={'schema':'ORBITTRACE_PARETO_PROMINENCE_SCALE64_V1_PRETRUTH','scientific_role':'ZERO_LABEL_SCALE_TRANSLATION_AUTHORIZATION','verdict':verdict,'prelabel_sha256':ph,'panels':panels,'gates':gates,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_2013_2014_access':False,'method_parameter_selection_from_result':False}
    (a.output/'PARETO_PROMINENCE_SCALE64_V1_PRETRUTH.json').write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps({'verdict':verdict,'prelabel_sha256':ph,'panels':panels,'gates':gates},indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
