#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import warnings
from pathlib import Path
from typing import Any

import hdbscan
import numpy as np
from persistable import Persistable
from persistable.persistable_interactive import compute_defaults, X_START_LINE, Y_START_LINE, X_END_LINE, Y_END_LINE

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
WINDOW_CENTERS=tuple(float(x) for x in range(0,360,5))
WINDOW_HALF_WIDTH=5.0
LOCAL_CANDIDATE_CEILING=119


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


def circular_distance_deg(a:float,b:float)->float:
    return abs((float(a)-float(b)+180.0)%360.0-180.0)


def circular_mean_deg(values:list[float])->float:
    req(bool(values),"empty circular mean")
    r=np.radians(np.asarray(values,dtype=float))
    s=float(np.mean(np.sin(r))); c=float(np.mean(np.cos(r)))
    req(math.isfinite(s) and math.isfinite(c) and not(abs(s)<1e-15 and abs(c)<1e-15),"undefined circular mean")
    return float(np.degrees(math.atan2(s,c))%360.0)


def owner_center(mean_sol:float)->float:
    return min(WINDOW_CENTERS,key=lambda c:(circular_distance_deg(mean_sol,c),c))


def member_hash(members:frozenset[str])->str:
    return hashlib.sha256("|".join(sorted(members)).encode()).hexdigest()[:20]


def local_ladder(X:np.ndarray,ids:list[str],sols:list[float],center:float)->tuple[list[frozenset[str]],dict[str,Any]]:
    n=len(ids); req(X.shape[0]==n and len(sols)==n,"window row mismatch")
    if n<MIN_SUPPORT:
        return [],{"events":n,"positive_bar_count":0,"max_requested_g":0,"preownership_candidate_count":0,"owned_candidate_count":0,"warning_count":0,"skipped":"lt4"}
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter("always")
        p=Persistable(X,n_neighbors="auto",n_jobs=1)
        extent=np.asarray(p._find_end(),dtype=float)
        req(extent.shape==(2,) and np.all(np.isfinite(extent)) and np.all(extent>0),f"invalid find_end center={center}")
        defaults,_=compute_defaults(extent,p._default_granularity())
        start=np.asarray([defaults[X_START_LINE],defaults[Y_START_LINE]],dtype=float)
        end=np.asarray([defaults[X_END_LINE],defaults[Y_END_LINE]],dtype=float)
        req(start.shape==(2,) and end.shape==(2,) and np.all(np.isfinite(start)) and np.all(np.isfinite(end)),f"invalid midpoint slice center={center}")
        hc=p._bifiltration.lambda_linkage(start,end)
        pd=np.asarray(hc.persistence_diagram(),dtype=float)
        if pd.size==0:
            B=0
        else:
            req(pd.ndim==2 and pd.shape[1]==2 and np.all(np.isfinite(pd)),f"invalid persistence diagram center={center}")
            B=int(np.sum(np.abs(pd[:,1]-pd[:,0])>1e-12))
        memberships:dict[tuple[str,...],tuple[str,...]]={}
        maxg=min(MAX_G,B)
        if B>=2:
            for g in range(2,maxg+1):
                threshold=float(hc._compute_threshold(g)); req(np.isfinite(threshold),f"nonfinite threshold center={center} g={g}")
                labels=np.asarray(hc.persistence_based_flattening(threshold,flattening_mode="conservative",keep_low_persistence_clusters=False),dtype=np.int64)
                req(labels.shape==(n,),f"bad labels center={center} g={g}")
                for lab in sorted(int(x) for x in np.unique(labels) if int(x)>=0):
                    ix=np.flatnonzero(labels==lab)
                    if len(ix)>=MIN_SUPPORT:
                        key=tuple(sorted(ids[int(i)] for i in ix)); memberships[key]=key
        warn=[str(w.message) for w in ws]
    req(not any("enough neighbors" in s.lower() for s in warn),f"insufficient-neighbor warning center={center}: {warn}")
    req(len(memberships)<=LOCAL_CANDIDATE_CEILING,f"local candidate ceiling violated center={center} count={len(memberships)}")
    id_to_sol={eid:float(sol) for eid,sol in zip(ids,sols)}
    owned=[]
    for key in memberships:
        msol=circular_mean_deg([id_to_sol[eid] for eid in key])
        if owner_center(msol)==center: owned.append(frozenset(key))
    return owned,{"events":n,"positive_bar_count":B,"max_requested_g":maxg,"preownership_candidate_count":len(memberships),"owned_candidate_count":len(owned),"warning_count":len(warn)}


