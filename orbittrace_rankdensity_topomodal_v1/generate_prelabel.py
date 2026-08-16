#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
from gudhi.clustering.tomato import Tomato
from scipy.spatial import cKDTree

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
BUCKETS=(0,1,2,3)
COARSE_D=128
FINE_D=1024
MIN_SUPPORT=4
RADIUS=1.0
QUALITY_SHA256="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
STRUCTURAL_RESULT_SHA256="e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
INTRINSIC_SOURCE_BLOB="752df8212ce601227f6e9170b0fe994ba06b515d"
LOCAL_ORDERSTAT_SOURCE_BLOB="d3bf781ba697447beb8f695dca21a137c7212408"


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)

def sha256(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f"cannot import {path}")
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def arr_hash(a:np.ndarray)->str:
    x=np.ascontiguousarray(np.asarray(a,dtype="<f8")); return hashlib.sha256(x.tobytes()).hexdigest()

def family_id(members:tuple[str,...])->str:
    return hashlib.sha256(("RDTM1|"+"|".join(members)).encode()).hexdigest()[:20]

def universe_hash(ids:list[str])->str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def rankdensity_topomodal(parent:Any, structural:Any, events:list[dict[str,Any]])->tuple[list[dict[str,Any]],dict[str,Any]]:
    ordered=sorted(events,key=lambda e:str(e["id"])); ids=[str(e["id"]) for e in ordered]; n=len(ids)
    req(n>4,"subset too small")

    # Exact PR #1277/#1278 support-4 raw compactness coordinate: r_j with j=3.
    X=np.asarray(parent.geo_matrix(ordered),dtype=float); req(X.shape==(n,6) and np.all(np.isfinite(X)),"invalid GEO6")
    d,_idx=cKDTree(X).query(X,k=4,workers=1); d=np.asarray(d,dtype=float)
    req(d.shape==(n,4) and np.all(np.abs(d[:,0])<=1e-14),"self neighbor contract")
    r3=np.asarray(d[:,3],dtype=float); req(np.all(np.isfinite(r3)) and np.all(r3>0),"invalid third-other-neighbor radius")
    density_order=sorted(range(n),key=lambda i:(float(r3[i]),ids[i]))
    ranks=np.empty(n,dtype=np.int64)
    for rank,i in enumerate(density_order,1): ranks[int(i)]=rank
    q=1.0-ranks.astype(float)/float(n+1)
    req(np.all(q>0) and np.all(q<1) and len(np.unique(q))==n,"empirical density rank invalid")

    # Exact #1284 physical connectivity graph.
    Z=structural.physical_embedding(ordered)
    raw=cKDTree(Z).query_ball_point(Z,r=RADIUS,p=2.0,eps=0.0,return_sorted=True)
    neighbors=[list(map(int,row)) for row in raw]; req(len(neighbors)==n,"graph rows")
    adjacency=[set(row) for row in neighbors]
    for i,row in enumerate(neighbors):
        req(i in row and all(0<=j<n for j in row),"graph index/self")
    req(all(i in adjacency[j] for i,row in enumerate(neighbors) for j in row),"graph not symmetric")
    degrees=np.asarray([len(row) for row in neighbors],dtype=float)

    model=Tomato(graph_type="manual",density_type="manual"); model.fit(neighbors,weights=q)
    labels=np.asarray(model.leaf_labels_,dtype=np.int64); req(labels.shape==(n,),"leaf labels")
    L=int(model.n_leaves_); req(L>=1 and int(labels.min())>=0 and int(labels.max())+1==L,"leaf count")
    children=np.asarray(model.children_,dtype=np.int64).reshape((-1,2)); roots_expected=len(np.asarray(model.max_weight_per_cc_,dtype=float)); req(L-len(children)==roots_expected,"root arithmetic")
    diagram=np.asarray(model.diagram_,dtype=float)
    if diagram.size:
        req(diagram.ndim==2 and diagram.shape[1]==2 and np.all(np.isfinite(diagram)),"diagram")
        prominences=np.sort(np.asarray(diagram[:,0]-diagram[:,1],dtype=float))
    else: prominences=np.empty(0,dtype=float)
    req(len(prominences)==len(children) and np.all(prominences>=-1e-15),"prominence sequence")
    prominences=np.maximum(prominences,0.0)
    # Exact engineering invariant inherited from the frozen intrinsic ranker.
    for threshold in np.unique(prominences):
        model.merge_threshold_=float(threshold)
        expected=int(np.count_nonzero(prominences>threshold)+roots_expected)
        req(int(model.n_clusters_)==expected,f"threshold/merge count {threshold}")

    N=L+len(children); member_ix:[Any]=[None]*N; parent=np.full(N,-1,dtype=np.int64); creation=np.zeros(N,dtype=float)
    for leaf in range(L):
        ix=np.flatnonzero(labels==leaf); req(len(ix)>0,"empty leaf"); member_ix[leaf]=frozenset(int(i) for i in ix)
    req(sum(len(member_ix[i]) for i in range(L))==n,"leaf partition")
    for off,pair in enumerate(children):
        node=L+off; a,b=int(pair[0]),int(pair[1]); req(0<=a<node and 0<=b<node and a!=b,"bad children"); req(parent[a]==-1 and parent[b]==-1,"multiple parents")
        ma,mb=member_ix[a],member_ix[b]; req(ma is not None and mb is not None and ma.isdisjoint(mb),"bad child membership")
        member_ix[node]=frozenset(ma.union(mb)); parent[a]=node; parent[b]=node; creation[node]=float(prominences[off])
    roots=np.flatnonzero(parent==-1); req(len(roots)==roots_expected and sum(len(member_ix[int(r)]) for r in roots)==n,"roots")

    unique:dict[tuple[str,...],dict[str,Any]]={}; structural_rows=[]
    for node,ixset in enumerate(member_ix):
        req(ixset is not None,"missing node")
        if len(ixset)<MIN_SUPPORT: continue
        members=tuple(sorted(ids[i] for i in ixset)); fh=structural.member_hash(frozenset(members)); is_root=bool(parent[node]==-1); vals=q[np.asarray(sorted(ixset),dtype=np.int64)]
        peak=float(np.max(vals)); mean=float(np.mean(vals))
        if is_root: span=None
        else:
            par=int(parent[node]); sv=float(creation[par]-creation[node]); req(sv>=-1e-12,f"negative prominence span node={node}: {sv}"); span=max(0.0,sv)
        row={"family_id":family_id(members),"family_hash":fh,"event_ids":list(members),"member_count":len(members),"first_node":int(node),"is_root":is_root,"creation_prominence":float(creation[node]),"prominence_span":span,"peak_density":peak,"mean_density":mean}
        req(members not in unique,f"duplicate hierarchy membership {fh}"); unique[members]=row; structural_rows.append({"family_hash":fh,"member_count":len(members),"first_node":int(node),"is_root":is_root})
    def key(r:dict[str,Any])->tuple[Any,...]:
        if bool(r["is_root"]): return (0,-float(r["peak_density"]),-float(r["mean_density"]),-int(r["member_count"]),str(r["family_hash"]))
        return (1,-float(r["prominence_span"]),-float(r["peak_density"]),-float(r["mean_density"]),-int(r["member_count"]),str(r["family_hash"]))
    ranked=sorted(unique.values(),key=key)
    for k,r in enumerate(ranked,1): r["rank"]=k
    req([r["rank"] for r in ranked]==list(range(1,len(ranked)+1)),"rank continuity")
    counts=sorted((int(r["member_count"]) for r in ranked),reverse=True)
    graph_edges=int((sum(len(x) for x in neighbors)-n)//2)
    return ranked,{"candidate_count":len(ranked),"candidate_rows":sorted(structural_rows,key=lambda r:(-int(r["member_count"]),str(r["family_hash"]))),"leaf_count":L,"internal_node_count":len(children),"root_count":len(roots),"finite_persistence_point_count":len(prominences),"r3_sha256":arr_hash(r3),"q_sha256":arr_hash(q),"density_order_sha256":hashlib.sha256("\n".join(ids[i] for i in density_order).encode()).hexdigest(),"graph_edge_count":graph_edges,"median_radius_degree":float(np.median(degrees)),"p90_radius_degree":float(np.quantile(degrees,0.90)),"largest_candidate_count":counts[0] if counts else 0,"largest_candidate_fraction":float(counts[0]/n) if counts else 0.0}


def main()->int:
    ap=argparse.ArgumentParser()
    for name in ("intrinsic-runner","structural-runner","structural-result-json","local-orderstat-source","parent-runner","quality-source","support-source-parts","candidate-payload","baseline-payload","scorer-parts","v8-result-json"):
        ap.add_argument("--"+name,type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    intrinsic=load_module(a.intrinsic_runner,"rdtm_intrinsic"); structural=load_module(a.structural_runner,"rdtm_structural"); parent=load_module(a.parent_runner,"rdtm_parent")
    req(sha256(a.quality_source)==QUALITY_SHA256 and sha256(a.v8_result_json)==V8_RESULT_SHA256 and sha256(a.structural_result_json)==STRUCTURAL_RESULT_SHA256,"frozen input hash")
    req(tuple(parent.YEARS)==YEARS and tuple(parent.BLIND)==BLIND and int(parent.MIN_CLUSTER_SIZE)==10 and int(parent.MIN_SAMPLES)==10,"parent constants")
    # Historical source is pinned by workflow Git blob; perform semantic assertions here too.
    local_src=a.local_orderstat_source.read_text(); req("PAIRS = {s: (s - 1, 2 * s - 1) for s in SUPPORTS}" in local_src and "compactness = -np.log(rj)" in local_src,"historical support-4 coordinate source changed")
    structural_json=json.loads(a.structural_result_json.read_text()); expected={(int(r["denominator"]),int(r["bucket"])):r for r in structural_json["fits"]}; req(set(expected)=={(d,b) for d in (128,1024) for b in BUCKETS},"structural panels")

    qmod=load_module(a.quality_source,"rdtm_gmn"); qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100; runtime=qmod.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS="orbittrace-rankdensity-topomodal-v1-target-excluded"; support.RANKING_VARIANTS=("persistence",); req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"firewall"); setattr(a,"fixed4_baseline_json",a.v8_result_json); _c,base,_s=support.load_sources(a); scan,_cal,hidden_unused,sources=support.parse_catalogue(base); del hidden_unused; req(sorted(scan)==list(YEARS) and [x["key"] for x in sources]==list(MONTH_KEYS),"sources")
    events=[]
    for y in YEARS: events.extend(parent.normalize_event(row,y) for row in list(scan[y]))
    req(len(events)==738682 and len({str(e["id"]) for e in events})==len(events),"universe"); req(all(not(BLIND[0]<=float(e["sol"])<=BLIND[1]) for e in events),"protected event")
    Xfull=parent.geo_matrix(events); yrs=np.asarray([int(e["year"]) for e in events],dtype=np.int64); ids=[str(e["id"]) for e in events]; hashes=np.asarray([intrinsic.event_hash_u64(x) for x in ids],dtype=np.uint64)

    subsets=[]; runtime_rows={}
    for d in (128,1024):
        for b in BUCKETS:
            ii=intrinsic.selected_indices(hashes,d,b); sub=[events[int(i)] for i in ii]; sx=np.asarray(Xfull[ii]); sy=np.asarray(yrs[ii]); sid=[ids[int(i)] for i in ii]; req(all(np.any(sy==y) for y in YEARS),"subset lost year"); print(f"[rdtm-prelabel] d={d} b={b} n={len(sid)}",flush=True)
            succ,ss=rankdensity_topomodal(parent,structural,sub); par,ps=intrinsic.recurrent_ranked(parent,sx,sy,sid); ex=expected[(d,b)]
            req(int(ex["events_total"])==len(sid) and {str(k):int(v) for k,v in ex["events_by_year"].items()}=={str(y):int(np.sum(sy==y)) for y in YEARS},"#1284 event mismatch")
            req(ps["candidate_rows"]==ex["recurrent_eom"]["candidate_rows"] and len(par)==int(ex["recurrent_eom"]["candidate_count"]),"recurrent comparator mismatch")
            budget=len(succ)>=len(par)
            subsets.append({"denominator":d,"bucket":b,"events_total":len(sid),"events_by_year":{str(y):int(np.sum(sy==y)) for y in YEARS},"event_universe_sha256":universe_hash(sid),"equal_budget_k":len(par),"candidate_budget_sufficient":budget,"successor_summary":ss,"recurrent_summary":ps,"successor_candidates":succ,"recurrent_candidates":par})
            runtime_rows[(d,b)]={"succ_sets":[frozenset(x["event_ids"]) for x in succ],"par_sets":[frozenset(x["event_ids"]) for x in par],"ids":frozenset(sid)}

    cross=[]; succ_scores=[]; par_scores=[]; wins=0
    for b in BUCKETS:
        c=runtime_rows[(128,b)]; f=runtime_rows[(1024,b)]; sm=structural.cross_scale_metrics(c["succ_sets"],f["succ_sets"],f["ids"]); pm=structural.cross_scale_metrics(c["par_sets"],f["par_sets"],f["ids"]); sv=float(sm["fine_to_coarse_mean_best_jaccard"]); pv=float(pm["fine_to_coarse_mean_best_jaccard"]); wins+=int(sv>pv); succ_scores.extend(float(x) for x in sm["fine_to_coarse_scores"]); par_scores.extend(float(x) for x in pm["fine_to_coarse_scores"]); cross.append({"bucket":b,"successor":sm,"recurrent_eom":pm,"strict_win":sv>pv})
    pooled_s=float(np.mean(np.asarray(succ_scores,dtype=float))) if succ_scores else 0.0; pooled_p=float(np.mean(np.asarray(par_scores,dtype=float))) if par_scores else 0.0
    structural_gates={"pooled_fine_to_coarse_mean_best_jaccard_strictly_greater":pooled_s>pooled_p,"strict_bucket_wins_at_least_3_of_4":wins>=3}
    pre={"schema":"ORBITTRACE_RANKDENSITY_TOPOMODAL_V1_PRELABEL","scientific_role":"PRELABEL_RANKDENSITY_TOPOMODAL_V1","configuration":{"density":"GEO6_third_nearest_other_empirical_rank_q","density_rank":"q=1-rank/(n+1)_ascending_r3_event_id","graph":"exact_1284_physical_radius_1","hierarchy":"complete_gudhi_3.12_manual_topomato","min_candidate_support":4,"ranking":"exact_intrinsic_topomodal_sparse_recovery_v1_semantics","equal_budget":"K_equals_recurrent_candidate_count"},"structural_source_run_id":31955621864,"structural_source_artifact_id":9265889512,"structural_result_sha256":STRUCTURAL_RESULT_SHA256,"intrinsic_source_blob":INTRINSIC_SOURCE_BLOB,"local_orderstat_source_blob":LOCAL_ORDERSTAT_SOURCE_BLOB,"subsets":subsets,"cross_scale":{"buckets":cross,"successor_pooled_fine_to_coarse_mean_best_jaccard":pooled_s,"recurrent_pooled_fine_to_coarse_mean_best_jaccard":pooled_p,"successor_strict_bucket_wins":wins,"gates":structural_gates},"candidate_budget_shortage_any_panel":any(not x["candidate_budget_sufficient"] for x in subsets),"blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"shower_truth_used":False,"sonotaco_2013_2014_access":False,"asfn_event_level_access":False,"efn_event_level_access":False,"amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"method_parameter_selection_from_result":False}
    out=a.output/"RANKDENSITY_TOPOMODAL_V1_PRELABEL.json"; out.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+"\n"); print(json.dumps({"prelabel_sha256":sha256(out),"structural":pre["cross_scale"],"candidate_counts":[{"d":x["denominator"],"b":x["bucket"],"successor":len(x["successor_candidates"]),"parent":len(x["recurrent_candidates"])} for x in subsets]},indent=2,sort_keys=True),flush=True); return 0

if __name__=="__main__": raise SystemExit(main())