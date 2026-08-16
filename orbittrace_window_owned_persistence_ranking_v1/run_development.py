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
WINDOW_CENTERS=tuple(float(x) for x in range(0,360,5))
WINDOW_HALF_WIDTH=5.0
MIN_SUPPORT=4
MAX_G=15
EXPECTED_PARENT={
    "2022":{"recovered_at_25":22,"recovered_at_50":45,"recovered_at_100":89,"recovered_at_500":193,"top100_dominant_precision":0.7856486013,"mrr":0.0224982696,"qualified_matches":236,"fragmentation_median_top500":1.0},
    "2023":{"recovered_at_25":23,"recovered_at_50":46,"recovered_at_100":89,"recovered_at_500":192,"top100_dominant_precision":0.7867680237,"mrr":0.0220239289,"qualified_matches":244,"fragmentation_median_top500":1.0},
}


def req(ok:bool,msg:str)->None:
    if not ok: raise RuntimeError(msg)


def sha256(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path)
    req(spec is not None and spec.loader is not None,f"cannot import {path}")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


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


def family_id(members:tuple[str,...])->str:
    return hashlib.sha256("|".join(members).encode()).hexdigest()


def candidate_sort_key(f:dict[str,Any]):
    return (
        -int(bool(f["both_years_present"])),
        int(f["g_first"]),
        -int(f["g_span"]),
        -min(int(f["member_count_2022"]),int(f["member_count_2023"])),
        -int(f["member_count_total"]),
        str(f["family_id"]),
    )


def build_successor_candidates(X:np.ndarray,events:list[dict[str,Any]])->tuple[list[dict[str,Any]],dict[str,Any]]:
    req(X.shape[0]==len(events),"candidate matrix/event mismatch")
    ids=[str(e["id"]) for e in events]
    sols=[float(e["sol"]) for e in events]
    years=[int(e["year"]) for e in events]
    global_rows:dict[tuple[str,...],dict[str,Any]]={}
    window_summary=[]
    max_local_exact=0
    for center in WINDOW_CENTERS:
        ix=np.asarray([i for i,s in enumerate(sols) if circular_distance_deg(s,center)<=WINDOW_HALF_WIDTH],dtype=np.int64)
        n=len(ix)
        if n<MIN_SUPPORT:
            window_summary.append({"center":center,"events":n,"positive_bar_count":0,"max_g":0,"local_exact_memberships":0,"owned_memberships":0,"warning_count":0})
            continue
        subX=np.asarray(X[ix],dtype=float)
        subids=[ids[int(i)] for i in ix]
        subsols=[sols[int(i)] for i in ix]
        subyears=[years[int(i)] for i in ix]
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter("always")
            p=Persistable(subX,n_neighbors="auto",n_jobs=1)
            extent=np.asarray(p._find_end(),dtype=float)
            req(extent.shape==(2,) and np.all(np.isfinite(extent)) and np.all(extent>0),f"invalid find_end center={center}")
            defaults,_=compute_defaults(extent,p._default_granularity())
            start=np.asarray([defaults[X_START_LINE],defaults[Y_START_LINE]],dtype=float)
            end=np.asarray([defaults[X_END_LINE],defaults[Y_END_LINE]],dtype=float)
            req(start.shape==(2,) and end.shape==(2,) and np.all(np.isfinite(start)) and np.all(np.isfinite(end)),f"invalid midpoint slice center={center}")
            hc=p._bifiltration.lambda_linkage(start,end)
            pd=np.asarray(hc.persistence_diagram(),dtype=float)
            if pd.size==0: B=0
            else:
                req(pd.ndim==2 and pd.shape[1]==2 and np.all(np.isfinite(pd)),f"invalid persistence diagram center={center}")
                B=int(np.sum(np.abs(pd[:,1]-pd[:,0])>1e-12))
            maxg=min(MAX_G,B)
            local:dict[tuple[str,...],dict[str,Any]]={}
            if B>=2:
                for g in range(2,maxg+1):
                    threshold=float(hc._compute_threshold(g)); req(np.isfinite(threshold),f"nonfinite threshold center={center} g={g}")
                    labels=np.asarray(hc.persistence_based_flattening(threshold,flattening_mode="conservative",keep_low_persistence_clusters=False),dtype=np.int64)
                    req(labels.shape==(n,),f"bad labels center={center} g={g}")
                    for lab in sorted(int(x) for x in np.unique(labels) if int(x)>=0):
                        lix=np.flatnonzero(labels==lab)
                        if len(lix)<MIN_SUPPORT: continue
                        local_positions=tuple(int(j) for j in lix)
                        members=tuple(sorted(subids[j] for j in local_positions))
                        row=local.setdefault(members,{"g_values":set(),"member_ids":members})
                        row["g_values"].add(int(g))
            warning_messages=[str(w.message) for w in ws]
        req(not any("enough neighbors" in s.lower() for s in warning_messages),f"insufficient-neighbor warning center={center}: {warning_messages}")
        max_local_exact=max(max_local_exact,len(local))
        id_to_sol={eid:sol for eid,sol in zip(subids,subsols)}
        id_to_year={eid:year for eid,year in zip(subids,subyears)}
        owned_count=0
        for members,row in local.items():
            msol=circular_mean_deg([id_to_sol[eid] for eid in members])
            if owner_center(msol)!=center: continue
            owned_count+=1
            gvals=sorted(int(g) for g in row["g_values"])
            n22=sum(id_to_year[eid]==2022 for eid in members)
            n23=sum(id_to_year[eid]==2023 for eid in members)
            out={
                "family_id":family_id(members),
                "owner_center":float(center),
                "event_ids":list(members),
                "member_count_total":len(members),
                "member_count_2022":int(n22),
                "member_count_2023":int(n23),
                "both_years_present":bool(n22>0 and n23>0),
                "g_first":int(gvals[0]),
                "g_last":int(gvals[-1]),
                "g_span":len(gvals),
                "g_values":gvals,
            }
            prior=global_rows.get(members)
            req(prior is None or prior==out,f"owned duplicate disagrees for {out['family_id']}")
            global_rows[members]=out
        window_summary.append({"center":center,"events":n,"positive_bar_count":B,"max_g":maxg,"local_exact_memberships":len(local),"owned_memberships":owned_count,"warning_count":len(warning_messages)})
        del p,hc,pd,subX
    candidates=list(global_rows.values())
    candidates.sort(key=candidate_sort_key)
    for rank,row in enumerate(candidates,1): row["rank"]=rank
    req(len({f["family_id"] for f in candidates})==len(candidates),"family ID collision")
    req(len({tuple(f["event_ids"]) for f in candidates})==len(candidates),"duplicate final membership")
    return candidates,{"candidate_count":len(candidates),"both_year_candidate_count":sum(bool(f["both_years_present"]) for f in candidates),"max_local_exact_memberships":max_local_exact,"active_owned_windows":sum(int(r["owned_memberships"]>0) for r in window_summary),"window_summary":window_summary}


