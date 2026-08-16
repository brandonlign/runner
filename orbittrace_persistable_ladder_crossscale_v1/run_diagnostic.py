#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import warnings
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from persistable import Persistable
from persistable.persistable_interactive import (
    compute_defaults,
    X_START_LINE, Y_START_LINE, X_END_LINE, Y_END_LINE,
)

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
QUALITY_SHA256="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PERSISTABLE_COMMIT="7eb75b2e8d2fe5a18e49248aa7d1c97f829415be"
SALT="ORBITTRACE_SCALE_STRESS_V1|"
COARSE_D=128
FINE_D=1024
BUCKETS=(0,1,2,3)
MIN_SUPPORT=4
MAX_G=15
CANDIDATE_CEILING=119


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def sha256(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path)
    req(spec is not None and spec.loader is not None,f"cannot import {path}")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def event_hash_u64(eid:str)->int:
    return int.from_bytes(hashlib.sha256((SALT+str(eid)).encode()).digest()[:8],"big")


def selected_indices(hashes:np.ndarray,denominator:int,bucket:int)->np.ndarray:
    return np.flatnonzero((hashes%np.uint64(denominator))==np.uint64(bucket))


def member_hash(members:frozenset[str])->str:
    return hashlib.sha256("|".join(sorted(members)).encode()).hexdigest()[:20]


def ladder_candidates(X:np.ndarray,ids:list[str])->tuple[list[frozenset[str]],dict[str,Any]]:
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter("always")
        p=Persistable(X,n_neighbors="auto",n_jobs=1)
        extent=np.asarray(p._find_end(),dtype=float)
        req(extent.shape==(2,) and np.all(np.isfinite(extent)) and np.all(extent>0),f"invalid find_end {extent}")
        defaults,_=compute_defaults(extent,p._default_granularity())
        start=np.asarray([defaults[X_START_LINE],defaults[Y_START_LINE]],dtype=float)
        end=np.asarray([defaults[X_END_LINE],defaults[Y_END_LINE]],dtype=float)
        req(start.shape==(2,) and end.shape==(2,) and np.all(np.isfinite(start)) and np.all(np.isfinite(end)),"invalid midpoint slice")
        hc=p._bifiltration.lambda_linkage(start,end)
        pd=np.asarray(hc.persistence_diagram(),dtype=float)
        req(pd.ndim==2 and pd.shape[1]==2 and np.all(np.isfinite(pd)),"invalid persistence diagram")
        prom=np.abs(pd[:,1]-pd[:,0])
        B=int(np.sum(prom>1e-12))
        req(B>=2,f"too few positive bars {B}")
        maxg=min(MAX_G,B)
        memberships:dict[tuple[str,...],tuple[str,...]]={}
        per_g=[]
        for g in range(2,maxg+1):
            threshold=float(hc._compute_threshold(g))
            req(np.isfinite(threshold),f"nonfinite threshold g={g}")
            labels=np.asarray(hc.persistence_based_flattening(threshold,flattening_mode="conservative",keep_low_persistence_clusters=False),dtype=np.int64)
            req(labels.shape==(len(ids),),f"bad labels g={g}")
            retained=0
            for lab in sorted(int(x) for x in np.unique(labels) if int(x)>=0):
                ix=np.flatnonzero(labels==lab)
                if len(ix)>=MIN_SUPPORT:
                    key=tuple(sorted(ids[int(i)] for i in ix))
                    memberships[key]=key
                    retained+=1
            per_g.append({"g":g,"threshold":threshold,"retained_clusters":retained})
        warn=[str(w.message) for w in ws]
    req(not any("enough neighbors" in s.lower() for s in warn),f"insufficient-neighbor warning {warn}")
    candidates=[frozenset(k) for k in memberships]
    req(len(candidates)<=CANDIDATE_CEILING,f"candidate ceiling violated {len(candidates)}")
    counts=sorted((len(c) for c in candidates),reverse=True)
    return candidates,{
        "find_end":extent.tolist(),
        "midpoint_slice":[start.tolist(),end.tolist()],
        "positive_bar_count":B,
        "max_requested_g":maxg,
        "candidate_count":len(candidates),
        "largest_candidate_count":int(counts[0]) if counts else 0,
        "largest_candidate_fraction":float(counts[0]/len(ids)) if counts else 0.0,
        "per_g":per_g,
        "warnings":warn,
        "candidate_rows":sorted(({"family_hash":member_hash(c),"member_count":len(c)} for c in candidates),key=lambda r:(-r["member_count"],r["family_hash"])),
    }


