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
STRUCTURAL_RESULT_SHA256 = "e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497"
SALT = "ORBITTRACE_SCALE_STRESS_V1|"
COARSE_D = 128
FINE_D = 1024
BUCKETS = (0, 1, 2, 3)


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def event_hash_u64(eid: str) -> int:
    return int.from_bytes(hashlib.sha256((SALT + str(eid)).encode()).digest()[:8], "big")


def selected_indices(hashes: np.ndarray, denominator: int, bucket: int) -> np.ndarray:
    return np.flatnonzero((hashes % np.uint64(denominator)) == np.uint64(bucket))


def universe_hash(ids: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def compact_metrics(m: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in m.items() if k != "first_rank_by_label"}


def aggregate(panels: list[dict[str, Any]], key: str) -> dict[str, Any]:
    vals = [p[key] for p in panels]
    return {
        "qualified_total": int(sum(int(v["qualified_matches"]) for v in vals)),
        "mrr_mean": float(np.mean([float(v["mrr"]) for v in vals])) if vals else 0.0,
        "precision_mean": float(np.mean([float(v["top100_dominant_precision"]) for v in vals])) if vals else 0.0,
        "fragmentation_mean": float(np.mean([float(v["fragmentation_median_top500"]) for v in vals])) if vals else 0.0,
        "recovered_at_25_total": int(sum(int(v["recovered_at_25"]) for v in vals)),
        "recovered_at_50_total": int(sum(int(v["recovered_at_50"]) for v in vals)),
        "recovered_at_100_total": int(sum(int(v["recovered_at_100"]) for v in vals)),
        "recovered_at_500_total": int(sum(int(v["recovered_at_500"]) for v in vals)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prelabel", type=Path, required=True)
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

    req(sha256(a.quality_source) == QUALITY_SHA256, "frozen GMN runtime utility changed")
    req(sha256(a.v8_result_json) == V8_RESULT_SHA256, "frozen GMN support artifact changed")
    prelabel_sha = sha256(a.prelabel)
    pre = json.loads(a.prelabel.read_text())
    req(pre["schema"] == "ORBITTRACE_TOPOMODAL_DEATH_SUPPORT_V1_PRELABEL", "wrong prelabel schema")
    req(pre["scientific_role"] == "PRELABEL_TOPOMODAL_DEATH_SUPPORT_V1", "wrong prelabel role")
    req(pre["structural_source_run_id"] == 31955621864 and pre["structural_source_artifact_id"] == 9265889512, "wrong structural provenance")
    req(pre["structural_result_sha256"] == STRUCTURAL_RESULT_SHA256, "wrong structural result hash")
    cfg = pre["configuration"]
    req(cfg["candidate_semantics"] == "one_dying_child_support_per_finite_tomato_persistence_feature", "candidate semantics changed")
    req(cfg["infinite_root_features_reported"] is False, "root features added after freeze")
    req(cfg["survival_rule"] == "larger_active_mode_peak_then_lexicographically_smaller_mode_key", "survival rule changed")
    req(cfg["ranking"] == "finite_persistence_desc_then_family_hash_asc", "ranking changed")
    req(cfg["equal_budget"] == "min(successor_candidate_count,recurrent_candidate_count)_both_methods_truncated", "candidate budget changed")
    req(pre["blind_exclusion"] == list(BLIND), "blind exclusion changed")
    req(pre["target_information_access"] is False and pre["target_region_events_accessed"] is False, "target firewall flag changed")
    req(pre["shower_truth_used"] is False, "prelabel claims truth use")
    req(len(pre["subsets"]) == 8, "wrong subset count")
    subset_map = {(int(r["denominator"]), int(r["bucket"])): r for r in pre["subsets"]}
    req(set(subset_map) == {(d, b) for d in (COARSE_D, FINE_D) for b in BUCKETS}, "wrong prelabel panel set")
    all_k_positive = True
    for row in pre["subsets"]:
        successor = list(row["death_support_candidates"])
        recurrent = list(row["recurrent_candidates"])
        K = min(len(successor), len(recurrent))
        req(int(row["equal_budget_k"]) == K, "stored K changed")
        all_k_positive = all_k_positive and K >= 1
        req([int(x["rank"]) for x in successor] == list(range(1, len(successor) + 1)), "successor rank discontinuity")
        req([int(x["rank"]) for x in recurrent] == list(range(1, len(recurrent) + 1)), "recurrent rank discontinuity")
        expected = sorted(successor, key=lambda r: (-float(r["persistence"]), str(r["family_hash"])))
        req([str(x["family_id"]) for x in expected] == [str(x["family_id"]) for x in successor], "successor prelabel rank order invalid")
        req(row["death_support_summary"]["roots_reported_as_candidates"] is False, "root candidate survived prelabel")
        req(float(row["death_support_summary"]["diagram_reconstruction_max_abs_error"]) <= 1e-12, "persistence reconstruction tolerance failed")

    parent_runner = load_module(a.parent_runner, "topomodal_death_eval_parent")
    req(tuple(parent_runner.YEARS) == YEARS and tuple(parent_runner.BLIND) == BLIND, "parent constants changed")
    req(int(parent_runner.MIN_CLUSTER_SIZE) == 10 and int(parent_runner.MIN_SAMPLES) == 10, "parent support changed")

    qmod = load_module(a.quality_source, "topomodal_death_eval_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-topomodal-death-support-v1-target-excluded-evaluator"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(isinstance(hidden_sealed, dict), "hidden truth payload has unexpected type")
    req(sorted(scan) == list(YEARS), f"wrong GMN years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")

    events: list[dict[str, Any]] = []
    for year in YEARS:
        raw = list(scan[year])
        norm = [parent_runner.normalize_event(row, year) for row in raw]
        req(len(norm) == len(raw), f"normalization count changed {year}")
        events.extend(norm)
    req(len(events) == 738682, f"pooled target-excluded event count changed: {len(events)}")
    req(len({str(e["id"]) for e in events}) == len(events), "duplicate event IDs")
    req(all(not (BLIND[0] <= float(e["sol"]) <= BLIND[1]) for e in events), "protected row survived parser")
    ids_full = [str(e["id"]) for e in events]
    years_full = np.asarray([int(e["year"]) for e in events], dtype=np.int64)
    hashes = np.asarray([event_hash_u64(eid) for eid in ids_full], dtype=np.uint64)

    panels: list[dict[str, Any]] = []
    for denominator in (COARSE_D, FINE_D):
        for bucket in BUCKETS:
            frozen = subset_map[(denominator, bucket)]
            ix = selected_indices(hashes, denominator, bucket)
            ids = [ids_full[int(i)] for i in ix]
            years = np.asarray(years_full[ix], dtype=np.int64)
            req(len(ids) == int(frozen["events_total"]), f"event count mismatch d={denominator} b={bucket}")
            req(universe_hash(ids) == str(frozen["event_universe_sha256"]), f"event universe hash mismatch d={denominator} b={bucket}")
            req({str(y): int(np.sum(years == y)) for y in YEARS} == {str(k): int(v) for k, v in frozen["events_by_year"].items()}, f"annual count mismatch d={denominator} b={bucket}")

            successor = list(frozen["death_support_candidates"])
            recurrent = list(frozen["recurrent_candidates"])
            K = int(frozen["equal_budget_k"])
            if K < 1:
                continue
            successor_equal = successor[:K]
            recurrent_equal = recurrent[:K]
            req(len(successor_equal) == len(recurrent_equal) == K, "equal budget truncation failed")
            for year in YEARS:
                annual_ids = {ids[int(i)] for i in np.flatnonzero(years == year)}
                parent_m = compact_metrics(parent_runner.metrics(recurrent_equal, hidden_sealed, annual_ids))
                succ_m = compact_metrics(parent_runner.metrics(successor_equal, hidden_sealed, annual_ids))
                parent_full = compact_metrics(parent_runner.metrics(recurrent, hidden_sealed, annual_ids))
                succ_full = compact_metrics(parent_runner.metrics(successor, hidden_sealed, annual_ids))
                panels.append(
                    {
                        "denominator": int(denominator),
                        "bucket": int(bucket),
                        "year": int(year),
                        "equal_budget_k": int(K),
                        "parent_equal_budget": parent_m,
                        "death_support_equal_budget": succ_m,
                        "parent_full_diagnostic": parent_full,
                        "death_support_full_diagnostic": succ_full,
                        "qualified_nonlower": int(succ_m["qualified_matches"]) >= int(parent_m["qualified_matches"]),
                        "qualified_strict_win": int(succ_m["qualified_matches"]) > int(parent_m["qualified_matches"]),
                    }
                )

    # K<1 is a binding scientific failure; preserve whatever panels could be evaluated.
    scale_results: dict[str, Any] = {}
    for denominator in (COARSE_D, FINE_D):
        ps = [p for p in panels if int(p["denominator"]) == denominator]
        if len(ps) != 8:
            scale_results[str(denominator)] = {"panel_count": len(ps), "all_k_positive": False}
            continue
        parent_agg = aggregate(ps, "parent_equal_budget")
        succ_agg = aggregate(ps, "death_support_equal_budget")
        nonlower = sum(bool(p["qualified_nonlower"]) for p in ps)
        wins = sum(bool(p["qualified_strict_win"]) for p in ps)
        scale_results[str(denominator)] = {
            "panel_count": 8,
            "all_k_positive": True,
            "parent_equal_budget": parent_agg,
            "death_support_equal_budget": succ_agg,
            "qualified_nonlower_panels": int(nonlower),
            "qualified_strict_win_panels": int(wins),
            "qualified_loss_panels": int(8 - nonlower),
        }

    if all_k_positive and all(scale_results[str(d)].get("panel_count") == 8 for d in (COARSE_D, FINE_D)):
        fine_p = scale_results[str(FINE_D)]["parent_equal_budget"]
        fine_s = scale_results[str(FINE_D)]["death_support_equal_budget"]
        coarse_p = scale_results[str(COARSE_D)]["parent_equal_budget"]
        coarse_s = scale_results[str(COARSE_D)]["death_support_equal_budget"]
        gates = {
            "fine_qualified_total_strictly_greater": int(fine_s["qualified_total"]) > int(fine_p["qualified_total"]),
            "fine_qualified_nonlower_at_least_6_of_8": int(scale_results[str(FINE_D)]["qualified_nonlower_panels"]) >= 6,
            "fine_mrr_mean_not_lower": float(fine_s["mrr_mean"]) >= float(fine_p["mrr_mean"]),
            "fine_precision_mean_not_lower": float(fine_s["precision_mean"]) >= float(fine_p["precision_mean"]),
            "fine_fragmentation_mean_not_higher": float(fine_s["fragmentation_mean"]) <= float(fine_p["fragmentation_mean"]),
            "coarse_qualified_total_not_lower": int(coarse_s["qualified_total"]) >= int(coarse_p["qualified_total"]),
            "coarse_qualified_nonlower_at_least_6_of_8": int(scale_results[str(COARSE_D)]["qualified_nonlower_panels"]) >= 6,
            "coarse_mrr_mean_not_lower": float(coarse_s["mrr_mean"]) >= float(coarse_p["mrr_mean"]),
            "coarse_precision_mean_not_lower": float(coarse_s["precision_mean"]) >= float(coarse_p["precision_mean"]),
            "coarse_fragmentation_mean_not_higher": float(coarse_s["fragmentation_mean"]) <= float(coarse_p["fragmentation_mean"]),
        }
    else:
        gates = {
            "fine_qualified_total_strictly_greater": False,
            "fine_qualified_nonlower_at_least_6_of_8": False,
            "fine_mrr_mean_not_lower": False,
            "fine_precision_mean_not_lower": False,
            "fine_fragmentation_mean_not_higher": False,
            "coarse_qualified_total_not_lower": False,
            "coarse_qualified_nonlower_at_least_6_of_8": False,
            "coarse_mrr_mean_not_lower": False,
            "coarse_precision_mean_not_lower": False,
            "coarse_fragmentation_mean_not_higher": False,
        }
    verdict = "PASS_TOPOMODAL_DEATH_SUPPORT_V1" if all_k_positive and all(gates.values()) else "FAIL_TOPOMODAL_DEATH_SUPPORT_V1"
    result = {
        "schema": "ORBITTRACE_TOPOMODAL_DEATH_SUPPORT_V1",
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_SPARSE_RECOVERY_DEVELOPMENT",
        "verdict": verdict,
        "prelabel_sha256": prelabel_sha,
        "all_subsets_have_positive_equal_budget": bool(all_k_positive),
        "structural_source_run_id": 31955621864,
        "structural_source_artifact_id": 9265889512,
        "structural_result_sha256": STRUCTURAL_RESULT_SHA256,
        "panels": panels,
        "scale_aggregates": scale_results,
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
    out = a.output / "TOPOMODAL_DEATH_SUPPORT_V1.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "prelabel_sha256": prelabel_sha, "all_k_positive": all_k_positive, "scale_aggregates": scale_results, "gates": gates}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
