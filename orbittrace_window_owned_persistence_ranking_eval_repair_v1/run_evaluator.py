#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

YEARS=(2022,2023)
MONTH_KEYS=tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1,13))
BLIND=(20.0,55.0)
QUALITY_SHA256="dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256="fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PRELABEL_SHA256="beae39cc987100373d236a19e656415dd63f183cfbbb4202345e0cde7e3b6f11"
SOURCE_RUN_ID=31956064964
SOURCE_ARTIFACT_ID=9266239856
SOURCE_CANDIDATE_COUNT=1028
SOURCE_BOTH_YEAR_COUNT=1014
EXPECTED_PARENT={
    "2022":{"recovered_at_25":22,"recovered_at_50":45,"recovered_at_100":89,"recovered_at_500":193,"top100_dominant_precision":0.7856486013,"mrr":0.0224982696,"qualified_matches":236,"fragmentation_median_top500":1.0},
    "2023":{"recovered_at_25":23,"recovered_at_50":46,"recovered_at_100":89,"recovered_at_500":192,"top100_dominant_precision":0.7867680237,"mrr":0.0220239289,"qualified_matches":244,"fragmentation_median_top500":1.0},
}


def req(ok:bool,msg:str)->None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path)
    req(spec is not None and spec.loader is not None,f"cannot import {path}")
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def annual_gate(parent:dict[str,Any],succ:dict[str,Any])->dict[str,bool]:
    # Exact gate copied from the frozen original successor implementation.
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


