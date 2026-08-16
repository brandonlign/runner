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
MIN_SUPPORT=4
RADIUS=1.0
B=199
ALPHA=0.05
NULL_SALT="ORBITTRACE_SIGPRUNE_TM_V1|"
QUALITY_SHA256="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
STRUCTURAL_RESULT_SHA256="e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
RANKDENSITY_PRELABEL_SHA256="b6bf31e9add2b9c2e220ccb91d0778859abe86505731d6a0f071ed9eb7c13533"


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)

def sha256(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f"cannot import {path}")
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def arr_hash(a:np.ndarray,dtype:str="<f8")->str:
    x=np.ascontiguousarray(np.asarray(a,dtype=dtype)); return hashlib.sha256(x.tobytes()).hexdigest()

def universe_hash(ids:list[str])->str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()

def member_hash(members:tuple[str,...])->str:
    return hashlib.sha256("|".join(members).encode()).hexdigest()[:20]

def family_id(members:tuple[str,...])->str:
    return hashlib.sha256(("SPTM1|"+"|".join(members)).encode()).hexdigest()[:20]

def graph_hash(neighbors:list[list[int]])->str:
    h=hashlib.sha256()
    for i,row in enumerate(neighbors):
        h.update(str(i).encode()); h.update(b":"); h.update(",".join(str(int(j)) for j in row).encode()); h.update(b"\n")
    return h.hexdigest()

def null_seed(denominator:int,bucket:int,replicate:int)->int:
    s=f"{NULL_SALT}{denominator}|{bucket}|{replicate}".encode()
    return int.from_bytes(hashlib.sha256(s).digest()[:8],"big")


def build_graph_and_q(parent:Any,structural:Any,events:list[dict[str,Any]])->tuple[list[dict[str,Any]],list[str],np.ndarray,np.ndarray,np.ndarray,list[list[int]],np.ndarray,str]:
    ordered=sorted(events,key=lambda e:str(e["id"])); ids=[str(e["id"]) for e in ordered]; n=len(ids); req(n>4,"subset too small")
    X=np.asarray(parent.geo_matrix(ordered),dtype=float); req(X.shape==(n,6) and np.all(np.isfinite(X)),"invalid GEO6")
    d,_idx=cKDTree(X).query(X,k=4,workers=1); d=np.asarray(d,dtype=float); req(d.shape==(n,4) and np.all(np.abs(d[:,0])<=1e-14),"self-neighbor contract")
    r3=np.asarray(d[:,3],dtype=float); req(np.all(np.isfinite(r3)) and np.all(r3>0),"invalid r3")
    order=np.lexsort((np.asarray(ids,dtype=str),r3)); ranks=np.empty(n,dtype=np.int64); ranks[order]=np.arange(1,n+1,dtype=np.int64); q=1.0-ranks.astype(float)/float(n+1)
    req(np.all(q>0) and np.all(q<1) and len(np.unique(q))==n,"invalid q")
    Z=structural.physical_embedding(ordered); raw=cKDTree(Z).query_ball_point(Z,r=RADIUS,p=2.0,eps=0.0,return_sorted=True); neighbors=[list(map(int,row)) for row in raw]; req(len(neighbors)==n,"graph rows")
    adjacency=[set(row) for row in neighbors]
    for i,row in enumerate(neighbors): req(i in row and all(0<=j<n for j in row),"graph self/index")
    req(all(i in adjacency[j] for i,row in enumerate(neighbors) for j in row),"graph not symmetric")
    degree=np.asarray([len(row) for row in neighbors],dtype=float)
    return ordered,ids,r3,ranks,q,neighbors,degree,graph_hash(neighbors)


