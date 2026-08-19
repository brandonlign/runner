#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment

PRETRUTH_SHA256 = "e32c4aa6ea61f5933330f0a7bdcff34a655b588bda4c230bf339e8432f2a01ea"
PAPER_RESULT_GIT_BLOB = "1ac067658d7a1d99b1a276099ca6d3fee83a6c0b"
YEARS = (2013, 2014)
ROUTES = ("sugar", "hdbscan")


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_truth(root: Path, route: str, year: int) -> dict[str, str]:
    xs = list(root.rglob(f"truth_{route}_{year}.json"))
    req(len(xs) == 1, f"truth file missing/ambiguous for {route} {year}: {xs}")
    obj = json.loads(xs[0].read_text())
    req(isinstance(obj, dict), f"truth must be dict: {xs[0]}")
    return {str(k): str(v) for k, v in obj.items()}


def score(families: list[dict[str, Any]], truth: dict[str, str], budget: int) -> dict[str, Any]:
    # Exact semantics of the current paper evaluator: eligible showers have >=4
    # year-specific truth members; candidate hypotheses are one-to-one matched by
    # maximum F1 with a Hungarian assignment at the frozen comparator budget.
    counts = Counter(v for v in truth.values() if v != "SPORADIC")
    labels = sorted(k for k, n in counts.items() if n >= 4)
    ids = set(truth)
    active: list[tuple[int, str, set[str]]] = []
    for i, family in enumerate(families):
        mem = set(map(str, family["event_ids"])) & ids
        if mem:
            active.append((int(family.get("rank", i + 1)), str(family["family_id"]), mem))
    active.sort(key=lambda z: (z[0], z[1]))
    active = active[: int(budget)]

    truth_sets = {lab: {eid for eid, value in truth.items() if value == lab} for lab in labels}
    matrix = np.zeros((len(labels), len(active)), dtype=float)
    for i, lab in enumerate(labels):
        a = truth_sets[lab]
        for j, (_, _, pred) in enumerate(active):
            overlap = len(a & pred)
            if overlap:
                precision = overlap / len(pred)
                recall = overlap / len(a)
                matrix[i, j] = 2.0 * precision * recall / (precision + recall)

    n = max(len(labels), len(active))
    if n == 0:
        return {"eligible_showers": 0, "macro_f1": 0.0, "recovered_f1_gt_0_5": 0, "candidate_used": 0}
    cost = np.zeros((n, n), dtype=float)
    cost[: len(labels), : len(active)] = -matrix
    ri, cj = linear_sum_assignment(cost)
    vals = [
        float(matrix[i, j]) if j < len(active) else 0.0
        for i, j in zip(ri.tolist(), cj.tolist())
        if i < len(labels)
    ]
    return {
        "eligible_showers": len(labels),
        "macro_f1": float(np.mean(vals)) if vals else 0.0,
        "recovered_f1_gt_0_5": int(sum(v > 0.5 for v in vals)),
        "candidate_used": len(active),
    }


