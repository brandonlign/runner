#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
DENOMS = (128, 1024)
BUCKETS = (0, 1, 2, 3)
BASELINE_M2D_SHA = "7b1ddfcd32cd0b52321e3b3dfc614a88dd9b973f947c1d4d0de74fddf26b59cd"
QUALITY_SHA = "dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990"
V8_SHA = "fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b"


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    req(spec is not None and spec.loader is not None, f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def evaluate(cands: list[dict[str, Any]], hidden: dict[str, str], annual: set[str]) -> dict[str, Any]:
    cnt = Counter(v for k, v in hidden.items() if k in annual and v != "SPORADIC")
    labels = sorted(k for k, n in cnt.items() if n >= 4)
    L, C = len(labels), len(cands)
    if L == 0:
        return {"eligible_showers": 0, "candidate_count": C, "macro_f1": 0.0, "macro_precision": 0.0, "macro_recall": 0.0, "recovered_f1_gt_05": 0, "recovered_f1_gt_08": 0}
    f = np.zeros((L, C), float)
    p = np.zeros_like(f)
    r = np.zeros_like(f)
    labix = {lab: i for i, lab in enumerate(labels)}
    for j, c in enumerate(cands):
        ids = [str(x) for x in c["event_ids"] if str(x) in annual]
        n = len(ids)
        if n == 0:
            continue
        cc = Counter(hidden.get(eid, "SPORADIC") for eid in ids)
        for lab, ov in cc.items():
            if lab not in labix:
                continue
            i = labix[lab]
            pp = ov / n
            rr = ov / cnt[lab]
            ff = 2 * pp * rr / (pp + rr) if pp + rr else 0.0
            f[i, j], p[i, j], r[i, j] = ff, pp, rr
    if C:
        ri, cj = linear_sum_assignment(f, maximize=True)
    else:
        ri, cj = np.asarray([], int), np.asarray([], int)
    assigned = np.zeros(L, float)
    ap = np.zeros(L, float)
    ar = np.zeros(L, float)
    for i, j in zip(ri, cj):
        assigned[i], ap[i], ar[i] = f[i, j], p[i, j], r[i, j]
    return {
        "eligible_showers": L,
        "candidate_count": C,
        "macro_f1": float(np.mean(assigned)),
        "macro_precision": float(np.mean(ap)),
        "macro_recall": float(np.mean(ar)),
        "recovered_f1_gt_05": int(np.sum(assigned > 0.5)),
        "recovered_f1_gt_08": int(np.sum(assigned > 0.8)),
    }


def agg(rows: list[dict[str, Any]], side: str) -> dict[str, Any]:
    vals = [r[side] for r in rows]
    return {
        "panels": len(vals),
        "mean_macro_f1": mean(float(v["macro_f1"]) for v in vals),
        "mean_macro_precision": mean(float(v["macro_precision"]) for v in vals),
        "mean_macro_recall": mean(float(v["macro_recall"]) for v in vals),
        "total_recovered_f1_gt_05": sum(int(v["recovered_f1_gt_05"]) for v in vals),
        "total_recovered_f1_gt_08": sum(int(v["recovered_f1_gt_08"]) for v in vals),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    for n in ("refined-pretruth", "literature-pretruth", "parent-runner", "quality-source", "support-source-parts", "candidate-payload", "baseline-payload", "scorer-parts", "v8-result-json", "output"):
        ap.add_argument("--" + n, type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    req(sha(a.quality_source) == QUALITY_SHA and sha(a.v8_result_json) == V8_SHA, "runtime input changed")

    pre = json.loads(a.refined_pretruth.read_text())
    lit = json.loads(a.literature_pretruth.read_text())
    req(pre.get("schema") == "ORBITTRACE_M2D_SUPPORT_PRUNED_CUT_V1_PRETRUTH", "wrong refined pretruth")
    req(pre.get("scientific_role") == "TARGET_EXCLUDED_GMN_SUPPORT_PRUNED_M2D_RANKING_FROZEN_BEFORE_TRUTH", "wrong refined role")
    req(pre.get("baseline_m2d_prelabel_sha256") == BASELINE_M2D_SHA, "baseline identity changed")
    req(pre.get("shower_truth_used") is False and pre.get("target_information_access") is False and pre.get("target_region_events_accessed") is False and pre.get("orbittrace_reveal_access") is False, "pretruth firewall")
    req(lit.get("scientific_role") == "TARGET_EXCLUDED_GMN_SPARSE_LITERATURE_COMPARATORS_FROZEN_BEFORE_TRUTH", "wrong literature pretruth")
    req(lit.get("internal_prelabel_sha256") == BASELINE_M2D_SHA, "literature baseline mismatch")

    subsets = {(int(s["denominator"]), int(s["bucket"])): s for s in pre["subsets"]}
    req(set(subsets) == {(d, b) for d in DENOMS for b in BUCKETS}, "panel set changed")

    q = load(a.quality_source, "support_pruned_q")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    rt = q.v1.mult.load_frozen_runtime()
    support = rt.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-m2d-support-pruned-cut-v1-gmn-truth"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "blind changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _c, base, _s = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(isinstance(hidden, dict), "truth unavailable")
    req(sorted(scan) == list(YEARS) and [x["key"] for x in sources] == list(MONTH_KEYS), "GMN source changed")

    comparisons: list[dict[str, Any]] = []
    for d in DENOMS:
        for b in BUCKETS:
            s = subsets[(d, b)]
            refined = list(s["refined_candidates"])
            baseline = list(s["baseline_candidates"])
            for y in YEARS:
                annual = set(str(x) for x in s["annual_event_ids"][str(y)])
                pp = lit["panels"][f"d{d}_b{b}_y{y}"]
                req(int(pp["event_count"]) == len(annual), "annual universe drift")
                for comp in ("sugar2017", "hdbscan2025"):
                    comparator = list(pp[comp]["clusters"])
                    k = len(comparator)
                    req(len(refined) >= k and len(baseline) >= k, f"capacity shortfall d{d} b{b} y{y} {comp}")
                    rm = evaluate(refined[:k], hidden, annual)
                    bm = evaluate(baseline[:k], hidden, annual)
                    cm = evaluate(comparator, hidden, annual)
                    comparisons.append({
                        "denominator": d,
                        "bucket": b,
                        "year": y,
                        "comparator": comp,
                        "capacity_k": k,
                        "refined": rm,
                        "baseline_m2d": bm,
                        "literature": cm,
                    })
    req(len(comparisons) == 32, "comparison count")

    routes: dict[str, Any] = {}
    for comp in ("sugar2017", "hdbscan2025"):
        rows = [r for r in comparisons if r["comparator"] == comp]
        routes[comp] = {"refined": agg(rows, "refined"), "baseline_m2d": agg(rows, "baseline_m2d"), "literature": agg(rows, "literature")}

    scales: dict[str, Any] = {}
    for d in DENOMS:
        rows = [r for r in comparisons if r["denominator"] == d]
        scales[str(d)] = {"refined": agg(rows, "refined"), "baseline_m2d": agg(rows, "baseline_m2d")}

    size = pre["size_summary"]
    active = int(size["discarded_subsupport_events_across_sparse_fits"]) > 0
    gates = {
        "mechanism_active_before_truth": active,
        "sugar_refined_f1_not_lower_than_baseline": routes["sugar2017"]["refined"]["mean_macro_f1"] >= routes["sugar2017"]["baseline_m2d"]["mean_macro_f1"],
        "sugar_refined_recovery_not_lower_than_baseline": routes["sugar2017"]["refined"]["total_recovered_f1_gt_05"] >= routes["sugar2017"]["baseline_m2d"]["total_recovered_f1_gt_05"],
        "hdb_refined_f1_not_lower_than_baseline": routes["hdbscan2025"]["refined"]["mean_macro_f1"] >= routes["hdbscan2025"]["baseline_m2d"]["mean_macro_f1"],
        "hdb_refined_recovery_not_lower_than_baseline": routes["hdbscan2025"]["refined"]["total_recovered_f1_gt_05"] >= routes["hdbscan2025"]["baseline_m2d"]["total_recovered_f1_gt_05"],
        "still_beats_sugar_published_config": routes["sugar2017"]["refined"]["mean_macro_f1"] > routes["sugar2017"]["literature"]["mean_macro_f1"] and routes["sugar2017"]["refined"]["total_recovered_f1_gt_05"] >= routes["sugar2017"]["literature"]["total_recovered_f1_gt_05"],
        "still_beats_hdb_published_config": routes["hdbscan2025"]["refined"]["mean_macro_f1"] > routes["hdbscan2025"]["literature"]["mean_macro_f1"] and routes["hdbscan2025"]["refined"]["total_recovered_f1_gt_05"] >= routes["hdbscan2025"]["literature"]["total_recovered_f1_gt_05"],
        "coarse_scale_f1_not_lower": scales["128"]["refined"]["mean_macro_f1"] >= scales["128"]["baseline_m2d"]["mean_macro_f1"],
        "coarse_scale_recovery_not_lower": scales["128"]["refined"]["total_recovered_f1_gt_05"] >= scales["128"]["baseline_m2d"]["total_recovered_f1_gt_05"],
        "fine_scale_f1_not_lower": scales["1024"]["refined"]["mean_macro_f1"] >= scales["1024"]["baseline_m2d"]["mean_macro_f1"],
        "fine_scale_recovery_not_lower": scales["1024"]["refined"]["total_recovered_f1_gt_05"] >= scales["1024"]["baseline_m2d"]["total_recovered_f1_gt_05"],
        "mean_top_budget_member_count_strictly_lower": float(size["refined_mean_top_budget_member_count"]) < float(size["baseline_mean_top_budget_member_count"]),
        "p90_top_budget_member_count_not_higher": float(size["refined_p90_top_budget_member_count"]) <= float(size["baseline_p90_top_budget_member_count"]),
    }
    verdict = "PASS_M2D_SUPPORT_PRUNED_CUT_V1_GMN_DEVELOPMENT" if all(gates.values()) else "FAIL_M2D_SUPPORT_PRUNED_CUT_V1_GMN_DEVELOPMENT"
    result = {
        "schema": "ORBITTRACE_M2D_SUPPORT_PRUNED_CUT_V1_GMN_RESULT",
        "scientific_role": "TARGET_EXCLUDED_GMN_SUPPORT_PRUNED_M2D_DEVELOPMENT",
        "verdict": verdict,
        "refined_pretruth_sha256": sha(a.refined_pretruth),
        "literature_pretruth_sha256": sha(a.literature_pretruth),
        "routes": routes,
        "scales": scales,
        "size_summary": size,
        "gates": gates,
        "comparisons": comparisons,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
    }
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "routes": routes, "scales": scales, "size_summary": size, "gates": gates, "result_sha256": sha(a.output)}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
