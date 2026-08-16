#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
BUCKETS=(0,1,2,3)
MIN_SUPPORT=4
RADIUS=1.0
B=999
NULL_SALT="ORBITTRACE_COMPONENT_BJ_V1|"
QUALITY_SHA256="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
STRUCTURAL_RESULT_SHA256="e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
ROOT_REFERENCE_PRELABEL_SHA256="bb5f071e19a39297170730985c65181a05ca92dbe7b366f1a84e77d99e074a9a"


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)

def sha256(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path); req(spec is not None and spec.loader is not None,f"cannot import {path}"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def arr_hash(a:np.ndarray,dtype:str="<f8")->str:
    return hashlib.sha256(np.ascontiguousarray(np.asarray(a,dtype=dtype)).tobytes()).hexdigest()
def universe_hash(ids:list[str])->str:return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()
def member_hash(members:tuple[str,...])->str:return hashlib.sha256("|".join(members).encode()).hexdigest()[:20]
def family_id(members:tuple[str,...])->str:return hashlib.sha256(("CBJ1|"+"|".join(members)).encode()).hexdigest()[:20]
def graph_hash(neighbors:list[list[int]])->str:
    h=hashlib.sha256()
    for i,row in enumerate(neighbors):h.update(f"{i}:".encode());h.update(",".join(map(str,row)).encode());h.update(b"\n")
    return h.hexdigest()
def null_seed(d:int,b:int,m:int,rep:int)->int:
    return int.from_bytes(hashlib.sha256(f"{NULL_SALT}{d}|{b}|{m}|{rep}".encode()).digest()[:8],"big")


def bj_score(pvals:np.ndarray)->tuple[float,int]:
    p=np.sort(np.asarray(pvals,dtype=float)); m=len(p); req(m>=1 and np.all(np.isfinite(p)) and np.all((p>0)&(p<1)),"invalid BJ pvalues")
    best=0.0; bestk=1
    for j,a0 in enumerate(p,1):
        x=float(j/m); a=float(a0)
        if not a<x: val=0.0
        elif j==m: val=float(m*math.log(1.0/a))
        else:
            val=float(m*(x*math.log(x/a)+(1.0-x)*math.log((1.0-x)/(1.0-a))))
        req(math.isfinite(val) and val>=-1e-12,"invalid BJ value"); val=max(0.0,val)
        if val>best:best=val;bestk=j
    return best,bestk


def connected_components(neighbors:list[list[int]])->list[tuple[int,...]]:
    n=len(neighbors); seen=np.zeros(n,dtype=bool); out=[]
    for start in range(n):
        if seen[start]:continue
        stack=[start];seen[start]=True;comp=[]
        while stack:
            i=stack.pop();comp.append(i)
            for j in reversed(neighbors[i]):
                if not seen[j]:seen[j]=True;stack.append(j)
        out.append(tuple(sorted(comp)))
    req(sum(len(x) for x in out)==n and len({i for c in out for i in c})==n,"component partition")
    return out


def build_panel(parent:Any,structural:Any,events:list[dict[str,Any]],d:int,b:int,root_reference:list[dict[str,Any]])->tuple[list[dict[str,Any]],dict[str,Any]]:
    ordered=sorted(events,key=lambda e:str(e["id"]));ids=[str(e["id"]) for e in ordered];n=len(ids);req(n>4,"small panel")
    X=np.asarray(parent.geo_matrix(ordered),dtype=float);req(X.shape==(n,6) and np.all(np.isfinite(X)),"GEO6")
    dist,_=cKDTree(X).query(X,k=4,workers=1);dist=np.asarray(dist,dtype=float);req(dist.shape==(n,4) and np.all(np.abs(dist[:,0])<=1e-14),"self neighbor")
    r3=np.asarray(dist[:,3],dtype=float);req(np.all(r3>0)&np.all(np.isfinite(r3)),"r3")
    order=sorted(range(n),key=lambda i:(float(r3[i]),ids[i]));ranks=np.empty(n,dtype=np.int64)
    for rank,i in enumerate(order,1):ranks[i]=rank
    pvals=ranks.astype(float)/float(n+1);q=1.0-pvals;req(len(np.unique(ranks))==n and np.all((pvals>0)&(pvals<1)),"rank p")
    Z=structural.physical_embedding(ordered);raw=cKDTree(Z).query_ball_point(Z,r=RADIUS,p=2.0,eps=0.0,return_sorted=True);neighbors=[list(map(int,row)) for row in raw];req(len(neighbors)==n,"graph rows")
    adj=[set(x) for x in neighbors]
    for i,row in enumerate(neighbors):req(i in row and all(0<=j<n for j in row),"graph index")
    req(all(i in adj[j] for i,row in enumerate(neighbors) for j in row),"graph symmetry")
    comps=connected_components(neighbors);report=[c for c in comps if len(c)>=MIN_SUPPORT]
    memberships=[tuple(sorted(ids[i] for i in c)) for c in report]
    ref_members=sorted(tuple(sorted(map(str,r["event_ids"]))) for r in root_reference)
    req(sorted(memberships)==ref_members,f"root membership identity mismatch d={d} b={b}")

    sizes=sorted(set(len(x) for x in memberships));null_by_size:dict[int,np.ndarray]={}
    for m in sizes:
        vals=np.empty(B,dtype=float)
        for rep in range(1,B+1):
            rng=np.random.Generator(np.random.PCG64(null_seed(d,b,m,rep)));ix=np.asarray(rng.choice(n,size=m,replace=False,shuffle=False),dtype=np.int64);req(len(ix)==m and len(np.unique(ix))==m,"null sample")
            vals[rep-1]=bj_score(pvals[ix])[0]
        req(np.all(np.isfinite(vals))&np.all(vals>=0),"null BJ");null_by_size[m]=vals

    rows=[]
    for members,c in zip(memberships,report):
        m=len(c);ix=np.asarray(c,dtype=np.int64);raw_bj,argmax=bj_score(pvals[ix]);null=null_by_size[m];pbj=float((1+int(np.count_nonzero(null>=raw_bj)))/(B+1));fh=member_hash(members)
        rows.append({"family_id":family_id(members),"family_hash":fh,"event_ids":list(members),"member_count":m,"bj":raw_bj,"bj_argmax_k":int(argmax),"p_bj":pbj,"q_max":float(np.max(q[ix]))})
    rows.sort(key=lambda r:(float(r["p_bj"]),-float(r["bj"]),-float(r["q_max"]),str(r["family_hash"])))
    for rank,r in enumerate(rows,1):r["rank"]=rank
    req([r["rank"] for r in rows]==list(range(1,len(rows)+1)),"rank continuity")
    degree=np.asarray([len(x) for x in neighbors],dtype=float)
    return rows,{"candidate_count":len(rows),"all_connected_component_count":len(comps),"subsupport_component_count":len(comps)-len(report),"component_sizes":sorted([len(x) for x in report],reverse=True),"r3_sha256":arr_hash(r3),"rank_sha256":arr_hash(ranks,dtype="<i8"),"pvalue_sha256":arr_hash(pvals),"density_order_sha256":hashlib.sha256("\n".join(ids[i] for i in order).encode()).hexdigest(),"graph_sha256":graph_hash(neighbors),"graph_edge_count":int((sum(len(x) for x in neighbors)-n)//2),"median_radius_degree":float(np.median(degree)),"p90_radius_degree":float(np.quantile(degree,0.90)),"distinct_component_sizes":sizes,"null_by_size":{str(m):{"values":[float(x) for x in null_by_size[m].tolist()],"sha256":arr_hash(null_by_size[m]),"min":float(np.min(null_by_size[m])),"median":float(np.median(null_by_size[m])),"max":float(np.max(null_by_size[m]))} for m in sizes}}


def main()->int:
    ap=argparse.ArgumentParser()
    for name in ("root-reference-prelabel","intrinsic-runner","structural-runner","structural-result-json","parent-runner","quality-source","support-source-parts","candidate-payload","baseline-payload","scorer-parts","v8-result-json"):ap.add_argument("--"+name,type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    req(sha256(a.root_reference_prelabel)==ROOT_REFERENCE_PRELABEL_SHA256,"root reference prelabel hash")
    ref=json.loads(a.root_reference_prelabel.read_text());req(ref["schema"]=="ORBITTRACE_SIGNIFICANCE_PRUNED_TOPOMODAL_V1_PRELABEL" and ref["shower_truth_used"] is False,"root reference role")
    refmap={(int(x["denominator"]),int(x["bucket"])):x for x in ref["subsets"]};req(set(refmap)=={(d,b) for d in (128,1024) for b in BUCKETS},"root reference panels")
    intrinsic=load_module(a.intrinsic_runner,"cbj_intrinsic");structural=load_module(a.structural_runner,"cbj_structural");parent=load_module(a.parent_runner,"cbj_parent")
    req(sha256(a.quality_source)==QUALITY_SHA256 and sha256(a.v8_result_json)==V8_RESULT_SHA256 and sha256(a.structural_result_json)==STRUCTURAL_RESULT_SHA256,"frozen input hash");req(tuple(parent.YEARS)==YEARS and tuple(parent.BLIND)==BLIND,"parent constants")
    sj=json.loads(a.structural_result_json.read_text());expected={(int(r["denominator"]),int(r["bucket"])):r for r in sj["fits"]}
    qmod=load_module(a.quality_source,"cbj_gmn");qmod.v1.mult.YEARS=YEARS;qmod.v1.mult.MONTH_KEYS=MONTH_KEYS;qmod.v1.mult.TOP_K=100;runtime=qmod.v1.mult.load_frozen_runtime();support=runtime.load_support_module(a.support_source_parts);support.YEARS=YEARS;support.MONTH_KEYS=MONTH_KEYS;support.CORPUS="orbittrace-component-berkjones-scan-v1-target-excluded";support.RANKING_VARIANTS=("persistence",);req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"firewall");setattr(a,"fixed4_baseline_json",a.v8_result_json);_c,base,_s=support.load_sources(a);scan,_cal,hidden_unused,sources=support.parse_catalogue(base);del hidden_unused;req(sorted(scan)==list(YEARS) and [x["key"] for x in sources]==list(MONTH_KEYS),"sources")
    events=[]
    for y in YEARS:events.extend(parent.normalize_event(row,y) for row in list(scan[y]))
    req(len(events)==738682 and all(not(BLIND[0]<=float(e["sol"])<=BLIND[1]) for e in events),"universe/firewall");Xfull=parent.geo_matrix(events);yrs=np.asarray([int(e["year"]) for e in events],dtype=np.int64);ids=[str(e["id"]) for e in events];hashes=np.asarray([intrinsic.event_hash_u64(x) for x in ids],dtype=np.uint64)
    subsets=[];runtime_rows={}
    for d in (128,1024):
        for b in BUCKETS:
            ii=intrinsic.selected_indices(hashes,d,b);sub=[events[int(i)] for i in ii];sx=np.asarray(Xfull[ii]);sy=np.asarray(yrs[ii]);sid=[ids[int(i)] for i in ii];print(f"[cbj-prelabel] d={d} b={b} n={len(sid)}",flush=True)
            succ,ss=build_panel(parent,structural,sub,d,b,refmap[(d,b)]["successor_candidates"]);par,ps=intrinsic.recurrent_ranked(parent,sx,sy,sid);ex=expected[(d,b)]
            req(ps["candidate_rows"]==ex["recurrent_eom"]["candidate_rows"] and len(par)==int(ex["recurrent_eom"]["candidate_count"]),"parent mismatch");budget=len(succ)>=len(par)
            subsets.append({"denominator":d,"bucket":b,"events_total":len(sid),"events_by_year":{str(y):int(np.sum(sy==y)) for y in YEARS},"event_universe_sha256":universe_hash(sid),"equal_budget_k":len(par),"candidate_budget_sufficient":budget,"successor_summary":ss,"successor_candidates":succ,"recurrent_candidates":par})
            runtime_rows[(d,b)]={"succ_sets":[frozenset(x["event_ids"]) for x in succ],"par_sets":[frozenset(x["event_ids"]) for x in par],"ids":frozenset(sid)}
    cross=[];succ_scores=[];par_scores=[];wins=0
    for b in BUCKETS:
        c=runtime_rows[(128,b)];f=runtime_rows[(1024,b)];sm=structural.cross_scale_metrics(c["succ_sets"],f["succ_sets"],f["ids"]);pm=structural.cross_scale_metrics(c["par_sets"],f["par_sets"],f["ids"]);sv=float(sm["fine_to_coarse_mean_best_jaccard"]);pv=float(pm["fine_to_coarse_mean_best_jaccard"]);wins+=int(sv>pv);succ_scores.extend(float(x) for x in sm["fine_to_coarse_scores"]);par_scores.extend(float(x) for x in pm["fine_to_coarse_scores"]);cross.append({"bucket":b,"successor":sm,"recurrent_eom":pm,"strict_win":sv>pv})
    ps=float(np.mean(succ_scores)) if succ_scores else 0.0;pp=float(np.mean(par_scores)) if par_scores else 0.0;sg={"pooled_fine_to_coarse_mean_best_jaccard_strictly_greater":ps>pp,"strict_bucket_wins_at_least_3_of_4":wins>=3}
    pre={"schema":"ORBITTRACE_COMPONENT_BERKJONES_SCAN_V1_PRELABEL","scientific_role":"PRELABEL_COMPONENT_BERKJONES_SCAN_V1","configuration":{"event_p":"GEO6_third_nearest_other_rank_over_n_plus_1","graph":"exact_1284_physical_radius_1","candidates":"support4_connected_components","scan":"full_one_sided_berk_jones","B":B,"null":"size_conditioned_sampling_without_replacement","ranking":"p_bj_asc_bj_desc_qmax_desc_hash","min_candidate_support":MIN_SUPPORT},"root_reference_prelabel_sha256":ROOT_REFERENCE_PRELABEL_SHA256,"structural_result_sha256":STRUCTURAL_RESULT_SHA256,"subsets":subsets,"cross_scale":{"buckets":cross,"successor_pooled_fine_to_coarse_mean_best_jaccard":ps,"recurrent_pooled_fine_to_coarse_mean_best_jaccard":pp,"successor_strict_bucket_wins":wins,"gates":sg},"candidate_budget_shortage_any_panel":any(not x["candidate_budget_sufficient"] for x in subsets),"blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"shower_truth_used":False,"sonotaco_2013_2014_access":False,"asfn_event_level_access":False,"efn_event_level_access":False,"amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"method_parameter_selection_from_result":False}
    out=a.output/"COMPONENT_BERKJONES_SCAN_V1_PRELABEL.json";out.write_text(json.dumps(pre,indent=2,sort_keys=True,allow_nan=False)+"\n");print(json.dumps({"prelabel_sha256":sha256(out),"candidate_budget_shortage":pre["candidate_budget_shortage_any_panel"],"cross_scale":pre["cross_scale"],"panels":[{"d":x["denominator"],"b":x["bucket"],"candidates":len(x["successor_candidates"]),"parent":len(x["recurrent_candidates"]),"sizes":len(x["successor_summary"]["distinct_component_sizes"])} for x in subsets]},indent=2,sort_keys=True),flush=True);return 0

if __name__=="__main__":raise SystemExit(main())