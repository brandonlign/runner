#!/usr/bin/env python3
"""Fixture-backed target-excluded GMN balanced shrinkage QDA successor."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.covariance import LedoitWolf

from orbittrace_gmn_v31_principle_local_geometry_oof_v1 import run_development as parent

q = parent.q
EXPECTED_HARD = 226
FEATURE_DIM = 23
EXPECTED_FEATURE_SHA = "fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5"
EXPECTED_HARD_ORDER_SHA = "2dcaaffaefca68e877fea82ff46a68bbd4c7960dedfdd00a114311d41605b65e"
EXPECTED_PARENT_MARGIN_SHA = "f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd"
EXPECTED_FISHER_SCALED_SHA = "9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e"
EXPECTED_FISHER_METRICS = {
    "recovered_at_100": 69,
    "recovered_at_50": 41,
    "top100_dominant_precision": 0.7677499561973543,
    "mrr": 0.05055989766869564,
    "qualified_matches": 95,
}
DIVERSITY_LAMBDA = 0.8
DIVERSITY_SCALE = 1.0
BLIND = (20.0, 55.0)


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--fixture-root", type=Path, required=True)
    p.add_argument("--quality-source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_sha(x: np.ndarray) -> str:
    a = np.ascontiguousarray(x)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode())
    h.update(json.dumps(list(a.shape), separators=(",", ":")).encode())
    h.update(a.tobytes(order="C"))
    return h.hexdigest()


def order_sha(order: list[str]) -> str:
    return hashlib.sha256("\n".join(map(str, order)).encode()).hexdigest()


def verify_metrics(name: str, metrics: dict[str, Any], expected: dict[str, Any]) -> None:
    for key, value in expected.items():
        got = metrics[key]
        if isinstance(value, float):
            req(abs(float(got) - value) < 1e-15, f"{name} metric {key} changed: {got}")
        else:
            req(int(got) == value, f"{name} metric {key} changed: {got}")


def load_fixture(root: Path) -> dict[str, Any]:
    manifest = json.loads((root / "GMN_DEVELOPMENT_FIXTURE_V1.json").read_text())
    req(manifest["verdict"] == "PASS_GMN_DEVELOPMENT_FIXTURE_V1", "fixture verdict invalid")
    req(manifest["scientific_change"] is False, "fixture scientific_change invalid")
    req(manifest["fixture_role"] == "AUTHORIZED_TARGET_EXCLUDED_GMN_DEVELOPMENT_CACHE_ONLY", "fixture role invalid")
    req(manifest["candidate_count"] == EXPECTED_HARD and manifest["feature_dimension"] == FEATURE_DIM, "fixture dimensions changed")
    req(manifest["feature_matrix_sha256"] == EXPECTED_FEATURE_SHA, "fixture feature hash changed")
    req(manifest["hard_order_sha256"] == EXPECTED_HARD_ORDER_SHA, "fixture hard-order hash changed")
    req(manifest["parent_margin_sha256"] == EXPECTED_PARENT_MARGIN_SHA, "fixture parent margin hash changed")
    req(manifest["fisher_scaled_sha256"] == EXPECTED_FISHER_SCALED_SHA, "fixture Fisher score hash changed")
    req(manifest["fisher_metrics"]["recovered_at_100"] == 69, "fixture Fisher parent changed")
    req(manifest["future_fixture_use_requires_exact_hash_match"] is True, "fixture exact-match governance absent")
    req(manifest["blind_exclusion"] == [20.0, 55.0], "fixture blind interval changed")
    for key in ("sonotaco_2013_2014_access", "target_information_access", "target_region_events_accessed", "maarsy_scientific_access", "dms_scientific_access"):
        req(manifest[key] is False, f"fixture firewall flag {key} changed")

    X = np.load(root / "features.npy", allow_pickle=False)
    cm = np.load(root / "centroids.npy", allow_pickle=False)
    positive = np.load(root / "positive.npy", allow_pickle=False)
    folds_saved = np.load(root / "folds.npy", allow_pickle=False)
    parent_margin = np.load(root / "parent_margin.npy", allow_pickle=False)
    fisher_fixture = np.load(root / "fisher_scaled.npy", allow_pickle=False)
    payload = json.loads((root / "development_labels_and_memberships.json").read_text())

    req(X.shape == (EXPECTED_HARD, FEATURE_DIM) and np.isfinite(X).all(), "fixture X invalid")
    req(cm.shape == (EXPECTED_HARD, 8) and np.isfinite(cm).all(), "fixture centroids invalid")
    req(positive.shape == (EXPECTED_HARD,) and positive.dtype == np.bool_, "fixture positive vector invalid")
    req(folds_saved.shape == (EXPECTED_HARD,) and np.issubdtype(folds_saved.dtype, np.integer), "fixture fold vector invalid")
    req(parent_margin.shape == (EXPECTED_HARD,) and np.isfinite(parent_margin).all(), "fixture parent margin invalid")
    req(fisher_fixture.shape == (EXPECTED_HARD,) and np.isfinite(fisher_fixture).all(), "fixture Fisher score invalid")
    req(array_sha(X) == EXPECTED_FEATURE_SHA, "fixture X hash mismatch")
    req(array_sha(parent_margin) == EXPECTED_PARENT_MARGIN_SHA, "fixture parent margin array hash mismatch")
    req(array_sha(fisher_fixture) == EXPECTED_FISHER_SCALED_SHA, "fixture Fisher score array hash mismatch")

    hard = payload["hard_families"]
    hard_order = [str(x) for x in payload["hard_order"]]
    ids = [str(x) for x in payload["ids"]]
    groups = [str(x) for x in payload["groups"]]
    truths = {str(k): v for k, v in payload["truths"].items()}
    eligible = payload["eligible"]
    req(len(hard) == len(hard_order) == len(ids) == len(groups) == EXPECTED_HARD, "fixture family payload length changed")
    req([str(f["family_id"]) for f in hard] == ids, "fixture family IDs changed")
    req(set(hard_order) == set(ids) and order_sha(hard_order) == EXPECTED_HARD_ORDER_SHA, "fixture hard order invalid")
    req(np.array_equal(positive, np.asarray([bool(truths[fid]["positive"]) for fid in ids], dtype=bool)), "fixture positive/truth mismatch")
    folds = np.asarray([q.v1.deterministic_fold(g) for g in groups], dtype=np.int64)
    req(np.array_equal(folds, folds_saved), "fixture fold assignment changed")
    req(set(folds.tolist()) == set(range(5)), "fixture does not span five folds")

    return {
        "manifest": manifest,
        "X": X,
        "cm": cm,
        "positive": positive,
        "folds": folds,
        "parent_margin": parent_margin,
        "fisher_fixture": fisher_fixture,
        "hard": hard,
        "hard_order": hard_order,
        "ids": ids,
        "groups": groups,
        "truths": truths,
        "eligible": eligible,
    }


def oof_fisher_and_qda(X: np.ndarray, positive: np.ndarray, groups: list[str]) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    folds = np.asarray([q.v1.deterministic_fold(g) for g in groups], dtype=int)
    fisher_raw = np.zeros(len(X), dtype=float)
    qda_raw = np.zeros(len(X), dtype=float)
    diag: list[dict[str, Any]] = []

    for fold in range(5):
        train = folds != fold
        test = folds == fold
        req(train.any() and test.any(), f"empty fold {fold}")
        train_groups = {groups[i] for i in np.where(train)[0]}
        test_groups = {groups[i] for i in np.where(test)[0]}
        req(train_groups.isdisjoint(test_groups), f"group leakage fold {fold}")
        req(positive[train].any() and (~positive[train]).any(), f"fold {fold} lacks both classes")

        mu = np.mean(X[train], axis=0)
        sd = np.std(X[train], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        ztr = (X[train] - mu[None, :]) / scale[None, :]
        zte = (X[test] - mu[None, :]) / scale[None, :]
        req(np.isfinite(ztr).all() and np.isfinite(zte).all(), f"nonfinite z-space fold {fold}")

        pos = positive[train]
        neg = ~pos
        P = ztr[pos]
        N = ztr[neg]
        req(len(P) >= 2 and len(N) >= 2, f"insufficient class references fold {fold}")
        mu_pos = np.mean(P, axis=0)
        mu_neg = np.mean(N, axis=0)

        lw_pos = LedoitWolf(assume_centered=False, store_precision=False).fit(P)
        lw_neg = LedoitWolf(assume_centered=False, store_precision=False).fit(N)
        cov_pos = np.asarray(lw_pos.covariance_, dtype=float)
        cov_neg = np.asarray(lw_neg.covariance_, dtype=float)
        for name, cov, shrink in (("positive", cov_pos, float(lw_pos.shrinkage_)), ("nonpositive", cov_neg, float(lw_neg.shrinkage_))):
            req(cov.shape == (FEATURE_DIM, FEATURE_DIM), f"{name} covariance shape changed fold {fold}")
            req(np.isfinite(cov).all(), f"nonfinite {name} covariance fold {fold}")
            req(np.allclose(cov, cov.T, rtol=0.0, atol=1e-12), f"nonsymmetric {name} covariance fold {fold}")
            evals = np.linalg.eigvalsh(cov)
            req(np.isfinite(evals).all() and float(np.min(evals)) > 0.0, f"{name} covariance not positive definite fold {fold}")
            req(math.isfinite(shrink) and 0.0 <= shrink <= 1.0, f"invalid {name} shrinkage fold {fold}")

        pooled = 0.5 * (cov_pos + cov_neg)
        pooled_eigs = np.linalg.eigvalsh(pooled)
        req(np.isfinite(pooled_eigs).all() and float(np.min(pooled_eigs)) > 0.0, f"Fisher pooled covariance invalid fold {fold}")
        direction = np.linalg.solve(pooled, mu_pos - mu_neg)
        midpoint = 0.5 * (mu_pos + mu_neg)
        req(np.isfinite(direction).all() and float(np.linalg.norm(direction)) > 0.0, f"invalid Fisher direction fold {fold}")

        sign_pos, logdet_pos = np.linalg.slogdet(cov_pos)
        sign_neg, logdet_neg = np.linalg.slogdet(cov_neg)
        req(float(sign_pos) > 0.0 and float(sign_neg) > 0.0, f"nonpositive QDA covariance determinant fold {fold}")
        req(math.isfinite(float(logdet_pos)) and math.isfinite(float(logdet_neg)), f"nonfinite QDA logdet fold {fold}")
        precision_pos = np.linalg.inv(cov_pos)
        precision_neg = np.linalg.inv(cov_neg)
        req(np.isfinite(precision_pos).all() and np.isfinite(precision_neg).all(), f"nonfinite QDA precision fold {fold}")

        test_indices = np.where(test)[0]
        for j, global_i in enumerate(test_indices.tolist()):
            x = zte[j]
            fisher_raw[global_i] = float(np.dot(x - midpoint, direction))
            dp = x - mu_pos
            dn = x - mu_neg
            D_pos = float(dp @ precision_pos @ dp)
            D_neg = float(dn @ precision_neg @ dn)
            req(math.isfinite(D_pos) and math.isfinite(D_neg) and D_pos >= 0.0 and D_neg >= 0.0, f"invalid QDA quadratic form fold {fold}")
            qda_raw[global_i] = 0.5 * (D_neg + float(logdet_neg) - D_pos - float(logdet_pos))

        diag.append({
            "fold": fold,
            "train_examples": int(train.sum()),
            "test_examples": int(test.sum()),
            "positive_references": int(pos.sum()),
            "nonpositive_references": int(neg.sum()),
            "zero_variance_features": int(np.sum(sd == 0.0)),
            "positive_ledoit_wolf_shrinkage": float(lw_pos.shrinkage_),
            "nonpositive_ledoit_wolf_shrinkage": float(lw_neg.shrinkage_),
            "positive_logdet": float(logdet_pos),
            "nonpositive_logdet": float(logdet_neg),
            "positive_min_eigenvalue": float(np.min(np.linalg.eigvalsh(cov_pos))),
            "nonpositive_min_eigenvalue": float(np.min(np.linalg.eigvalsh(cov_neg))),
        })

    req(np.isfinite(fisher_raw).all(), "nonfinite reconstructed Fisher score")
    req(np.isfinite(qda_raw).all(), "nonfinite QDA score")
    return fisher_raw, qda_raw, diag


def main() -> int:
    a = args()
    a.output.mkdir(parents=True, exist_ok=True)
    req(sha(a.quality_source) == parent.QUALITY_SHA, "active GMN ranker source changed")
    fx = load_fixture(a.fixture_root)

    X = fx["X"]
    positive = fx["positive"]
    groups = fx["groups"]
    fisher_raw, qda_raw, fold_diag = oof_fisher_and_qda(X, positive, groups)

    parent_margin = fx["parent_margin"]
    parent_margin_scale = float(np.median(np.abs(parent_margin)))
    fisher_raw_scale = float(np.median(np.abs(fisher_raw)))
    req(math.isfinite(parent_margin_scale) and parent_margin_scale > 0.0, "invalid parent margin scale")
    req(math.isfinite(fisher_raw_scale) and fisher_raw_scale > 0.0, "invalid Fisher raw scale")
    fisher_unit_factor = float(parent_margin_scale / fisher_raw_scale)
    fisher_scaled = fisher_raw * fisher_unit_factor
    req(array_sha(fisher_scaled) == EXPECTED_FISHER_SCALED_SHA, "binding Fisher scaled score did not reproduce")
    req(np.array_equal(fisher_scaled, fx["fisher_fixture"]), "fixture Fisher score differs from exact reconstruction")

    ids = fx["ids"]
    hard_order = fx["hard_order"]
    hard = fx["hard"]
    truths = fx["truths"]
    eligible = fx["eligible"]
    cm = fx["cm"]
    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}
    tie = [(hard_rank[fid], fid) for fid in ids]

    fisher_idx = q.diversity_order(fisher_scaled, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    fisher_local_order = [ids[i] for i in fisher_idx]
    fisher_fused_order = parent.equal_rank_fusion(hard_order, fisher_local_order)
    fisher_metrics = q.v1.monotone_metrics(hard, fisher_fused_order, truths, eligible)
    verify_metrics("Fisher parent", fisher_metrics, EXPECTED_FISHER_METRICS)

    fisher_scaled_scale = float(np.median(np.abs(fisher_scaled)))
    qda_scale = float(np.median(np.abs(qda_raw)))
    req(math.isfinite(fisher_scaled_scale) and fisher_scaled_scale > 0.0, "invalid scaled Fisher typical magnitude")
    req(math.isfinite(qda_scale) and qda_scale > 0.0, "invalid QDA typical magnitude")
    qda_unit_factor = float(fisher_scaled_scale / qda_scale)
    req(math.isfinite(qda_unit_factor) and qda_unit_factor > 0.0, "invalid QDA unit factor")
    qda_scaled = qda_raw * qda_unit_factor
    req(np.isfinite(qda_scaled).all(), "nonfinite scaled QDA score")

    qda_idx = q.diversity_order(qda_scaled, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    qda_local_order = [ids[i] for i in qda_idx]
    qda_fused_order = parent.equal_rank_fusion(hard_order, qda_local_order)
    candidate = q.v1.monotone_metrics(hard, qda_fused_order, truths, eligible)
    req(int(candidate["qualified_matches"]) == EXPECTED_FISHER_METRICS["qualified_matches"], "qualified universe changed")

    gates = {
        "recovered_at_100_strictly_above_fisher_parent": int(candidate["recovered_at_100"]) > EXPECTED_FISHER_METRICS["recovered_at_100"],
        "recovered_at_50_not_below_fisher_parent": int(candidate["recovered_at_50"]) >= EXPECTED_FISHER_METRICS["recovered_at_50"],
        "top100_precision_not_below_fisher_parent": float(candidate["top100_dominant_precision"]) >= EXPECTED_FISHER_METRICS["top100_dominant_precision"],
        "mrr_not_below_fisher_parent": float(candidate["mrr"]) >= EXPECTED_FISHER_METRICS["mrr"],
        "qualified_count_identical": int(candidate["qualified_matches"]) == EXPECTED_FISHER_METRICS["qualified_matches"],
    }
    passed = all(gates.values())
    verdict = "PASS_GMN_BALANCED_SHRINKAGE_QDA_OOF" if passed else "FAIL_GMN_BALANCED_SHRINKAGE_QDA_OOF"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_BALANCED_SHRINKAGE_QDA_ARCHITECTURAL_SUCCESSOR_ONLY",
        "first_valid_outcome_binding": True,
        "candidate_count": EXPECTED_HARD,
        "feature_dimension": FEATURE_DIM,
        "fixture_verdict": fx["manifest"]["verdict"],
        "fixture_scientific_change": False,
        "feature_matrix_sha256": array_sha(X),
        "parent_margin_sha256": array_sha(parent_margin),
        "fisher_reconstructed_raw_sha256": array_sha(fisher_raw),
        "fisher_reconstructed_scaled_sha256": array_sha(fisher_scaled),
        "qda_raw_sha256": array_sha(qda_raw),
        "qda_scaled_sha256": array_sha(qda_scaled),
        "fisher_parent_median_absolute_scaled_score": fisher_scaled_scale,
        "qda_median_absolute_raw_score": qda_scale,
        "qda_unit_factor": qda_unit_factor,
        "mechanism": "equal-prior separate-class Ledoit-Wolf Gaussian quadratic discriminant",
        "positive_covariance_estimator": "LedoitWolf(assume_centered=False,store_precision=False)",
        "nonpositive_covariance_estimator": "LedoitWolf(assume_centered=False,store_precision=False)",
        "class_prior": "equal",
        "strict_whole_shower_oof": True,
        "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
        "fusion": "equal rank-sum with immutable P19 hard order",
        "fisher_parent": parent.metric_subset(fisher_metrics),
        "candidate": parent.metric_subset(candidate),
        "pass_gates": gates,
        "fold_diagnostics": fold_diag,
        "class_prior_search": False,
        "covariance_pooling_search": False,
        "covariance_estimator_search": False,
        "regularization_search": False,
        "feature_search": False,
        "dimensionality_reduction_search": False,
        "fisher_blend_search": False,
        "probability_calibration_search": False,
        "threshold_search": False,
        "scale_statistic_search": False,
        "unit_transform_search": False,
        "diversity_search": False,
        "fusion_search": False,
        "candidate_generation_recomputed": False,
        "membership_changed": False,
        "family_deletion": False,
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "blind_exclusion": list(BLIND),
    }
    out = a.output / "GMN_BALANCED_SHRINKAGE_QDA_OOF_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "fisher100": fisher_metrics["recovered_at_100"],
        "candidate100": candidate["recovered_at_100"],
        "fisher50": fisher_metrics["recovered_at_50"],
        "candidate50": candidate["recovered_at_50"],
        "fisher_precision": fisher_metrics["top100_dominant_precision"],
        "candidate_precision": candidate["top100_dominant_precision"],
        "fisher_mrr": fisher_metrics["mrr"],
        "candidate_mrr": candidate["mrr"],
        "qualified": candidate["qualified_matches"],
        "qda_unit_factor": qda_unit_factor,
        "qda_scaled_sha256": array_sha(qda_scaled),
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
