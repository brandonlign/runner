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
SOURCE_PRELABEL_SHA256 = "278d659542668e52033a5369f9afdf685e010a2c14c7ff5211b0b60dd73f2d4a"
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_RESULT_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
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


def zero_filled_mrr(metrics: dict[str, Any]) -> float:
    eligible = int(metrics["eligible_labels"])
    qualified = int(metrics["qualified_matches"])
    conditional = float(metrics["mrr"])
    req(eligible >= qualified >= 0, "invalid eligible/qualified counts")
    if eligible == 0:
        return 0.0
    if qualified == 0:
        req(conditional == 0.0, "nonzero conditional MRR with zero qualified matches")
        return 0.0
    return conditional * qualified / eligible


def aggregate(panels: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [p[key] for p in panels]
    eligible_total = sum(int(x["eligible_labels"]) for x in values)
    reciprocal_mass = sum(float(x["mrr"]) * int(x["qualified_matches"]) for x in values)
    return {
        "qualified_total": sum(int(x["qualified_matches"]) for x in values),
        "conditional_mrr_mean": float(np.mean([float(x["mrr"]) for x in values])),
        "zero_filled_mrr_mean": float(np.mean([zero_filled_mrr(x) for x in values])),
        "zero_filled_mrr_pooled": reciprocal_mass / eligible_total if eligible_total else 0.0,
        "eligible_total": eligible_total,
        "reciprocal_mass": reciprocal_mass,
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
    ap.add_argument("--pretruth", type=Path, required=True)
    ap.add_argument("--parent-runner", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--support-source-parts", type=Path, required=True)
    ap.add_argument("--candidate-payload", type=Path, required=True)
    ap.add_argument("--baseline-payload", type=Path, required=True)
    ap.add_argument("--scorer-parts", type=Path, required=True)
    ap.add_argument("--v8-result-json", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    req(sha256(args.quality_source) == QUALITY_SHA256, "quality source changed")
    req(sha256(args.v8_result_json) == V8_RESULT_SHA256, "v8 result changed")
    prelabel_sha = sha256(args.prelabel)
    pretruth_sha = sha256(args.pretruth)

    pre = json.loads(args.prelabel.read_text())
    audit = json.loads(args.pretruth.read_text())
    req(pre["schema"] == "ORBITTRACE_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRELABEL", "wrong prelabel schema")
    req(pre["scientific_role"] == "PRELABEL_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1", "wrong prelabel role")
    req(pre["source_prelabel_sha256"] == SOURCE_PRELABEL_SHA256, "wrong source prelabel")
    req(pre["configuration"] == {
        "abort": "more_than_one_recurrent_parent_overlap",
        "discard": "zero_recurrent_parent_overlap",
        "equal_budget": "stored_recurrent_candidate_count_per_panel",
        "ranking": "corroborating_parent_rank_then_native_support_rank_then_family_hash",
        "retain": "full_topomodal_support_candidate_iff_exact_event_overlap_with_exactly_one_recurrent_parent",
    }, "catalogue configuration changed")
    req(pre["shower_truth_used"] is False, "prelabel used shower truth")
    req(pre["target_information_access"] is False and pre["target_region_events_accessed"] is False, "prelabel firewall")
    req(pre["sonotaco_2013_2014_access"] is False, "prelabel SonotaCo access")

    req(audit["schema"] == "ORBITTRACE_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRETRUTH", "wrong pretruth schema")
    req(audit["scientific_role"] == "ZERO_LABEL_PRETRUTH_AUTHORIZATION", "wrong pretruth role")
    req(audit["verdict"] == "PASS_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRETRUTH", "pretruth did not pass")
    req(audit["prelabel_sha256"] == prelabel_sha, "pretruth/prelabel mismatch")
    req(len(audit["gates"]) == 12 and all(bool(v) for v in audit["gates"].values()), "not all pretruth gates passed")
    req(audit["shower_truth_used"] is False, "pretruth used shower truth")
    req(audit["target_information_access"] is False and audit["target_region_events_accessed"] is False, "pretruth firewall")

    subset_map = {(int(r["denominator"]), int(r["bucket"])): r for r in pre["subsets"]}
    req(set(subset_map) == {(d, b) for d in (128, 1024) for b in BUCKETS}, "wrong panel set")
    for row in pre["subsets"]:
        successor = list(row["successor_candidates"])
        recurrent = list(row["recurrent_candidates"])
        K = int(row["equal_budget_k"])
        req(len(recurrent) == K and len(successor) >= K and K >= 1, "equal budget/capacity changed")
        req([int(x["rank"]) for x in recurrent] == list(range(1, K + 1)), "parent rank discontinuity")
        req([int(x["overlap_consensus_rank"]) for x in successor] == list(range(1, len(successor) + 1)), "successor rank discontinuity")
        expected_order = sorted(successor, key=lambda x: (int(x["corroborating_parent_rank"]), int(x["native_support_rank"]), str(x["family_hash"])))
        req([str(x["family_hash"]) for x in successor] == [str(x["family_hash"]) for x in expected_order], "successor order changed")
        req(all(x["catalogue_source"] == "recurrent_overlap_confirmed_topomodal" for x in successor), "unknown successor source")
        annual_union = set(row["annual_event_ids"]["2022"]) | set(row["annual_event_ids"]["2023"])
        req(len(annual_union) == int(row["event_count"]), "annual universe count mismatch")
        req(all(set(x["event_ids"]).issubset(annual_union) for x in successor + recurrent), "membership outside frozen panel")
        for x in successor:
            parent_rank = int(x["corroborating_parent_rank"])
            req(1 <= parent_rank <= K, "invalid corroborating parent rank")
            req(set(x["event_ids"]) & set(recurrent[parent_rank - 1]["event_ids"]), "successor lost exact parent overlap")

    parent = load_module(args.parent_runner, "overlap_consensus_truth_parent")
    q = load_module(args.quality_source, "overlap_consensus_truth_gmn")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(args.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-recurrent-topomodal-overlap-consensus-v1"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "firewall changed")
    setattr(args, "fixed4_baseline_json", args.v8_result_json)
    _candidate, baseline, _scorer = support.load_sources(args)
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
    for row in pre["subsets"]:
        for year in YEARS:
            req(set(row["annual_event_ids"][str(year)]).issubset(full_ids), "frozen panel ids absent from truth runtime")

    panels: list[dict[str, Any]] = []
    for denominator in (128, 1024):
        for bucket in BUCKETS:
            frozen = subset_map[(denominator, bucket)]
            K = int(frozen["equal_budget_k"])
            successor = frozen["successor_candidates"][:K]
            recurrent = frozen["recurrent_candidates"]
            for year in YEARS:
                annual = set(frozen["annual_event_ids"][str(year)])
                parent_metrics = compact(parent.metrics(recurrent, hidden, annual))
                successor_metrics = compact(parent.metrics(successor, hidden, annual))
                req(int(parent_metrics["eligible_labels"]) == int(successor_metrics["eligible_labels"]), "eligibility changed between catalogues")
                panels.append({
                    "denominator": denominator,
                    "bucket": bucket,
                    "year": year,
                    "equal_budget_k": K,
                    "parent_equal_budget": parent_metrics,
                    "successor_equal_budget": successor_metrics,
                    "parent_zero_filled_mrr": zero_filled_mrr(parent_metrics),
                    "successor_zero_filled_mrr": zero_filled_mrr(successor_metrics),
                    "qualified_nonlower": int(successor_metrics["qualified_matches"]) >= int(parent_metrics["qualified_matches"]),
                    "qualified_strict_win": int(successor_metrics["qualified_matches"]) > int(parent_metrics["qualified_matches"]),
                })

    scales: dict[str, Any] = {}
    for denominator in (128, 1024):
        subset = [p for p in panels if p["denominator"] == denominator]
        req(len(subset) == 8, f"missing annual panels d={denominator}")
        parent_agg = aggregate(subset, "parent_equal_budget")
        successor_agg = aggregate(subset, "successor_equal_budget")
        nonlower = sum(bool(p["qualified_nonlower"]) for p in subset)
        strict = sum(bool(p["qualified_strict_win"]) for p in subset)
        scales[str(denominator)] = {
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
        "fine_zero_filled_mrr_mean_not_lower": fine_successor["zero_filled_mrr_mean"] >= fine_parent["zero_filled_mrr_mean"],
        "fine_precision_mean_not_lower": fine_successor["precision_mean"] >= fine_parent["precision_mean"],
        "fine_fragmentation_mean_not_higher": fine_successor["fragmentation_mean"] <= fine_parent["fragmentation_mean"],
        "coarse_qualified_total_not_lower": coarse_successor["qualified_total"] >= coarse_parent["qualified_total"],
        "coarse_qualified_nonlower_at_least_6_of_8": scales["128"]["qualified_nonlower_panels"] >= 6,
        "coarse_zero_filled_mrr_mean_not_lower": coarse_successor["zero_filled_mrr_mean"] >= coarse_parent["zero_filled_mrr_mean"],
        "coarse_precision_mean_not_lower": coarse_successor["precision_mean"] >= coarse_parent["precision_mean"],
        "coarse_fragmentation_mean_not_higher": coarse_successor["fragmentation_mean"] <= coarse_parent["fragmentation_mean"],
    }
    verdict = "PASS_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1" if all(gates.values()) else "FAIL_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1"

    out = {
        "schema": "ORBITTRACE_RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_TRUTH",
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_SPARSE_RECOVERY_DEVELOPMENT",
        "verdict": verdict,
        "source_stage1_run_id": 32043362123,
        "source_stage1_artifact_id": 9292356070,
        "source_prelabel_sha256": SOURCE_PRELABEL_SHA256,
        "prelabel_sha256": prelabel_sha,
        "pretruth_sha256": pretruth_sha,
        "ranking_metric_gate": "zero_filled_eligible_query_mrr_panel_mean",
        "historical_conditional_mrr_role": "diagnostic_only",
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
        "retroactive_previous_result_change": False,
    }
    path = args.output / "RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_TRUTH.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "scales": scales, "gates": gates}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
