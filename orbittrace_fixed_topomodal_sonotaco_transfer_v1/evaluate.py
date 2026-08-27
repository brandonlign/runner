#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

EXPECTED_COMMON = {2013: 15988, 2014: 13258}
EXPECTED_POOLED = 29246
EXPECTED_HDB_AUC = 0.345475559012312
EXPECTED_HDB_K40 = 0.46086713246967964
EXPECTED_HDB_REC40 = 52
EXPECTED_HDB_NATIVE = 0.4762894120871253


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


def support_event(row: dict[str, Any]) -> dict[str, Any]:
    out = {
        "id": str(row["id"]),
        "year": int(row["year"]),
        "sol": float(row["sol"]),
        "lon": float(row["sun_lon"]),
        "lat": float(row["ecl_lat"]),
        "vg": float(row["vg"]),
    }
    req(all(math.isfinite(float(out[k])) for k in ("sol", "lon", "lat", "vg")), f"nonfinite row {out['id']}")
    req(out["vg"] > 0.0, f"nonpositive vg {out['id']}")
    return out


def as_benchmark_families(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rank, row in enumerate(rows, 1):
        ids = sorted(map(str, row["event_ids"]))
        req(ids and len(ids) == int(row["member_count"]), "candidate membership mismatch")
        out.append({
            "family_id": str(row["family_id"]),
            "member_ids": ids,
            "member_count": len(ids),
            "primary_score": float(row["modal_contrast"]),
            "secondary_score": 0.0,
            "rank": rank,
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-root", type=Path, required=True)
    ap.add_argument("--truth-root", type=Path, required=True)
    ap.add_argument("--benchmark-module", type=Path, required=True)
    ap.add_argument("--benchmark-result", type=Path, required=True)
    ap.add_argument("--support-source", type=Path, required=True)
    ap.add_argument("--structural-source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    benchmark = load_module(a.benchmark_module, "topomodal_sonotaco_benchmark")
    support = load_module(a.support_source, "topomodal_sonotaco_support")
    structural = load_module(a.structural_source, "topomodal_sonotaco_structural")

    req(tuple(benchmark.YEARS) == (2013, 2014), "benchmark years changed")
    req(tuple(benchmark.BUDGETS) == (10, 20, 30, 40), "benchmark budgets changed")
    req(float(support.RADIUS) == 1.0 and int(support.MIN_SUPPORT) == 4, "support method constants changed")
    req(float(structural.RADIUS) == 1.0 and int(structural.MIN_SUPPORT) == 4, "structural constants changed")
    req(math.isclose(float(structural.H_SOL), 2.0 * math.sin(math.radians(5.0) / 2.0), rel_tol=0, abs_tol=1e-15), "solar scale changed")
    req(math.isclose(float(structural.H_RAD), 2.0 * math.sin(math.radians(4.0) / 2.0), rel_tol=0, abs_tol=1e-15), "radiant scale changed")
    req(math.isclose(float(structural.H_LOGV), math.log(1.1), rel_tol=0, abs_tol=1e-15), "speed scale changed")

    baseline = json.loads(a.benchmark_result.read_text())
    req(baseline["schema"] == "ORBITTRACE_SYMMETRIC_TUNED_LITERATURE_BENCHMARK_V2", "wrong benchmark baseline")
    req(baseline["winner_by_prespecified_primary_metric"] == "hdbscan", "baseline winner changed")
    hdb = baseline["aggregate"]["hdbscan"]
    req(float(hdb["mean_test_auc_macro_f1"]) == EXPECTED_HDB_AUC, "HDB AUC baseline changed")
    req(float(hdb["mean_test_macro_f1_at_40"]) == EXPECTED_HDB_K40, "HDB K40 baseline changed")
    req(int(hdb["total_test_recovered_at_40"]) == EXPECTED_HDB_REC40, "HDB K40 recovery baseline changed")
    req(float(hdb["mean_native_macro_f1"]) == EXPECTED_HDB_NATIVE, "HDB native baseline changed")

    pooled, ids_by_year, universe = benchmark.merge_common_rows(a.rows_root)
    req({int(y): int(universe["common_counts"][str(y)]) for y in (2013, 2014)} == EXPECTED_COMMON, "common event counts changed")
    req(len(pooled) == EXPECTED_POOLED, f"pooled count changed: {len(pooled)}")
    events = [support_event(r) for r in pooled]
    req(len({e["id"] for e in events}) == EXPECTED_POOLED, "duplicate pooled IDs")

    print(f"[fixed-transfer] generating support-resolved TopoModal catalogue on n={len(events)}", flush=True)
    support_rows, structural_summary = support.support_resolved_cut(structural, events)
    families = as_benchmark_families(support_rows)
    req(bool(families), "transferred method produced no candidates")
    req(all(set(families[i]["member_ids"]).isdisjoint(families[j]["member_ids"])
            for i in range(len(families)) for j in range(i + 1, len(families))), "transferred candidates overlap")
    candidate_manifest = {
        "candidate_count": len(families),
        "structural_summary": structural_summary,
        "candidate_rows": [
            {"rank": int(f["rank"]), "family_id": f["family_id"], "member_count": int(f["member_count"]), "modal_contrast": float(f["primary_score"])}
            for f in families
        ],
        "truth_used": False,
    }
    (a.output / "FIXED_TOPOMODAL_SONOTACO_PRETRUTH.json").write_text(json.dumps(candidate_manifest, indent=2, sort_keys=True, allow_nan=False) + "\n")

    truth = benchmark.common_truth(a.truth_root, ids_by_year)
    annual = {str(y): benchmark.curve(families, truth[y]) for y in (2013, 2014)}
    aggregate = {
        "mean_test_auc_macro_f1": float(np.mean([annual[str(y)]["auc_macro_f1"] for y in (2013, 2014)])),
        "mean_test_macro_f1_at_40": float(np.mean([annual[str(y)]["budgets"]["40"]["macro_f1"] for y in (2013, 2014)])),
        "total_test_recovered_at_40": int(sum(annual[str(y)]["budgets"]["40"]["recovered_f1_gt_0_5"] for y in (2013, 2014))),
        "mean_native_macro_f1": float(np.mean([annual[str(y)]["native"]["macro_f1"] for y in (2013, 2014)])),
    }
    all_aggregate = {k: dict(v) for k, v in baseline["aggregate"].items()}
    all_aggregate["fixed_support_resolved_topomodal"] = aggregate
    ordered = sorted(all_aggregate, key=lambda m: (float(all_aggregate[m]["mean_test_auc_macro_f1"]), int(all_aggregate[m]["total_test_recovered_at_40"]), float(all_aggregate[m]["mean_test_macro_f1_at_40"])), reverse=True)
    winner = ordered[0]
    passed = winner == "fixed_support_resolved_topomodal" and aggregate["mean_test_auc_macro_f1"] > EXPECTED_HDB_AUC
    verdict = "PASS_FIXED_TOPOMODAL_SONOTACO_TRANSFER_V1" if passed else "FAIL_FIXED_TOPOMODAL_SONOTACO_TRANSFER_V1"
    result = {
        "schema": "ORBITTRACE_FIXED_TOPOMODAL_SONOTACO_TRANSFER_V1",
        "scientific_role": "FIXED_GMN_DEVELOPED_METHOD_TO_SONOTACO_COMMON_UNIVERSE_TRANSFER",
        "verdict": verdict,
        "method": {"sonotaco_tuning": False, "radius": 1.0, "minimum_support": 4, "ranking": "modal_contrast_desc_then_frozen_membership_hash", "candidate_count": len(families)},
        "universe": universe,
        "annual": annual,
        "aggregate": aggregate,
        "existing_symmetric_v2_aggregate": baseline["aggregate"],
        "four_method_aggregate": all_aggregate,
        "ranking": ordered,
        "winner_by_existing_primary_metric": winner,
        "strict_auc_delta_vs_tuned_hdbscan": float(aggregate["mean_test_auc_macro_f1"] - EXPECTED_HDB_AUC),
        "sonotaco_labels_used_for_method_selection": False,
        "post_result_parameter_search": False,
    }
    (a.output / "FIXED_TOPOMODAL_SONOTACO_TRANSFER_V1.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "aggregate": aggregate, "ranking": ordered, "annual": annual}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
