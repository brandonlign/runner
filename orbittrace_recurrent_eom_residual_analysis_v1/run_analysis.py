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

PANELS = (("sugar", 2013, 34), ("sugar", 2014, 46), ("hdbscan", 2013, 11), ("hdbscan", 2014, 9))
EXPECTED_PRETRUTH_SHA = "c6afbc0c3443b6c34e3f90b0f63453a0a35bfae3f3c84ffe8a479f8f50cffeef"
EXPECTED_PARENT_RESULT_SHA = "c2395a86be5ba8a8b801210ac6e64b97c446e724991207aef85062ee00b89f12"
EXPECTED_TRUTH_SHA = {
    ("sugar", 2013): "e3c075e8c4b5d4020007ba31cc4c49f1161593f21b83d63b521fc668a0f26cb3",
    ("sugar", 2014): "6497a7c61d257b46a0f4f082eb05cdd2e590a6a5559cb00cb8e216a1c659c273",
    ("hdbscan", 2013): "b77cdf076ff51d81b45a38e8d6aa573f0beb43124753da7ae97e5143eb3c8f56",
    ("hdbscan", 2014): "eeeb98e249ef6be9cd9a1979316ac72da81578d9bb911752cc94b3793182c6e8",
}
EXPECTED_PARENT_RECOVERED = {
    ("sugar", 2013): 23,
    ("sugar", 2014): 24,
    ("hdbscan", 2013): 11,
    ("hdbscan", 2014): 9,
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def q(xs: list[float], p: float) -> float | None:
    return float(np.quantile(xs, p)) if xs else None


def exact_assignment(mat: np.ndarray, candidate_indices: list[int]) -> dict[int, tuple[int | None, float]]:
    n_truth = mat.shape[0]
    n = max(n_truth, len(candidate_indices))
    cost = np.zeros((n, n), dtype=np.float64)
    if candidate_indices:
        cost[:n_truth, :len(candidate_indices)] = -mat[:, candidate_indices]
    ri, cj = linear_sum_assignment(cost)
    out: dict[int, tuple[int | None, float]] = {}
    for i, j in zip(ri.tolist(), cj.tolist()):
        if i >= n_truth:
            continue
        if j < len(candidate_indices):
            jj = candidate_indices[j]
            out[i] = (jj, float(mat[i, jj]))
        else:
            out[i] = (None, 0.0)
    req(len(out) == n_truth, "Hungarian assignment omitted truth rows")
    return out


def panel(route: str, year: int, budget: int, pretruth: dict[str, Any], truth_root: Path) -> dict[str, Any]:
    truth_path = truth_root / f"truth_{route}_{year}.json"
    req(sha(truth_path) == EXPECTED_TRUTH_SHA[(route, year)], f"truth changed for {route} {year}")
    truth = json.loads(truth_path.read_text())
    req(isinstance(truth, dict), "truth payload not mapping")

    counts = Counter(v for v in truth.values() if v != "SPORADIC")
    labels = sorted(k for k, n in counts.items() if n >= 4)
    truth_sets = [{eid for eid, v in truth.items() if v == label} for label in labels]
    truth_ids = set(truth)

    candidates = pretruth["routes"][route]["candidates"]
    req([int(f["rank"]) for f in candidates] == list(range(1, len(candidates) + 1)), "candidate ranks changed")

    f1 = np.zeros((len(labels), len(candidates)), dtype=np.float64)
    recall = np.zeros_like(f1)
    precision = np.zeros_like(f1)
    pred_sizes: list[int] = []
    overlaps = np.zeros_like(f1, dtype=np.int64)

    for j, fam in enumerate(candidates):
        pred = set(map(str, fam["event_ids"])) & truth_ids
        pred_sizes.append(len(pred))
        for i, actual in enumerate(truth_sets):
            ov = len(actual & pred)
            overlaps[i, j] = ov
            if ov == 0:
                continue
            p = ov / len(pred)
            r = ov / len(actual)
            precision[i, j] = p
            recall[i, j] = r
            f1[i, j] = 2.0 * p * r / (p + r)

    budget_indices = [j for j, fam in enumerate(candidates) if int(fam["rank"]) <= budget]
    assigned = exact_assignment(f1, budget_indices)

    records: list[dict[str, Any]] = []
    for i, label in enumerate(labels):
        best_budget_j = max(budget_indices, key=lambda j: (f1[i, j], recall[i, j], precision[i, j], -int(candidates[j]["rank"]), str(candidates[j]["family_id"])))
        best_all_j = max(range(len(candidates)), key=lambda j: (f1[i, j], recall[i, j], precision[i, j], -int(candidates[j]["rank"]), str(candidates[j]["family_id"])))
        best_recall_j = max(range(len(candidates)), key=lambda j: (recall[i, j], precision[i, j], -int(candidates[j]["rank"]), str(candidates[j]["family_id"])))
        first_recoverable = [j for j in range(len(candidates)) if f1[i, j] > 0.5]
        first_recoverable_rank = min((int(candidates[j]["rank"]) for j in first_recoverable), default=None)

        assigned_j, assigned_f1 = assigned[i]
        if assigned_f1 > 0.5:
            category = "RECOVERED"
        elif f1[i, best_all_j] > 0.5:
            category = "RANKING_SELECTION_FAILURE"
        elif recall[i, best_recall_j] > 0.5 and precision[i, best_recall_j] <= 0.5:
            category = "MEMBERSHIP_CONTAMINATION"
        else:
            category = "CANDIDATE_GENERATION_FAILURE"

        records.append({
            "truth_label": label,
            "truth_member_count": len(truth_sets[i]),
            "category": category,
            "assigned_budget_f1": assigned_f1,
            "assigned_candidate_rank": int(candidates[assigned_j]["rank"]) if assigned_j is not None else None,
            "best_budget_f1": float(f1[i, best_budget_j]),
            "best_all_f1": float(f1[i, best_all_j]),
            "best_all_f1_rank": int(candidates[best_all_j]["rank"]),
            "best_all_recall": float(recall[i, best_recall_j]),
            "best_all_precision_at_recall": float(precision[i, best_recall_j]),
            "best_recall_rank": int(candidates[best_recall_j]["rank"]),
            "best_recall_member_count": pred_sizes[best_recall_j],
            "best_recall_overlap": int(overlaps[i, best_recall_j]),
            "first_recoverable_rank": first_recoverable_rank,
        })

    cat = Counter(r["category"] for r in records)
    req(cat["RECOVERED"] == EXPECTED_PARENT_RECOVERED[(route, year)], f"parent recovery mismatch for {route} {year}")
    misses = len(records) - cat["RECOVERED"]
    mc = [r for r in records if r["category"] == "MEMBERSHIP_CONTAMINATION"]
    rk = [r for r in records if r["category"] == "RANKING_SELECTION_FAILURE"]

    return {
        "route": route,
        "year": year,
        "budget": budget,
        "eligible_showers": len(records),
        "recovered": cat["RECOVERED"],
        "residual_misses": misses,
        "category_counts": {
            "RANKING_SELECTION_FAILURE": cat["RANKING_SELECTION_FAILURE"],
            "MEMBERSHIP_CONTAMINATION": cat["MEMBERSHIP_CONTAMINATION"],
            "CANDIDATE_GENERATION_FAILURE": cat["CANDIDATE_GENERATION_FAILURE"],
        },
        "category_fractions_of_misses": {
            k: (cat[k] / misses if misses else 0.0)
            for k in ("RANKING_SELECTION_FAILURE", "MEMBERSHIP_CONTAMINATION", "CANDIDATE_GENERATION_FAILURE")
        },
        "best_budget_f1": {
            "median": float(np.median([r["best_budget_f1"] for r in records])),
            "q1": q([r["best_budget_f1"] for r in records], 0.25),
            "q3": q([r["best_budget_f1"] for r in records], 0.75),
        },
        "best_all_f1": {
            "median": float(np.median([r["best_all_f1"] for r in records])),
            "q1": q([r["best_all_f1"] for r in records], 0.25),
            "q3": q([r["best_all_f1"] for r in records], 0.75),
        },
        "membership_contamination": {
            "count": len(mc),
            "precision_median": float(np.median([r["best_all_precision_at_recall"] for r in mc])) if mc else None,
            "recall_median": float(np.median([r["best_all_recall"] for r in mc])) if mc else None,
            "member_count_median": float(np.median([r["best_recall_member_count"] for r in mc])) if mc else None,
            "excess_background_median": float(np.median([r["best_recall_member_count"] - r["best_recall_overlap"] for r in mc])) if mc else None,
        },
        "ranking_selection": {
            "count": len(rk),
            "first_recoverable_rank_median": float(np.median([r["first_recoverable_rank"] for r in rk])) if rk else None,
            "distance_below_budget_median": float(np.median([r["first_recoverable_rank"] - budget for r in rk])) if rk else None,
        },
        "records": records,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pretruth", type=Path, required=True)
    ap.add_argument("--parent-result", type=Path, required=True)
    ap.add_argument("--truth-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()

    req(sha(a.pretruth) == EXPECTED_PRETRUTH_SHA, "parent pretruth changed")
    req(sha(a.parent_result) == EXPECTED_PARENT_RESULT_SHA, "parent result changed")
    pretruth = json.loads(a.pretruth.read_text())
    parent = json.loads(a.parent_result.read_text())
    req(parent["verdict"] == "PASS_RECURRENT_EOM_SONOTACO_V31_SUPERIORITY_V1", "unexpected parent verdict")
    req(pretruth["truth_accessed"] is False, "parent pretruth says truth accessed")
    req(pretruth["blind_exclusion"] == [20.0, 55.0], "parent blind changed")

    panels = [panel(route, year, budget, pretruth, a.truth_root) for route, year, budget in PANELS]
    totals = Counter()
    eligible = recovered = misses = 0
    for p in panels:
        eligible += p["eligible_showers"]
        recovered += p["recovered"]
        misses += p["residual_misses"]
        totals.update(p["category_counts"])

    membership_panels = sum(p["category_counts"]["MEMBERSHIP_CONTAMINATION"] > 0 for p in panels)
    membership_fraction = totals["MEMBERSHIP_CONTAMINATION"] / misses if misses else 0.0
    authorize = membership_panels >= 2 and membership_fraction >= 0.15

    result = {
        "schema": "ORBITTRACE_RECURRENT_EOM_RESIDUAL_ANALYSIS_V1",
        "scientific_role": "EXPOSED_SONOTACO_DEVELOPMENT_DIAGNOSTIC_ONLY",
        "parent_method": "recurrent-EOM HDBSCAN v1",
        "parent_pretruth_sha256": EXPECTED_PRETRUTH_SHA,
        "parent_result_sha256": EXPECTED_PARENT_RESULT_SHA,
        "panels": panels,
        "pooled_panel_diagnostic": {
            "eligible_panel_showers": eligible,
            "recovered": recovered,
            "residual_misses": misses,
            "category_counts": dict(totals),
            "category_fractions_of_misses": {k: totals[k] / misses for k in totals},
            "note": "Panel-level pooled diagnostic; Sugar and HDBSCAN row universes overlap and are not unique physical-shower counts.",
        },
        "physcore_successor_gate": {
            "required_membership_positive_panels": 2,
            "observed_membership_positive_panels": membership_panels,
            "required_membership_fraction_of_misses": 0.15,
            "observed_membership_fraction_of_misses": membership_fraction,
            "authorized": authorize,
        },
        "verdict": "AUTHORIZE_RECURRENT_EOM_PHYSCORE_SUCCESSOR" if authorize else "DO_NOT_AUTHORIZE_RECURRENT_EOM_PHYSCORE_SUCCESSOR",
        "interpretation": "Ranking/selection and candidate-generation dominate the residuals; fixed PhysCore membership cleanup is not the next justified successor." if not authorize else "Membership contamination is sufficiently prevalent to justify one fixed PhysCore-cleanup successor.",
        "post_result_parameter_search": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "pristine_external_access": False,
    }

    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "pooled": result["pooled_panel_diagnostic"],
        "gate": result["physcore_successor_gate"],
        "result_sha256": sha(a.output),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