def observed_mode_audit(neighbors:list[list[int]],q:np.ndarray)->tuple[Tomato,np.ndarray,np.ndarray,np.ndarray,dict[int,float],set[int],dict[str,Any]]:
    n=len(q); model=Tomato(graph_type="manual",density_type="manual"); model.fit(neighbors,weights=q)
    leaf_labels=np.asarray(model.leaf_labels_,dtype=np.int64); req(leaf_labels.shape==(n,),"leaf labels"); L=int(model.n_leaves_); req(L>=1 and int(leaf_labels.min())>=0 and int(leaf_labels.max())+1==L,"leaf count")
    children=np.asarray(model.children_,dtype=np.int64).reshape((-1,2)); roots_expected=len(np.asarray(model.max_weight_per_cc_,dtype=float)); req(L-len(children)==roots_expected,"root arithmetic")
    diagram=np.asarray(model.diagram_,dtype=float)
    if diagram.size:
        req(diagram.ndim==2 and diagram.shape[1]==2 and np.all(np.isfinite(diagram)),"diagram")
        prominence=np.asarray(diagram[:,0]-diagram[:,1],dtype=float); req(np.all(prominence>=-1e-15),"negative prominence"); prominence=np.maximum(prominence,0.0)
    else:
        diagram=np.empty((0,2),dtype=float); prominence=np.empty(0,dtype=float)
    req(len(diagram)==len(children),"diagram/children count")
    leaf_peaks=np.empty(L,dtype=float)
    leaf_members=[]
    for leaf in range(L):
        ix=np.flatnonzero(leaf_labels==leaf); req(len(ix)>0,"empty leaf"); leaf_members.append(ix); leaf_peaks[leaf]=float(np.max(q[ix]))
    req(len(np.unique(leaf_peaks))==L,"leaf peaks not unique")
    finite_by_leaf:dict[int,float]={}; used:set[int]=set(); maxerr=0.0
    for birth,prom in zip(diagram[:,0].tolist(),prominence.tolist()):
        dif=np.abs(leaf_peaks-float(birth)); leaf=int(np.argmin(dif)); err=float(dif[leaf]); maxerr=max(maxerr,err); req(err<=1e-12,f"diagram birth does not map to leaf peak: {err}"); req(leaf not in used,"finite diagram birth maps duplicate leaf"); used.add(leaf); finite_by_leaf[leaf]=float(prom)
    root_leaves=set(range(L)).difference(used); req(len(root_leaves)==roots_expected,"unmatched leaf/root count")
    max_weights=np.sort(np.asarray(model.max_weight_per_cc_,dtype=float)); root_peaks=np.sort(leaf_peaks[np.asarray(sorted(root_leaves),dtype=np.int64)]); req(max_weights.shape==root_peaks.shape and np.allclose(max_weights,root_peaks,rtol=0,atol=1e-12),"root peak audit")
    return model,leaf_labels,leaf_peaks,prominence,finite_by_leaf,root_leaves,{"leaf_count":L,"internal_node_count":len(children),"root_count":roots_expected,"finite_mode_count":len(finite_by_leaf),"diagram_birth_leaf_peak_max_abs_error":maxerr}


def permutation_maxima(neighbors:list[list[int]],q:np.ndarray,denominator:int,bucket:int)->np.ndarray:
    vals=np.empty(B,dtype=float)
    for rep in range(1,B+1):
        seed=null_seed(denominator,bucket,rep); rng=np.random.Generator(np.random.PCG64(seed)); qp=np.asarray(rng.permutation(q),dtype=float); req(arr_hash(np.sort(qp))==arr_hash(np.sort(q)),"null q multiset changed")
        m=Tomato(graph_type="manual",density_type="manual"); m.fit(neighbors,weights=qp); d=np.asarray(m.diagram_,dtype=float)
        if d.size:
            p=np.asarray(d[:,0]-d[:,1],dtype=float); req(np.all(np.isfinite(p)) and np.all(p>=-1e-15),"null prominence"); vals[rep-1]=float(np.max(np.maximum(p,0.0)))
        else: vals[rep-1]=0.0
    req(np.all(np.isfinite(vals)) and np.all(vals>=0),"null maxima invalid")
    return vals


def p_fwer(prominence:float,null_max:np.ndarray)->float:
    return float((1+int(np.count_nonzero(null_max>=float(prominence))))/(B+1))


