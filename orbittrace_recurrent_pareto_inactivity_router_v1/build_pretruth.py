#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path
from typing import Any
import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

YEARS=(2022,2023); MONTH_KEYS=tuple(f'{y}-{m:02d}' for y in YEARS for m in range(1,13)); BLIND=(20.0,55.0)
SALT='ORBITTRACE_SCALE_STRESS_V1|'; D64=64; BUCKETS=(0,1,2,3)
EXPECTED_ACTIVITY={(64,0):True,(64,1):False,(64,2):False,(64,3):True,**{(128,b):False for b in BUCKETS},**{(1024,b):False for b in BUCKETS}}
SCALE_STRESS_SHA='0c6926aa84d9b88f19f5bb2817b2846b53d09579dbef6b5c4d9c9bb9fd252288'
PARETO_PRELABEL_SHA='5752ef8b36a5d317455e649723c26692fe2636262dc6d74befbe2ffb95945310'
QUALITY_SHA='dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990'; V8_SHA='fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b'

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f'cannot import {p}'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def h64(eid:str)->int:return int.from_bytes(hashlib.sha256((SALT+str(eid)).encode()).digest()[:8],'big')
def mem(r:dict[str,Any])->frozenset[str]:return frozenset(str(x) for x in r['event_ids'])
def mh(m:frozenset[str])->str:return hashlib.sha256('|'.join(sorted(m)).encode()).hexdigest()[:20]
def disjoint(rows:list[dict[str,Any]])->bool:
    ss=[mem(x) for x in rows]; return all(not a&b for i,a in enumerate(ss) for b in ss[i+1:])
def canon_hashes(rows:list[dict[str,Any]])->list[str]:return sorted(mh(mem(x)) for x in rows)