def recurrent_candidates(parent:Any,X:np.ndarray,years:np.ndarray,ids:list[str])->tuple[list[frozenset[str]],dict[str,Any]]:
    model=hdbscan.HDBSCAN(min_cluster_size=10,min_samples=10,metric="euclidean",cluster_selection_method="eom",cluster_selection_epsilon=0.0,allow_single_cluster=False,prediction_data=False).fit(X)
    tree=model.condensed_tree_._raw_tree
    recurrent,_annual=parent.recurrent_stability(tree,years)
    labels=np.asarray(parent.eom_labels(tree,recurrent),dtype=np.int64)
    candidates=[]
    for lab in sorted(int(x) for x in np.unique(labels) if int(x)>=0):
        ix=np.flatnonzero(labels==lab)
        members=frozenset(ids[int(i)] for i in ix)
        req(len(members)>=10,"recurrent comparator sub-10 membership")
        candidates.append(members)
    counts=sorted((len(c) for c in candidates),reverse=True)
    return candidates,{"candidate_count":len(candidates),"largest_candidate_count":int(counts[0]) if counts else 0}


def restricted_candidates(coarse:list[frozenset[str]],fine_universe:frozenset[str])->list[frozenset[str]]:
    out=[]
    seen=set()
    for c in coarse:
        r=frozenset(c.intersection(fine_universe))
        if len(r)>=MIN_SUPPORT:
            key=tuple(sorted(r))
            if key not in seen:
                seen.add(key); out.append(r)
    return out


def directional(A:list[frozenset[str]],B:list[frozenset[str]])->tuple[float,list[float],float]:
    vals=[]; exact=0
    for a in A:
        best=0.0; ex=False
        for b in B:
            inter=len(a.intersection(b))
            if inter: best=max(best,float(inter/len(a.union(b))))
            ex=ex or (a==b)
        vals.append(best); exact+=int(ex)
    return (float(np.mean(np.asarray(vals,dtype=float))) if vals else 0.0,vals,float(exact/len(A)) if A else 0.0)


