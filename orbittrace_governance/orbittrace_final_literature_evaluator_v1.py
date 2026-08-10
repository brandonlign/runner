#!/usr/bin/env python3
"""Candidate-independent final OrbitTrace literature evaluator primitives.

No data transport lives here. Inputs are already-frozen candidate/comparator memberships plus truth
opened only after output freeze. Matching uses exact Fraction arithmetic; bootstrap semantics are
fixed in FINAL_LITERATURE_EVALUATOR_FREEZE_V1.md.
"""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from typing import Any, Iterable

import numpy as np

BOOTSTRAP_SEED = 2026081001
BOOTSTRAP_REPLICATES = 10_000
SIZE_BINS = (
    ("4-9", 4, 9),
    ("10-24", 10, 24),
    ("25-49", 25, 49),
    ("50-99", 50, 99),
    ("100+", 100, None),
)


def size_bin(n: int) -> str | None:
    for name, lo, hi in SIZE_BINS:
        if n >= lo and (hi is None or n <= hi):
            return name
    return None


def exact_f1(candidate: set[str], truth: set[str]) -> Fraction:
    if not candidate or not truth:
        return Fraction(0, 1)
    tp = len(candidate & truth)
    return Fraction(2 * tp, len(candidate) + len(truth))


def _hungarian_min_exact(cost: list[list[Fraction]]) -> list[int]:
    """Assign every row to one unique column; requires rows <= columns.

    Classic O(n*m) augmenting Hungarian implementation with exact Fraction arithmetic.
    Iteration order is stable ascending column index; equal reduced costs therefore have a frozen
    deterministic first-column tie behavior.
    """
    n = len(cost)
    if n == 0:
        return []
    m = len(cost[0])
    if n > m or any(len(row) != m for row in cost):
        raise ValueError("exact Hungarian requires rectangular rows<=columns")
    zero = Fraction(0, 1)
    inf: Fraction | None = None
    u = [zero for _ in range(n + 1)]
    v = [zero for _ in range(m + 1)]
    p = [0 for _ in range(m + 1)]
    way = [0 for _ in range(m + 1)]
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv: list[Fraction | None] = [inf for _ in range(m + 1)]
        used = [False for _ in range(m + 1)]
        while True:
            used[j0] = True
            i0 = p[j0]
            delta: Fraction | None = None
            j1 = 0
            for j in range(1, m + 1):
                if used[j]:
                    continue
                cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                if minv[j] is None or cur < minv[j]:
                    minv[j] = cur
                    way[j] = j0
                if delta is None or minv[j] < delta:  # strict: first j wins equality
                    delta = minv[j]
                    j1 = j
            if delta is None:
                raise RuntimeError("no augmenting column")
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                elif minv[j] is not None:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    assignment = [-1 for _ in range(n)]
    for j in range(1, m + 1):
        if p[j] != 0:
            assignment[p[j] - 1] = j - 1
    if any(j < 0 for j in assignment):
        raise RuntimeError("incomplete exact assignment")
    return assignment


def one_to_one_scores(
    candidates: list[dict[str, Any]],
    truth_by_label: dict[str, Iterable[str]],
) -> dict[str, Any]:
    """Return deterministic maximum-total-F1 scores for all eligible truth labels.

    `candidates` must already be in frozen rank/ID order and each needs `family_id,event_ids`.
    Truth labels are sorted canonically. Distinct zero dummies allow every shower to be unmatched.
    """
    labels = sorted(
        label for label, ids in truth_by_label.items()
        if len(set(map(str, ids))) >= 4
    )
    truths = {label: set(map(str, truth_by_label[label])) for label in labels}
    candidate_sets = [set(map(str, row["event_ids"])) for row in candidates]
    real_count = len(candidates)
    # Every truth row can take any real candidate plus its own/different zero dummy.
    weights: list[list[Fraction]] = []
    for label in labels:
        row = [exact_f1(cset, truths[label]) for cset in candidate_sets]
        row.extend(Fraction(0, 1) for _ in labels)
        weights.append(row)
    assignment = _hungarian_min_exact([[-w for w in row] for row in weights])
    per_label: list[dict[str, Any]] = []
    total = Fraction(0, 1)
    for i, (label, col) in enumerate(zip(labels, assignment)):
        truth = truths[label]
        if col < real_count:
            candidate = candidates[col]
            cset = candidate_sets[col]
            tp = len(cset & truth)
            precision = Fraction(tp, len(cset)) if cset else Fraction(0, 1)
            recall = Fraction(tp, len(truth)) if truth else Fraction(0, 1)
            f1 = weights[i][col]
            family_id: str | None = str(candidate["family_id"])
            candidate_index: int | None = col
        else:
            precision = recall = f1 = Fraction(0, 1)
            family_id = None
            candidate_index = None
        total += f1
        per_label.append({
            "label": label,
            "truth_size": len(truth),
            "size_bin": size_bin(len(truth)),
            "candidate_index": candidate_index,
            "family_id": family_id,
            "precision_num": precision.numerator,
            "precision_den": precision.denominator,
            "recall_num": recall.numerator,
            "recall_den": recall.denominator,
            "f1_num": f1.numerator,
            "f1_den": f1.denominator,
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "recovered_f1_gt_0_5": bool(f1 > Fraction(1, 2)),
        })
    return {
        "eligible_labels": len(labels),
        "candidate_budget_used": real_count,
        "total_f1_num": total.numerator,
        "total_f1_den": total.denominator,
        "macro_f1": float(total / len(labels)) if labels else 0.0,
        "recovered_f1_gt_0_5": sum(int(row["recovered_f1_gt_0_5"]) for row in per_label),
        "per_label": per_label,
    }