def eom_catalogues(parent:Any,X:np.ndarray,years:np.ndarray,event_ids:list[str])->tuple[list[dict[str,Any]],list[dict[str,Any]],tuple[int,...],tuple[int,...]]:
    model=hdbscan.HDBSCAN(min_cluster_size=10,min_samples=10,metric='euclidean',cluster_selection_method='eom',cluster_selection_epsilon=0.0,allow_single_cluster=False,prediction_data=False).fit(X)
    tree=model.condensed_tree_._raw_tree; ordinary=compute_stability(tree); recurrent,_=parent.recurrent_stability(tree,years)
    def rows(stab:dict[Any,float],prefix:str):
        labels=np.asarray(parent.eom_labels(tree,stab),dtype=np.int64); nodes=tuple(int(x) for x in parent.selected_eom_nodes(tree,stab)); req(sorted(int(x) for x in np.unique(labels) if int(x)>=0)==list(range(len(nodes))),f'bad {prefix} labels')
        out=[]
        for lab,node in enumerate(nodes):
            ix=np.flatnonzero(labels==lab); ids=tuple(sorted(event_ids[int(i)] for i in ix)); req(len(ids)>=10,'sub10 family')
            out.append({'family_id':hashlib.sha256((prefix+'|'+'|'.join(ids)).encode()).hexdigest()[:20],'family_hash':mh(frozenset(ids)),'event_ids':list(ids),'member_count':len(ids),'node_id':node,'ordinary_stability':float(ordinary[float(node)]),'route_stability':float(stab[float(node)])})
        out.sort(key=lambda r:(-r['route_stability'],-r['ordinary_stability'],-r['member_count'],r['family_id']))
        for rank,r in enumerate(out,1):r['rank']=rank
        return out,nodes
    o,on=rows(ordinary,'EOM1'); r,rn=rows(recurrent,'REOM1'); return o,r,on,rn

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('protocol','scale-stress-result','pareto-prelabel','support-cut-generator','structural-runner','pareto-builder','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json','output'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.scale_stress_result)==SCALE_STRESS_SHA,'scale-stress result changed'); req(sha(a.pareto_prelabel)==PARETO_PRELABEL_SHA,'Pareto prelabel changed'); req(sha(a.quality_source)==QUALITY_SHA and sha(a.v8_result_json)==V8_SHA,'runtime inputs changed')
    scale=json.loads(a.scale_stress_result.read_text()); pareto_pre=json.loads(a.pareto_prelabel.read_text())
    req(scale['schema']=='ORBITTRACE_RECURRENT_EOM_SCALE_STRESS_V1' and scale['shower_truth_used'] is False,'scale-stress role changed')
    req(pareto_pre['schema']=='ORBITTRACE_RECURRENT_TOPOMODAL_PARETO_PROMINENCE_V1_PRELABEL' and pareto_pre['shower_truth_used'] is False,'Pareto role changed')
    for obj in (scale,pareto_pre):
        req(obj.get('target_information_access') is False and obj.get('target_region_events_accessed') is False,'firewall provenance')
    scale_map={(int(x['denominator']),int(x['bucket'])):x for x in scale['all_fits'] if int(x['denominator']) in (64,128,1024) and int(x['bucket']) in BUCKETS}
    req(set(scale_map)==set(EXPECTED_ACTIVITY),'scale-stress panel set changed')
    for k,v in EXPECTED_ACTIVITY.items():req(bool(scale_map[k]['mechanism_active']) is v,f'frozen activity mismatch {k}')
    sparse={(int(x['denominator']),int(x['bucket'])):x for x in pareto_pre['subsets']}; req(set(sparse)=={(d,b) for d in (128,1024) for b in BUCKETS},'sparse Pareto panel set')
    # Verify the frozen sparse Pareto parent catalogues are exactly the recurrent catalogues in the scale-stress result.
    for k,row in sparse.items():
        expected=sorted(str(x) for x in scale_map[k]['recurrent_membership_hashes']); got=canon_hashes(list(row['recurrent_candidates'])); req(got==expected,f'sparse recurrent identity mismatch {k}')
        req(EXPECTED_ACTIVITY[k] is False,f'sparse panel unexpectedly active {k}')

    cut=load(a.support_cut_generator,'router_cut'); structural=load(a.structural_runner,'router_struct'); pareto=load(a.pareto_builder,'router_pareto'); parent=load(a.parent_runner,'router_parent')
    req(tuple(cut.YEARS)==YEARS and tuple(cut.BLIND)==BLIND and float(cut.RADIUS)==1.0 and int(cut.MIN_SUPPORT)==4,'support-cut constants changed')
    req(tuple(structural.BLIND)==BLIND and float(structural.RADIUS)==1.0 and int(structural.MIN_SUPPORT)==4,'structural constants changed')
    req(tuple(parent.BLIND)==BLIND and int(parent.MIN_CLUSTER_SIZE)==10 and int(parent.MIN_SAMPLES)==10,'parent constants changed')
    q=load(a.quality_source,'router_gmn'); q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=MONTH_KEYS; q.v1.mult.TOP_K=100
    runtime=q.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS='orbittrace-recurrent-pareto-inactivity-router-v1-pretruth'; support.RANKING_VARIANTS=('persistence',)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,'blind changed'); setattr(a,'fixed4_baseline_json',a.v8_result_json)
    _c,base,_s=support.load_sources(a); scan,_cal,hidden_unused,sources=support.parse_catalogue(base); del hidden_unused
    req(sorted(scan)==list(YEARS) and [x['key'] for x in sources]==list(MONTH_KEYS),'GMN source set changed')
    events=[]
    for y in YEARS:events.extend(parent.normalize_event(r,y) for r in list(scan[y]))
    req(len(events)==738682 and len({str(e['id']) for e in events})==738682,'event universe changed'); req(all(not(BLIND[0]<=float(e['sol'])<=BLIND[1]) for e in events),'protected event survived')
    Xfull=parent.geo_matrix(events); yrsfull=np.asarray([int(e['year']) for e in events],dtype=np.int64); idsfull=[str(e['id']) for e in events]; hashes=np.asarray([h64(x) for x in idsfull],dtype=np.uint64)

    routed=[]; audit=[]
    # Reuse immutable d128/d1024 Pareto outputs exactly.
    for d in (128,1024):
        for b in BUCKETS:
            row=sparse[(d,b)]; K=int(row['equal_budget_k']); succ=list(row['successor_candidates']); par=list(row['recurrent_candidates']); req(len(par)==K and len(succ)>=K,'sparse budget changed')
            universe=set(row['annual_event_ids']['2022'])|set(row['annual_event_ids']['2023']); req(all(mem(x).issubset(universe) for x in succ+par),'sparse candidate outside universe')
            routed.append({'denominator':d,'bucket':b,'mechanism_active':False,'route':'pareto_prominence','equal_budget_k':K,'event_count':int(row['event_count']),'annual_event_ids':row['annual_event_ids'],'recurrent_candidates':par,'routed_candidates':succ})
            audit.append({'denominator':d,'bucket':b,'mechanism_active':False,'route':'pareto_prominence','source':'sealed_pareto_prelabel','K':K,'routed_capacity':len(succ),'pretruth_pass':True})

    # Construct only d64. Critically, do not construct or inspect TopoModal on ACTIVE panels.
    for b in BUCKETS:
        ix=np.flatnonzero((hashes%np.uint64(D64))==np.uint64(b)); sub=[events[int(i)] for i in ix]; X=np.asarray(Xfull[ix],dtype=float); yrs=np.asarray(yrsfull[ix],dtype=np.int64); ids=[idsfull[int(i)] for i in ix]
        req(len(ids)==int(scale_map[(64,b)]['events_total']),f'd64 event count mismatch b={b}')
        ordinary,rec,onodes,rnodes=eom_catalogues(parent,X,yrs,ids); active=onodes!=rnodes; req(active is EXPECTED_ACTIVITY[(64,b)],f'd64 activity reconstruction mismatch b={b}')
        req(canon_hashes(rec)==sorted(str(x) for x in scale_map[(64,b)]['recurrent_membership_hashes']),f'd64 recurrent identity mismatch b={b}')
        K=len(rec); annual={str(y):[ids[int(i)] for i in np.flatnonzero(yrs==y)] for y in YEARS}
        if active:
            route=list(rec); source='exact_recurrent_active'; capacity=K
        else:
            support_rows,_ss=cut.support_resolved_cut(structural,sub); req(disjoint(support_rows),'d64 support rows overlap')
            retained=[]
            for r0 in support_rows:
                s=mem(r0); hits=[i+1 for i,p in enumerate(rec) if s&mem(p)]; req(len(hits)<=1,f'd64 inactive child overlaps multiple recurrent parents b={b}')
                if hits:
                    r=dict(r0); r['native_support_rank']=int(r0['rank']); r['corroborating_parent_rank']=hits[0]; r['catalogue_source']='recurrent_overlap_confirmed_topomodal'; retained.append(r)
            req(retained and disjoint(retained),f'd64 inactive retained empty/non-disjoint b={b}')
            route,_M,_L=pareto.build(retained); req(len(route)>=K,f'd64 inactive Pareto capacity {len(route)}<{K} b={b}'); source='exact_pareto_inactive'; capacity=len(route)
        universe=set(ids); req(disjoint(route) and all(mem(x).issubset(universe) for x in route+rec),'d64 routed membership invalid')
        routed.append({'denominator':64,'bucket':b,'mechanism_active':active,'route':'recurrent_eom' if active else 'pareto_prominence','equal_budget_k':K,'event_count':len(ids),'annual_event_ids':annual,'recurrent_candidates':rec,'routed_candidates':route})
        audit.append({'denominator':64,'bucket':b,'mechanism_active':active,'route':'recurrent_eom' if active else 'pareto_prominence','source':source,'K':K,'routed_capacity':capacity,'pretruth_pass':True})

    routed.sort(key=lambda x:(int(x['denominator']),int(x['bucket']))); audit.sort(key=lambda x:(int(x['denominator']),int(x['bucket'])))
    req(len(routed)==12 and len(audit)==12,'router panel count'); req({(int(x['denominator']),int(x['bucket'])) for x in routed}==set(EXPECTED_ACTIVITY),'router panel identity')
    # Active panels must be exact recurrent identity through the full routed order.
    for x in routed:
        if x['mechanism_active']:
            req(len(x['routed_candidates'])==len(x['recurrent_candidates']) and [mem(z) for z in x['routed_candidates']]==[mem(z) for z in x['recurrent_candidates']],f'active route changed recurrent {x["denominator"]}/{x["bucket"]}')
    gates={'protected_firewall':True,'exact_12_panel_universes':True,'exact_activity_map':True,'active_recurrent_identity':True,'sealed_sparse_pareto_identity':True,'d64_inactive_unique_parent_corroboration':True,'d64_inactive_capacity_at_least_k':True,'all_routed_catalogues_disjoint_and_in_universe':True,'no_truth_or_external_access':True}
    verdict='PASS_RECURRENT_PARETO_INACTIVITY_ROUTER_V1_PRETRUTH' if all(gates.values()) else 'FAIL_RECURRENT_PARETO_INACTIVITY_ROUTER_V1_PRETRUTH'
    pre={'schema':'ORBITTRACE_RECURRENT_PARETO_INACTIVITY_ROUTER_V1_PRELABEL','scientific_role':'PRELABEL_SAMPLE_SIZE_ROUTER','configuration':{'route_switch':'exact_recurrent_selected_nodes_equal_ordinary_selected_nodes','active_route':'exact_recurrent_eom','inactive_route':'exact_recurrent_topomodal_pareto_prominence','no_sample_size_threshold':True,'equal_budget':'recurrent_candidate_count'},'panels':routed,'scale_stress_sha256':SCALE_STRESS_SHA,'pareto_prelabel_sha256':PARETO_PRELABEL_SHA,'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'sonotaco_scientific_access':False,'asfn_efn_event_level_access':False,'amos_scientific_access':False,'maarsy_scientific_access':False,'dms_scientific_access':False,'post_result_parameter_search':False}
    pp=a.output/'RECURRENT_PARETO_INACTIVITY_ROUTER_V1_PRELABEL.json'; pp.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+'\n'); ph=sha(pp)
    out={'schema':'ORBITTRACE_RECURRENT_PARETO_INACTIVITY_ROUTER_V1_PRETRUTH','scientific_role':'ZERO_LABEL_ROUTER_AUTHORIZATION','verdict':verdict,'prelabel_sha256':ph,'gates':gates,'panel_audit':audit,'activity_map':{f'{d}:{b}':v for (d,b),v in sorted(EXPECTED_ACTIVITY.items())},'shower_truth_used':False,'target_information_access':False,'target_region_events_accessed':False,'external_scientific_access':False,'post_result_parameter_search':False}
    (a.output/'RECURRENT_PARETO_INACTIVITY_ROUTER_V1_PRETRUTH.json').write_text(json.dumps(out,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'verdict':verdict,'prelabel_sha256':ph,'gates':gates,'panel_audit':audit},indent=2,sort_keys=True),flush=True); return 0
if __name__=='__main__':raise SystemExit(main())
