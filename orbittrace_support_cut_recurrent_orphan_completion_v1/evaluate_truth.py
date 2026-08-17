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
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
PRELABEL_SHA256 = "278d659542668e52033a5369f9afdf685e010a2c14c7ff5211b0b60dd73f2d4a"
STRUCTURAL_SHA256 = "38b68cf74dc3d69128beb484abd2af3a266c40987266d2941f4855a53a0ed374"
BUCKETS = (0, 1, 2, 3)


def req(x: bool, message: str) -> None:
    if not x:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compact(metrics: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metrics.items() if k != "first_rank_by_label"}


def aggregate(panels: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [p[key] for p in panels]
    return {
        "qualified_total": sum(int(x["qualified_matches"]) for x in values),
        "mrr_mean": float(np.mean([float(x["mrr"]) for x in values])),
        "precision_mean": float(np.mean([float(x["top100_dominant_precision"]) for x in values])),
        "fragmentation_mean": float(np.mean([float(x["fragmentation_median_top500"]) for x in values])),
        "recovered_at_25_total": sum(int(x["recovered_at_25"]) for x in values),
        "recovered_at_50_total": sum(int(x["recovered_at_50"]) for x in values),
        "recovered_at_100_total": sum(int(x["recovered_at_100"]) for x in values),
        "recovered_at_500_total": sum(int(x["recovered_at_500"]) for x in values),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prelabel", type=Path, required=True)
    ap.add_argument("--structural-result", type=Path, required=True)
    ap.add_argument("--parent-runner", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    # Exact frozen inputs. The evaluator has no authority to generate or reorder candidates.
    req(sha256(a.quality_source) == QUALITY_SHA256, "quality source changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "v8 result changed")
    req(sha256(a.prelabel) == PRELABEL_SHA256, "orphan-completion prelabel changed")
    req(sha256(a.structural_result) == STRUCTURAL_SHA256, "structural result changed")

    pre = json.loads(a.prelabel.read_text())
    structural = json.loads(a.structural_result.read_text())
    req(pre["schema"] == "ORBITTRACE_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_PRELABEL", "wrong prelabel schema")
    req(pre["scientific_role"] == "PRELABEL_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1", "wrong prelabel role")
    req(pre["shower_truth_used"] is False, "prelabel used shower truth")
    req(pre["target_information_access"] is False and pre["target_region_events_accessed"] is False, "prelabel firewall")
    req(pre["configuration"] == {
        "equal_budget": "stored_recurrent_candidate_count_per_panel",
        "rule": "max_exact_intersection_support_projection_else_zero_overlap_recurrent_orphan_then_native_support_append",
    }, "catalogue rule changed")
    req(structural["schema"] == "ORBITTRACE_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_STRUCTURAL", "wrong structural schema")
    req(structural["scientific_role"] == "ZERO_LABEL_STRUCTURAL_GATE", "wrong structural role")
    req(structural["shower_truth_used"] is False, "structural stage used truth")
    req(structural["verdict"] == "PASS_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_STRUCTURAL", "structural gate did not pass")
    req(all(bool(v) for v in structural["gates"].values()) and len(structural["gates"]) == 8, "not all structural gates passed")
    req(structural["prelabel_sha256"] == PRELABEL_SHA256, "structural/prelabel mismatch")

    subset_map = {(int(r["denominator"]), int(r["bucket"])): r for r in pre["subsets"]}
    req(set(subset_map) == {(d, b) for d in (128, 1024) for b in BUCKETS}, "wrong panel set")
    for r in pre["subsets"]:
        succ = r["successor_candidates"]
        parent_rows = r["recurrent_candidates"]
        K = int(r["equal_budget_k"])
        req(K == len(parent_rows) and len(succ) >= K and K >= 1, "equal budget changed")
        req([int(x["rank"]) for x in parent_rows] == list(range(1, len(parent_rows) + 1)), "parent rank discontinuity")
        req([int(x["orphan_completion_rank"]) for x in succ] == list(range(1, len(succ) + 1)), "successor rank discontinuity")
        req(all(x["catalogue_source"] in {"support_projection", "recurrent_orphan", "support_append"} for x in succ), "unknown source type")
        annual_union = set(r["annual_event_ids"]["2022"]) | set(r["annual_event_ids"]["2023"])
        req(len(annual_union) == int(r["event_count"]), "annual universe count mismatch")
        req(all(set(x["event_ids"]).issubset(annual_union) for x in succ), "successor membership outside frozen panel")
        req(all(set(x["event_ids"]).issubset(annual_union) for x in parent_rows), "parent membership outside frozen panel")

    # Load exactly the established target-excluded GMN truth/runtime used by prior sparse-GMN endpoints.
    parent = load_module(a.parent_runner, "orphan_truth_parent")
    q = load_module(a.quality_source, "orphan_truth_gmn")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-support-cut-recurrent-orphan-completion-truth-v1"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, baseline, _scorer = support.load_sources(a)
    scan, _calibration, hidden, sources = support.parse_catalogue(baseline)
    req(isinstance(hidden, dict), "hidden truth unavailable")
    req(sorted(scan) == list(YEARS) and [x["key"] for x in sources] == list(MONTH_KEYS), "truth/source set changed")

    events = []
    for year in YEARS:
        events.extend(parent.normalize_event(row, year) for row in list(scan[year]))
    req(len(events) == 738682, "target-excluded event universe changed")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected region entered truth runtime")
    full_ids = {str(e["id"]) for e in events}
    req(len(full_ids) == len(events), "event ids are not unique")
    for r in pre["subsets"]:
        for year in YEARS:
            req(set(r["annual_event_ids"][str(year)]).issubset(full_ids), "frozen panel ids absent from truth runtime")

    panels: list[dict[str, Any]] = []
    for d in (128, 1024):
        for b in BUCKETS:
            frozen = subset_map[(d, b)]
            K = int(frozen["equal_budget_k"])
            successor = frozen["successor_candidates"][:K]
            recurrent = frozen["recurrent_candidates"][:K]
            for year in YEARS:
                annual = set(frozen["annual_event_ids"][str(year)])
                parent_metrics = compact(parent.metrics(recurrent, hidden, annual))
                successor_metrics = compact(parent.metrics(successor, hidden, annual))
                panels.append({
                    "denominator": d,
                    "bucket": b,
                    "year": year,
                    "equal_budget_k": K,
                    "parent_equal_budget": parent_metrics,
                    "successor_equal_budget": successor_metrics,
                    "qualified_nonlower": int(successor_metrics["qualified_matches"]) >= int(parent_metrics["qualified_matches"]),
                    "qualified_strict_win": int(successor_metrics["qualified_matches"]) > int(parent_metrics["qualified_matches"]),
                })

    scales: dict[str, Any] = {}
    for d in (128, 1024):
        ps = [p for p in panels if p["denominator"] == d]
        req(len(ps) == 8, f"missing annual panels d={d}")
        parent_agg = aggregate(ps, "parent_equal_budget")
        successor_agg = aggregate(ps, "successor_equal_budget")
        nonlower = sum(bool(p["qualified_nonlower"]) for p in ps)
        strict = sum(bool(p["qualified_strict_win"]) for p in ps)
        scales[str(d)] = {
            "panel_count": 8,
            "parent_equal_budget": parent_agg,
            "successor_equal_budget": successor_agg,
            "qualified_nonlower_panels": nonlower,
            "qualified_strict_win_panels": strict,
            "qualified_loss_panels": 8 - nonlower,
        }

    fine_parent = scales["1024"]["parent_equal_budget"]
    fine_successor = scales["1024"]["successor_equal_budget"]
    coarse_parent = scales["128"]["parent_equal_budget"]
    coarse_successor = scales["128"]["successor_equal_budget"]
    gates = {
        "fine_qualified_total_strictly_greater": fine_successor["qualified_total"] > fine_parent["qualified_total"],
        "fine_qualified_nonlower_at_least_6_of_8": scales["1024"]["qualified_nonlower_panels"] >= 6,
        "fine_mrr_mean_not_lower": fine_successor["mrr_mean"] >= fine_parent["mrr_mean"],
        "fine_precision_mean_not_lower": fine_successor["precision_mean"] >= fine_parent["precision_mean"],
        "fine_fragmentation_mean_not_higher": fine_successor["fragmentation_mean"] <= fine_parent["fragmentation_mean"],
        "coarse_qualified_total_not_lower": coarse_successor["qualified_total"] >= coarse_parent["qualified_total"],
        "coarse_qualified_nonlower_at_least_6_of_8": scales["128"]["qualified_nonlower_panels"] >= 6,
        "coarse_mrr_mean_not_lower": coarse_successor["mrr_mean"] >= coarse_parent["mrr_mean"],
        "coarse_precision_mean_not_lower": coarse_successor["precision_mean"] >= coarse_parent["precision_mean"],
        "coarse_fragmentation_mean_not_higher": coarse_successor["fragmentation_mean"] <= coarse_parent["fragmentation_mean"],
    }
    verdict = "PASS_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1" if all(gates.values()) else "FAIL_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1"
    out = {
        "schema": "ORBITTRACE_SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_TRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_SPARSE_RECOVERY_DEVELOPMENT",
        "verdict": verdict,
        "stage1_run_id": 32043362123,
        "stage1_artifact_id": 9292356070,
        "prelabel_sha256": PRELABEL_SHA256,
        "structural_result_sha256": STRUCTURAL_SHA256,
        "panels": panels,
        "scale_aggregates": scales,
        "gates": gates,
        "blind_exclusion": list(BLIND),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_event_level_access": False,
        "efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "method_parameter_selection_from_result": False,
    }
    path = a.output / "SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_TRUTH.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "scales": scales, "gates": gates}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
