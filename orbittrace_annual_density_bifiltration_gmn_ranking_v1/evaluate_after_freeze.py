#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

YEARS = (2022, 2023)
DENOMINATORS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
BLIND = (20.0, 55.0)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
SPARSE_SOURCE_BLOB = "752df8212ce601227f6e9170b0fe994ba06b515d"
PARENT_SOURCE_BLOB = "fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c"
QUALITY_SHA256 = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA256 = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"
BIF_PRETRUTH_SHA = "63519bbd8a95b0bd5db0d0f5fdccbdb67b3f1dac0158529bb808f4c798170b0b"
BIF_STRUCTURAL_SHA = "d930e9a8221cbe6b56026618f513f3f8b84143f2f43deb0a5b1ccc1ca7e4bbe7"
ORIGINAL_PRELABEL_SHA256 = "95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    import subprocess
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dump(path: Path, obj: Any) -> str:
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def adapt_bifiltration_rows_for_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add the identity-only field required by the frozen recurrent metrics adapter.

    The parent evaluator's metrics() copies family_id into an annual candidate,
    while truth() evaluates only event_ids. The frozen bifiltration prelabel
    stores family_hash rather than family_id, so using that immutable membership
    hash as family_id changes no membership, ordering, budget, or truth metric.
    """
    adapted: list[dict[str, Any]] = []
    for row in rows:
        req("family_id" not in row, "unexpected family_id already present in frozen bifiltration row")
        req("family_hash" in row and "event_ids" in row, "bifiltration row missing frozen identity/membership")
        out = dict(row)
        out["family_id"] = str(row["family_hash"])
        req(out["event_ids"] == row["event_ids"], "metrics adapter changed membership")
        adapted.append(out)
    req(len(adapted) == len(rows), "metrics adapter changed candidate count")
    return adapted


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prelabel", type=Path, required=True)
    ap.add_argument("--sparse-source", type=Path, required=True)
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

    req(git_blob(a.sparse_source) == SPARSE_SOURCE_BLOB, "sparse evaluator source changed")
    req(git_blob(a.parent_runner) == PARENT_SOURCE_BLOB, "recurrent wrapper source changed")
    req(sha256(a.quality_source) == QUALITY_SHA256, "GMN utility changed")
    req(sha256(a.v8_result_json) == V8_SHA256, "GMN support artifact changed")

    prelabel_sha = sha256(a.prelabel)
    req(prelabel_sha == ORIGINAL_PRELABEL_SHA256, "endpoint prelabel changed from successful pretruth run 32037435314")
    pre = json.loads(a.prelabel.read_text())
    req(pre.get("schema") == "ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_GMN_RANKING_V1_PRELABEL", "wrong prelabel schema")
    req(pre.get("scientific_role") == "PRELABEL_TARGET_EXCLUDED_GMN_RANKING_RECOVERY", "wrong prelabel role")
    req(pre.get("frozen_bif_pretruth_sha256") == BIF_PRETRUTH_SHA, "wrong bif candidate source")
    req(pre.get("frozen_bif_structural_sha256") == BIF_STRUCTURAL_SHA, "wrong bif structural source")
    req(pre.get("shower_truth_used") is False, "prelabel truth flag")
    req(pre.get("target_information_access") is False and pre.get("target_region_events_accessed") is False, "prelabel firewall")
    req(pre.get("sonotaco_2013_2014_access") is False, "SonotaCo entered prelabel")
    subsets = {(int(s["denominator"]), int(s["bucket"])): s for s in pre.get("subsets", [])}
    req(set(subsets) == {(d, b) for d in DENOMINATORS for b in BUCKETS}, "wrong prelabel subset set")

    sparse = load_module(a.sparse_source, "bifrank_eval_sparse")
    parent = load_module(a.parent_runner, "bifrank_eval_parent")
    req(tuple(parent.YEARS) == YEARS and tuple(parent.BLIND) == BLIND, "parent constants changed")

    qmod = load_module(a.quality_source, "bifrank_eval_gmn_utility")
    qmod.v1.mult.YEARS = YEARS
    qmod.v1.mult.MONTH_KEYS = MONTH_KEYS
    qmod.v1.mult.TOP_K = 100
    runtime = qmod.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-annual-density-bifiltration-gmn-ranking-v1-target-excluded-evaluation"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "target firewall changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan, _cal, hidden_sealed, sources = support.parse_catalogue(base)
    req(sorted(scan) == list(YEARS), f"wrong GMN years: {sorted(scan)}")
    req([x["key"] for x in sources] == list(MONTH_KEYS), "GMN source list changed")
    req(isinstance(hidden_sealed, dict), "sealed GMN label mapping unavailable")

    # Candidate construction and order are already immutable in the downloaded prelabel artifact.
    panel_results: list[dict[str, Any]] = []
    for denominator in DENOMINATORS:
        for bucket in BUCKETS:
            s = subsets[(denominator, bucket)]
            recurrent = list(s["recurrent_candidates"])
            bif_all = list(s["bifiltration_candidates"])
            bif_metric_all = adapt_bifiltration_rows_for_metrics(bif_all)
            k = int(s["equal_budget_k"])
            req(len(recurrent) == k, "recurrent K changed")
            req(len(bif_all) >= k, "bif candidate list shorter than K")
            bif_equal = bif_metric_all[:k]
            for year in YEARS:
                annual_ids = set(str(x) for x in s["annual_event_ids"][str(year)])
                req(annual_ids, f"empty annual universe d={denominator} b={bucket} y={year}")
                req(all(eid in hidden_sealed for eid in annual_ids), "annual event missing label mapping")
                parent_m = sparse.compact_metrics(parent.metrics(recurrent, hidden_sealed, annual_ids))
                succ_m = sparse.compact_metrics(parent.metrics(bif_equal, hidden_sealed, annual_ids))
                full_m = sparse.compact_metrics(parent.metrics(bif_metric_all, hidden_sealed, annual_ids))
                panel_results.append({
                    "denominator": denominator,
                    "bucket": bucket,
                    "year": year,
                    "equal_budget_k": k,
                    "parent": parent_m,
                    "bifiltration_equal_budget": succ_m,
                    "bifiltration_full_diagnostic": full_m,
                    "qualified_nonlower": int(succ_m["qualified_matches"]) >= int(parent_m["qualified_matches"]),
                    "qualified_strict_win": int(succ_m["qualified_matches"]) > int(parent_m["qualified_matches"]),
                })

    req(len(panel_results) == 16, "wrong panel count")
    scale_results: dict[str, Any] = {}
    for denominator in DENOMINATORS:
        panels = [p for p in panel_results if int(p["denominator"]) == denominator]
        req(len(panels) == 8, f"wrong annual panel count d={denominator}")
        parent_agg = sparse.aggregate(panels, "parent")
        succ_agg = sparse.aggregate(panels, "bifiltration_equal_budget")
        nonlower = sum(bool(p["qualified_nonlower"]) for p in panels)
        wins = sum(bool(p["qualified_strict_win"]) for p in panels)
        scale_results[str(denominator)] = {
            "parent": parent_agg,
            "bifiltration_equal_budget": succ_agg,
            "qualified_nonlower_panels": nonlower,
            "qualified_strict_win_panels": wins,
            "qualified_loss_panels": 8 - nonlower,
        }

    fine_p = scale_results["1024"]["parent"]
    fine_s = scale_results["1024"]["bifiltration_equal_budget"]
    coarse_p = scale_results["128"]["parent"]
    coarse_s = scale_results["128"]["bifiltration_equal_budget"]
    gates = {
        "fine_qualified_total_strictly_greater": int(fine_s["qualified_total"]) > int(fine_p["qualified_total"]),
        "fine_qualified_nonlower_at_least_6_of_8": int(scale_results["1024"]["qualified_nonlower_panels"]) >= 6,
        "fine_mrr_mean_not_lower": float(fine_s["mrr_mean"]) >= float(fine_p["mrr_mean"]),
        "fine_precision_mean_not_lower": float(fine_s["precision_mean"]) >= float(fine_p["precision_mean"]),
        "fine_fragmentation_mean_not_higher": float(fine_s["fragmentation_mean"]) <= float(fine_p["fragmentation_mean"]),
        "coarse_qualified_total_not_lower": int(coarse_s["qualified_total"]) >= int(coarse_p["qualified_total"]),
        "coarse_qualified_nonlower_at_least_6_of_8": int(scale_results["128"]["qualified_nonlower_panels"]) >= 6,
        "coarse_mrr_mean_not_lower": float(coarse_s["mrr_mean"]) >= float(coarse_p["mrr_mean"]),
        "coarse_precision_mean_not_lower": float(coarse_s["precision_mean"]) >= float(coarse_p["precision_mean"]),
        "coarse_fragmentation_mean_not_higher": float(coarse_s["fragmentation_mean"]) <= float(coarse_p["fragmentation_mean"]),
    }
    verdict = "PASS_ANNUAL_DENSITY_BIFILTRATION_V1_GMN_RANKING_RECOVERY" if all(gates.values()) else "FAIL_ANNUAL_DENSITY_BIFILTRATION_V1_GMN_RANKING_RECOVERY"
    result = {
        "schema": "ORBITTRACE_ANNUAL_DENSITY_BIFILTRATION_V1_GMN_RANKING_RECOVERY",
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_SPARSE_RANKING_RECOVERY_DEVELOPMENT",
        "verdict": verdict,
        "prelabel_sha256": prelabel_sha,
        "frozen_bif_pretruth_sha256": BIF_PRETRUTH_SHA,
        "frozen_bif_structural_sha256": BIF_STRUCTURAL_SHA,
        "panels": panel_results,
        "scale_aggregates": scale_results,
        "gates": gates,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "asfn_efn_event_level_access": False,
        "amos_scientific_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "post_result_parameter_search": False,
        "engineering_repair": {
            "prior_run": 32037435314,
            "prior_failure": "KeyError: family_id before result serialization",
            "adapter": "family_id_equals_frozen_family_hash",
            "scientific_candidate_change": False,
        },
    }
    result_sha = dump(a.output / "BIFILTRATION_GMN_RANKING_V1_RESULT.json", result)
    print(json.dumps({"verdict": verdict, "prelabel_sha256": prelabel_sha, "result_sha256": result_sha, "scale_aggregates": scale_results, "gates": gates}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
