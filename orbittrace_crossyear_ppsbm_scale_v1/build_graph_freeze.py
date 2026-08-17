#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

YEARS=(2022,2023)
DENOMINATORS=(128,1024)
BUCKETS=(0,1,2,3)
BLIND=(20.0,55.0)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
RADIUS=1.0
EXPECTED_EVENTS=738682
PROTOCOL_BLOB="939c529ca1db732d23fd6e8b4f0b6957176a5042"
ENDPOINT_SHA="95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c"
PARENT_BLOB="fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
QUALITY_SHA="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
EXPECTED_K={(128,0):29,(128,1):35,(128,2):38,(128,3):33,(1024,0):8,(1024,1):5,(1024,2):6,(1024,3):9}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    import subprocess
    return subprocess.check_output(["git","hash-object",str(path)],text=True).strip()


def load_module(path: Path, name: str) -> Any:
    spec=importlib.util.spec_from_file_location(name,path)
    req(spec is not None and spec.loader is not None,f"cannot import {path}")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dump(path: Path, obj: Any) -> str:
    raw=(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--endpoint-prelabel",type=Path,required=True)
    ap.add_argument("--protocol",type=Path,required=True)
    ap.add_argument("--parent-runner",type=Path,required=True)
    ap.add_argument("--quality-source",type=Path,required=True)
    ap.add_argument("--support-source-parts",type=Path,required=True)
    ap.add_argument("--candidate-payload",type=Path,required=True)
    ap.add_argument("--baseline-payload",type=Path,required=True)
    ap.add_argument("--scorer-parts",type=Path,required=True)
    ap.add_argument("--v8-result-json",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)

    req(git_blob(a.protocol)==PROTOCOL_BLOB,"protocol changed after freeze")
    req(sha256(a.endpoint_prelabel)==ENDPOINT_SHA,"endpoint prelabel changed")
    req(git_blob(a.parent_runner)==PARENT_BLOB,"GEO6 parent changed")
    req(sha256(a.quality_source)==QUALITY_SHA,"GMN utility changed")
    req(sha256(a.v8_result_json)==V8_SHA,"v8 support artifact changed")

    endpoint=json.loads(a.endpoint_prelabel.read_text())
    req(endpoint.get("schema")=="ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_GMN_RANKING_V1_PRELABEL","wrong endpoint schema")
    req(endpoint.get("scientific_role")=="PRELABEL_TARGET_EXCLUDED_GMN_RANKING_RECOVERY","wrong endpoint role")
    req(endpoint.get("shower_truth_used") is False,"endpoint used truth")
    req(endpoint.get("target_information_access") is False and endpoint.get("target_region_events_accessed") is False,"endpoint firewall")
    req(endpoint.get("sonotaco_2013_2014_access") is False,"endpoint SonotaCo access")
    subsets={(int(s["denominator"]),int(s["bucket"])):s for s in endpoint.get("subsets",[])}
    req(set(subsets)==set(EXPECTED_K),"wrong sparse panel set")
    for key,k in EXPECTED_K.items():
        req(int(subsets[key]["equal_budget_k"])==k and len(subsets[key]["recurrent_candidates"])==k,f"reference K changed {key}")

    parent=load_module(a.parent_runner,"ppsbm_parent")
    req(tuple(parent.YEARS)==YEARS and tuple(parent.BLIND)==BLIND,"parent constants changed")
    qmod=load_module(a.quality_source,"ppsbm_gmn_utility")
    qmod.v1.mult.YEARS=YEARS; qmod.v1.mult.MONTH_KEYS=MONTH_KEYS; qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime()
    support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS; support.MONTH_KEYS=MONTH_KEYS
    support.CORPUS="orbittrace-crossyear-ppsbm-scale-v1-zero-label-graph-freeze"
    support.RANKING_VARIANTS=("persistence",)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"target firewall changed")
    setattr(a,"fixed4_baseline_json",a.v8_result_json)
    _candidate,base,_scorer=support.load_sources(a)
    scan,_cal,hidden_sealed,sources=support.parse_catalogue(base)
    del hidden_sealed
    req(sorted(scan)==list(YEARS),f"wrong GMN years {sorted(scan)}")
    req([x["key"] for x in sources]==list(MONTH_KEYS),"GMN source list changed")

    events=[]
    for year in YEARS:
        events.extend(parent.normalize_event(row,year) for row in list(scan[year]))
    req(len(events)==EXPECTED_EVENTS,f"target-excluded event count changed {len(events)}")
    req(len({str(e["id"]) for e in events})==len(events),"duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events),"protected event survived parser")
    event_by_id={str(e["id"]):e for e in events}

    manifest_panels=[]
    for d in DENOMINATORS:
        for b in BUCKETS:
            s=subsets[(d,b)]
            annual={str(y):sorted(str(x) for x in s["annual_event_ids"][str(y)]) for y in YEARS}
            panel_ids=sorted(set(annual["2022"])|set(annual["2023"]))
            req(len(panel_ids)==int(s["event_count"]),f"panel event count mismatch d={d} b={b}")
            req(set(panel_ids).issubset(event_by_id),f"missing panel event d={d} b={b}")
            ordered=[event_by_id[eid] for eid in panel_ids]
            years=np.asarray([int(e["year"]) for e in ordered],dtype=np.int64)
            x=np.asarray(parent.geo_matrix(ordered),dtype=float)
            req(x.shape==(len(ordered),6) and np.all(np.isfinite(x)),"invalid GEO6")
            tree=cKDTree(x)
            raw=tree.query_ball_point(x,r=RADIUS,p=2.0,eps=0.0,return_sorted=True)
            degree=np.zeros(len(ordered),dtype=np.int64)
            raw_edges=[]; max_dist=0.0
            for i,row in enumerate(raw):
                for jj in row:
                    j=int(jj)
                    if j<=i or int(years[i])==int(years[j]):
                        continue
                    dist=float(np.linalg.norm(x[i]-x[j]))
                    req(dist<=RADIUS+1e-12,"out-of-radius edge")
                    raw_edges.append((i,j)); degree[i]+=1; degree[j]+=1; max_dist=max(max_dist,dist)
            active_old=np.flatnonzero(degree>0)
            req(len(active_old)>0,f"empty recurrence graph d={d} b={b}")
            remap={int(old):new for new,old in enumerate(active_old.tolist())}
            vertices=[{"id":panel_ids[int(old)],"year":int(years[int(old)]),"crossyear_degree":int(degree[int(old)])} for old in active_old]
            edges=[[remap[i],remap[j]] for i,j in raw_edges if i in remap and j in remap]
            req(all(vertices[i]["year"]!=vertices[j]["year"] for i,j in edges),"same-year edge survived")
            req(all(int(v["crossyear_degree"])>0 for v in vertices),"zero-degree inference vertex survived")
            graph={
                "schema":"ORBITTRACE_CROSSYEAR_PPSBM_GRAPH_V1",
                "denominator":d,"bucket":b,"radius":RADIUS,
                "vertices":vertices,"edges":edges,
                "full_panel_event_count":len(panel_ids),
                "active_vertex_count":len(vertices),
                "zero_degree_removed_count":len(panel_ids)-len(vertices),
                "crossyear_edge_count":len(edges),
                "maximum_edge_distance":max_dist,
            }
            graph_path=a.output/f"PPSBM_GRAPH_D{d}_B{b}.json"
            graph_sha=dump(graph_path,graph)
            manifest_panels.append({
                "denominator":d,"bucket":b,"reference_k":EXPECTED_K[(d,b)],
                "full_panel_event_count":len(panel_ids),"active_vertex_count":len(vertices),
                "crossyear_edge_count":len(edges),"graph_file":graph_path.name,"graph_sha256":graph_sha,
                "annual_event_ids":annual,
                "reference_candidates":s["recurrent_candidates"],
            })

    manifest={
        "schema":"ORBITTRACE_CROSSYEAR_PPSBM_GRAPH_FREEZE_V1",
        "scientific_role":"ZERO_LABEL_RAW_CROSSYEAR_GRAPH_FREEZE",
        "protocol_blob":PROTOCOL_BLOB,
        "endpoint_sha256":ENDPOINT_SHA,
        "panels":manifest_panels,
        "shower_truth_used":False,"target_information_access":False,"target_region_events_accessed":False,
        "sonotaco_2013_2014_access":False,"asfn_efn_event_level_access":False,
        "amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,
        "orbital_information_access":False,"station_metadata_access":False,"uncertainty_metadata_access":False,
        "post_result_parameter_search":False,
    }
    manifest_sha=dump(a.output/"PPSBM_GRAPH_FREEZE_V1.json",manifest)
    print(json.dumps({"graph_freeze_sha256":manifest_sha,"panels":[{"d":p["denominator"],"b":p["bucket"],"active":p["active_vertex_count"],"edges":p["crossyear_edge_count"],"K":p["reference_k"]} for p in manifest_panels]},indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