def window_owned_candidates(X:np.ndarray,events:list[dict[str,Any]])->tuple[list[frozenset[str]],dict[str,Any]]:
    req(X.shape[0]==len(events),"global row mismatch")
    ids=[str(e["id"]) for e in events]; sols=[float(e["sol"]) for e in events]
    global_memberships:dict[tuple[str,...],frozenset[str]]={}; window_rows=[]; max_pre=0; active_windows=0
    for center in WINDOW_CENTERS:
        ix=np.asarray([i for i,s in enumerate(sols) if circular_distance_deg(s,center)<=WINDOW_HALF_WIDTH],dtype=np.int64)
        subX=np.asarray(X[ix],dtype=float) if len(ix) else np.empty((0,X.shape[1]),dtype=float)
        subids=[ids[int(i)] for i in ix]; subsols=[sols[int(i)] for i in ix]
        owned,row=local_ladder(subX,subids,subsols,center); row={"center":center,**row}; window_rows.append(row)
        max_pre=max(max_pre,int(row["preownership_candidate_count"])); active_windows+=int(int(row["owned_candidate_count"])>0)
        for c in owned: global_memberships[tuple(sorted(c))]=c
    candidates=list(global_memberships.values()); counts=sorted((len(c) for c in candidates),reverse=True)
    return candidates,{"candidate_count":len(candidates),"active_owned_windows":active_windows,"max_local_preownership_candidate_count":max_pre,"largest_candidate_count":int(counts[0]) if counts else 0,"largest_candidate_fraction":float(counts[0]/len(events)) if counts and events else 0.0,"window_rows":window_rows,"candidate_rows":sorted(({"family_hash":member_hash(c),"member_count":len(c)} for c in candidates),key=lambda r:(-r["member_count"],r["family_hash"]))}


def recurrent_candidates(parent:Any,X:np.ndarray,years:np.ndarray,ids:list[str])->tuple[list[frozenset[str]],dict[str,Any]]:
    model=hdbscan.HDBSCAN(min_cluster_size=10,min_samples=10,metric="euclidean",cluster_selection_method="eom",cluster_selection_epsilon=0.0,allow_single_cluster=False,prediction_data=False).fit(X)
    tree=model.condensed_tree_._raw_tree; recurrent,_annual=parent.recurrent_stability(tree,years); labels=np.asarray(parent.eom_labels(tree,recurrent),dtype=np.int64)
    candidates=[]
    for lab in sorted(int(x) for x in np.unique(labels) if int(x)>=0):
        ix=np.flatnonzero(labels==lab); members=frozenset(ids[int(i)] for i in ix); req(len(members)>=10,"recurrent comparator sub-10 membership"); candidates.append(members)
    return candidates,{"candidate_count":len(candidates)}


def restricted_candidates(coarse:list[frozenset[str]],fine_universe:frozenset[str])->list[frozenset[str]]:
    out=[]; seen=set()
    for c in coarse:
        r=frozenset(c.intersection(fine_universe))
        if len(r)>=MIN_SUPPORT:
            key=tuple(sorted(r))
            if key not in seen: seen.add(key); out.append(r)
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
    return float(np.mean(np.asarray(vals,dtype=float))) if vals else 0.0, vals, float(exact/len(A)) if A else 0.0


def symmetric_metrics(coarse:list[frozenset[str]],fine:list[frozenset[str]],fine_universe:frozenset[str])->dict[str,Any]:
    restricted=restricted_candidates(coarse,fine_universe)
    f2c,fvals,fexact=directional(fine,restricted); c2f,cvals,cexact=directional(restricted,fine)
    return {"fine_candidate_count":len(fine),"restricted_coarse_candidate_count":len(restricted),"fine_to_coarse_mean_best_jaccard":f2c,"coarse_to_fine_mean_best_jaccard":c2f,"symmetric_mean_best_jaccard":float((f2c+c2f)/2),"fine_to_coarse_exact_fraction":fexact,"coarse_to_fine_exact_fraction":cexact,"fine_to_coarse_best_jaccards":[float(x) for x in fvals],"coarse_to_fine_best_jaccards":[float(x) for x in cvals]}


