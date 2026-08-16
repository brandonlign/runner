#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
from typing import Any
import numpy as np
from scipy.spatial import cKDTree
from gudhi.clustering.tomato import Tomato

MAP_SHA="92f6ce1961b0e8642f6bdd1cc455b07785ed8224c8f8f3d467d69fac2b82921c"
STATION_STRUCT_SHA="a7cc8921a9431028f08c92479a001021160ee0e8cce6ed346a80d0d2510a8bb8"
INTRINSIC_BLOB="752df8212ce601227f6e9170b0fe994ba06b515d"
MIN_SUPPORT=4; RADIUS=1.0

def req(x:bool,m:str)->None:
    if not x: raise RuntimeError(m)
def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p:Path,n:str)->Any:
    s=importlib.util.spec_from_file_location(n,p); req(s is not None and s.loader is not None,f"cannot import {p}"); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def ah(a:np.ndarray)->str:return hashlib.sha256(np.ascontiguousarray(np.asarray(a,dtype='<f8')).tobytes()).hexdigest()

def station_ranked(parent:Any, structural:Any, events:list[dict[str,Any]], mapping:dict[str,int])->tuple[list[dict[str,Any]],dict[str,Any]]:
    ordered=sorted(events,key=lambda e:str(e['id'])); ids=[str(e['id']) for e in ordered]; n=len(ids); req(n>4,'subset too small')
    w=np.asarray([mapping.get(eid,-1) for eid in ids],dtype=float); req(w.shape==(n,) and np.all(np.isfinite(w)) and np.all(w>=2) and np.all(w==np.floor(w)),'incomplete/invalid num_stat')
    Z=np.asarray(structural.physical_embedding(ordered),dtype=float); req(Z.shape==(n,6) and np.all(np.isfinite(Z)),'physical embedding')
    raw=cKDTree(Z).query_ball_point(Z,r=RADIUS,p=2.0,eps=0.0,return_sorted=True); neighbors=[list(map(int,x)) for x in raw]; req(len(neighbors)==n,'graph rows')
    adj=[set(x) for x in neighbors]; req(all(i in adj[i] for i in range(n)) and all(i in adj[j] for i,row in enumerate(neighbors) for j in row),'graph symmetry/self')
    total=float(np.sum(w)); req(total>0 and np.isfinite(total),'station total')
    rho=np.asarray([float(np.sum(w[np.asarray(row,dtype=np.int64)]))/total for row in neighbors],dtype=float); req(np.all(np.isfinite(rho)) and np.all(rho>0),'station density')
    model=Tomato(graph_type='manual',density_type='manual'); model.fit(neighbors,weights=rho)
    labels=np.asarray(model.leaf_labels_,dtype=np.int64); L=int(model.n_leaves_); req(labels.shape==(n,) and L>=1 and int(labels.min())>=0 and int(labels.max())+1==L,'leaf contract')
    children=np.asarray(model.children_,dtype=np.int64).reshape((-1,2)); roots_expected=len(np.asarray(model.max_weight_per_cc_,dtype=float)); req(L-len(children)==roots_expected,'root arithmetic')
    diag=np.asarray(model.diagram_,dtype=float)
    if diag.size: req(diag.ndim==2 and diag.shape[1]==2 and np.all(np.isfinite(diag)),'diagram'); prom=np.sort(np.asarray(diag[:,0]-diag[:,1],dtype=float))
    else: prom=np.empty(0,dtype=float)
    req(len(prom)==len(children) and np.all(prom>=-1e-15),'prominence'); prom=np.maximum(prom,0.0)
    for t in np.unique(prom): model.merge_threshold_=float(t); req(int(model.n_clusters_)==int(np.count_nonzero(prom>t)+roots_expected),'merge invariant')
    N=L+len(children); member:[Any]=[None]*N; par=np.full(N,-1,dtype=np.int64); creation=np.zeros(N,dtype=float)
    for leaf in range(L):
        ix=np.flatnonzero(labels==leaf); req(len(ix)>0,'empty leaf'); member[leaf]=frozenset(int(i) for i in ix)
    for off,pair in enumerate(children):
        node=L+off; a,b=int(pair[0]),int(pair[1]); req(0<=a<node and 0<=b<node and a!=b and par[a]==-1 and par[b]==-1,'children'); ma,mb=member[a],member[b]; req(ma is not None and mb is not None and ma.isdisjoint(mb),'membership'); member[node]=frozenset(ma|mb); par[a]=node; par[b]=node; creation[node]=float(prom[off])
    roots=np.flatnonzero(par==-1); req(len(roots)==roots_expected and sum(len(member[int(r)]) for r in roots)==n,'roots')
    unique={}; structural_rows=[]
    for node,ixset in enumerate(member):
        req(ixset is not None,'missing node')
        if len(ixset)<MIN_SUPPORT: continue
        mids=tuple(sorted(ids[i] for i in ixset)); fh=structural.member_hash(frozenset(mids)); root=bool(par[node]==-1); vals=rho[np.asarray(sorted(ixset),dtype=np.int64)]; peak=float(np.max(vals)); mean=float(np.mean(vals))
        if root: span=None
        else: span=max(0.0,float(creation[int(par[node])]-creation[node])); req(span>=0,'span')
        fid=hashlib.sha256(('SWTM1|'+'|'.join(mids)).encode()).hexdigest()[:20]
        row={'family_id':fid,'family_hash':fh,'event_ids':list(mids),'member_count':len(mids),'first_node':node,'is_root':root,'creation_prominence':float(creation[node]),'prominence_span':span,'peak_density':peak,'mean_density':mean}
        req(mids not in unique,'duplicate'); unique[mids]=row; structural_rows.append({'family_hash':fh,'member_count':len(mids),'first_node':node,'is_root':root})
    def key(r):
        if r['is_root']: return (0,-float(r['peak_density']),-float(r['mean_density']),-int(r['member_count']),str(r['family_hash']))
        return (1,-float(r['prominence_span']),-float(r['peak_density']),-float(r['mean_density']),-int(r['member_count']),str(r['family_hash']))
    ranked=sorted(unique.values(),key=key)
    for i,r in enumerate(ranked,1): r['rank']=i
    req([r['rank'] for r in ranked]==list(range(1,len(ranked)+1)),'ranks')
    return ranked,{'candidate_count':len(ranked),'candidate_rows':sorted(structural_rows,key=lambda r:(-r['member_count'],r['family_hash'])),'leaf_count':L,'internal_node_count':len(children),'root_count':len(roots),'station_density_sha256':ah(rho),'station_weight_sha256':ah(w),'station_support_total':total,'station_support_mean_per_event':float(np.mean(w)),'graph_edge_count':int((sum(len(x) for x in neighbors)-n)//2)}

def main()->int:
    ap=argparse.ArgumentParser()
    for n in ('base-generator','intrinsic-runner','structural-runner','original-structural-result','station-structural-result','numstat-mapping','availability-result','local-orderstat-source','parent-runner','quality-source','support-source-parts','candidate-payload','baseline-payload','scorer-parts','v8-result-json'): ap.add_argument('--'+n,type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha(a.numstat_mapping)==MAP_SHA,'mapping hash'); station_struct=json.loads(a.station_structural_result.read_text()); req(sha(a.station_structural_result)==STATION_STRUCT_SHA and station_struct['interpretation']=='SUPPORTS_STATION_WEIGHTED_TOPOMODAL_CROSS_SCALE_COHERENCE','station structural prerequisite')
    avail=json.loads(a.availability_result.read_text()); req(avail['verdict']=='PASS_TOPOMODAL_NUMSTAT_AVAILABILITY_V1' and avail['audited_mapping_sha256']==MAP_SHA,'availability prerequisite')
    mapping=json.loads(a.numstat_mapping.read_text()); req(len(mapping)==23080 and all(isinstance(v,int) and not isinstance(v,bool) and v>=2 for v in mapping.values()),'mapping values')
    base=load(a.base_generator,'swtm_base_generator'); structural=load(a.structural_runner,'swtm_structural')
    # Engineering-only evaluator repair: the inherited harness verifies event counts and
    # recurrent-EOM membership rows against its structural-result input. Bind that check
    # to the already-sealed station-weighted zero-label artifact, whose recurrent-EOM rows
    # were generated in the same frozen runtime. Candidate generation/ranking is unchanged.
    base.STRUCTURAL_RESULT_SHA256=STATION_STRUCT_SHA
    base.rankdensity_topomodal=lambda parent,structural_mod,events: station_ranked(parent,structural_mod,events,mapping)
    old=sys.argv[:]
    sys.argv=[str(a.base_generator),'--intrinsic-runner',str(a.intrinsic_runner),'--structural-runner',str(a.structural_runner),'--structural-result-json',str(a.station_structural_result),'--local-orderstat-source',str(a.local_orderstat_source),'--parent-runner',str(a.parent_runner),'--quality-source',str(a.quality_source),'--support-source-parts',str(a.support_source_parts),'--candidate-payload',str(a.candidate_payload),'--baseline-payload',str(a.baseline_payload),'--scorer-parts',str(a.scorer_parts),'--v8-result-json',str(a.v8_result_json),'--output',str(a.output)]
    try: rc=int(base.main())
    finally: sys.argv=old
    req(rc==0,'base prelabel harness')
    p=a.output/'RANKDENSITY_TOPOMODAL_V1_PRELABEL.json'; req(p.is_file(),'base prelabel missing'); pre=json.loads(p.read_text())
    expected={(int(x['denominator']),int(x['bucket'])):x for x in station_struct['fits']}
    for row in pre['subsets']:
        ex=expected[(int(row['denominator']),int(row['bucket']))]; ss=row['successor_summary']; es=ex['station_weighted_topomodal']; req(ss['candidate_count']==es['candidate_count'] and ss['candidate_rows']==es['candidate_rows'],'station structural membership mismatch')
    sm=station_struct['summary']; cs=pre['cross_scale']['summary']; req(abs(float(cs['successor_pooled'])-float(sm['station_weighted_topomodal_pooled_fine_to_coarse_mean_best_jaccard']))<1e-12,'pooled structural mismatch'); req(int(cs['strict_wins'])==4,'bucket wins mismatch')
    pre['schema']='ORBITTRACE_STATION_WEIGHTED_TOPOMODAL_RECOVERY_V1_PRELABEL'; pre['scientific_role']='PRELABEL_STATION_WEIGHTED_TOPOMODAL_RECOVERY_V1'; pre['station_structural_result_sha256']=STATION_STRUCT_SHA; pre['availability_mapping_sha256']=MAP_SHA; pre['intrinsic_source_blob']=INTRINSIC_BLOB; pre['configuration']={'density':'sum_num_stat_in_radius_neighborhood_over_total_subset_num_stat','station_weight':'exact_integer_num_stat_no_transform_no_cap_no_imputation','graph':'exact_1284_physical_radius_1','hierarchy':'complete_gudhi_3.12_manual_topomato','ranking':'exact_intrinsic_1284_root_then_finite_prominence_peak_mean_support_hash','min_candidate_support':4,'equal_budget':'recurrent_candidate_count'}; pre['structural_prerequisite_pass']=True; pre['method_parameter_selection_from_result']=False
    out=a.output/'STATION_WEIGHTED_TOPOMODAL_RECOVERY_V1_PRELABEL.json'; out.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+'\n'); p.unlink(); print(json.dumps({'prelabel_sha256':sha(out),'candidate_budget_shortage_any_panel':pre['candidate_budget_shortage_any_panel'],'cross_scale':pre['cross_scale']},indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