def compact_metrics(m:dict[str,Any])->dict[str,Any]:
    return {k:v for k,v in m.items() if k!="first_rank_by_label"}


def verify_parent_metrics(metrics:dict[str,dict[str,Any]])->None:
    for year in YEARS:
        y=str(year); exp=EXPECTED_PARENT[y]; got=metrics[y]
        for k,v in exp.items():
            if isinstance(v,int): req(int(got[k])==v,f"parent {y} {k} changed: {got[k]} != {v}")
            else: req(abs(float(got[k])-float(v))<=1e-9,f"parent {y} {k} changed: {got[k]} != {v}")


def annual_gate(parent:dict[str,Any],succ:dict[str,Any])->dict[str,bool]:
    return {
        "recovered_at_25_not_lower":int(succ["recovered_at_25"])>=int(parent["recovered_at_25"]),
        "recovered_at_50_not_lower":int(succ["recovered_at_50"])>=int(parent["recovered_at_50"]),
        "recovered_at_100_not_lower":int(succ["recovered_at_100"])>=int(parent["recovered_at_100"]),
        "recovered_at_500_not_lower":int(succ["recovered_at_500"])>=int(parent["recovered_at_500"]),
        "top100_precision_not_lower":float(succ["top100_dominant_precision"])>=float(parent["top100_dominant_precision"]),
        "mrr_not_lower":float(succ["mrr"])>=float(parent["mrr"]),
        "qualified_matches_not_lower":int(succ["qualified_matches"])>=int(parent["qualified_matches"]),
        "fragmentation_not_higher":float(succ["fragmentation_median_top500"])<=float(parent["fragmentation_median_top500"]),
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
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    req(sha256(a.quality_source)==QUALITY_SHA256,"frozen GMN utility changed")
    req(sha256(a.v8_result_json)==V8_RESULT_SHA256,"frozen GMN support artifact changed")
    parent=load_module(a.parent_runner,"window_rank_parent")
    req(tuple(parent.YEARS)==YEARS and tuple(parent.BLIND)==BLIND,"parent constants changed")
    req(int(parent.MIN_CLUSTER_SIZE)==10 and int(parent.MIN_SAMPLES)==10,"parent HDBSCAN support changed")

    qmod=load_module(a.quality_source,"window_rank_gmn_utility")
    qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime(); support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS; support.CORPUS="orbittrace-window-owned-persistence-ranking-v1-target-excluded"; support.RANKING_VARIANTS=("persistence",)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"target firewall changed")
    setattr(a,"fixed4_baseline_json",a.v8_result_json)
    _candidate,base,_scorer=support.load_sources(a)
    scan,_cal,hidden_sealed,sources=support.parse_catalogue(base)
    req(sorted(scan)==list(YEARS),f"wrong GMN years {sorted(scan)}")
    req([x["key"] for x in sources]==list(MONTH_KEYS),"GMN source list changed")

    events=[]
    for year in YEARS:
        raw=list(scan[year]); norm=[parent.normalize_event(row,year) for row in raw]
        req(len(norm)==len(raw),f"normalization count changed {year}"); events.extend(norm)
    req(len(events)==738682,f"pooled event count changed {len(events)}")
    req(len({str(e["id"]) for e in events})==len(events),"duplicate event IDs")
    req(all(not(BLIND[0]<=float(e["sol"])<=BLIND[1]) for e in events),"protected row survived parser")

    X=parent.geo_matrix(events); years=np.asarray([int(e["year"]) for e in events],dtype=np.int64)
    parent_model=hdbscan.HDBSCAN(min_cluster_size=10,min_samples=10,metric="euclidean",cluster_selection_method="eom",cluster_selection_epsilon=0.0,allow_single_cluster=False,prediction_data=False).fit(X)
    tree=parent_model.condensed_tree_._raw_tree
    recurrent,annual_stability=parent.recurrent_stability(tree,years)
    parent_labels=np.asarray(parent.eom_labels(tree,recurrent),dtype=np.int64)
    parent_nodes=parent.selected_eom_nodes(tree,recurrent)
    req(len(parent_nodes)==len(set(int(x) for x in parent_labels if int(x)>=0)),"parent node/label count mismatch")
    ordinary=parent.compute_stability(tree)
    parent_candidates=parent.candidates_from_labels(parent_labels,parent_nodes,events,ordinary,recurrent,True)

    successor_candidates,successor_summary=build_successor_candidates(X,events)
    req(len(successor_candidates)>=100,f"successor has only {len(successor_candidates)} candidates")

    prelabel={
        "scientific_role":"PRELABEL_WINDOW_OWNED_PERSISTENCE_RANKING_V1",
        "events_total":len(events),
        "events_by_year":{str(y):int(np.sum(years==y)) for y in YEARS},
        "configuration":{"representation":"GEO6","window_width_deg":10.0,"window_step_deg":5.0,"window_centers":list(WINDOW_CENTERS),"min_support":MIN_SUPPORT,"max_g":MAX_G,"persistable_commit":PERSISTABLE_COMMIT,"ranking":["both_years_present desc","g_first asc","g_span desc","min annual count desc","member_count_total desc","family_id asc"]},
        "parent_candidate_count":len(parent_candidates),
        "parent_candidates":parent_candidates,
        "successor_summary":successor_summary,
        "successor_candidates":successor_candidates,
        "annual_parent_recurrent_stability":{str(k):list(v) for k,v in sorted(annual_stability.items())},
        "blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"sonotaco_2013_2014_access":False,"asfn_event_level_access":False,"efn_event_level_access":False,"amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,
    }
    prelabel_path=a.output/"WINDOW_OWNED_PERSISTENCE_RANKING_V1_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel,indent=2,sort_keys=True,allow_nan=False)+"\n")
    prelabel_sha=sha256(prelabel_path)

    # Truth is not passed into any evaluator until all memberships and orders above are persisted.
    hidden=hidden_sealed
    ids_by_year={y:{str(e["id"]) for e in events if int(e["year"])==y} for y in YEARS}
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden),"label outside accessible event IDs")
    parent_metrics={str(y):parent.metrics(parent_candidates,hidden,ids_by_year[y]) for y in YEARS}
    verify_parent_metrics(parent_metrics)
    successor_metrics={str(y):parent.metrics(successor_candidates,hidden,ids_by_year[y]) for y in YEARS}
    gates={str(y):annual_gate(parent_metrics[str(y)],successor_metrics[str(y)]) for y in YEARS}
    strict100=any(int(successor_metrics[str(y)]["recovered_at_100"])>int(parent_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    passed=bool(strict100 and len(successor_candidates)>=100 and all(all(g.values()) for g in gates.values()))
    verdict="PASS_WINDOW_OWNED_PERSISTENCE_RANKING_V1_GMN_DEVELOPMENT" if passed else "FAIL_WINDOW_OWNED_PERSISTENCE_RANKING_V1_GMN_DEVELOPMENT"
    result={
        "verdict":verdict,"scientific_role":"TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY","prelabel_sha256":prelabel_sha,
        "events_total":len(events),"events_by_year":{str(y):len(ids_by_year[y]) for y in YEARS},
        "parent_candidate_count":len(parent_candidates),"successor_candidate_count":len(successor_candidates),"successor_both_year_candidate_count":int(successor_summary["both_year_candidate_count"]),
        "strict_recovered_at_100_improvement_some_year":strict100,
        "parent_metrics":parent_metrics,"successor_metrics":successor_metrics,"annual_gates":gates,
        "ranking":{"both_years_present":"desc","g_first":"asc","g_span":"desc","min_annual_count":"desc","member_count_total":"desc","family_id":"asc"},
        "blind_exclusion":list(BLIND),"target_information_access":False,"target_region_events_accessed":False,"sonotaco_2013_2014_access":False,"asfn_event_level_access":False,"efn_event_level_access":False,"amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,
    }
    (a.output/"WINDOW_OWNED_PERSISTENCE_RANKING_V1_GMN_DEVELOPMENT.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"verdict":verdict,"parent":{y:compact_metrics(m) for y,m in parent_metrics.items()},"successor":{y:compact_metrics(m) for y,m in successor_metrics.items()},"successor_candidate_count":len(successor_candidates),"both_year_candidate_count":successor_summary["both_year_candidate_count"],"strict100":strict100},indent=2,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