def load_paper_panels(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    obj = json.loads(path.read_text())
    req(obj.get("verdict") == "PASS_TEMPORAL_FAIR_LITERATURE_4_OF_4", "paper benchmark verdict changed")
    req(obj.get("panel_wins") == 4, "paper panel count changed")
    panels: dict[tuple[str, int], dict[str, Any]] = {}
    for row in obj["panels"]:
        panels[(str(row["route"]), int(row["year"]))] = row
    req(set(panels) == {(r, y) for r in ROUTES for y in YEARS}, "paper panel identities changed")
    expected = {("sugar", 2013): 40, ("sugar", 2014): 43, ("hdbscan", 2013): 14, ("hdbscan", 2014): 14}
    for key, budget in expected.items():
        req(int(panels[key]["budget"]) == budget, f"paper budget drift for {key}")
    return panels


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pretruth", type=Path, required=True)
    ap.add_argument("--truth-root", type=Path, required=True)
    ap.add_argument("--paper-result", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    req(sha256(args.pretruth) == PRETRUTH_SHA256, "DCRR pretruth hash changed")
    pretruth = json.loads(args.pretruth.read_text())
    req(pretruth.get("truth_accessed") is False, "DCRR pretruth is not truth-blind")
    req(pretruth.get("shower_label_fields_accessed") is False, "DCRR pretruth accessed labels")
    req(all(bool(v.get("mechanism_active")) for v in pretruth["routes"].values()), "DCRR inactive on a paper route")

    paper = load_paper_panels(args.paper_result)
    panels: list[dict[str, Any]] = []
    literature_wins = 0
    current_nonregression = 0
    strict_improvements = 0

    for route in ROUTES:
        families = list(pretruth["routes"][route]["dcrr_candidates"])
        for year in YEARS:
            key = (route, year)
            frozen = paper[key]
            budget = int(frozen["budget"])
            truth = find_truth(args.truth_root, route, year)
            dcrr = score(families, truth, budget)
            literature = frozen["literature"]
            current = frozen["recurrent"]

            lit_macro = float(dcrr["macro_f1"]) > float(literature["macro_f1"])
            lit_recovery = int(dcrr["recovered_f1_gt_0_5"]) >= int(literature["recovered_f1_gt_0_5"])
            cur_macro = float(dcrr["macro_f1"]) >= float(current["macro_f1"])
            cur_recovery = int(dcrr["recovered_f1_gt_0_5"]) >= int(current["recovered_f1_gt_0_5"])
            strict = float(dcrr["macro_f1"]) > float(current["macro_f1"])

            literature_wins += int(lit_macro and lit_recovery)
            current_nonregression += int(cur_macro and cur_recovery)
            strict_improvements += int(strict)
            panels.append({
                "route": route,
                "year": year,
                "budget": budget,
                "dcrr": dcrr,
                "current_recurrent_eom": current,
                "literature": literature,
                "dcrr_minus_current_macro_f1": float(dcrr["macro_f1"]) - float(current["macro_f1"]),
                "dcrr_minus_literature_macro_f1": float(dcrr["macro_f1"]) - float(literature["macro_f1"]),
                "gates": {
                    "beats_literature_macro_f1": lit_macro,
                    "literature_recovery_not_lower": lit_recovery,
                    "current_recurrent_macro_f1_not_lower": cur_macro,
                    "current_recurrent_recovery_not_lower": cur_recovery,
                    "strict_macro_f1_improvement_vs_current": strict,
                },
            })

    mean_dcrr = float(np.mean([p["dcrr"]["macro_f1"] for p in panels]))
    mean_current = float(np.mean([p["current_recurrent_eom"]["macro_f1"] for p in panels]))
    gates = {
        "beats_literature_all_4": literature_wins == 4,
        "no_macro_or_recovery_regression_vs_current_all_4": current_nonregression == 4,
        "strict_macro_improvement_vs_current_some_panel": strict_improvements >= 1,
        "mean_macro_f1_strictly_higher_than_current": mean_dcrr > mean_current,
    }
    passed = all(gates.values())
    result = {
        "schema": "ORBITTRACE_DUAL_CUT_RECURRENT_RANK_V1_PAPER_BENCHMARK",
        "verdict": "PASS_DUAL_CUT_RECURRENT_RANK_V1_PAPER_BENCHMARK" if passed else "FAIL_DUAL_CUT_RECURRENT_RANK_V1_PAPER_BENCHMARK",
        "scientific_role": "PRIMARY_EXACT_CURRENT_PAPER_EQUAL_TEMPORAL_SONOTACO_BENCHMARK",
        "pretruth_sha256": PRETRUTH_SHA256,
        "paper_result_git_blob": PAPER_RESULT_GIT_BLOB,
        "truth_loaded_only_after_pretruth": True,
        "post_result_method_change_authorized": False,
        "panels": panels,
        "aggregate": {
            "mean_dcrr_macro_f1": mean_dcrr,
            "mean_current_recurrent_eom_macro_f1": mean_current,
            "mean_macro_f1_delta": mean_dcrr - mean_current,
            "literature_panel_wins": literature_wins,
            "current_recurrent_nonregression_panels": current_nonregression,
            "strict_macro_improvement_panels": strict_improvements,
        },
        "promotion_gates": gates,
    }
    out = args.output / "RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
