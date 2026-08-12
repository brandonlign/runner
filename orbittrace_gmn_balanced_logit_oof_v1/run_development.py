#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

from orbittrace_gmn_v31_principle_local_geometry_oof_v1 import run_development as parent

q = parent.q
N = 226
D = 23
DIV_L = 0.8
DIV_S = 1.0
BLIND = (20.0, 55.0)
FEATURE_SHA = "fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5"
ORDER_SHA = "2dcaaffaefca68e877fea82ff46a68bbd4c7960dedfdd00a114311d41605b65e"
MARGIN_SHA = "f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd"
FISHER_SHA = "9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e"
PARENT = {
    "recovered_at_100": 69,
    "recovered_at_50": 41,
    "top100_dominant_precision": 0.7677499561973543,
    "mrr": 0.05055989766869564,
    "qualified_matches": 95,
}


def req(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def verify_parent(metrics: dict) -> None:
    for key, expected in PARENT.items():
        got = metrics[key]
        if isinstance(expected, float):
            req(abs(float(got) - expected) < 1e-15, f"parent {key} changed: {got}")
        else:
            req(int(got) == expected, f"parent {key} changed: {got}")


def load_fixture(root: Path):
    manifest = json.loads((root / "GMN_DEVELOPMENT_FIXTURE_V1.json").read_text())
    req(manifest["verdict"] == "PASS_GMN_DEVELOPMENT_FIXTURE_V1", "fixture verdict changed")
    req(manifest["scientific_change"] is False, "fixture scientific role changed")
    req(manifest["feature_matrix_sha256"] == FEATURE_SHA, "fixture feature identity changed")
    req(manifest["hard_order_sha256"] == ORDER_SHA, "fixture hard-order identity changed")
    req(manifest["parent_margin_sha256"] == MARGIN_SHA, "fixture parent-margin identity changed")
    req(manifest["fisher_scaled_sha256"] == FISHER_SHA, "fixture Fisher identity changed")
    req(manifest["blind_exclusion"] == [20.0, 55.0], "blind exclusion changed")
    for key in (
        "sonotaco_2013_2014_access",
        "target_information_access",
        "target_region_events_accessed",
        "maarsy_scientific_access",
        "dms_scientific_access",
    ):
        req(manifest[key] is False, f"firewall changed: {key}")

    X = np.load(root / "features.npy", allow_pickle=False)
    cm = np.load(root / "centroids.npy", allow_pickle=False)
    y = np.load(root / "positive.npy", allow_pickle=False)
    fisher_scaled = np.load(root / "fisher_scaled.npy", allow_pickle=False)
    parent_margin = np.load(root / "parent_margin.npy", allow_pickle=False)
    payload = json.loads((root / "development_labels_and_memberships.json").read_text())

    req(X.shape == (N, D) and np.isfinite(X).all(), "feature matrix changed")
    req(parent.array_sha(X) == FEATURE_SHA, "feature matrix hash changed")
    req(parent.array_sha(fisher_scaled) == FISHER_SHA, "Fisher score hash changed")
    req(parent.array_sha(parent_margin) == MARGIN_SHA, "parent margin hash changed")

    ids = list(map(str, payload["ids"]))
    order = list(map(str, payload["hard_order"]))
    groups = list(map(str, payload["groups"]))
    hard = payload["hard_families"]
    truths = {str(k): v for k, v in payload["truths"].items()}
    eligible = payload["eligible"]

    req(len(ids) == N and len(set(ids)) == N, "family identities changed")
    req(parent.order_sha(order) == ORDER_SHA, "hard order hash changed")
    req([str(f["family_id"]) for f in hard] == ids, "hard-family payload order changed")
    req(len(groups) == N, "group vector changed")
    req(np.array_equal(y, np.asarray([bool(truths[i]["positive"]) for i in ids], dtype=bool)), "target changed")
    req(y.dtype == np.bool_ or y.dtype == bool, "target dtype changed")
    req(y.any() and (~y).any(), "target degenerate")

    return X, cm, y.astype(bool), fisher_scaled, parent_margin, ids, order, groups, hard, truths, eligible, manifest


def balanced_logit_oof(X: np.ndarray, y: np.ndarray, groups: list[str]):
    folds = np.asarray([q.v1.deterministic_fold(g) for g in groups], dtype=int)
    req(set(folds.tolist()) == set(range(5)), "five-fold assignment changed")
    out = np.zeros(len(X), dtype=float)
    diagnostics = []

    for fold in range(5):
        train = folds != fold
        test = folds == fold
        train_idx = np.where(train)[0]
        test_idx = np.where(test)[0]
        req(train.any() and test.any(), f"empty fold {fold}")
        train_groups = {groups[i] for i in train_idx.tolist()}
        test_groups = {groups[i] for i in test_idx.tolist()}
        req(train_groups.isdisjoint(test_groups), f"group leakage fold {fold}")
        req(y[train].any() and (~y[train]).any(), f"fold {fold} lacks both classes")

        mu = np.mean(X[train], axis=0)
        sd = np.std(X[train], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        ztr = (X[train] - mu[None, :]) / scale[None, :]
        zte = (X[test] - mu[None, :]) / scale[None, :]
        req(np.isfinite(ztr).all() and np.isfinite(zte).all(), f"nonfinite z-space fold {fold}")

        model = LogisticRegression(
            penalty=None,
            solver="lbfgs",
            fit_intercept=True,
            class_weight="balanced",
            tol=1e-12,
            max_iter=10000,
        )
        model.fit(ztr, y[train].astype(int))
        n_iter = int(np.max(model.n_iter_))
        req(n_iter < 10000, f"logit did not converge fold {fold}")
        req(model.coef_.shape == (1, D), f"coefficient shape changed fold {fold}")
        req(model.intercept_.shape == (1,), f"intercept shape changed fold {fold}")
        req(np.isfinite(model.coef_).all() and np.isfinite(model.intercept_).all(), f"nonfinite logit fit fold {fold}")

        score = np.asarray(model.decision_function(zte), dtype=float)
        req(score.shape == (int(test.sum()),), f"decision shape changed fold {fold}")
        req(np.isfinite(score).all(), f"nonfinite held-out logit fold {fold}")
        out[test_idx] = score

        diagnostics.append({
            "fold": fold,
            "train_examples": int(train.sum()),
            "test_examples": int(test.sum()),
            "positive_references": int(y[train].sum()),
            "nonpositive_references": int((~y[train]).sum()),
            "train_group_count": len(train_groups),
            "test_group_count": len(test_groups),
            "zero_variance_features": int(np.sum(sd == 0.0)),
            "n_iter": n_iter,
            "coefficient_norm": float(np.linalg.norm(model.coef_[0])),
            "intercept": float(model.intercept_[0]),
        })

    req(np.isfinite(out).all(), "nonfinite complete OOF logit")
    return out, diagnostics


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture-root", type=Path, required=True)
    ap.add_argument("--quality-source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    req(parent.sha(args.quality_source) == parent.QUALITY_SHA, "ranker source changed")
    X, cm, y, fisher_scaled, parent_margin, ids, order, groups, hard, truths, eligible, manifest = load_fixture(args.fixture_root)

    hard_rank = {fid: i + 1 for i, fid in enumerate(order)}
    tie = [(hard_rank[fid], fid) for fid in ids]

    # Reproduce the exact strongest Fisher parent before interpreting the candidate.
    parent_idx = q.diversity_order(fisher_scaled, cm, DIV_L, DIV_S, tie)
    parent_local_order = [ids[i] for i in parent_idx]
    parent_fused_order = parent.equal_rank_fusion(order, parent_local_order)
    parent_metrics = q.v1.monotone_metrics(hard, parent_fused_order, truths, eligible)
    verify_parent(parent_metrics)
    req(int(parent_metrics["recovered_at_25"]) == 24, "parent recovered@25 changed")

    raw, fold_diagnostics = balanced_logit_oof(X, y, groups)
    parent_scale = float(np.median(np.abs(parent_margin)))
    raw_scale = float(np.median(np.abs(raw)))
    req(math.isfinite(parent_scale) and parent_scale > 0.0, "invalid parent score unit")
    req(math.isfinite(raw_scale) and raw_scale > 0.0, "invalid logit score unit")
    unit_factor = float(parent_scale / raw_scale)
    scaled = raw * unit_factor
    req(np.isfinite(scaled).all(), "nonfinite scaled logit")

    idx = q.diversity_order(scaled, cm, DIV_L, DIV_S, tie)
    local_order = [ids[i] for i in idx]
    fused_order = parent.equal_rank_fusion(order, local_order)
    candidate = q.v1.monotone_metrics(hard, fused_order, truths, eligible)
    req(int(candidate["qualified_matches"]) == 95, "qualified universe changed")

    gates = {
        "recovered_at_100_strictly_above_fisher_parent": int(candidate["recovered_at_100"]) > 69,
        "recovered_at_50_not_below_fisher_parent": int(candidate["recovered_at_50"]) >= 41,
        "top100_precision_not_below_fisher_parent": float(candidate["top100_dominant_precision"]) >= PARENT["top100_dominant_precision"],
        "mrr_not_below_fisher_parent": float(candidate["mrr"]) >= PARENT["mrr"],
        "qualified_count_identical": int(candidate["qualified_matches"]) == 95,
    }
    passed = all(gates.values())
    verdict = "PASS_GMN_BALANCED_LOGIT_OOF_V1" if passed else "FAIL_GMN_BALANCED_LOGIT_OOF_V1"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_BALANCED_DISCRIMINATIVE_LOG_LIKELIHOOD_SUCCESSOR_ONLY",
        "first_valid_outcome_binding": True,
        "candidate_count": N,
        "feature_dimension": D,
        "feature_matrix_sha256": parent.array_sha(X),
        "hard_order_sha256": parent.order_sha(order),
        "parent_margin_sha256": parent.array_sha(parent_margin),
        "fisher_parent_scaled_sha256": parent.array_sha(fisher_scaled),
        "logit_raw_sha256": parent.array_sha(raw),
        "logit_scaled_sha256": parent.array_sha(scaled),
        "parent_margin_median_absolute_score": parent_scale,
        "logit_raw_median_absolute_score": raw_scale,
        "unit_factor": unit_factor,
        "estimator": {
            "class": "sklearn.linear_model.LogisticRegression",
            "penalty": None,
            "solver": "lbfgs",
            "fit_intercept": True,
            "class_weight": "balanced",
            "tol": 1e-12,
            "max_iter": 10000,
        },
        "mechanism": "strict-whole-shower OOF equal-class direct conditional linear log-likelihood",
        "strict_whole_shower_oof": True,
        "diversity": {"lambda": DIV_L, "scale": DIV_S},
        "fusion": "equal rank-sum with immutable P19 hard order",
        "fisher_parent": parent.metric_subset(parent_metrics),
        "candidate": parent.metric_subset(candidate),
        "candidate_recovered_at_25": int(candidate["recovered_at_25"]),
        "pass_gates": gates,
        "fold_diagnostics": fold_diagnostics,
        "regularization_search": False,
        "penalty_search": False,
        "solver_search": False,
        "class_weight_search": False,
        "group_weighting": False,
        "feature_search": False,
        "feature_transform_search": False,
        "interaction_search": False,
        "nonlinear_basis_search": False,
        "calibration_search": False,
        "threshold_search": False,
        "score_blend_search": False,
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
    out = args.output / "GMN_BALANCED_LOGIT_OOF_V1_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "fisher100": parent_metrics["recovered_at_100"],
        "candidate100": candidate["recovered_at_100"],
        "fisher50": parent_metrics["recovered_at_50"],
        "candidate50": candidate["recovered_at_50"],
        "fisher25": parent_metrics["recovered_at_25"],
        "candidate25": candidate["recovered_at_25"],
        "fisher_precision": parent_metrics["top100_dominant_precision"],
        "candidate_precision": candidate["top100_dominant_precision"],
        "fisher_mrr": parent_metrics["mrr"],
        "candidate_mrr": candidate["mrr"],
        "qualified": candidate["qualified_matches"],
        "unit_factor": unit_factor,
        "scaled_sha256": parent.array_sha(scaled),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