def extract_candidates(model:Tomato,leaf_labels:np.ndarray,leaf_peaks:np.ndarray,finite_by_leaf:dict[int,float],root_leaves:set[int],null_max:np.ndarray,tau:float,ids:list[str],q:np.ndarray)->tuple[list[dict[str,Any]],dict[str,Any]]:
    significant={leaf for leaf,p in finite_by_leaf.items() if float(p)>tau and p_fwer(float(p),null_max)<=ALPHA}
    req(all(p_fwer(float(finite_by_leaf[l]),null_max)<=ALPHA for l in significant),"significant mode pvalue")
    model.merge_threshold_=float(tau); labels=np.asarray(model.labels_,dtype=np.int64); req(labels.shape==(len(ids),) and int(labels.min())>=0,"final labels")
    positive=sorted(int(x) for x in np.unique(labels)); req(positive==list(range(int(model.n_clusters_))),"final labels compact")
    expected_clusters=len(root_leaves)+sum(float(p)>tau for p in finite_by_leaf.values()); req(int(model.n_clusters_)==expected_clusters,"threshold cluster-count invariant")
    rows=[]; skipped_small=0; survivor_finite=0; survivor_roots=0
    for lab in positive:
        ix=np.flatnonzero(labels==lab); req(len(ix)>0,"empty final cluster"); leaves=sorted(set(int(x) for x in leaf_labels[ix])); survivor=max(leaves,key=lambda l:(float(leaf_peaks[l]),-l)); survivor_peak=float(leaf_peaks[survivor]); is_root=survivor in root_leaves
        if is_root:
            prom=None; pf=None; survivor_roots+=1
        else:
            req(survivor in finite_by_leaf,"survivor finite map"); prom=float(finite_by_leaf[survivor]); pf=p_fwer(prom,null_max); req(prom>tau and pf<=ALPHA,f"nonsignificant finite survivor lab={lab}"); survivor_finite+=1
        members=tuple(sorted(ids[int(i)] for i in ix))
        if len(members)<MIN_SUPPORT:
            skipped_small+=1; continue
        fh=member_hash(members); rows.append({"family_id":family_id(members),"family_hash":fh,"event_ids":list(members),"member_count":len(members),"final_label":lab,"initial_leaf_count":len(leaves),"survivor_leaf":int(survivor),"survivor_peak_q":survivor_peak,"is_root_survivor":bool(is_root),"finite_prominence":prom,"p_fwer":pf})
    def key(r:dict[str,Any])->tuple[Any,...]:
        if not bool(r["is_root_survivor"]): return (0,float(r["p_fwer"]),-float(r["finite_prominence"]),-float(r["survivor_peak_q"]),str(r["family_hash"]))
        return (1,-float(r["survivor_peak_q"]),-int(r["member_count"]),str(r["family_hash"]))
    rows.sort(key=key)
    for rank,r in enumerate(rows,1):r["rank"]=rank
    req([int(r["rank"]) for r in rows]==list(range(1,len(rows)+1)),"rank continuity")
    req(len({str(r["family_hash"]) for r in rows})==len(rows),"candidate hash collision")
    return rows,{"candidate_count":len(rows),"final_cluster_count_before_support":len(positive),"small_final_clusters_below_support":skipped_small,"significant_finite_mode_count":len(significant),"finite_survivor_cluster_count":survivor_finite,"root_survivor_cluster_count":survivor_roots,"candidate_rows":sorted([{"family_hash":r["family_hash"],"member_count":r["member_count"],"is_root_survivor":r["is_root_survivor"]} for r in rows],key=lambda x:(-int(x["member_count"]),str(x["family_hash"]))) }


