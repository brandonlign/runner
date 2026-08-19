#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

SUPPORT_PRETRUTH_SHA = "6ae27f985340eaa41870ab4c4f8cd15d6a1cd97e03ef828254f4c24d7896176a"
BASELINE_M2D = {
    "mean_test_auc_macro_f1": 0.35364538749003405,
    "mean_test_macro_f1_at_40": 0.5012446318461822,
    "total_test_recovered_at_40": 58,
    "mean_native_macro_f1": 0.7266723655790133,
}
TUNED_HDB = {
    "mean_test_auc_macro_f1": 0.345475559012312,
    "mean_test_macro_f1_at_40": 0.46086713246967964,
    "total_test_recovered_at_40": 52,
    "mean_native_macro_f1": 0.4762894120871253,
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows-root", type=Path, required=True)
    ap.add_argument("--truth-root", type=Path, required=True)
    ap.add_argument("--support-pretruth", type=Path, required=True)
    ap.add_argument("--ranked-pretruth", type=Path, required=True)
    ap.add_argument("--expected-ranked-sha", required=True)
    ap.add_argument("--baseline-runner", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.support_pretruth) == SUPPORT_PRETRUTH_SHA, "support pretruth changed")
    req(sha(a.ranked_pretruth) == a.expected_ranked_sha, "ranked pretruth SHA mismatch")
    support = json.loads(a.support_pretruth.read_text())
    ranked_pre = json.loads(a.ranked_pretruth.read_text())
    req(ranked_pre.get("scientific_role") == "ZERO_LABEL_EXACT_M2D_RANKING_OF_SEALED_SUPPORT_PRUNED_CANDIDATES", "wrong ranked role")
    req(ranked_pre.get("support_pretruth_sha256") == SUPPORT_PRETRUTH_SHA, "ranked support provenance")
    req(ranked_pre.get("truth_artifact_downloaded") is False and ranked_pre.get("truth_used") is False and ranked_pre.get("shower_labels_accessed") is False, "ranking firewall")
    req(ranked_pre.get("post_result_parameter_search") is False, "ranking post-result search")
    ranked = list(ranked_pre["candidates"])
    req(len(ranked) == int(ranked_pre["candidate_count"]) == 907, "ranked candidate count")
    req([int(r["internal_mass_rank"]) for r in ranked] == list(range(1, 908)), "rank sequence")

    base = load(a.baseline_runner, "spc_sonotaco_truth_base")
    pooled, ids_by_year, universe = base.merge_common(a.rows_root)
    req(len(pooled) == 29246 and universe["common_counts"] == {"2013": 15988, "2014": 13258}, "common universe changed")

    # This is the first truth access in this evaluator.
    truth = base.common_truth(a.truth_root, ids_by_year)
    fam = [{"family_id": r["family_id"], "member_ids": r["event_ids"], "member_count": r["member_count"], "rank": int(r["internal_mass_rank"])} for r in ranked]
    curves = {y: base.curve(fam, truth[y]) for y in base.YEARS}
    agg = base.aggregate(curves)

    size = support["size_summary"]
    bs = size["baseline_support_resolved"]
    rs = size["support_pruned"]
    gates = {
        "auc_not_lower_than_baseline_m2d": agg["mean_test_auc_macro_f1"] >= BASELINE_M2D["mean_test_auc_macro_f1"],
        "k40_f1_not_lower_than_baseline_m2d": agg["mean_test_macro_f1_at_40"] >= BASELINE_M2D["mean_test_macro_f1_at_40"],
        "recovered_at_40_not_lower_than_baseline_m2d": agg["total_test_recovered_at_40"] >= BASELINE_M2D["total_test_recovered_at_40"],
        "native_f1_not_lower_than_baseline_m2d": agg["mean_native_macro_f1"] >= BASELINE_M2D["mean_native_macro_f1"],
        "auc_strictly_beats_tuned_hdbscan": agg["mean_test_auc_macro_f1"] > TUNED_HDB["mean_test_auc_macro_f1"],
        "k40_f1_strictly_beats_tuned_hdbscan": agg["mean_test_macro_f1_at_40"] > TUNED_HDB["mean_test_macro_f1_at_40"],
        "recovered_at_40_at_least_tuned_hdbscan": agg["total_test_recovered_at_40"] >= TUNED_HDB["total_test_recovered_at_40"],
        "mean_member_count_strictly_lower": float(rs["mean_member_count"]) < float(bs["mean_member_count"]),
        "p90_member_count_not_higher": float(rs["p90_member_count"]) <= float(bs["p90_member_count"]),
        "max_member_count_strictly_lower": int(rs["max_member_count"]) < int(bs["max_member_count"]),
        "support_pruning_active": int(support["cut_summary"]["discarded_subsupport_event_count"]) > 0,
        "ranking_sealed_before_truth": True,
        "no_post_result_parameter_search": True,
    }
    verdict = "PASS_M2D_SUPPORT_PRUNED_CUT_V1_SONOTACO_TRANSFER" if all(gates.values()) else "FAIL_M2D_SUPPORT_PRUNED_CUT_V1_SONOTACO_TRANSFER"
    result = {
        "schema": "ORBITTRACE_M2D_SUPPORT_PRUNED_CUT_V1_SONOTACO_RESULT",
        "scientific_role": "NO_TUNING_SONOTACO_TRANSFER_ON_EXACT_SYMMETRIC_COMMON_UNIVERSE",
        "verdict": verdict,
        "support_pretruth_sha256": SUPPORT_PRETRUTH_SHA,
        "ranked_pretruth_sha256": sha(a.ranked_pretruth),
        "candidate_count": len(ranked),
        "aggregate": agg,
        "curves": {str(y): curves[y] for y in base.YEARS},
        "baseline_m2d": BASELINE_M2D,
        "tuned_hdbscan": TUNED_HDB,
        "size_summary": size,
        "gates": gates,
        "ranked_pretruth_reexecuted": False,
        "method_changed_after_truth": False,
        "post_result_parameter_search": False,
    }
    out = a.output / "M2D_SUPPORT_PRUNED_CUT_V1_SONOTACO_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "aggregate": agg, "size_summary": size, "gates": gates, "result_sha256": sha(out)}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