def compact_metrics(m:dict[str,Any])->dict[str,Any]:
    return {k:v for k,v in m.items() if k!="first_rank_by_label"}


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--prelabel",type=Path,required=True)
    ap.add_argument("--parent-runner",type=Path,required=True)
    ap.add_argument("--quality-source",type=Path,required=True)
    ap.add_argument("--support-source-parts",type=Path,required=True)
    ap.add_argument("--candidate-payload",type=Path,required=True)
    ap.add_argument("--baseline-payload",type=Path,required=True)
    ap.add_argument("--scorer-parts",type=Path,required=True)
    ap.add_argument("--v8-result-json",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)

    req(sha256(a.prelabel)==PRELABEL_SHA256,"immutable prelabel SHA-256 changed")
    req(sha256(a.quality_source)==QUALITY_SHA256,"frozen GMN utility changed")
    req(sha256(a.v8_result_json)==V8_RESULT_SHA256,"frozen GMN support artifact changed")

    prelabel=json.loads(a.prelabel.read_text())
    req(prelabel["scientific_role"]=="PRELABEL_WINDOW_OWNED_PERSISTENCE_RANKING_V1","wrong prelabel role")
    req(int(prelabel["events_total"])==738682,"prelabel event count changed")
    req(prelabel["events_by_year"]=={"2022":315024,"2023":423658},"prelabel annual counts changed")
    req(prelabel["blind_exclusion"]==[20.0,55.0],"prelabel blind exclusion changed")
    for k in ("target_information_access","target_region_events_accessed","sonotaco_2013_2014_access","asfn_event_level_access","efn_event_level_access","amos_scientific_access","maarsy_scientific_access","dms_scientific_access"):
        req(prelabel[k] is False,f"forbidden prelabel access flag {k}")

    successor_candidates=prelabel["successor_candidates"]
    req(len(successor_candidates)==SOURCE_CANDIDATE_COUNT,"successor candidate count changed")
    req(int(prelabel["successor_summary"]["both_year_candidate_count"])==SOURCE_BOTH_YEAR_COUNT,"both-year count changed")
    req([int(r["rank"]) for r in successor_candidates]==list(range(1,SOURCE_CANDIDATE_COUNT+1)),"stored successor rank/order changed")
    req(len({str(r["family_id"]) for r in successor_candidates})==SOURCE_CANDIDATE_COUNT,"duplicate successor family ID")
    req(len({tuple(r["event_ids"]) for r in successor_candidates})==SOURCE_CANDIDATE_COUNT,"duplicate successor membership")

    # Load only the historical evaluator and target-excluded GMN sealed truth plumbing.
    # No successor candidate generation or Persistable import occurs in this repair.
    parent=load_module(a.parent_runner,"window_rank_repair_parent")
    req(tuple(parent.YEARS)==YEARS and tuple(parent.BLIND)==BLIND,"parent constants changed")
    req(int(parent.MIN_CLUSTER_SIZE)==10 and int(parent.MIN_SAMPLES)==10,"parent support constants changed")

    qmod=load_module(a.quality_source,"window_rank_repair_gmn_utility")
    qmod.v1.mult.YEARS=YEARS
    qmod.v1.mult.MONTH_KEYS=MONTH_KEYS
    qmod.v1.mult.TOP_K=100
    runtime=qmod.v1.mult.load_frozen_runtime()
    support=runtime.load_support_module(a.support_source_parts)
    support.YEARS=YEARS
    support.MONTH_KEYS=MONTH_KEYS
    support.CORPUS="orbittrace-window-owned-persistence-ranking-v1-target-excluded"
    support.RANKING_VARIANTS=("persistence",)
    req((float(support.BLIND_LOW),float(support.BLIND_HIGH))==BLIND,"target firewall changed")
    setattr(a,"fixed4_baseline_json",a.v8_result_json)
    _candidate,base,_scorer=support.load_sources(a)
    scan,_cal,hidden_sealed,sources=support.parse_catalogue(base)
    req(sorted(scan)==list(YEARS),f"wrong GMN years {sorted(scan)}")
    req([x["key"] for x in sources]==list(MONTH_KEYS),"GMN source list changed")

    events=[]
    for year in YEARS:
        raw=list(scan[year])
        norm=[parent.normalize_event(row,year) for row in raw]
        req(len(norm)==len(raw),f"normalization count changed {year}")
        events.extend(norm)
    req(len(events)==738682,f"pooled event count changed {len(events)}")
    req(len({str(e["id"]) for e in events})==len(events),"duplicate event IDs")
    req(all(not(BLIND[0]<=float(e["sol"])<=BLIND[1]) for e in events),"protected row survived parser")

    ids_by_year={y:{str(e["id"]) for e in events if int(e["year"])==y} for y in YEARS}
    hidden=hidden_sealed
    req(all(eid in ids_by_year[2022] or eid in ids_by_year[2023] for eid in hidden),"label outside accessible event IDs")
    accessible_ids=ids_by_year[2022] | ids_by_year[2023]
    req(all(all(str(eid) in accessible_ids for eid in row["event_ids"]) for row in successor_candidates),"successor contains event outside accessible target-excluded GMN")

    # Immutable comparator: do not recompute the parent under a new dependency environment.
    parent_metrics=json.loads(json.dumps(EXPECTED_PARENT))
    successor_metrics={str(y):parent.metrics(successor_candidates,hidden,ids_by_year[y]) for y in YEARS}
    gates={str(y):annual_gate(parent_metrics[str(y)],successor_metrics[str(y)]) for y in YEARS}
    strict100=any(int(successor_metrics[str(y)]["recovered_at_100"])>int(parent_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    passed=bool(strict100 and len(successor_candidates)>=100 and all(all(g.values()) for g in gates.values()))
    verdict="PASS_WINDOW_OWNED_PERSISTENCE_RANKING_V1_GMN_DEVELOPMENT" if passed else "FAIL_WINDOW_OWNED_PERSISTENCE_RANKING_V1_GMN_DEVELOPMENT"

    result={
        "verdict":verdict,
        "scientific_role":"TARGET_EXCLUDED_GMN_2022_2023_DEVELOPMENT_ONLY",
        "repair_role":"EVALUATOR_ONLY_IMMUTABLE_PRELABEL_REPAIR_V1",
        "source_run_id":SOURCE_RUN_ID,
        "source_artifact_id":SOURCE_ARTIFACT_ID,
        "prelabel_sha256":PRELABEL_SHA256,
        "events_total":738682,
        "events_by_year":{"2022":315024,"2023":423658},
        "successor_candidate_count":SOURCE_CANDIDATE_COUNT,
        "successor_both_year_candidate_count":SOURCE_BOTH_YEAR_COUNT,
        "strict_recovered_at_100_improvement_some_year":strict100,
        "parent_metrics":parent_metrics,
        "successor_metrics":successor_metrics,
        "annual_gates":gates,
        "ranking":{"both_years_present":"desc","g_first":"asc","g_span":"desc","min_annual_count":"desc","member_count_total":"desc","family_id":"asc"},
        "blind_exclusion":[20.0,55.0],
        "target_information_access":False,"target_region_events_accessed":False,
        "sonotaco_2013_2014_access":False,"asfn_event_level_access":False,"efn_event_level_access":False,
        "amos_scientific_access":False,"maarsy_scientific_access":False,"dms_scientific_access":False,
    }
    out=a.output/"WINDOW_OWNED_PERSISTENCE_RANKING_V1_GMN_DEVELOPMENT_EVAL_REPAIR.json"
    out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "verdict":verdict,
        "parent":{y:compact_metrics(m) for y,m in parent_metrics.items()},
        "successor":{y:compact_metrics(m) for y,m in successor_metrics.items()},
        "annual_gates":gates,
        "strict100":strict100,
        "successor_candidate_count":SOURCE_CANDIDATE_COUNT,
    },indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