def main()->int:
    ap=argparse.ArgumentParser()
    for name in ("rankdensity-generator","intrinsic-runner","structural-runner","structural-result-json","parent-runner","quality-source","support-source-parts","candidate-payload","baseline-payload","scorer-parts","v8-result-json"):
        ap.add_argument("--"+name,type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    rd=load_module(a.rankdensity_generator,"sigprune_rd"); intrinsic=load_module(a.intrinsic_runner,"sigprune_intrinsic"); structural=load_module(a.structural_runner,"sigprune_structural"); parent=load_module(a.parent_runner,"sigprune_parent")
    req(sha256(a.quality_source)==QUALITY_SHA256 and sha256(a.v8_result_json)==V8_RESULT_SHA256 and sha256(a.structural_result_json)==STRUCTURAL_RESULT_SHA256,"frozen input hash")
    req(tuple(parent.YEARS)==YEARS and tuple(parent.BLIND)==BLIND and int(parent.MIN_CLUSTER_SIZE)==10 and int(parent.MIN_SAMPLES)==10,"parent constants")
    structural_json=json.loads(a.structural_result_json.read_text()); expected={(int(r["denominator"]),int(r["bucket"])):r for r in structural_json["fits"]}; req(set(expected)=={(d,b) for d in (128,1024) for b in BUCKETS},"structural panels")

    qmod=load_module(a.quality_source,"sigprune_gmn"); qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100; runtime=qmod.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS="orbittrace-significance-pruned-topomodal-v1-target-excluded"; support.RANKING_VARIANTS=("persistence",); req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"firewall"); setattr(a,"fixed4_baseline_json",a.v8_result_json); _c,base,_s=support.load_sources(a); scan,_cal,hidden_unused,sources=support.parse_catalogue(base); del hidden_unused; req(sorted(scan)==list(YEARS) and [x["key"] for x in sources]==list(MONTH_KEYS),"sources")
    events=[]
    for y in YEARS:events.extend(parent.normalize_event(row,y) for row in list(scan[y]))
    req(len(events)==738682 and len({str(e["id"]) for e in events})==len(events),"universe"); req(all(not(BLIND[0]<=float(e["sol"])<=BLIND[1]) for e in events),"protected event")
    Xfull=parent.geo_matrix(events); yrs=np.asarray([int(e["year"]) for e in events],dtype=np.int64); ids_full=[str(e["id"]) for e in events]; hashes=np.asarray([intrinsic.event_hash_u64(x) for x in ids_full],dtype=np.uint64)

    subsets=[]; runtime_rows={}
    for denominator in (128,1024):
        for bucket in BUCKETS:
            ii=intrinsic.selected_indices(hashes,denominator,bucket); sub=[events[int(i)] for i in ii]; sx=np.asarray(Xfull[ii]); sy=np.asarray(yrs[ii]); sid=[ids_full[int(i)] for i in ii]; req(all(np.any(sy==y) for y in YEARS),"subset lost year"); print(f"[sigprune-prelabel] d={denominator} b={bucket} n={len(sid)}",flush=True)
            ordered,ids,r3,ranks,q,neighbors,degree,gh=build_graph_and_q(parent,structural,sub); req(ids==sorted(sid),"ordered IDs")
            model,leaf_labels,leaf_peaks,obs_prom,finite_by_leaf,root_leaves,audit=observed_mode_audit(neighbors,q)
            null_max=permutation_maxima(neighbors,q,denominator,bucket); desc=np.sort(null_max)[::-1]; req(len(desc)==B,"null count"); tau=float(desc[9]); req(0.0<=tau<=1.0,"tau range")
            succ,ss=extract_candidates(model,leaf_labels,leaf_peaks,finite_by_leaf,root_leaves,null_max,tau,ids,q)
            par,ps=intrinsic.recurrent_ranked(parent,sx,sy,sid); ex=expected[(denominator,bucket)]
            req(int(ex["events_total"])==len(sid) and {str(k):int(v) for k,v in ex["events_by_year"].items()}=={str(y):int(np.sum(sy==y)) for y in YEARS},"#1284 event mismatch")
            req(ps["candidate_rows"]==ex["recurrent_eom"]["candidate_rows"] and len(par)==int(ex["recurrent_eom"]["candidate_count"]),"recurrent mismatch")
            budget=len(succ)>=len(par)
            summary={**ss,**audit,"tau":tau,"null_max_count":B,"null_max_sha256":arr_hash(null_max),"null_max_sorted_sha256":arr_hash(np.sort(null_max)),"null_max_min":float(np.min(null_max)),"null_max_median":float(np.median(null_max)),"null_max_max":float(np.max(null_max)),"observed_finite_prominence_sha256":arr_hash(np.sort(obs_prom)),"r3_sha256":arr_hash(r3),"q_sha256":arr_hash(q),"density_rank_sha256":arr_hash(ranks,dtype="<i8"),"graph_sha256":gh,"graph_edge_count":int((sum(len(x) for x in neighbors)-len(ids))//2),"median_radius_degree":float(np.median(degree)),"p90_radius_degree":float(np.quantile(degree,0.90))}
            subsets.append({"denominator":denominator,"bucket":bucket,"events_total":len(sid),"events_by_year":{str(y):int(np.sum(sy==y)) for y in YEARS},"event_universe_sha256":universe_hash(sid),"equal_budget_k":len(par),"candidate_budget_sufficient":budget,"successor_summary":summary,"null_max_prominences":[float(x) for x in null_max.tolist()],"successor_candidates":succ,"recurrent_candidates":par})
            runtime_rows[(denominator,bucket)]={"succ_sets":[frozenset(x["event_ids"]) for x in succ],"par_sets":[frozenset(x["event_ids"]) for x in par],"ids":frozenset(sid)}

    cross=[]; succ_scores=[]; par_scores=[]; wins=0
    for bucket in BUCKETS:
        c=runtime_rows[(128,bucket)]; f=runtime_rows[(1024,bucket)]; sm=structural.cross_scale_metrics(c["succ_sets"],f["succ_sets"],f["ids"]); pm=structural.cross_scale_metrics(c["par_sets"],f["par_sets"],f["ids"]); sv=float(sm["fine_to_coarse_mean_best_jaccard"]); pv=float(pm["fine_to_coarse_mean_best_jaccard"]); wins+=int(sv>pv); succ_scores.extend(float(x) for x in sm["fine_to_coarse_scores"]); par_scores.extend(float(x) for x in pm["fine_to_coarse_scores"]); cross.append({"bucket":bucket,"successor":sm,"recurrent_eom":pm,"strict_win":sv>pv})
    pooled_s=float(np.mean(np.asarray(succ_scores,dtype=float))) if succ_scores else 0.0; pooled_p=float(np.mean(np.asarray(par_scores,dtype=float))) if par_scores else 0.0
    structural_gates={"pooled_fine_to_coarse_mean_best_jaccard_strictly_greater":pooled_s>pooled_p,"strict_bucket_wins_at_least_3_of_4":wins>=3}
    pre={"schema":"ORBITTRACE_SIGNIFICANCE_PRUNED_TOPOMODAL_V1_PRELABEL","scientific_role":"PRELABEL_SIGNIFICANCE_PRUNED_TOPOMODAL_V1","configuration":{"density":"GEO6_third_nearest_other_empirical_rank_q","graph":"exact_1284_physical_radius_1","hierarchy":"gudhi_3.12_manual_topomato_significance_simplified_flat_partition","null":"permute_q_over_fixed_graph","B":B,"alpha":ALPHA,"null_statistic":"maximum_finite_mode_prominence","tau_rule":"10th_largest_of_199_null_maxima_strict_survival","min_candidate_support":MIN_SUPPORT,"ranking":"finite_significant_p_fwer_then_prominence_then_peak_q_then_roots"},"structural_source_run_id":31955621864,"structural_source_artifact_id":9265889512,"structural_result_sha256":STRUCTURAL_RESULT_SHA256,"rankdensity_reference_prelabel_sha256":RANKDENSITY_PRELABEL_SHA256,"subsets":subsets,"cross_scale":{"buckets":cross,"successor_pooled_fine_to_coarse_mean_best_jaccard":pooled_s,"recurrent_pooled_fine_to_coarse_mean_best_jaccard":pooled_p,"successor_strict_bucket_wins":wins,"gates":structural_gates},"candidate_budget_shortage_any_panel":any(not x["candidate_budget_sufficient"] for x in subsets),"blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"shower_truth_used":False,"sonotaco_2013_2014_access":False,"asfn_event_level_access":False,"efn_event_level_access":False,"amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"method_parameter_selection_from_result":False}
    out=a.output/"SIGNIFICANCE_PRUNED_TOPOMODAL_V1_PRELABEL.json"; out.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+"\n"); print(json.dumps({"prelabel_sha256":sha256(out),"candidate_budget_shortage":pre["candidate_budget_shortage_any_panel"],"cross_scale":pre["cross_scale"],"panels":[{"d":x["denominator"],"b":x["bucket"],"tau":x["successor_summary"]["tau"],"significant":x["successor_summary"]["significant_finite_mode_count"],"candidates":len(x["successor_candidates"]),"parent":len(x["recurrent_candidates"])} for x in subsets]},indent=2,sort_keys=True),flush=True); return 0

if __name__=="__main__":raise SystemExit(main())