def main()->int:
    ap=argparse.ArgumentParser()
    for name in ("parent-runner","quality-source","support-source-parts","candidate-payload","baseline-payload","scorer-parts","v8-result-json","output"):
        ap.add_argument("--"+name,type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    req(sha256(a.quality_source)==QUALITY_SHA256,"frozen GMN runtime utility changed"); req(sha256(a.v8_result_json)==V8_RESULT_SHA256,"frozen GMN support artifact changed")
    parent=load_module(a.parent_runner,"window_owned_parent"); req(tuple(parent.YEARS)==YEARS and tuple(parent.BLIND)==BLIND,"parent constants changed"); req(int(parent.MIN_CLUSTER_SIZE)==10 and int(parent.MIN_SAMPLES)==10,"parent support changed")
    qmod=load_module(a.quality_source,"window_owned_gmn_utility"); qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts); support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS="orbittrace-window-owned-persistence-v1-target-excluded"; support.RANKING_VARIANTS=("persistence",)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"target firewall changed"); setattr(a,"fixed4_baseline_json",a.v8_result_json)
    _candidate,base,_scorer=support.load_sources(a); scan,_cal,hidden_unused,sources=support.parse_catalogue(base); del hidden_unused
    req(sorted(scan)==list(YEARS),f"wrong years {sorted(scan)}"); req([x["key"] for x in sources]==list(MONTH_KEYS),"source list changed")
    events=[]
    for year in YEARS:
        raw=list(scan[year]); norm=[parent.normalize_event(row,year) for row in raw]; req(len(norm)==len(raw),f"normalization changed {year}"); events.extend(norm)
    req(len(events)==738682,f"pooled event count changed {len(events)}"); req(len({str(e["id"]) for e in events})==len(events),"duplicate IDs"); req(all(not(BLIND[0]<=float(e["sol"])<=BLIND[1]) for e in events),"protected row survived")
    Xfull=parent.geo_matrix(events); years_full=np.asarray([int(e["year"]) for e in events],dtype=np.int64); ids_full=[str(e["id"]) for e in events]; hashes=np.asarray([event_hash_u64(eid) for eid in ids_full],dtype=np.uint64)
    fits={}
    for d in (COARSE_D,FINE_D):
        for b in BUCKETS:
            ix=selected_indices(hashes,d,b); subevents=[events[int(i)] for i in ix]; X=np.asarray(Xfull[ix],dtype=float); years=np.asarray(years_full[ix],dtype=np.int64); ids=[ids_full[int(i)] for i in ix]
            req(all(np.any(years==y) for y in YEARS),"subset lost year"); print(f"[window-owned] d={d} b={b} n={len(ids)}",flush=True)
            wc,ws=window_owned_candidates(X,subevents); rc,rs=recurrent_candidates(parent,X,years,ids); req(int(ws["max_local_preownership_candidate_count"])<=LOCAL_CANDIDATE_CEILING,"local ceiling changed")
            fits[(d,b)]={"ids":frozenset(ids),"window":wc,"recurrent":rc,"row":{"denominator":d,"bucket":b,"events_total":len(ids),"window_owned":ws,"recurrent_eom":rs}}
            print(json.dumps({"denominator":d,"bucket":b,"events_total":len(ids),"window_candidate_count":len(wc),"active_windows":ws["active_owned_windows"],"max_local_pre":ws["max_local_preownership_candidate_count"],"recurrent_candidate_count":len(rc)},sort_keys=True),flush=True)
    pairs=[]; wscores=[]; rscores=[]; wins=0; nonempty=True; noncollapse=True; ceiling=True; wfvals=[]; rfvals=[]; wcvals=[]; rcvals=[]
    for b in BUCKETS:
        coarse=fits[(COARSE_D,b)]; fine=fits[(FINE_D,b)]; req(fine["ids"].issubset(coarse["ids"]),f"nested fail {b}")
        wm=symmetric_metrics(coarse["window"],fine["window"],fine["ids"]); rm=symmetric_metrics(coarse["recurrent"],fine["recurrent"],fine["ids"])
        w=float(wm["symmetric_mean_best_jaccard"]); rr=float(rm["symmetric_mean_best_jaccard"]); wscores.append(w); rscores.append(rr); wins+=int(w>rr)
        wfvals.extend(wm["fine_to_coarse_best_jaccards"]); rfvals.extend(rm["fine_to_coarse_best_jaccards"]); wcvals.extend(wm["coarse_to_fine_best_jaccards"]); rcvals.extend(rm["coarse_to_fine_best_jaccards"])
        nonempty=nonempty and len(coarse["window"])>0 and len(fine["window"])>0; nc=int(wm["fine_candidate_count"])>=int(rm["fine_candidate_count"]); noncollapse=noncollapse and nc
        ceiling=ceiling and int(coarse["row"]["window_owned"]["max_local_preownership_candidate_count"])<=LOCAL_CANDIDATE_CEILING and int(fine["row"]["window_owned"]["max_local_preownership_candidate_count"])<=LOCAL_CANDIDATE_CEILING
        pairs.append({"bucket":b,"window_owned":wm,"recurrent_eom":rm,"window_strict_win":bool(w>rr),"fine_candidate_noncollapse":bool(nc)})
    wf=float(np.mean(np.asarray(wfvals,dtype=float))) if wfvals else 0.0; rf=float(np.mean(np.asarray(rfvals,dtype=float))) if rfvals else 0.0; wc=float(np.mean(np.asarray(wcvals,dtype=float))) if wcvals else 0.0; rc=float(np.mean(np.asarray(rcvals,dtype=float))) if rcvals else 0.0
    wpool=float((wf+wc)/2); rpool=float((rf+rc)/2); wmed=float(np.median(np.asarray(wscores,dtype=float))); rmed=float(np.median(np.asarray(rscores,dtype=float)))
    gate={"window_owned_nonempty_all_eight":bool(nonempty),"local_candidate_ceiling_all_windows":bool(ceiling),"fine_candidate_noncollapse_all_four":bool(noncollapse),"pooled_symmetric_jaccard_strictly_better":wpool>rpool,"median_bucket_symmetric_jaccard_strictly_better":wmed>rmed,"bucket_wins_at_least_three_of_four":wins>=3,"pooled_fine_to_coarse_not_below":wf>=rf,"pooled_coarse_to_fine_not_below":wc>=rc}
    interpretation="SUPPORTS_WINDOW_OWNED_PERSISTENCE_CROSS_SCALE_COHERENCE" if all(gate.values()) else "REFUTES_WINDOW_OWNED_PERSISTENCE_CROSS_SCALE_COHERENCE"
    result={"schema":"ORBITTRACE_WINDOW_OWNED_PERSISTENCE_V1","scientific_role":"ZERO_LABEL_STRUCTURAL_DIAGNOSTIC_ONLY","interpretation":interpretation,"upstream_persistable_commit":PERSISTABLE_COMMIT,"configuration":{"window_width_deg":10.0,"window_step_deg":5.0,"window_centers":list(WINDOW_CENTERS),"min_support":MIN_SUPPORT,"max_g":MAX_G,"ownership":"nearest_center_to_candidate_circular_mean_sol"},"fits":[fits[(d,b)]["row"] for d in (COARSE_D,FINE_D) for b in BUCKETS],"nested_pairs":pairs,"summary":{"window_pooled_symmetric_mean_best_jaccard":wpool,"recurrent_eom_pooled_symmetric_mean_best_jaccard":rpool,"window_pooled_fine_to_coarse":wf,"recurrent_eom_pooled_fine_to_coarse":rf,"window_pooled_coarse_to_fine":wc,"recurrent_eom_pooled_coarse_to_fine":rc,"window_median_bucket_symmetric":wmed,"recurrent_eom_median_bucket_symmetric":rmed,"window_bucket_wins":wins,"gate":gate},"blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"shower_truth_used":False,"sonotaco_2013_2014_access":False,"asfn_event_level_access":False,"efn_event_level_access":False,"amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"method_parameter_selection_from_result":False}
    (a.output/"WINDOW_OWNED_PERSISTENCE_V1.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n"); print(json.dumps({"interpretation":interpretation,"summary":result["summary"],"pairs":pairs},indent=2,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
