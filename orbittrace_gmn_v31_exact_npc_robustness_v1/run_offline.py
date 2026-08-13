#!/usr/bin/env python3
"""Frozen target-excluded GMN v31 successor using exact Euclidean 1-NPC robustness radius."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import minimize

import run_urc_union_ranker as q

EXPECTED_N = 226
EXPECTED_D = 23
EXPECTED_CM_D = 8
BLIND = [20.0, 55.0]
PACKAGE_MANIFEST_SHA = "16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7"
FEATURE_SHA = "fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5"
CENTROID_SHA = "a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f"
PARENT_PRELABEL_SHA = "b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09"
PARENT_MARGIN_SHA = "f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd"
DIVERSITY_LAMBDA = 0.8
DIVERSITY_SCALE = 1.0
SLSQP_FTOL = 1e-12
SLSQP_MAXITER = 1000
PRIMAL_TOL = 1e-8
REGION_TOL = 1e-7
LOWER_BOUND_TOL = 1e-8
HARD_CONTROL = {
    "recovered_at_25": 21,
    "recovered_at_50": 38,
    "recovered_at_100": 59,
    "top100_dominant_precision": 0.6884631112636006,
    "mrr": 0.046734076055452344,
    "qualified_matches": 95,
}
PARENT_CONTROL = {
    "recovered_at_25": 23,
    "recovered_at_50": 41,
    "recovered_at_100": 66,
    "top100_dominant_precision": 0.7229521515453452,
    "mrr": 0.050244164168646674,
    "qualified_matches": 95,
}


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--package-manifest", type=Path)
    p.add_argument("--features", type=Path)
    p.add_argument("--centroids", type=Path)
    p.add_argument("--output", type=Path)
    return p.parse_args()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_sha(arr: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(str(arr.dtype).encode())
    h.update(str(tuple(arr.shape)).encode())
    h.update(np.ascontiguousarray(arr).tobytes())
    return h.hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256("\n".join(order).encode()).hexdigest()


def metric_close(x: float, y: float) -> bool:
    return abs(float(x) - float(y)) <= 1e-15


def metric_subset(metrics: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metrics.items() if k != "first_rank_by_label"}


def equal_rank_fusion(hard_order: list[str], local_order: list[str]) -> list[str]:
    req(len(hard_order) == len(local_order) and set(hard_order) == set(local_order), "rank universe mismatch")
    h = {fid: i + 1 for i, fid in enumerate(hard_order)}
    l = {fid: i + 1 for i, fid in enumerate(local_order)}
    return sorted(hard_order, key=lambda fid: (h[fid] + l[fid], h[fid], fid))


def fixed_opposite_projection(
    z: np.ndarray,
    current_refs: np.ndarray,
    opposite_ref: np.ndarray,
) -> tuple[float, np.ndarray, dict[str, Any]]:
    """Exact fixed-opposite Euclidean projection QP from Voracek & Hein 2022."""
    x0 = np.asarray(z, dtype=float)
    C = np.asarray(current_refs, dtype=float)
    wj = np.asarray(opposite_ref, dtype=float)
    req(x0.ndim == 1 and C.ndim == 2 and wj.shape == x0.shape and C.shape[1] == len(x0), "QP shape mismatch")
    req(len(C) > 0 and np.isfinite(x0).all() and np.isfinite(C).all() and np.isfinite(wj).all(), "nonfinite QP input")

    # ||u-wj||^2 <= ||u-wi||^2  <=>  (wi-wj)^T u <= (||wi||^2-||wj||^2)/2.
    A = C - wj[None, :]
    b = (np.sum(C * C, axis=1) - float(np.dot(wj, wj))) / 2.0
    req(A.shape == (len(C), len(x0)) and b.shape == (len(C),) and np.isfinite(A).all() and np.isfinite(b).all(), "invalid QP halfspaces")

    def objective(u: np.ndarray) -> float:
        d = u - x0
        return 0.5 * float(np.dot(d, d))

    def gradient(u: np.ndarray) -> np.ndarray:
        return np.asarray(u, dtype=float) - x0

    def ineq(u: np.ndarray) -> np.ndarray:
        return b - A @ np.asarray(u, dtype=float)

    def ineq_jac(_u: np.ndarray) -> np.ndarray:
        return -A

    res = minimize(
        objective,
        x0.copy(),
        method="SLSQP",
        jac=gradient,
        constraints={"type": "ineq", "fun": ineq, "jac": ineq_jac},
        options={"ftol": SLSQP_FTOL, "maxiter": SLSQP_MAXITER, "disp": False},
    )
    req(bool(res.success), f"SLSQP fixed-opposite projection failed: {res.message}")
    u = np.asarray(res.x, dtype=float)
    req(u.shape == x0.shape and np.isfinite(u).all() and math.isfinite(float(res.fun)), "nonfinite SLSQP solution")
    violation = float(np.max(A @ u - b))
    req(violation <= PRIMAL_TOL, f"SLSQP primal violation {violation}")

    radius = float(np.linalg.norm(u - x0))
    req(math.isfinite(radius) and radius >= 0.0, "invalid projection radius")

    current_query_dist = np.linalg.norm(C - x0[None, :], axis=1)
    nearest_current = float(np.min(current_query_dist))
    opposite_query = float(np.linalg.norm(wj - x0))
    # Triangle-inequality lower bound used in nearest-prototype robustness literature.
    lower_bound = max(0.0, (opposite_query - nearest_current) / 2.0)
    req(radius + LOWER_BOUND_TOL >= lower_bound, f"projection radius {radius} below analytic lower bound {lower_bound}")

    projected_opp = float(np.linalg.norm(u - wj))
    projected_current_min = float(np.min(np.linalg.norm(C - u[None, :], axis=1)))
    req(projected_opp <= projected_current_min + REGION_TOL, "projected point not in fixed-opposite class-flip region")

    diag = {
        "iterations": int(getattr(res, "nit", -1)),
        "objective": float(res.fun),
        "radius": radius,
        "max_primal_violation": violation,
        "nearest_current_query_distance": nearest_current,
        "opposite_query_distance": opposite_query,
        "triangle_lower_bound": lower_bound,
        "projected_opposite_distance": projected_opp,
        "projected_current_min_distance": projected_current_min,
    }
    return radius, u, diag


def nearest_index(dist: np.ndarray, ids: list[str], hard_rank: dict[str, int]) -> int:
    req(len(dist) == len(ids) and len(ids) > 0, "nearest-index universe mismatch")
    return min(range(len(ids)), key=lambda k: (float(dist[k]), int(hard_rank[ids[k]]), ids[k]))


def exact_signed_robustness(
    z: np.ndarray,
    positive_refs: np.ndarray,
    positive_ids: list[str],
    nonpositive_refs: np.ndarray,
    nonpositive_ids: list[str],
    hard_rank: dict[str, int],
) -> tuple[float, dict[str, Any]]:
    x = np.asarray(z, dtype=float)
    P = np.asarray(positive_refs, dtype=float)
    N = np.asarray(nonpositive_refs, dtype=float)
    req(len(P) == len(positive_ids) and len(N) == len(nonpositive_ids) and len(P)>0 and len(N)>0, "robustness reference universe mismatch")
    dp = np.linalg.norm(P - x[None, :], axis=1)
    dn = np.linalg.norm(N - x[None, :], axis=1)
    req(np.isfinite(dp).all() and np.isfinite(dn).all(), "nonfinite nearest-prototype distances")
    ip = nearest_index(dp, positive_ids, hard_rank)
    inn = nearest_index(dn, nonpositive_ids, hard_rank)
    best_p = (float(dp[ip]), hard_rank[positive_ids[ip]], positive_ids[ip])
    best_n = (float(dn[inn]), hard_rank[nonpositive_ids[inn]], nonpositive_ids[inn])
    predicted_positive = best_p < best_n

    if predicted_positive:
        current_refs, current_ids = P, positive_ids
        opposite_refs, opposite_ids = N, nonpositive_ids
    else:
        current_refs, current_ids = N, nonpositive_ids
        opposite_refs, opposite_ids = P, positive_ids

    best_radius = math.inf
    winning_opp = None
    winning_diag = None
    qp_iterations = 0
    max_violation = -math.inf
    min_lb_slack = math.inf
    for j, opp_id in enumerate(opposite_ids):
        r, _u, diag = fixed_opposite_projection(x, current_refs, opposite_refs[j])
        qp_iterations += max(0, int(diag["iterations"]))
        max_violation = max(max_violation, float(diag["max_primal_violation"]))
        min_lb_slack = min(min_lb_slack, float(r - diag["triangle_lower_bound"]))
        # Deterministic tie handling for numerically equal radii: immutable hard rank then family ID.
        if (r, hard_rank[opp_id], opp_id) < (best_radius, hard_rank.get(winning_opp, 10**12) if winning_opp is not None else 10**12, winning_opp or "~"):
            best_radius = float(r)
            winning_opp = opp_id
            winning_diag = diag

    req(math.isfinite(best_radius) and best_radius >= 0.0 and winning_opp is not None and winning_diag is not None, "exact robustness minimum missing")
    signed = best_radius if predicted_positive else -best_radius
    diag = {
        "predicted_positive": bool(predicted_positive),
        "nearest_positive_family_id": positive_ids[ip],
        "nearest_positive_distance": float(dp[ip]),
        "nearest_nonpositive_family_id": nonpositive_ids[inn],
        "nearest_nonpositive_distance": float(dn[inn]),
        "opposite_prototypes_evaluated": len(opposite_ids),
        "winning_opposite_family_id": winning_opp,
        "exact_radius": best_radius,
        "signed_exact_radius": signed,
        "winning_projection": winning_diag,
        "total_slsqp_iterations": int(qp_iterations),
        "max_qp_primal_violation": float(max_violation),
        "minimum_radius_minus_triangle_lower_bound": float(min_lb_slack),
    }
    return signed, diag


def run_self_tests() -> int:
    # Test 1: 1D midpoint. Query .25, current prototype 0, opposite prototype 2 => boundary 1, radius .75.
    r, u, _ = fixed_opposite_projection(np.array([0.25]), np.array([[0.0]]), np.array([2.0]))
    req(abs(r - 0.75) <= 1e-9 and abs(float(u[0]) - 1.0) <= 1e-9, f"1D midpoint self-test failed: r={r}, u={u}")

    # Test 2: 2D single-prototype case; perpendicular distance to vertical bisector x=1 is .75.
    r, u, _ = fixed_opposite_projection(np.array([0.25, 0.5]), np.array([[0.0, 0.0]]), np.array([2.0, 0.0]))
    req(abs(r - 0.75) <= 1e-9 and np.linalg.norm(u - np.array([1.0, 0.5])) <= 1e-9, f"2D bisector self-test failed: r={r}, u={u}")

    # Test 3: multi-prototype wedge. Nearest-distance gap lower bound=.5, exact polyhedral radius=.75.
    current = np.array([[-1.0, 0.0], [1.0, 0.0]])
    opp = np.array([0.0, 2.0])
    z = np.array([0.0, 0.0])
    r, u, diag = fixed_opposite_projection(z, current, opp)
    req(abs(r - 0.75) <= 1e-8 and np.linalg.norm(u - np.array([0.0, 0.75])) <= 1e-8, f"multi-prototype wedge self-test failed: r={r}, u={u}")
    req(abs(float(diag["triangle_lower_bound"]) - 0.5) <= 1e-12 and r > float(diag["triangle_lower_bound"]), "exact radius did not exceed lower bound in wedge self-test")

    # Test 4: signed class symmetry on the same wedge geometry.
    ranks = {"p": 1, "n1": 2, "n2": 3}
    signed_neg, dneg = exact_signed_robustness(
        z,
        np.array([[0.0, 2.0]]), ["p"],
        current, ["n1", "n2"], ranks,
    )
    req(dneg["predicted_positive"] is False and abs(signed_neg + 0.75) <= 1e-8, f"negative sign symmetry failed: {signed_neg}, {dneg}")
    signed_pos, dpos = exact_signed_robustness(
        z,
        current, ["n1", "n2"],
        np.array([[0.0, 2.0]]), ["p"], ranks,
    )
    req(dpos["predicted_positive"] is True and abs(signed_pos - 0.75) <= 1e-8, f"positive sign symmetry failed: {signed_pos}, {dpos}")

    print(json.dumps({
        "verdict": "PASS_EXACT_NPC_ROBUSTNESS_ENGINEERING_SELF_TESTS",
        "one_dimensional_radius": 0.75,
        "two_dimensional_radius": 0.75,
        "multi_prototype_exact_radius": 0.75,
        "multi_prototype_triangle_lower_bound": 0.5,
        "signed_symmetry": True,
        "slsqp_ftol": SLSQP_FTOL,
        "slsqp_maxiter": SLSQP_MAXITER,
        "primal_tolerance": PRIMAL_TOL,
        "region_tolerance": REGION_TOL,
    }, indent=2, sort_keys=True))
    return 0


def main() -> int:
    a = parse_args()
    if a.self_test:
        return run_self_tests()
    req(a.package_manifest is not None and a.features is not None and a.centroids is not None and a.output is not None, "science mode requires package/features/centroids/output")
    a.output.mkdir(parents=True, exist_ok=True)

    req(file_sha(a.package_manifest) == PACKAGE_MANIFEST_SHA, "offline package manifest changed")
    manifest = json.loads(a.package_manifest.read_text())
    X = np.load(a.features, allow_pickle=False)
    cm = np.load(a.centroids, allow_pickle=False)

    req(manifest["verdict"] == "PASS_GMN_V31_OFFLINE_DEVELOPMENT_PACKAGE_V1", "offline package not authoritative PASS")
    req(manifest["scientific_role"] == "ENGINEERING_PROVENANCE_ONLY_NO_SUCCESSOR_EVALUATED", "offline package role changed")
    req(manifest["development_role"] == "GMN_2022_2023_TARGET_EXCLUDED_ONLY", "development role changed")
    req(manifest["candidate_count"] == EXPECTED_N and manifest["feature_dimension"] == EXPECTED_D and manifest["centroid_dimension"] == EXPECTED_CM_D, "package dimensions changed")
    req(X.shape == (EXPECTED_N, EXPECTED_D) and np.isfinite(X).all(), "invalid offline X")
    req(cm.shape == (EXPECTED_N, EXPECTED_CM_D) and np.isfinite(cm).all(), "invalid offline centroids")
    req(array_sha(X) == manifest["feature_matrix_sha256"] == FEATURE_SHA, "offline X hash changed")
    req(array_sha(cm) == manifest["centroid_matrix_sha256"] == CENTROID_SHA, "offline centroid hash changed")
    req(manifest["parent_prelabel_sha256"] == PARENT_PRELABEL_SHA, "parent prelabel provenance changed")
    req(manifest["parent_margin_sha256"] == PARENT_MARGIN_SHA, "parent margin provenance changed")
    req(manifest["blind_exclusion"] == BLIND, "blind interval changed")
    for key in (
        "raw_event_rows_exported", "raw_event_ids_exported", "raw_hidden_label_mapping_exported",
        "new_feature_or_score_created", "new_rank_evaluated", "successor_selected",
        "sonotaco_2013_2014_access", "target_information_access", "target_region_events_accessed",
        "maarsy_scientific_access", "dms_scientific_access",
    ):
        req(manifest[key] is False, f"package firewall/provenance changed: {key}")

    ids = [str(x) for x in manifest["family_input_order"]]
    hard_order = [str(x) for x in manifest["hard_order"]]
    rows = manifest["rows"]
    eligible_labels = [str(x) for x in manifest["eligible_labels"]]
    req(len(ids) == EXPECTED_N and len(set(ids)) == EXPECTED_N, "family input order changed")
    req(len(hard_order) == EXPECTED_N and len(set(hard_order)) == EXPECTED_N and set(hard_order) == set(ids), "hard order changed")
    req(len(rows) == EXPECTED_N and [str(r["family_id"]) for r in rows] == ids, "row/input alignment changed")
    req(len(eligible_labels) == 355 and len(set(eligible_labels)) == 355, "eligible-label universe changed")

    truths = {str(r["family_id"]): r["truth"] for r in rows}
    groups = [str(r["strict_group"]) for r in rows]
    folds = np.asarray([int(r["fold"]) for r in rows], dtype=int)
    y = np.asarray([bool(r["truth"]["positive"]) for r in rows], dtype=bool)
    req(set(folds.tolist()) == set(range(5)), "five-fold universe changed")
    req(int(y.sum()) == 111 and int((~y).sum()) == 115, "positive/nonpositive family counts changed")

    families = [{"family_id": fid} for fid in ids]
    eligible = {label: None for label in eligible_labels}
    hard_metrics = q.v1.monotone_metrics(families, hard_order, truths, eligible)
    for key in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "qualified_matches"):
        req(int(hard_metrics[key]) == int(HARD_CONTROL[key]), f"offline evaluator hard {key} mismatch: {hard_metrics[key]}")
        req(int(manifest["parent_baseline_metrics"][key]) == int(HARD_CONTROL[key]), f"package hard {key} mismatch")
    for key in ("top100_dominant_precision", "mrr"):
        req(metric_close(hard_metrics[key], HARD_CONTROL[key]), f"offline evaluator hard {key} mismatch: {hard_metrics[key]}")
        req(metric_close(manifest["parent_baseline_metrics"][key], HARD_CONTROL[key]), f"package hard {key} mismatch")
    for key in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "qualified_matches"):
        req(int(manifest["parent_fused_metrics"][key]) == int(PARENT_CONTROL[key]), f"recorded parent {key} changed")
    for key in ("top100_dominant_precision", "mrr"):
        req(metric_close(manifest["parent_fused_metrics"][key], PARENT_CONTROL[key]), f"recorded parent {key} changed")

    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}
    scores = np.zeros(EXPECTED_N, dtype=float)
    evidence_rows: list[dict[str, Any]] = []
    fold_diag: list[dict[str, Any]] = []

    for fold in range(5):
        train = folds != fold
        test = folds == fold
        req(train.any() and test.any(), f"empty fold {fold}")
        train_indices = np.where(train)[0]
        test_indices = np.where(test)[0]
        train_groups = {groups[i] for i in train_indices.tolist()}
        test_groups = {groups[i] for i in test_indices.tolist()}
        req(train_groups.isdisjoint(test_groups), f"strict group leakage fold {fold}")

        mu = np.mean(X[train], axis=0)
        sd = np.std(X[train], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        Ztr = (X[train] - mu[None, :]) / scale[None, :]
        Zte = (X[test] - mu[None, :]) / scale[None, :]
        ytr = y[train]
        req(np.isfinite(Ztr).all() and np.isfinite(Zte).all() and ytr.any() and (~ytr).any(), f"invalid standardized fold {fold}")

        train_ids = [ids[i] for i in train_indices.tolist()]
        P = Ztr[ytr]
        N = Ztr[~ytr]
        pos_ids = [train_ids[i] for i in np.where(ytr)[0].tolist()]
        neg_ids = [train_ids[i] for i in np.where(~ytr)[0].tolist()]
        req(len(P) == len(pos_ids) and len(N) == len(neg_ids) and len(P)>0 and len(N)>0, f"class reference alignment changed fold {fold}")

        fold_scores: list[float] = []
        fold_radii: list[float] = []
        fold_qps = 0
        fold_iterations = 0
        fold_max_violation = -math.inf
        fold_min_lb_slack = math.inf
        fold_pred_positive = 0
        for j, global_i in enumerate(test_indices.tolist()):
            score, diag = exact_signed_robustness(Zte[j], P, pos_ids, N, neg_ids, hard_rank)
            scores[global_i] = score
            fold_scores.append(score)
            fold_radii.append(abs(score))
            fold_qps += int(diag["opposite_prototypes_evaluated"])
            fold_iterations += int(diag["total_slsqp_iterations"])
            fold_max_violation = max(fold_max_violation, float(diag["max_qp_primal_violation"]))
            fold_min_lb_slack = min(fold_min_lb_slack, float(diag["minimum_radius_minus_triangle_lower_bound"]))
            fold_pred_positive += int(bool(diag["predicted_positive"]))
            evidence_rows.append({"family_id": ids[global_i], "fold": fold, **diag})

        fold_diag.append({
            "fold": fold,
            "train_examples": int(train.sum()),
            "test_examples": int(test.sum()),
            "positive_references": int(ytr.sum()),
            "nonpositive_references": int((~ytr).sum()),
            "heldout_positive": int(y[test].sum()),
            "predicted_positive_by_1npc": int(fold_pred_positive),
            "zero_variance_parent_features": int(np.sum(sd == 0.0)),
            "train_group_count": len(train_groups),
            "test_group_count": len(test_groups),
            "fixed_opposite_qps_solved": int(fold_qps),
            "total_slsqp_iterations": int(fold_iterations),
            "max_qp_primal_violation": float(fold_max_violation),
            "minimum_radius_minus_triangle_lower_bound": float(fold_min_lb_slack),
            "signed_score_min": float(np.min(fold_scores)),
            "signed_score_median": float(np.median(fold_scores)),
            "signed_score_max": float(np.max(fold_scores)),
            "radius_min": float(np.min(fold_radii)),
            "radius_median": float(np.median(fold_radii)),
            "radius_max": float(np.max(fold_radii)),
        })

    req(scores.shape == (EXPECTED_N,) and np.isfinite(scores).all(), "invalid exact robustness score vector")
    req(len(evidence_rows) == EXPECTED_N and len({r["family_id"] for r in evidence_rows}) == EXPECTED_N, "robustness evidence universe changed")

    tie = [(hard_rank[fid], fid) for fid in ids]
    local_idx = q.diversity_order(scores, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    local_order = [ids[i] for i in local_idx]
    fused_order = equal_rank_fusion(hard_order, local_order)
    local_metrics = q.v1.monotone_metrics(families, local_order, truths, eligible)
    fused = q.v1.monotone_metrics(families, fused_order, truths, eligible)
    req(int(local_metrics["qualified_matches"]) == 95 and int(fused["qualified_matches"]) == 95, "qualified universe changed")

    gates = {
        "recovered_at_100_strictly_better_than_parent": int(fused["recovered_at_100"]) > PARENT_CONTROL["recovered_at_100"],
        "recovered_at_50_not_worse_than_parent": int(fused["recovered_at_50"]) >= PARENT_CONTROL["recovered_at_50"],
        "recovered_at_25_not_worse_than_parent": int(fused["recovered_at_25"]) >= PARENT_CONTROL["recovered_at_25"],
        "top100_precision_not_worse_than_parent": float(fused["top100_dominant_precision"]) >= PARENT_CONTROL["top100_dominant_precision"],
        "mrr_not_worse_than_parent": float(fused["mrr"]) >= PARENT_CONTROL["mrr"],
        "qualified_count_identical": int(fused["qualified_matches"]) == PARENT_CONTROL["qualified_matches"],
    }
    passed = all(gates.values())
    verdict = "PASS_GMN_V31_EXACT_NPC_ROBUSTNESS_V1" if passed else "FAIL_GMN_V31_EXACT_NPC_ROBUSTNESS_V1"

    evidence = {
        "scientific_role": "TARGET_EXCLUDED_GMN_OOF_EXACT_1NPC_ROBUSTNESS_EVIDENCE",
        "candidate_count": EXPECTED_N,
        "signed_exact_radius_sha256": array_sha(scores),
        "rows": sorted(evidence_rows, key=lambda r: r["family_id"]),
        "raw_event_rows_accessed": False,
        "raw_event_ids_accessed": False,
        "raw_hidden_label_mapping_accessed": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": BLIND,
    }
    (a.output / "GMN_V31_EXACT_NPC_ROBUSTNESS_EVIDENCE.json").write_text(json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n")

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_2022_2023_V31_SUCCESSOR_DEVELOPMENT_ONLY",
        "first_valid_outcome_binding": True,
        "candidate_count": EXPECTED_N,
        "feature_dimension": EXPECTED_D,
        "feature_matrix_sha256": array_sha(X),
        "centroid_matrix_sha256": array_sha(cm),
        "package_manifest_sha256": file_sha(a.package_manifest),
        "parent_prelabel_sha256": manifest["parent_prelabel_sha256"],
        "parent_margin_sha256": manifest["parent_margin_sha256"],
        "signed_exact_radius_sha256": array_sha(scores),
        "hard_order_sha256": order_sha(hard_order),
        "local_diversified_order_sha256": order_sha(local_order),
        "fused_order_sha256": order_sha(fused_order),
        "hard_control": HARD_CONTROL,
        "parent_control": PARENT_CONTROL,
        "hard_reproduced_metrics": metric_subset(hard_metrics),
        "exact_robustness_local_only": metric_subset(local_metrics),
        "exact_robustness_equal_rank_fusion": metric_subset(fused),
        "pass_gates": gates,
        "strict_whole_shower_oof": True,
        "fold_count": 5,
        "parent_standardization": "fold-training mean/population-standard-deviation z-score",
        "classifier": "binary 1-nearest-prototype with exact frozen positive/nonpositive training references",
        "metric": "ordinary Euclidean in standardized 23D parent representation",
        "local_score": "signed exact minimal L2 perturbation to change 1-NPC class",
        "fixed_opposite_region": "intersection over current-class prototypes of ||u-wj||^2 <= ||u-wi||^2",
        "fixed_opposite_solver": {"method": "SLSQP", "ftol": SLSQP_FTOL, "maxiter": SLSQP_MAXITER, "initial_point": "query", "analytic_gradient": True, "analytic_constraint_jacobian": True},
        "qp_validation": {"primal_violation_max": PRIMAL_TOL, "projected_region_distance_tolerance": REGION_TOL, "triangle_lower_bound_tolerance": LOWER_BOUND_TOL},
        "all_opposite_prototypes_evaluated": True,
        "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
        "fusion": "equal rank-sum with immutable P19 hard order",
        "fold_diagnostics": fold_diag,
        "k_search": False,
        "prototype_pruning": False,
        "approximate_radius": False,
        "relative_margin_or_normalization": False,
        "radius_transform_search": False,
        "class_prior_weighting": False,
        "reference_deletion": False,
        "reference_relabeling": False,
        "reference_weighting": False,
        "learned_metric": False,
        "feature_search": False,
        "scaling_search": False,
        "fold_search": False,
        "diversity_search": False,
        "fusion_search": False,
        "candidate_generation_recomputed": False,
        "membership_changed": False,
        "post_result_second_search": False,
        "raw_event_rows_accessed": False,
        "raw_event_ids_accessed": False,
        "raw_hidden_label_mapping_accessed": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": BLIND,
        "sonotaco_benchmark_authorized_by_this_result": bool(passed),
        "claim_boundary": "GMN development only; PASS authorizes only a separately frozen one-shot exposed SonotaCo comparison.",
    }
    (a.output / "GMN_V31_EXACT_NPC_ROBUSTNESS_V1_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "parent": PARENT_CONTROL,
        "candidate": {k: fused[k] for k in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "recovered_at_500", "top100_dominant_precision", "mrr", "qualified_matches")},
        "local_only": {k: local_metrics[k] for k in ("recovered_at_25", "recovered_at_50", "recovered_at_100", "recovered_at_500", "top100_dominant_precision", "mrr", "qualified_matches")},
        "gates": gates,
        "signed_exact_radius_sha256": array_sha(scores),
        "total_fixed_opposite_qps": int(sum(fd["fixed_opposite_qps_solved"] for fd in fold_diag)),
        "total_slsqp_iterations": int(sum(fd["total_slsqp_iterations"] for fd in fold_diag)),
        "max_qp_primal_violation": float(max(fd["max_qp_primal_violation"] for fd in fold_diag)),
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
