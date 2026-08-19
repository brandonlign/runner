#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

ECT_SCHEMA = "ORBITTRACE_ENVELOPE_CORE_TOPOMODAL_V1_PRETRUTH"
ECT_ROLE = "TARGET_EXCLUDED_GMN_ECT_V1_HIERARCHICAL_CANDIDATES_FROZEN_BEFORE_CORE_TRUTH_TEST"
BWM_EVALUATOR_SHA = "1578f5eb28fc7e66a2c73f3ef66a6697e20b53b992a7fc979276720047e534d6"
YEARS = (2022, 2023)
MONTH_KEYS = tuple(f"{y}-{m:02d}" for y in YEARS for m in range(1, 13))
BLIND = (20.0, 55.0)
DENOMS = (128, 1024)
BUCKETS = (0, 1, 2, 3)


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


def pair_arrays(cands: list[dict[str, Any]], hidden: dict[str, str], annual: set[str]) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    cnt = Counter(v for k, v in hidden.items() if k in annual and v != "SPORADIC")
    labels = sorted(k for k, n in cnt.items() if n >= 4)
    L, C = len(labels), len(cands)
    ef = np.zeros((L, C), float); ep = np.zeros_like(ef); er = np.zeros_like(ef)
    cf = np.zeros_like(ef); cp = np.zeros_like(ef); cr = np.zeros_like(ef)
    labix = {lab: i for i, lab in enumerate(labels)}
    for j, cand in enumerate(cands):
        for f, p, r, key in (
            (ef, ep, er, "event_ids"),
            (cf, cp, cr, "core_event_ids"),
        ):
            ids = [str(x) for x in cand[key] if str(x) in annual]
            n = len(ids)
            if not n:
                continue
            cc = Counter(hidden.get(eid, "SPORADIC") for eid in ids)
            for lab, ov in cc.items():
                if lab not in labix:
                    continue
                i = labix[lab]
                pp = ov / n
                rr = ov / cnt[lab]
                ff = 2.0 * pp * rr / (pp + rr) if pp + rr else 0.0
                f[i, j], p[i, j], r[i, j] = ff, pp, rr
    return labels, ef, ep, er, cf, cp, cr


def paired_core_metrics(cands: list[dict[str, Any]], hidden: dict[str, str], annual: set[str]) -> dict[str, Any]:
    labels, ef, ep, er, cf, cp, cr = pair_arrays(cands, hidden, annual)
    _L, C = ef.shape
    if C:
        ri, cj = linear_sum_assignment(ef, maximize=True)
    else:
        ri, cj = np.asarray([], int), np.asarray([], int)
    rows: list[dict[str, float]] = []
    for i, j in zip(ri, cj):
        if float(ef[i, j]) <= 0.5:
            continue
        rows.append({
            "envelope_f1": float(ef[i, j]),
            "envelope_precision": float(ep[i, j]),
            "envelope_recall": float(er[i, j]),
            "core_f1": float(cf[i, j]),
            "core_precision": float(cp[i, j]),
            "core_recall": float(cr[i, j]),
            "core_member_fraction": len(cands[int(j)]["core_event_ids"]) / len(cands[int(j)]["event_ids"]),
        })
    if not rows:
        return {
            "eligible_showers": len(labels), "outer_recovered_pairs": 0,
            "mean_envelope_f1": 0.0, "mean_core_f1": 0.0,
            "mean_envelope_precision": 0.0, "mean_core_precision": 0.0,
            "mean_envelope_recall": 0.0, "mean_core_recall": 0.0,
            "mean_core_member_fraction": 0.0,
            "core_precision_improved_pairs": 0, "core_f1_not_lower_pairs": 0,
            "core_still_f1_gt_05_pairs": 0, "core_still_f1_gt_08_pairs": 0,
            "pair_rows": [],
        }
    return {
        "eligible_showers": len(labels),
        "outer_recovered_pairs": len(rows),
        "mean_envelope_f1": mean(x["envelope_f1"] for x in rows),
        "mean_core_f1": mean(x["core_f1"] for x in rows),
        "mean_envelope_precision": mean(x["envelope_precision"] for x in rows),
        "mean_core_precision": mean(x["core_precision"] for x in rows),
        "mean_envelope_recall": mean(x["envelope_recall"] for x in rows),
        "mean_core_recall": mean(x["core_recall"] for x in rows),
        "mean_core_member_fraction": mean(x["core_member_fraction"] for x in rows),
        "core_precision_improved_pairs": sum(x["core_precision"] > x["envelope_precision"] for x in rows),
        "core_f1_not_lower_pairs": sum(x["core_f1"] >= x["envelope_f1"] for x in rows),
        "core_still_f1_gt_05_pairs": sum(x["core_f1"] > 0.5 for x in rows),
        "core_still_f1_gt_08_pairs": sum(x["core_f1"] > 0.8 for x in rows),
        "pair_rows": rows,
    }


