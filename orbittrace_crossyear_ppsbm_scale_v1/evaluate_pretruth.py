#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

IMAGE="tiagopeixoto/graph-tool@sha256:4e613c0da8cfb85c05661c124da0ef2d167ec4a5a3347ae10a8f5030bab0a375"
VERSION="3.6 (commit fd9762d9, Sun Aug 2 18:45:30 2026 +0200)"
MIN_SUPPORT=4
BUCKETS=(0,1,2,3)


def req(ok: bool,msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path,obj: Any) -> str:
    raw=(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def membership_hash(ids: list[str] | tuple[str,...]) -> str:
    vals=tuple(sorted(str(x) for x in ids))
    return hashlib.sha256(("\n".join(vals)+"\n").encode()).hexdigest()


def restrict_pp(candidates: list[dict[str,Any]], fine_ids: set[str], fine_year: dict[str,int]) -> list[frozenset[str]]:
    seen=set(); out=[]
    for row in candidates:
        members=tuple(sorted(set(map(str,row["event_ids"])) & fine_ids))
        if members in seen: continue
        n22=sum(fine_year[eid]==2022 for eid in members); n23=sum(fine_year[eid]==2023 for eid in members)
        if n22<MIN_SUPPORT or n23<MIN_SUPPORT: continue
        seen.add(members); out.append(frozenset(members))
    return out


def restrict_reference(candidates: list[dict[str,Any]], universe: set[str]) -> list[frozenset[str]]:
    seen=set(); out=[]
    for row in candidates:
        members=tuple(sorted(set(map(str,row["event_ids"])) & universe))
        if len(members)<MIN_SUPPORT or members in seen: continue
        seen.add(members); out.append(frozenset(members))
    return out


def mean_best_jaccard(fine: list[dict[str,Any]], coarse_sets: list[frozenset[str]]) -> float:
    if not fine: return 0.0
    vals=[]
    for row in fine:
        a=frozenset(map(str,row["event_ids"])); best=0.0
        for b in coarse_sets:
            inter=len(a&b)
            if inter: best=max(best,inter/len(a|b))
        vals.append(best)
    return float(np.mean(vals))


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--graph-freeze",type=Path,required=True)
    ap.add_argument("--graph-dir",type=Path,required=True)
    ap.add_argument("--partitions",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    freeze=json.loads(a.graph_freeze.read_text()); parts=json.loads(a.partitions.read_text())
    req(freeze.get("schema")=="ORBITTRACE_CROSSYEAR_PPSBM_GRAPH_FREEZE_V1","wrong graph freeze")
    req(parts.get("schema")=="ORBITTRACE_CROSSYEAR_PPSBM_PARTITIONS_V1","wrong partition schema")
    req(parts.get("graph_freeze_sha256")==sha256(a.graph_freeze),"partition does not bind graph freeze")
    req(parts.get("graph_tool_image")==IMAGE and parts.get("graph_tool_version")==VERSION and int(parts.get("openmp_threads"))==1,"runtime changed")
    req(parts.get("state")=="PPBlockState" and parts.get("uniform") is False and parts.get("degree_corrected") is True,"PP-SBM state changed")
    req(freeze.get("shower_truth_used") is False and parts.get("shower_truth_used") is False,"truth entered Stage1")

    fm={(int(p["denominator"]),int(p["bucket"])):p for p in freeze["panels"]}
    pm={(int(p["denominator"]),int(p["bucket"])):p for p in parts["panels"]}
    req(set(fm)==set(pm) and len(fm)==8,"wrong panel set")

    panel_rows=[]
    for key in sorted(fm):
        f=fm[key]; p=pm[key]; d,b=key
        graph_path=a.graph_dir/str(f["graph_file"])
        req(sha256(graph_path)==str(f["graph_sha256"])==str(p["graph_sha256"]),f"graph hash mismatch {key}")
        graph=json.loads(graph_path.read_text()); vertices=graph["vertices"]; edges=graph["edges"]
        active_ids=[str(v["id"]) for v in vertices]; active_set=set(active_ids); years=[int(v["year"]) for v in vertices]
        strict=all(0<=int(i)<len(vertices) and 0<=int(j)<len(vertices) and years[int(i)]!=years[int(j)] for i,j in edges) and float(graph["maximum_edge_distance"])<=1.0+1e-12
        positive=all(int(v["crossyear_degree"])>0 for v in vertices)
        candidates=list(p["eligible_candidates"])
        membership_ok=all(set(map(str,r["event_ids"])).issubset(active_set) and membership_hash(list(map(str,r["event_ids"])))==str(r["family_hash"]) for r in candidates)
        support_ok=all(int(r["members_2022"])>=MIN_SUPPORT and int(r["members_2023"])>=MIN_SUPPORT for r in candidates)
        all_members=[eid for r in candidates for eid in map(str,r["event_ids"])]
        disjoint=len(all_members)==len(set(all_members))
        capacity=len(candidates)>=int(f["reference_k"])
        panel_rows.append({
            "denominator":d,"bucket":b,"reference_k":int(f["reference_k"]),
            "inferred_block_count":int(p["inferred_block_count"]),"eligible_candidate_count":len(candidates),
            "active_vertex_count":int(p["active_vertex_count"]),"edge_count":int(p["edge_count"]),
            "description_length":float(p["description_length"]),
            "checks":{
                "strict_crossyear_graph":bool(strict),"positive_degree_inference":bool(positive),
                "fixed_seed_repeatability":bool(p["fixed_seed_repeatability"]),
                "candidate_membership_universe":bool(membership_ok),"annual_support_floor":bool(support_ok),
                "pairwise_disjoint":bool(disjoint),"capacity_at_least_reference_k":bool(capacity),
            },
        })

    cross=[]; pscores=[]; rscores=[]
    for b in BUCKETS:
        fine_f=fm[(1024,b)]; coarse_f=fm[(128,b)]
        fine_p=pm[(1024,b)]; coarse_p=pm[(128,b)]
        fine_ids=set(map(str,fine_f["annual_event_ids"]["2022"])) | set(map(str,fine_f["annual_event_ids"]["2023"]))
        fine_year={eid:2022 for eid in map(str,fine_f["annual_event_ids"]["2022"])}
        fine_year.update({eid:2023 for eid in map(str,fine_f["annual_event_ids"]["2023"])})
        coarse_pp=restrict_pp(list(coarse_p["eligible_candidates"]),fine_ids,fine_year)
        coarse_ref=restrict_reference(list(coarse_f["reference_candidates"]),fine_ids)
        pscore=mean_best_jaccard(list(fine_p["eligible_candidates"]),coarse_pp)
        rscore=mean_best_jaccard(list(fine_f["reference_candidates"]),coarse_ref)
        pscores.append(pscore); rscores.append(rscore)
        cross.append({"bucket":b,"ppsbm_mean_best_jaccard":pscore,"reference_mean_best_jaccard":rscore,"ppsbm_nonlower":pscore>=rscore})

    gates={
        "immutable_endpoint_source":freeze.get("endpoint_sha256")=="95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c",
        "runtime_pin":parts.get("graph_tool_image")==IMAGE and parts.get("graph_tool_version")==VERSION,
        "strict_crossyear_graph_all":all(r["checks"]["strict_crossyear_graph"] for r in panel_rows),
        "positive_degree_inference_all":all(r["checks"]["positive_degree_inference"] for r in panel_rows),
        "fixed_seed_repeatability_all":all(r["checks"]["fixed_seed_repeatability"] for r in panel_rows),
        "candidate_membership_universe_all":all(r["checks"]["candidate_membership_universe"] for r in panel_rows),
        "annual_support_floor_all":all(r["checks"]["annual_support_floor"] for r in panel_rows),
        "pairwise_disjoint_all":all(r["checks"]["pairwise_disjoint"] for r in panel_rows),
        "capacity_at_least_reference_k_all_8":all(r["checks"]["capacity_at_least_reference_k"] for r in panel_rows),
        "cross_scale_nonlower_4_of_4":sum(bool(r["ppsbm_nonlower"]) for r in cross)==4,
        "cross_scale_mean_not_lower":float(np.mean(pscores))>=float(np.mean(rscores)),
        "firewall":freeze.get("target_information_access") is False and freeze.get("target_region_events_accessed") is False and freeze.get("sonotaco_2013_2014_access") is False and freeze.get("asfn_efn_event_level_access") is False and freeze.get("amos_scientific_access") is False and freeze.get("maarsy_scientific_access") is False and freeze.get("dms_scientific_access") is False and freeze.get("orbital_information_access") is False and freeze.get("station_metadata_access") is False and freeze.get("uncertainty_metadata_access") is False and freeze.get("post_result_parameter_search") is False and parts.get("target_information_access") is False and parts.get("target_region_events_accessed") is False and parts.get("sonotaco_2013_2014_access") is False and parts.get("post_result_parameter_search") is False,
    }
    verdict="PASS_CROSSYEAR_PPSBM_SCALE_V1_PRETRUTH" if all(gates.values()) else "FAIL_CROSSYEAR_PPSBM_SCALE_V1_PRETRUTH"
    result={
        "schema":"ORBITTRACE_CROSSYEAR_PPSBM_SCALE_V1_PRETRUTH",
        "scientific_role":"ZERO_LABEL_TARGET_EXCLUDED_GMN_STRUCTURAL_AUTHORIZATION",
        "verdict":verdict,"graph_freeze_sha256":sha256(a.graph_freeze),"partitions_sha256":sha256(a.partitions),
        "panels":panel_rows,"cross_scale":cross,
        "aggregate":{"ppsbm_cross_scale_mean":float(np.mean(pscores)),"reference_cross_scale_mean":float(np.mean(rscores)),"ppsbm_bucket_wins_or_ties":int(sum(p>=r for p,r in zip(pscores,rscores))),"candidate_counts":[{"d":r["denominator"],"b":r["bucket"],"K":r["reference_k"],"ppsbm":r["eligible_candidate_count"],"B":r["inferred_block_count"]} for r in panel_rows]},
        "gates":gates,
        "shower_truth_used":False,"target_information_access":False,"target_region_events_accessed":False,
        "sonotaco_2013_2014_access":False,"asfn_efn_event_level_access":False,"amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,"orbital_information_access":False,"station_metadata_access":False,"uncertainty_metadata_access":False,"post_result_parameter_search":False,
    }
    out_sha=dump(a.output/"CROSSYEAR_PPSBM_SCALE_V1_PRETRUTH.json",result)
    print(json.dumps({"verdict":verdict,"pretruth_sha256":out_sha,"aggregate":result["aggregate"],"gates":gates,"cross_scale":cross},indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
