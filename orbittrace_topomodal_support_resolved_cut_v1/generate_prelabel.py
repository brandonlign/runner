#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, importlib.util, json
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from gudhi.clustering.tomato import Tomato
from hdbscan._hdbscan_tree import compute_stability
from scipy.spatial import cKDTree

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
QUALITY_SHA256="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
STRUCTURAL_RESULT_SHA256="e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
SALT="ORBITTRACE_SCALE_STRESS_V1|"
COARSE_D,FINE_D=128,1024
BUCKETS=(0,1,2,3)
RADIUS=1.0
MIN_SUPPORT=4


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)

def sha256(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def load_module(p:Path,name:str)->Any:
    s=importlib.util.spec_from_file_location(name,p); req(s is not None and s.loader is not None,f"cannot import {p}")
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def event_hash_u64(eid:str)->int: return int.from_bytes(hashlib.sha256((SALT+eid).encode()).digest()[:8],"big")
def selected_indices(h:np.ndarray,d:int,b:int)->np.ndarray: return np.flatnonzero((h%np.uint64(d))==np.uint64(b))
def family_id(prefix:str,members:tuple[str,...])->str: return hashlib.sha256((prefix+"|"+"|".join(members)).encode()).hexdigest()[:20]
def universe_hash(ids:list[str])->str: return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()
def diagram_sorted(a:np.ndarray)->np.ndarray:
    a=np.asarray(a,dtype=float)
    if a.size==0:return np.empty((0,2),dtype=float)
    req(a.ndim==2 and a.shape[1]==2 and np.all(np.isfinite(a)),"invalid diagram")
    return a[np.lexsort((a[:,1],a[:,0]))]


def support_resolved_cut(structural:Any,events:list[dict[str,Any]])->tuple[list[dict[str,Any]],dict[str,Any]]:
    ordered=sorted(events,key=lambda e:str(e["id"])); ids=[str(e["id"]) for e in ordered]
    Z=structural.physical_embedding(ordered)
    neigh=[list(map(int,r)) for r in cKDTree(Z).query_ball_point(Z,r=RADIUS,p=2.0,eps=0.0,return_sorted=True)]
    adj=[set(r) for r in neigh]
    req(len(neigh)==len(ids),"graph row count")
    for i,r in enumerate(neigh): req(r.count(i)==1 and all(0<=j<len(ids) for j in r),f"bad graph row {i}")
    req(all(i in adj[j] for i,r in enumerate(neigh) for j in r),"graph asymmetric")
    deg=np.asarray([len(r) for r in neigh],dtype=float); rho=deg/float(len(ids))
    req(np.all(np.isfinite(rho)) and np.all(rho>0),"bad density")

    model=Tomato(graph_type="manual",density_type="manual"); model.fit(neigh,weights=rho)
    labels=np.asarray(model.leaf_labels_,dtype=np.int64); L=int(model.n_leaves_)
    children=np.asarray(model.children_,dtype=np.int64).reshape((-1,2)); roots_expected=len(np.asarray(model.max_weight_per_cc_,dtype=float))
    req(labels.shape==(len(ids),) and L>=1 and int(labels.min())>=0 and int(labels.max())+1==L,"bad leaves")
    req(L-len(children)==roots_expected,"leaf/merge/root arithmetic")
    diagram=np.asarray(model.diagram_,dtype=float); ds=diagram_sorted(diagram)
    P=np.sort(np.asarray(diagram[:,0]-diagram[:,1],dtype=float)) if diagram.size else np.empty(0,dtype=float)
    req(len(P)==len(children)==len(ds) and np.all(P>=-1e-15),"bad finite persistence")
    P=np.maximum(P,0.0)

    N=L+len(children)
    members:[Any]=[None]*N; parent=np.full(N,-1,dtype=np.int64); kids:[Any]=[None]*N
    active_peak=np.full(N,np.nan,dtype=float); active_key:[Any]=[None]*N; merge_level=np.full(N,np.nan,dtype=float)
    for leaf in range(L):
        ix=np.flatnonzero(labels==leaf); req(len(ix)>0,f"empty leaf {leaf}")
        members[leaf]=frozenset(ids[int(i)] for i in ix)
        peak=float(np.max(rho[ix])); keys=sorted(ids[int(i)] for i in ix if float(rho[int(i)])==peak)
        req(bool(keys),"no peak key"); active_peak[leaf]=peak; active_key[leaf]=keys[0]

    reconstructed=[]; dying=set()
    for off,pair in enumerate(children):
        node=L+off; a,b=int(pair[0]),int(pair[1])
        req(0<=a<node and 0<=b<node and a!=b and parent[a]==-1 and parent[b]==-1,"bad hierarchy")
        ma,mb=members[a],members[b]; req(ma is not None and mb is not None and ma.isdisjoint(mb),"bad child membership")
        pa,pb=float(active_peak[a]),float(active_peak[b]); ka,kb=str(active_key[a]),str(active_key[b])
        if pa>pb or (pa==pb and ka<kb): winner,loser=a,b
        else: winner,loser=b,a
        members[node]=frozenset(ma.union(mb)); kids[node]=(a,b); parent[a]=node; parent[b]=node
        active_peak[node]=float(active_peak[winner]); active_key[node]=str(active_key[winner])
        req(loser not in dying,"mode died twice"); dying.add(loser)
        death=float(active_peak[loser])-float(P[off]); merge_level[node]=death
        reconstructed.append([float(active_peak[loser]),death])
    roots=np.flatnonzero(parent==-1); req(len(roots)==roots_expected,"root count")
    req(sum(len(members[int(r)]) for r in roots)==len(ids),"roots do not partition")
    rec=diagram_sorted(np.asarray(reconstructed,dtype=float)); req(rec.shape==ds.shape,"diagram shape")
    req(np.allclose(rec,ds,rtol=0.0,atol=1e-12),f"diagram reconstruction mismatch {float(np.max(np.abs(rec-ds))) if rec.size else 0.0}")
    for t in np.unique(P):
        model.merge_threshold_=float(t); req(int(model.n_clusters_)==int(np.count_nonzero(P>t)+roots_expected),f"threshold invariant {t}")

    # Independent exact #1284 full-hierarchy reconstruction supplied by its frozen source.
    full_candidates,full_summary=structural.topomodal_candidates(ordered)
    full_member_set={tuple(sorted(str(x) for x in m)) for m in full_candidates}

    selected_nodes:list[int]=[]
    def cut(node:int)->None:
        m=members[node]; req(m is not None,"missing node")
        ch=kids[node]
        if ch is None:
            if len(m)>=MIN_SUPPORT:selected_nodes.append(node)
            return
        a,b=ch
        if len(members[a])>=MIN_SUPPORT and len(members[b])>=MIN_SUPPORT:
            cut(a); cut(b)
        elif len(m)>=MIN_SUPPORT:
            selected_nodes.append(node)
    for r in roots: cut(int(r))
    req(len(selected_nodes)==len(set(selected_nodes)),"duplicate selected node")

    selected_sets=[members[n] for n in selected_nodes]; req(all(m is not None and len(m)>=MIN_SUPPORT for m in selected_sets),"sub-support selected")
    for i,a in enumerate(selected_sets):
        for b in selected_sets[i+1:]: req(a.isdisjoint(b),"cut candidates overlap")
    for r in roots:
        rm=members[int(r)]
        if len(rm)>=MIN_SUPPORT:
            union=frozenset().union(*(m for m in selected_sets if m.issubset(rm)))
            req(union==rm,"cut does not partition reportable root")
    req(all(tuple(sorted(m)) in full_member_set for m in selected_sets),"cut node absent from #1284 hierarchy")

    rows=[]
    for node,m in zip(selected_nodes,selected_sets):
        p=int(parent[node]); outside=0.0 if p==-1 else float(merge_level[p])
        req(np.isfinite(outside),f"missing outside merge {node}")
        contrast=float(active_peak[node])-outside; req(contrast>=-1e-12 and np.isfinite(contrast),f"bad contrast {node} {contrast}")
        contrast=max(contrast,0.0); tup=tuple(sorted(str(x) for x in m))
        rows.append({"family_id":family_id("TSRC1",tup),"family_hash":structural.member_hash(m),"event_ids":list(tup),"member_count":len(tup),"node":int(node),"is_root":bool(p==-1),"active_mode_peak":float(active_peak[node]),"active_mode_key":str(active_key[node]),"outside_merge_level":outside,"modal_contrast":contrast})
    rows.sort(key=lambda r:(-float(r["modal_contrast"]),str(r["family_hash"])))
    for rank,r in enumerate(rows,1):r["rank"]=rank
    req([r["rank"] for r in rows]==list(range(1,len(rows)+1)),"rank discontinuity")
    return rows,{"full_candidate_count":int(full_summary["candidate_count"]),"full_candidate_rows":full_summary["candidate_rows"],"cut_candidate_count":len(rows),"root_count":len(roots),"selected_root_count":sum(bool(r["is_root"]) for r in rows),"pairwise_disjoint":True,"diagram_reconstruction_max_abs_error":float(np.max(np.abs(rec-ds))) if rec.size else 0.0,"median_radius_degree":float(np.median(deg)),"p90_radius_degree":float(np.quantile(deg,0.9))}


def recurrent_ranked(parent_runner:Any,X:np.ndarray,years:np.ndarray,event_ids:list[str])->tuple[list[dict[str,Any]],dict[str,Any]]:
    model=hdbscan.HDBSCAN(min_cluster_size=10,min_samples=10,metric="euclidean",cluster_selection_method="eom",cluster_selection_epsilon=0.0,allow_single_cluster=False,prediction_data=False).fit(X)
    tree=model.condensed_tree_._raw_tree; ordinary=compute_stability(tree); recurrent,_=parent_runner.recurrent_stability(tree,years)
    labels=np.asarray(parent_runner.eom_labels(tree,recurrent),dtype=np.int64); nodes=tuple(int(x) for x in parent_runner.selected_eom_nodes(tree,recurrent))
    req(sorted(int(x) for x in np.unique(labels) if int(x)>=0)==list(range(len(nodes))),"bad recurrent labels")
    rows=[]
    for lab,node in enumerate(nodes):
        ix=np.flatnonzero(labels==lab); mem=tuple(sorted(event_ids[int(i)] for i in ix)); req(len(mem)>=10,"sub10 comparator")
        rows.append({"family_id":family_id("REOM1",mem),"family_hash":hashlib.sha256("|".join(mem).encode()).hexdigest()[:20],"event_ids":list(mem),"member_count":len(mem),"node_id":node,"ordinary_stability":float(ordinary[float(node)]),"recurrent_stability":float(recurrent[float(node)])})
    rows.sort(key=lambda r:(-r["recurrent_stability"],-r["ordinary_stability"],-r["member_count"],r["family_id"]))
    for rank,r in enumerate(rows,1):r["rank"]=rank
    summary=sorted([{"family_hash":r["family_hash"],"member_count":r["member_count"]} for r in rows],key=lambda r:(-r["member_count"],r["family_hash"]))
    return rows,{"candidate_count":len(rows),"candidate_rows":summary}


def main()->int:
    ap=argparse.ArgumentParser()
    for name in ("structural-runner","structural-result-json","parent-runner","quality-source","support-source-parts","candidate-payload","baseline-payload","scorer-parts","v8-result-json"):ap.add_argument("--"+name,type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha256(a.quality_source)==QUALITY_SHA256,"quality source changed"); req(sha256(a.v8_result_json)==V8_RESULT_SHA256,"v8 artifact changed"); req(sha256(a.structural_result_json)==STRUCTURAL_RESULT_SHA256,"#1284 result changed")
    sr=json.loads(a.structural_result_json.read_text()); req(sr["interpretation"]=="SUPPORTS_FIXED_SCALE_TOPOMODAL_HIERARCHY_CROSS_SCALE_COHERENCE","#1284 prerequisite")
    expected={(int(r["denominator"]),int(r["bucket"])):r for r in sr["fits"]}; req(set(expected)=={(d,b) for d in (128,1024) for b in BUCKETS},"panel set")
    structural=load_module(a.structural_runner,"src_structural"); parent_runner=load_module(a.parent_runner,"src_parent")
    req(tuple(structural.BLIND)==BLIND and float(structural.RADIUS)==1.0 and int(structural.MIN_SUPPORT)==4,"structural constants"); req(tuple(parent_runner.BLIND)==BLIND and int(parent_runner.MIN_CLUSTER_SIZE)==10 and int(parent_runner.MIN_SAMPLES)==10,"parent constants")
    q=load_module(a.quality_source,"src_gmn"); q.v1.mult.YEARS=YEARS; q.v1.mult.MONTH_KEYS=MONTH_KEYS; q.v1.mult.TOP_K=100
    runtime=q.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS="orbittrace-topomodal-support-resolved-cut-v1-target-excluded"; support.RANKING_VARIANTS=("persistence",)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"firewall changed"); setattr(a,"fixed4_baseline_json",a.v8_result_json)
    _c,base,_s=support.load_sources(a); scan,_cal,hidden_unused,sources=support.parse_catalogue(base); del hidden_unused
    req(sorted(scan)==list(YEARS) and [x["key"] for x in sources]==list(MONTH_KEYS),"GMN source set changed")
    events=[]
    for y in YEARS: events.extend(parent_runner.normalize_event(r,y) for r in list(scan[y]))
    req(len(events)==738682 and len({str(e["id"]) for e in events})==738682,"event universe changed"); req(all(not(BLIND[0]<=float(e["sol"])<=BLIND[1]) for e in events),"protected event survived")
    Xfull=parent_runner.geo_matrix(events); years_full=np.asarray([int(e["year"]) for e in events],dtype=np.int64); ids_full=[str(e["id"]) for e in events]; hashes=np.asarray([event_hash_u64(x) for x in ids_full],dtype=np.uint64)
    subsets=[]
    for d in (COARSE_D,FINE_D):
        for b in BUCKETS:
            ix=selected_indices(hashes,d,b); sub=[events[int(i)] for i in ix]; X=np.asarray(Xfull[ix],dtype=float); yrs=np.asarray(years_full[ix],dtype=np.int64); ids=[ids_full[int(i)] for i in ix]
            print(f"[support-cut-prelabel] d={d} b={b} n={len(ids)}",flush=True)
            succ,ss=support_resolved_cut(structural,sub); par,ps=recurrent_ranked(parent_runner,X,yrs,ids); ex=expected[(d,b)]
            req(ex["topomodal"]["candidate_rows"]==ss["full_candidate_rows"] and int(ex["topomodal"]["candidate_count"])==ss["full_candidate_count"],f"#1284 hierarchy mismatch d={d} b={b}")
            req(ex["recurrent_eom"]["candidate_rows"]==ps["candidate_rows"] and int(ex["recurrent_eom"]["candidate_count"])==len(par),f"comparator mismatch d={d} b={b}")
            K=min(len(succ),len(par)); subsets.append({"denominator":d,"bucket":b,"events_total":len(ids),"events_by_year":{str(y):int(np.sum(yrs==y)) for y in YEARS},"event_universe_sha256":universe_hash(ids),"equal_budget_k":K,"cut_summary":ss,"recurrent_summary":ps,"successor_candidates":succ,"recurrent_candidates":par})
    pre={"schema":"ORBITTRACE_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1_PRELABEL","scientific_role":"PRELABEL_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1","structural_source_run_id":31955621864,"structural_source_artifact_id":9265889512,"structural_result_sha256":STRUCTURAL_RESULT_SHA256,"configuration":{"cut_rule":"split_iff_both_immediate_children_support_ge_4_else_keep_parent","min_support":4,"ranking":"modal_contrast_desc_then_family_hash_asc","root_outside_merge_level":0.0,"equal_budget":"min(successor,recurrent)_both_truncated"},"subsets":subsets,"blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"shower_truth_used":False,"sonotaco_2013_2014_access":False,"asfn_event_level_access":False,"efn_event_level_access":False,"amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"method_parameter_selection_from_result":False}
    out=a.output/"TOPOMODAL_SUPPORT_RESOLVED_CUT_V1_PRELABEL.json"; out.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+"\n"); digest=sha256(out)
    print(json.dumps({"prelabel_sha256":digest,"subsets":[{"d":r["denominator"],"b":r["bucket"],"successor":len(r["successor_candidates"]),"recurrent":len(r["recurrent_candidates"]),"K":r["equal_budget_k"],"roots":r["cut_summary"]["selected_root_count"]} for r in subsets]},indent=2),flush=True); return 0

if __name__=="__main__": raise SystemExit(main())
