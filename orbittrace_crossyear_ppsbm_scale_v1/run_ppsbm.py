#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import graph_tool.all as gt

METHOD="ORBITTRACE_CROSSYEAR_PPSBM_SCALE_V1"
IMAGE="tiagopeixoto/graph-tool@sha256:4e613c0da8cfb85c05661c124da0ef2d167ec4a5a3347ae10a8f5030bab0a375"
VERSION="3.6 (commit fd9762d9, Sun Aug 2 18:45:30 2026 +0200)"
MIN_SUPPORT=4


def req(ok: bool,msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path,obj: Any) -> str:
    raw=(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def family_hash(ids: list[str] | tuple[str,...]) -> str:
    vals=tuple(sorted(str(x) for x in ids))
    return hashlib.sha256(("\n".join(vals)+"\n").encode()).hexdigest()


def panel_seed(d: int,b: int) -> int:
    raw=hashlib.sha256(f"{METHOD}|{d}|{b}".encode()).digest()
    return int.from_bytes(raw[:4],"big") & 0x7fffffff


def canonical_partition(blocks: np.ndarray,ids: list[str]) -> tuple[tuple[str,...],...]:
    groups=[]
    for label in sorted(set(map(int,blocks.tolist()))):
        members=tuple(sorted(ids[i] for i in np.flatnonzero(blocks==label).tolist()))
        groups.append(members)
    return tuple(sorted(groups))


def fit_once(g: Any,ids: list[str],seed: int) -> tuple[Any,np.ndarray,tuple[tuple[str,...],...],float]:
    gt.seed_rng(seed); np.random.seed(seed)
    state=gt.minimize_blockmodel_dl(
        g,
        state=gt.PPBlockState,
        state_args=dict(uniform=False,deg_corr=True),
    )
    blocks=np.asarray(state.get_blocks().a,dtype=np.int64).copy()
    canonical=canonical_partition(blocks,ids)
    entropy=float(state.entropy())
    return state,blocks,canonical,entropy


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--graph-freeze",type=Path,required=True)
    ap.add_argument("--graph-dir",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    req(getattr(gt,"__version__",None)==VERSION,"graph-tool version changed")
    gt.openmp_set_num_threads(1)
    req(gt.openmp_get_num_threads()==1,"OpenMP thread pin failed")

    manifest=json.loads(a.graph_freeze.read_text())
    req(manifest.get("schema")=="ORBITTRACE_CROSSYEAR_PPSBM_GRAPH_FREEZE_V1","wrong graph freeze schema")
    req(manifest.get("scientific_role")=="ZERO_LABEL_RAW_CROSSYEAR_GRAPH_FREEZE","wrong graph freeze role")
    req(manifest.get("shower_truth_used") is False,"graph freeze used truth")

    outputs=[]
    for p in manifest["panels"]:
        d=int(p["denominator"]); b=int(p["bucket"])
        graph_path=a.graph_dir/str(p["graph_file"])
        req(sha256(graph_path)==str(p["graph_sha256"]),f"graph hash mismatch d={d} b={b}")
        row=json.loads(graph_path.read_text())
        req(row.get("schema")=="ORBITTRACE_CROSSYEAR_PPSBM_GRAPH_V1","wrong graph schema")
        req(int(row["denominator"])==d and int(row["bucket"])==b,"graph panel mismatch")
        vertices=list(row["vertices"]); edges=[tuple(map(int,e)) for e in row["edges"]]
        ids=[str(v["id"]) for v in vertices]; years=np.asarray([int(v["year"]) for v in vertices],dtype=np.int64)
        req(len(ids)==len(set(ids)) and len(ids)>0,"invalid active vertex list")
        req(all(int(v["crossyear_degree"])>0 for v in vertices),"zero-degree vertex in inference graph")
        req(all(0<=i<len(ids) and 0<=j<len(ids) and i!=j for i,j in edges),"invalid edge index")
        req(all(int(years[i])!=int(years[j]) for i,j in edges),"same-year edge entered PP-SBM")

        g=gt.Graph(len(ids),directed=False)
        g.add_edge_list(edges)
        req(int(g.num_vertices())==len(ids) and int(g.num_edges())==len(edges),"graph-tool graph changed")
        seed=panel_seed(d,b)
        state1,blocks1,canon1,entropy1=fit_once(g,ids,seed)
        _state2,blocks2,canon2,entropy2=fit_once(g,ids,seed)
        repeat_identical=(canon1==canon2 and entropy1==entropy2)

        groups=[]
        for members in canon1:
            member_set=set(members)
            indices=[i for i,eid in enumerate(ids) if eid in member_set]
            n22=sum(int(years[i])==2022 for i in indices); n23=sum(int(years[i])==2023 for i in indices)
            internal_edges=sum(1 for i,j in edges if ids[i] in member_set and ids[j] in member_set)
            groups.append({
                "family_hash":family_hash(list(members)),
                "event_ids":list(members),
                "member_count":len(members),
                "members_2022":int(n22),"members_2023":int(n23),
                "bottleneck_annual_support":int(min(n22,n23)),
                "internal_crossyear_edge_count":int(internal_edges),
                "eligible":bool(n22>=MIN_SUPPORT and n23>=MIN_SUPPORT),
            })
        eligible=[dict(r) for r in groups if bool(r["eligible"])]
        eligible.sort(key=lambda r:(-int(r["bottleneck_annual_support"]),-int(r["internal_crossyear_edge_count"]),-int(r["member_count"]),str(r["family_hash"])))
        for rank,r in enumerate(eligible,1): r["diagnostic_rank"]=rank

        outputs.append({
            "denominator":d,"bucket":b,"seed":seed,
            "graph_sha256":str(p["graph_sha256"]),
            "active_vertex_count":len(ids),"edge_count":len(edges),
            "inferred_block_count":len(canon1),"eligible_candidate_count":len(eligible),
            "description_length":entropy1,
            "fixed_seed_repeatability":bool(repeat_identical),
            "all_blocks":groups,"eligible_candidates":eligible,
        })
        print(json.dumps({"d":d,"b":b,"seed":seed,"B":len(canon1),"eligible":len(eligible),"entropy":entropy1,"repeat":repeat_identical},sort_keys=True),flush=True)

    result={
        "schema":"ORBITTRACE_CROSSYEAR_PPSBM_PARTITIONS_V1",
        "scientific_role":"ZERO_LABEL_DEGREE_CORRECTED_PP_SBM_PARTITION",
        "graph_freeze_sha256":sha256(a.graph_freeze),
        "graph_tool_image":IMAGE,"graph_tool_version":VERSION,"openmp_threads":1,
        "state":"PPBlockState","uniform":False,"degree_corrected":True,
        "panels":outputs,
        "shower_truth_used":False,"target_information_access":False,"target_region_events_accessed":False,
        "sonotaco_2013_2014_access":False,"post_result_parameter_search":False,
    }
    out_sha=dump(a.output/"PPSBM_PARTITIONS_V1.json",result)
    print(json.dumps({"partitions_sha256":out_sha,"counts":[{"d":p["denominator"],"b":p["bucket"],"B":p["inferred_block_count"],"eligible":p["eligible_candidate_count"]} for p in outputs]},indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
