#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

PRETRUTH_SHA = "6ae27f985340eaa41870ab4c4f8cd15d6a1cd97e03ef828254f4c24d7896176a"
CPP_SHA = "4eef6f1b70b5baee5d1983d2480c02d73569b12af868ec23bbb6009d6ca1fa37"
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
    ap.add_argument("--structural-source", type=Path, required=True)
    ap.add_argument("--pretruth", type=Path, required=True)
    ap.add_argument("--baseline-runner", type=Path, required=True)
    ap.add_argument("--exact-cpp", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)

    req(sha(a.pretruth) == PRETRUTH_SHA, "sealed SonotaCo pretruth changed")
    req(sha(a.exact_cpp) == CPP_SHA, "exact M2D scorer changed")
    pre = json.loads(a.pretruth.read_text())
    req(pre.get("scientific_role") == "ZERO_LABEL_SUPPORT_PRUNED_SONOTACO_COMMON_UNIVERSE_PRETRUTH", "wrong pretruth role")
    req(pre.get("truth_used") is False and pre.get("shower_labels_accessed") is False and pre.get("orbittrace_member_ids_accessed") is False, "pretruth firewall")
    req(pre.get("post_result_parameter_search") is False and pre.get("configuration", {}).get("new_tuned_parameters") == [], "post-result tuning")
    candidates = list(pre["candidates"])
    req(len(candidates) == int(pre["candidate_count"]) == 907, "candidate count changed")

    base = load(a.baseline_runner, "support_pruned_sonotaco_baseline_exact")
    structural = load(a.structural_source, "support_pruned_sonotaco_structural_exact")
    req(float(structural.RADIUS) == 1.0 and int(structural.MIN_SUPPORT) == 4, "structural constants changed")

    pooled, ids_by_year, universe = base.merge_common(a.rows_root)
    events = sorted([base.support_event(r) for r in pooled], key=lambda e: e["id"])
    req(len(events) == 29246 and universe["common_counts"] == {"2013": 15988, "2014": 13258}, "common universe changed")

    with tempfile.TemporaryDirectory() as td_s:
        td = Path(td_s)
        binp, scoresp, exe = td / "input.bin", td / "scores.tsv", td / "exact"
        raw, d13, d14, cand_of, idx = base.build_binary(events, candidates, structural, binp)
        subprocess.run(["g++", "-O3", "-std=c++17", str(a.exact_cpp), "-o", str(exe)], check=True)
        subprocess.run([str(exe), str(binp), str(scoresp)], check=True)
        scores = base.parse_scores(scoresp)
        req(len(scores) == len(candidates), "missing accelerator scores")
        n = len(candidates)
        audit_ix = sorted(set([0, n // 4, n // 2, (3 * n) // 4, n - 1]))
        audits = []
        for ci in audit_ix:
            brute = base.brute_candidate(ci, candidates, raw, d13, d14, cand_of, idx)
            exact = scores[ci]
            req(abs(brute - exact) <= 1e-18, f"accelerator audit mismatch {ci}: {brute} {exact}")
            audits.append({"candidate": ci, "brute": brute, "accelerated": exact, "abs_diff": abs(brute - exact)})

    ranked = []
    for ci, c in enumerate(candidates):
        row = dict(c)
        row["internal_2d_mass"] = float(scores[ci])
        ranked.append(row)
    ranked.sort(key=lambda r: (-float(r["internal_2d_mass"]), -float(r["modal_contrast"]), str(r["family_hash"])))
    for i, row in enumerate(ranked, 1):
        row["internal_mass_rank"] = i

    ranked_pretruth = {
        "schema": "ORBITTRACE_M2D_SUPPORT_PRUNED_CUT_V1_SONOTACO_RANKED_PRETRUTH",
        "scientific_role": "ZERO_LABEL_EXACT_M2D_RANKING_OF_SEALED_SUPPORT_PRUNED_CANDIDATES",
        "universe": universe,
        "candidate_count": len(ranked),
        "candidates": ranked,
        "accelerator_audit": audits,
        "support_pretruth_sha256": PRETRUTH_SHA,
        "exact_cpp_sha256": CPP_SHA,
        "truth_used": False,
        "shower_labels_accessed": False,
        "post_result_parameter_search": False,
    }
    rp = a.output / "M2D_SUPPORT_PRUNED_CUT_V1_SONOTACO_RANKED_PRETRUTH.json"
    rp.write_text(json.dumps(ranked_pretruth, indent=2, sort_keys=True, allow_nan=False) + "\n")
    ranked_sha = sha(rp)

    # Truth is opened only after the complete M2D ranking above is written and hashed.
    truth = base.common_truth(a.truth_root, ids_by_year)
    fam = [{"family_id": r["family_id"], "member_ids": r["event_ids"], "member_count": r["member_count"], "rank": int(r["internal_mass_rank"])} for r in ranked]
    curves = {y: base.curve(fam, truth[y]) for y in base.YEARS}
    agg = base.aggregate(curves)

    size = pre["size_summary"]
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
        "support_pruning_active": int(pre["cut_summary"]["discarded_subsupport_event_count"]) > 0,
        "ranking_frozen_before_truth": True,
        "no_post_result_parameter_search": True,
    }
    verdict = "PASS_M2D_SUPPORT_PRUNED_CUT_V1_SONOTACO_TRANSFER" if all(gates.values()) else "FAIL_M2D_SUPPORT_PRUNED_CUT_V1_SONOTACO_TRANSFER"
    result = {
        "schema": "ORBITTRACE_M2D_SUPPORT_PRUNED_CUT_V1_SONOTACO_RESULT",
        "scientific_role": "NO_TUNING_SONOTACO_TRANSFER_ON_EXACT_SYMMETRIC_COMMON_UNIVERSE",
        "verdict": verdict,
        "support_pretruth_sha256": PRETRUTH_SHA,
        "ranked_pretruth_sha256": ranked_sha,
        "candidate_count": len(ranked),
        "aggregate": agg,
        "curves": {str(y): curves[y] for y in base.YEARS},
        "baseline_m2d": BASELINE_M2D,
        "tuned_hdbscan": TUNED_HDB,
        "size_summary": size,
        "gates": gates,
        "truth_opened_only_after_ranked_pretruth_write": True,
        "method_changed_after_truth": False,
        "post_result_parameter_search": False,
    }
    out = a.output / "M2D_SUPPORT_PRUNED_CUT_V1_SONOTACO_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "aggregate": agg, "size_summary": size, "gates": gates, "ranked_pretruth_sha256": ranked_sha, "result_sha256": sha(out)}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