def pooled(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pairs = [p for r in rows for p in r["paired"]["pair_rows"]]
    req(bool(pairs), "no recovered envelope pairs for pooled core metric")
    return {
        "outer_recovered_pairs": len(pairs),
        "mean_envelope_f1": mean(x["envelope_f1"] for x in pairs),
        "mean_core_f1": mean(x["core_f1"] for x in pairs),
        "mean_envelope_precision": mean(x["envelope_precision"] for x in pairs),
        "mean_core_precision": mean(x["core_precision"] for x in pairs),
        "mean_envelope_recall": mean(x["envelope_recall"] for x in pairs),
        "mean_core_recall": mean(x["core_recall"] for x in pairs),
        "mean_core_member_fraction": mean(x["core_member_fraction"] for x in pairs),
        "core_precision_improved_pairs": sum(x["core_precision"] > x["envelope_precision"] for x in pairs),
        "core_f1_not_lower_pairs": sum(x["core_f1"] >= x["envelope_f1"] for x in pairs),
        "core_still_f1_gt_05_pairs": sum(x["core_f1"] > 0.5 for x in pairs),
        "core_still_f1_gt_08_pairs": sum(x["core_f1"] > 0.8 for x in pairs),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ect-pretruth", type=Path, required=True)
    ap.add_argument("--expected-pretruth-sha", required=True)
    ap.add_argument("--frozen-bwm-evaluator", type=Path, required=True)
    for n in (
        "literature-pretruth", "parent-runner", "quality-source", "support-source-parts",
        "candidate-payload", "baseline-payload", "scorer-parts", "v8-result-json", "output",
    ):
        ap.add_argument("--" + n, type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)

    req(sha(a.ect_pretruth) == a.expected_pretruth_sha, "sealed ECT pretruth changed")
    req(sha(a.frozen_bwm_evaluator) == BWM_EVALUATOR_SHA, "frozen evaluator changed")
    pre = json.loads(a.ect_pretruth.read_text())
    req(pre.get("schema") == ECT_SCHEMA and pre.get("scientific_role") == ECT_ROLE, "wrong ECT identity")
    req(pre.get("structural_pass") is True, "ECT structural gate failed")
    req(pre.get("configuration", {}).get("core_replaces_envelope") is False, "core replacement changed")
    req(pre.get("configuration", {}).get("core_changes_envelope_rank") is False, "core rank role changed")
    req(pre.get("configuration", {}).get("new_tuned_parameters") == [], "unexpected ECT tuned parameters")
    req(
        pre.get("target_information_access") is False and pre.get("target_region_events_accessed") is False
        and pre.get("orbittrace_reveal_access") is False and pre.get("sonotaco_scientific_access") is False,
        "ECT protected-data firewall",
    )

    compat = copy.deepcopy(pre)
    compat["schema"] = "ORBITTRACE_BIF_WITNESS_MODULARITY_V1_PRETRUTH"
    compat["scientific_role"] = "TARGET_EXCLUDED_GMN_BWM_V1_RANKING_FROZEN_BEFORE_SHOWER_TRUTH"
    compat["support_pruned_pretruth_sha256"] = pre["support_pruned_pretruth_sha256"]
    compat["shower_truth_used"] = False
    compat["configuration"] = {"new_tuned_parameters": [], "modularity_resolution": 1.0, "community_passes": 1}
    for subset in compat["subsets"]:
        subset["bwm_candidates"] = subset["envelope_core_candidates"]
    ss = pre["size_summary"]
    compat["size_summary"] = {
        "bwm_max_top_budget_member_count": ss["envelope_max_top_budget_member_count"],
        "bwm_mean_top_budget_member_count": ss["envelope_mean_top_budget_member_count"],
        "bwm_p90_top_budget_member_count": ss["envelope_p90_top_budget_member_count"],
        "bwm_size_biased_top_budget_member_burden": ss["envelope_size_biased_top_budget_member_burden"],
        "support_pruned_max_top_budget_member_count": ss["envelope_max_top_budget_member_count"],
        "support_pruned_mean_top_budget_member_count": ss["envelope_mean_top_budget_member_count"],
        "support_pruned_p90_top_budget_member_count": ss["envelope_p90_top_budget_member_count"],
        "support_pruned_size_biased_top_budget_member_burden": ss["envelope_size_biased_top_budget_member_burden"],
    }
    compat["mechanism_summary"] = pre["mechanism_summary"]

    with tempfile.TemporaryDirectory(prefix="ect-flat-") as td:
        td_path = Path(td)
        compat_path = td_path / "BWM_COMPAT_FROM_ECT_ENVELOPES.json"
        raw_path = td_path / "BWM_COMPAT_RESULT.json"
        compat_path.write_text(json.dumps(compat, indent=2, sort_keys=True) + "\n")
        compat_sha = sha(compat_path)
        cmd = [
            sys.executable, str(a.frozen_bwm_evaluator),
            "--bwm-pretruth", str(compat_path), "--expected-pretruth-sha", compat_sha,
            "--literature-pretruth", str(a.literature_pretruth),
            "--parent-runner", str(a.parent_runner), "--quality-source", str(a.quality_source),
            "--support-source-parts", str(a.support_source_parts), "--candidate-payload", str(a.candidate_payload),
            "--baseline-payload", str(a.baseline_payload), "--scorer-parts", str(a.scorer_parts),
            "--v8-result-json", str(a.v8_result_json), "--output", str(raw_path),
        ]
        subprocess.run(cmd, check=True)
        flat = json.loads(raw_path.read_text())

    req(all(flat["gates"].values()), "unchanged envelope failed inherited flat gates")
    for route in flat["routes"].values():
        req(route["bwm"] == route["support_pruned"], "envelope route differs from support-pruned baseline")
    for scale in flat["scales"].values():
        req(scale["bwm"] == scale["support_pruned"], "envelope scale differs from support-pruned baseline")

    frozen = load(a.frozen_bwm_evaluator, "ect_frozen_bwm_eval")
    q = frozen.load(a.quality_source, "ect_truth_q")
    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    rt = q.v1.mult.load_frozen_runtime()
    support = rt.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = "orbittrace-envelope-core-topomodal-v1-gmn-truth"
    support.RANKING_VARIANTS = ("persistence",)
    req((float(support.BLIND_LOW), float(support.BLIND_HIGH)) == BLIND, "blind interval changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _c, base, _s = support.load_sources(a)
    scan, _cal, hidden, sources = support.parse_catalogue(base)
    req(isinstance(hidden, dict), "GMN truth unavailable")
    req(sorted(scan) == list(YEARS) and [x["key"] for x in sources] == list(MONTH_KEYS), "GMN source changed")

    lit = json.loads(a.literature_pretruth.read_text())
    subsets = {(int(s["denominator"]), int(s["bucket"])): s for s in pre["subsets"]}
    req(set(subsets) == {(d, b) for d in DENOMS for b in BUCKETS}, "panel set changed")

    paired_rows: list[dict[str, Any]] = []
    for d in DENOMS:
        for b in BUCKETS:
            s = subsets[(d, b)]
            cands = list(s["envelope_core_candidates"])
            for y in YEARS:
                annual = set(str(x) for x in s["annual_event_ids"][str(y)])
                pp = lit["panels"][f"d{d}_b{b}_y{y}"]
                req(int(pp["event_count"]) == len(annual), "annual universe drift")
                for comp in ("sugar2017", "hdbscan2025"):
                    k = len(pp[comp]["clusters"])
                    paired_rows.append({
                        "denominator": d, "bucket": b, "year": y, "comparator": comp,
                        "comparator_capacity_k": k,
                        "paired": paired_core_metrics(cands[:k], hidden, annual),
                    })
    req(len(paired_rows) == 32, "paired comparison count")

    core_routes = {comp: pooled([r for r in paired_rows if r["comparator"] == comp]) for comp in ("sugar2017", "hdbscan2025")}
    core_scales = {str(d): pooled([r for r in paired_rows if r["denominator"] == d]) for d in DENOMS}
    core_gates = {
        "sugar_core_precision_strictly_higher": core_routes["sugar2017"]["mean_core_precision"] > core_routes["sugar2017"]["mean_envelope_precision"],
        "sugar_core_f1_not_lower": core_routes["sugar2017"]["mean_core_f1"] >= core_routes["sugar2017"]["mean_envelope_f1"],
        "hdb_core_precision_strictly_higher": core_routes["hdbscan2025"]["mean_core_precision"] > core_routes["hdbscan2025"]["mean_envelope_precision"],
        "hdb_core_f1_not_lower": core_routes["hdbscan2025"]["mean_core_f1"] >= core_routes["hdbscan2025"]["mean_envelope_f1"],
        "coarse_core_precision_strictly_higher": core_scales["128"]["mean_core_precision"] > core_scales["128"]["mean_envelope_precision"],
        "coarse_core_f1_not_lower": core_scales["128"]["mean_core_f1"] >= core_scales["128"]["mean_envelope_f1"],
        "fine_core_precision_strictly_higher": core_scales["1024"]["mean_core_precision"] > core_scales["1024"]["mean_envelope_precision"],
        "fine_core_f1_not_lower": core_scales["1024"]["mean_core_f1"] >= core_scales["1024"]["mean_envelope_f1"],
    }
    verdict = "PASS_ENVELOPE_CORE_TOPOMODAL_V1_GMN_DEVELOPMENT" if all(core_gates.values()) else "FAIL_ENVELOPE_CORE_TOPOMODAL_V1_GMN_DEVELOPMENT"
    out = {
        "schema": "ORBITTRACE_ENVELOPE_CORE_TOPOMODAL_V1_GMN_RESULT",
        "scientific_role": "TARGET_EXCLUDED_GMN_ECT_V1_HIERARCHICAL_EXTRACTION_DEVELOPMENT_RESULT",
        "development_status": pre["development_status"],
        "verdict": verdict,
        "ect_pretruth_sha256": sha(a.ect_pretruth),
        "bwm_compat_projection_sha256": compat_sha,
        "frozen_evaluator_sha256": BWM_EVALUATOR_SHA,
        "flat_envelope_routes": flat["routes"],
        "flat_envelope_scales": flat["scales"],
        "flat_envelope_gates": flat["gates"],
        "flat_envelope_exactly_support_pruned": True,
        "core_routes": core_routes,
        "core_scales": core_scales,
        "core_gates": core_gates,
        "paired_rows": paired_rows,
        "size_summary": pre["size_summary"],
        "mechanism_summary": pre["mechanism_summary"],
        "structural_gates": pre["structural_gates"],
        "core_pair_selection": "outer Hungarian assignment under the exact frozen F1 matrix; evaluate same candidate-label pair only when outer F1 > 0.5, the existing recovery threshold",
        "target_information_access": False,
        "target_region_events_accessed": False,
        "orbittrace_reveal_access": False,
        "sonotaco_scientific_access": False,
        "post_result_parameter_search": False,
        "interpretation_boundary": "The unchanged envelope carries the literature-comparison claim. The nested core is evaluated only as an extraction refinement conditional on an independently detected envelope; it is never substituted into the flat benchmark after truth.",
    }
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(verdict)
    print(json.dumps({"flat_envelope_gates": flat["gates"], "core_routes": core_routes, "core_scales": core_scales, "core_gates": core_gates, "size_summary": pre["size_summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