def mean_for_bins(rows: list[dict[str, Any]], names: set[str]) -> float | None:
    values = [float(row["f1"]) for row in rows if row["size_bin"] in names]
    return float(np.mean(values)) if values else None


def point_metrics(assignment: dict[str, Any]) -> dict[str, Any]:
    rows = assignment["per_label"]
    strata = {}
    for name, _lo, _hi in SIZE_BINS:
        vals = [float(row["f1"]) for row in rows if row["size_bin"] == name]
        strata[name] = {"count": len(vals), "mean_f1": float(np.mean(vals)) if vals else None}
    return {
        "macro_f1": float(assignment["macro_f1"]),
        "recovered_f1_gt_0_5": int(assignment["recovered_f1_gt_0_5"]),
        "strata": strata,
        "mean_f1_4_24": mean_for_bins(rows, {"4-9", "10-24"}),
    }


def paired_bootstrap(
    candidate_units: list[dict[str, Any]],
    comparator_units: list[dict[str, Any]],
) -> dict[str, Any]:
    """Bootstrap fixed point assignments, paired by (year,label), preserving year×size counts."""
    cand = {(int(r["year"]), str(r["label"])): r for r in candidate_units}
    comp = {(int(r["year"]), str(r["label"])): r for r in comparator_units}
    if set(cand) != set(comp):
        raise ValueError("candidate/comparator bootstrap unit keys differ")
    units = []
    for key in sorted(cand):
        a, b = cand[key], comp[key]
        if a["size_bin"] != b["size_bin"] or int(a["truth_size"]) != int(b["truth_size"]):
            raise ValueError(f"paired truth metadata mismatch for {key}")
        units.append({
            "year": key[0],
            "label": key[1],
            "size_bin": a["size_bin"],
            "diff": float(a["f1"]) - float(b["f1"]),
        })
    strata: dict[tuple[int, str], list[int]] = defaultdict(list)
    for i, row in enumerate(units):
        if row["size_bin"] is None:
            continue
        strata[(int(row["year"]), str(row["size_bin"]))].append(i)
    # Sparse route requires both sparse estimands to exist in each test year.
    for year in (2013, 2014):
        if not strata.get((year, "4-9")):
            sparse_eligible = False
            break
        if not (strata.get((year, "4-9")) or strata.get((year, "10-24"))):
            sparse_eligible = False
            break
    else:
        sparse_eligible = True

    rng = np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED))
    macro = np.empty(BOOTSTRAP_REPLICATES, dtype=np.float64)
    s49 = np.empty(BOOTSTRAP_REPLICATES, dtype=np.float64)
    s424 = np.empty(BOOTSTRAP_REPLICATES, dtype=np.float64)
    for rep in range(BOOTSTRAP_REPLICATES):
        sampled: list[int] = []
        for key in sorted(strata):
            idx = np.asarray(strata[key], dtype=np.int64)
            sampled.extend(rng.choice(idx, size=len(idx), replace=True).tolist())
        diffs = np.asarray([units[i]["diff"] for i in sampled], dtype=np.float64)
        bins = [units[i]["size_bin"] for i in sampled]
        macro[rep] = float(np.mean(diffs))
        v49 = np.asarray([d for d, b in zip(diffs.tolist(), bins) if b == "4-9"], dtype=np.float64)
        v424 = np.asarray([d for d, b in zip(diffs.tolist(), bins) if b in {"4-9", "10-24"}], dtype=np.float64)
        s49[rep] = float(np.mean(v49)) if len(v49) else np.nan
        s424[rep] = float(np.mean(v424)) if len(v424) else np.nan
    q = lambda x: float(np.quantile(x[np.isfinite(x)], 0.025, method="linear")) if np.any(np.isfinite(x)) else None
    return {
        "seed": BOOTSTRAP_SEED,
        "replicates": BOOTSTRAP_REPLICATES,
        "stratification": "year_x_truth_size_bin",
        "point_assignment_held_fixed": True,
        "sparse_route_bootstrap_eligible": sparse_eligible,
        "macro_advantage_lower_95": q(macro),
        "sparse_4_9_advantage_lower_95": q(s49),
        "sparse_4_24_advantage_lower_95": q(s424),
        "macro_replicates": macro.tolist(),
        "sparse_4_9_replicates": s49.tolist(),
        "sparse_4_24_replicates": s424.tolist(),
    }


def self_test() -> None:
    truth = {
        "A": {"1", "2", "3", "4"},
        "B": {"5", "6", "7", "8"},
    }
    candidates = [
        {"family_id": "C1", "event_ids": ["1", "2", "3", "4"]},
        {"family_id": "C2", "event_ids": ["5", "6", "7"]},
    ]
    r = one_to_one_scores(candidates, truth)
    assert r["eligible_labels"] == 2
    assert r["per_label"][0]["family_id"] == "C1"
    assert r["per_label"][0]["f1"] == 1.0
    assert r["per_label"][1]["family_id"] == "C2"
    assert r["per_label"][1]["f1_num"] == 6 and r["per_label"][1]["f1_den"] == 7
    # Stable exact tie: first candidate column is used for first canonical truth row.
    tie = one_to_one_scores(
        [{"family_id": "X", "event_ids": ["1"]}, {"family_id": "Y", "event_ids": ["1"]}],
        {"A": {"1", "2", "3", "4"}},
    )
    assert tie["per_label"][0]["family_id"] == "X"


if __name__ == "__main__":
    self_test()
    print("PASS_FINAL_LITERATURE_EVALUATOR_V1_SELF_TEST")
