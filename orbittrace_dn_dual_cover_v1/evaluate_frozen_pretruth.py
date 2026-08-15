#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np

YEARS = (2022, 2023)
BLIND = (20.0, 55.0)
REQUIRED_TOTAL_AT100_GAIN = 5
PARENT_PRELABEL_SHA256 = "efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993"
PARENT_RESULT_SHA256 = "ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711"
EXPECTED_PARENT_TOTAL = 179


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--evaluation-freeze-json", type=Path, required=True)
    p.add_argument("--pretruth-json", type=Path, required=True)
    p.add_argument("--parent-runner", type=Path, required=True)
    p.add_argument("--parent-result-json", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--support-source-parts", type=Path, required=True)
    p.add_argument("--candidate-payload", type=Path, required=True)
    p.add_argument("--baseline-payload", type=Path, required=True)
    p.add_argument("--scorer-parts", type=Path, required=True)
    p.add_argument("--v8-result-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    freeze = json.loads(a.evaluation_freeze_json.read_text())
    req(freeze.get("method") == "VALSECCHI_DN_DUAL_COVER_HDBSCAN_V1", "wrong evaluation-freeze method")
    req(freeze.get("stage") == "FIRST_BINDING_GMN_LABEL_EVALUATION", "wrong evaluation-freeze stage")
    req(int(freeze.get("required_total_recovered_at_100_gain", -1)) == REQUIRED_TOTAL_AT100_GAIN, "scientific gain gate changed")
    req(int(freeze.get("parent_total_recovered_at_100", -1)) == EXPECTED_PARENT_TOTAL, "parent total changed")
    expected_pretruth_sha = str(freeze.get("pretruth_sha256", ""))
    req(len(expected_pretruth_sha) == 64, "evaluation freeze lacks exact pretruth SHA-256")
    req(sha(a.pretruth_json) == expected_pretruth_sha, "pretruth bytes differ from evaluation freeze")
    req(sha(a.parent_result_json) == PARENT_RESULT_SHA256, "exact parent result hash changed")

    pretruth = json.loads(a.pretruth_json.read_text())
    req(pretruth.get("verdict") == "PASS_DN_DUAL_COVER_V1_PRETRUTH_FEASIBILITY", "pretruth feasibility did not pass")
    req(pretruth.get("scientific_role") == "PRETRUTH_GEOMETRY_AND_CANDIDATE_CONSTRUCTION_ONLY", "wrong pretruth role")
    req(pretruth.get("hidden_truth_evaluated") is False, "pretruth claims hidden truth was evaluated")
    req(pretruth.get("hidden_truth_iterated") is False, "pretruth claims hidden truth was iterated")
    req(pretruth.get("hidden_truth_serialized") is False, "pretruth claims hidden truth was serialized")
    req(pretruth.get("blind_exclusion") == [20.0, 55.0], "pretruth blind interval changed")
    req(int(pretruth.get("physical_event_count", -1)) == 738682, "pretruth event count changed")
    req(int(pretruth.get("cover_row_count", -1)) == 1477364, "pretruth cover count changed")
    req(pretruth.get("mechanism_active") is True, "D_N mechanism inactive")
    candidates = pretruth.get("candidates")
    req(isinstance(candidates, list) and len(candidates) == int(pretruth.get("physical_candidate_count", -1)), "pretruth candidate payload mismatch")
    req(len(candidates) > 0, "pretruth has no physical candidates")
    req(all(len(c["event_ids"]) == len(set(c["event_ids"])) for c in candidates), "pretruth candidate repeats physical ID")
    req(len({tuple(c["event_ids"]) for c in candidates}) == len(candidates), "pretruth contains duplicate physical memberships")

    parent_result = json.loads(a.parent_result_json.read_text())
    req(parent_result.get("verdict") == "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_GMN_DEVELOPMENT", "wrong frozen parent result")
    parent_metrics = parent_result.get("successor_metrics")
    req(isinstance(parent_metrics, dict), "frozen parent metrics missing")
    req(int(parent_metrics["2022"]["recovered_at_100"]) == 89, "parent 2022 @100 changed")
    req(int(parent_metrics["2023"]["recovered_at_100"]) == 90, "parent 2023 @100 changed")

    parent_runner = load_module(a.parent_runner, "dn_eval_parent_runner")
    req(tuple(parent_runner.YEARS) == YEARS, "parent years changed")
    req(tuple(parent_runner.BLIND) == BLIND, "parent blind interval changed")
    req(sha(a.quality_source) == parent_runner.QUALITY_SHA, "frozen GMN utility changed")
    req(sha(a.v8_result_json) == parent_runner.V8_RESULT_SHA, "frozen GMN support artifact changed")

    # Labels are first opened only after the exact pretruth bytes and evaluator
    # gate above have been verified.
    qmod = parent_runner.load_module(a.quality_source, "dn_eval_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = parent_runner.MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = parent_runner.MONTH_KEYS
    support.CORPUS = "orbittrace-dn-dual-cover-v1-binding-label-evaluation"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"GMN evaluator accessed wrong years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(parent_runner.MONTH_KEYS), "GMN source list changed")

    ids_by_year: dict[int, set[str]] = {}
    all_ids: set[str] = set()
    for year in YEARS:
        rows = [parent_runner.normalize_event(row, year) for row in list(scan[year])]
        ids = {str(e["id"]) for e in rows}
        req(len(ids) == len(rows), f"duplicate accessible IDs in {year}")
        req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in rows), "protected region survived evaluator parser")
        ids_by_year[year] = ids
        all_ids |= ids
    req(len(ids_by_year[2022]) == 315024 and len(ids_by_year[2023]) == 423658, "accessible annual event counts changed")
    req(len(all_ids) == 738682, "accessible pooled event universe changed")
    req(all(eid in all_ids for c in candidates for eid in c["event_ids"]), "pretruth candidate contains ID outside evaluator universe")
    req(all(eid in all_ids for eid in hidden), "hidden label outside accessible evaluator universe")

    successor_metrics = {str(y): parent_runner.metrics(candidates, hidden, ids_by_year[y]) for y in YEARS}
    annual_gates = {str(y): parent_runner.annual_gate(parent_metrics[str(y)], successor_metrics[str(y)]) for y in YEARS}
    parent_total = sum(int(parent_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    successor_total = sum(int(successor_metrics[str(y)]["recovered_at_100"]) for y in YEARS)
    req(parent_total == EXPECTED_PARENT_TOTAL, f"parent total changed: {parent_total}")
    gain = successor_total - parent_total
    strong_gain = bool(gain >= REQUIRED_TOTAL_AT100_GAIN)
    passed = bool(strong_gain and all(all(g.values()) for g in annual_gates.values()))
    verdict = "PASS_DN_DUAL_COVER_V1_GMN_DEVELOPMENT" if passed else "FAIL_DN_DUAL_COVER_V1_GMN_DEVELOPMENT"

    result = {
        "verdict": verdict,
        "scientific_role": "FIRST_BINDING_TARGET_EXCLUDED_GMN_2022_2023_LABEL_EVALUATION",
        "pretruth_sha256": expected_pretruth_sha,
        "physical_candidate_count": len(candidates),
        "parent_total_recovered_at_100": parent_total,
        "successor_total_recovered_at_100": successor_total,
        "total_recovered_at_100_gain": gain,
        "required_total_recovered_at_100_gain": REQUIRED_TOTAL_AT100_GAIN,
        "strong_gain_gate": strong_gain,
        "parent_metrics": parent_metrics,
        "successor_metrics": successor_metrics,
        "annual_gates": annual_gates,
        "post_result_parameter_search": False,
        "metric": "published_Valsecchi_DN_exact_dual_cover",
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    path = a.output / "DN_DUAL_COVER_V1_GMN_DEVELOPMENT.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "parent_total": parent_total,
        "successor_total": successor_total,
        "gain": gain,
        "parent": {y: {k: v for k, v in parent_metrics[y].items() if k != "first_rank_by_label"} for y in parent_metrics},
        "successor": {y: {k: v for k, v in successor_metrics[y].items() if k != "first_rank_by_label"} for y in successor_metrics},
        "annual_gates": annual_gates,
    }, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