def symmetric_metrics(coarse:list[frozenset[str]],fine:list[frozenset[str]],fine_universe:frozenset[str])->dict[str,Any]:
    restricted=restricted_candidates(coarse,fine_universe)
    f2c,fvals,fexact=directional(fine,restricted)
    c2f,cvals,cexact=directional(restricted,fine)
    return {
        "fine_candidate_count":len(fine),
        "restricted_coarse_candidate_count":len(restricted),
        "fine_to_coarse_mean_best_jaccard":f2c,
        "coarse_to_fine_mean_best_jaccard":c2f,
        "symmetric_mean_best_jaccard":float((f2c+c2f)/2.0),
        "fine_to_coarse_exact_fraction":fexact,
        "coarse_to_fine_exact_fraction":cexact,
        "fine_to_coarse_best_jaccards":[float(x) for x in fvals],
        "coarse_to_fine_best_jaccards":[float(x) for x in cvals],
    }


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--parent-runner",type=Path,required=True)
    ap.add_argument("--quality-source",type=Path,required=True)
    ap.add_argument("--support-source-parts",type=Path,required=True)
    ap.add_argument("--candidate-payload",type=Path,required=True)
    ap.add_argument("--baseline-payload",type=Path,required=True)
    ap.add_argument("--scorer-parts",type=Path,required=True)
    ap.add_argument("--v8-result-json",type=Path,required=True)
    ap.add_argument("--synthetic-result-json",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    synth=json.loads(a.synthetic_result_json.read_text())
    req(synth.get("verdict")=="PASS_PERSISTABLE_LADDER_SYNTHETIC_FEASIBILITY","synthetic ladder activation gate not satisfied")
    req(synth.get("upstream_persistable_commit")==PERSISTABLE_COMMIT,"synthetic upstream identity changed")
    req(sha256(a.quality_source)==QUALITY_SHA256,"frozen GMN runtime utility changed")
    req(sha256(a.v8_result_json)==V8_RESULT_SHA256,"frozen GMN support artifact changed")
    parent=load_module(a.parent_runner,"persistable_ladder_parent")
    req(tuple(parent.YEARS)==YEARS and tuple(parent.BLIND)==BLIND,"parent constants changed")
    req(int(parent.MIN_CLUSTER_SIZE)==10 and int(parent.MIN_SAMPLES)==10,"parent support changed")

    qmod=load_module(a.quality_source,"persistable_ladder_gmn_utility")
    qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime()
    support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS
    support.CORPUS="orbittrace-persistable-ladder-crossscale-v1-target-excluded"
    support.RANKING_VARIANTS=("persistence",)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"target firewall changed")
    setattr(a,"fixed4_baseline_json",a.v8_result_json)
    _candidate,base,_scorer=support.load_sources(a)
    scan,_cal,hidden_unused,sources=support.parse_catalogue(base); del hidden_unused
    req(sorted(scan)==list(YEARS),f"wrong GMN years {sorted(scan)}")
    req([x["key"] for x in sources]==list(MONTH_KEYS),"GMN source list changed")

    events=[]
    for year in YEARS:
        raw=list(scan[year]); norm=[parent.normalize_event(row,year) for row in raw]
        req(len(norm)==len(raw),f"normalization count changed {year}"); events.extend(norm)
    req(len(events)==738682,f"pooled event count changed {len(events)}")
    req(len({str(e["id"]) for e in events})==len(events),"duplicate event IDs")
    req(all(not(BLIND[0]<=float(e["sol"])<=BLIND[1]) for e in events),"protected row survived parser")

    Xfull=parent.geo_matrix(events)
    years_full=np.asarray([int(e["year"]) for e in events],dtype=np.int64)
    ids_full=[str(e["id"]) for e in events]
    hashes=np.asarray([event_hash_u64(eid) for eid in ids_full],dtype=np.uint64)
    fits={}
    for d in (COARSE_D,FINE_D):
        for b in BUCKETS:
            ix=selected_indices(hashes,d,b)
            X=np.asarray(Xfull[ix],dtype=float); years=np.asarray(years_full[ix],dtype=np.int64); ids=[ids_full[int(i)] for i in ix]
            req(all(np.any(years==y) for y in YEARS),"subset lost a year")
            print(f"[ladder] d={d} b={b} n={len(ids)}",flush=True)
            lc,ls=ladder_candidates(X,ids); rc,rs=recurrent_candidates(parent,X,years,ids)
            fits[(d,b)]={"ids":frozenset(ids),"ladder":lc,"recurrent":rc,"row":{"denominator":d,"bucket":b,"events_total":len(ids),"events_by_year":{str(y):int(np.sum(years==y)) for y in YEARS},"ladder":ls,"recurrent_eom":rs}}
            print(json.dumps(fits[(d,b)]["row"],sort_keys=True),flush=True)

    pairs=[]; l_sym=[]; r_sym=[]; l_f=[]; r_f=[]; l_c=[]; r_c=[]; wins=0
    l_fvals=[]; r_fvals=[]; l_cvals=[]; r_cvals=[]
    nonempty=True; ceiling=True; noncollapse=True
    for b in BUCKETS:
        coarse=fits[(COARSE_D,b)]; fine=fits[(FINE_D,b)]
        req(fine["ids"].issubset(coarse["ids"]),f"nested subset failed {b}")
        lm=symmetric_metrics(coarse["ladder"],fine["ladder"],fine["ids"]); rm=symmetric_metrics(coarse["recurrent"],fine["recurrent"],fine["ids"])
        ls=float(lm["symmetric_mean_best_jaccard"]); rs=float(rm["symmetric_mean_best_jaccard"])
        l_sym.append(ls); r_sym.append(rs); wins+=int(ls>rs)
        l_f.append(float(lm["fine_to_coarse_mean_best_jaccard"])); r_f.append(float(rm["fine_to_coarse_mean_best_jaccard"]))
        l_c.append(float(lm["coarse_to_fine_mean_best_jaccard"])); r_c.append(float(rm["coarse_to_fine_mean_best_jaccard"]))
        l_fvals.extend(lm["fine_to_coarse_best_jaccards"]); r_fvals.extend(rm["fine_to_coarse_best_jaccards"])
        l_cvals.extend(lm["coarse_to_fine_best_jaccards"]); r_cvals.extend(rm["coarse_to_fine_best_jaccards"])
        nonempty=nonempty and len(coarse["ladder"])>0 and len(fine["ladder"])>0
        ceiling=ceiling and len(coarse["ladder"])<=CANDIDATE_CEILING and len(fine["ladder"])<=CANDIDATE_CEILING
        nc=int(lm["fine_candidate_count"])>=int(rm["fine_candidate_count"]); noncollapse=noncollapse and nc
        pairs.append({"bucket":b,"ladder":lm,"recurrent_eom":rm,"ladder_strict_win":bool(ls>rs),"fine_candidate_noncollapse":bool(nc)})

    lfpool=float(np.mean(np.asarray(l_fvals,dtype=float))) if l_fvals else 0.0
    rfpool=float(np.mean(np.asarray(r_fvals,dtype=float))) if r_fvals else 0.0
    lcpool=float(np.mean(np.asarray(l_cvals,dtype=float))) if l_cvals else 0.0
    rcpool=float(np.mean(np.asarray(r_cvals,dtype=float))) if r_cvals else 0.0
    lpool=float((lfpool+lcpool)/2); rpool=float((rfpool+rcpool)/2)
    lmed=float(np.median(np.asarray(l_sym,dtype=float))); rmed=float(np.median(np.asarray(r_sym,dtype=float)))
    gate={
        "ladder_nonempty_all_eight":bool(nonempty),
        "candidate_ceiling_all_eight":bool(ceiling),
        "fine_candidate_noncollapse_all_four":bool(noncollapse),
        "pooled_symmetric_jaccard_strictly_better":lpool>rpool,
        "median_bucket_symmetric_jaccard_strictly_better":lmed>rmed,
        "bucket_wins_at_least_three_of_four":wins>=3,
        "pooled_fine_to_coarse_not_below":lfpool>=rfpool,
        "pooled_coarse_to_fine_not_below":lcpool>=rcpool,
    }
    interpretation="SUPPORTS_PERSISTABLE_LADDER_CROSS_SCALE_COHERENCE" if all(gate.values()) else "REFUTES_PERSISTABLE_LADDER_CROSS_SCALE_COHERENCE"
    result={
        "schema":"ORBITTRACE_PERSISTABLE_LADDER_CROSSSCALE_V1",
        "scientific_role":"ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY",
        "interpretation":interpretation,
        "upstream_persistable_commit":PERSISTABLE_COMMIT,
        "fits":[fits[(d,b)]["row"] for d in (COARSE_D,FINE_D) for b in BUCKETS],
        "nested_pairs":pairs,
        "summary":{"ladder_pooled_symmetric_mean_best_jaccard":lpool,"recurrent_eom_pooled_symmetric_mean_best_jaccard":rpool,"ladder_pooled_fine_to_coarse":lfpool,"recurrent_eom_pooled_fine_to_coarse":rfpool,"ladder_pooled_coarse_to_fine":lcpool,"recurrent_eom_pooled_coarse_to_fine":rcpool,"ladder_median_bucket_symmetric":lmed,"recurrent_eom_median_bucket_symmetric":rmed,"ladder_bucket_wins":wins,"gate":gate},
        "blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"shower_truth_used":False,"sonotaco_2013_2014_access":False,"asfn_event_level_access":False,"efn_event_level_access":False,"amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"method_parameter_selection_from_result":False,
    }
    (a.output/"PERSISTABLE_LADDER_CROSSSCALE_V1.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"interpretation":interpretation,"summary":result["summary"],"pairs":pairs},indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
