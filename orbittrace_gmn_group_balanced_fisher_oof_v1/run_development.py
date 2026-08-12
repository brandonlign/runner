#!/usr/bin/env python3
"""Fixture-backed target-excluded GMN group-balanced Fisher successor."""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
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
EXPECTED_GROUP_STRUCTURE = {
    "groups": 201,
    "positive_families": 111,
    "nonpositive_families": 115,
    "positive_class_groups": 95,
    "nonpositive_class_groups": 114,
    "mixed_class_groups": 8,
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


def verify_metrics(name: str, metrics: dict[str, Any], expected: dict[str, Any]) -> None:
    for key, value in expected.items():
        got = metrics[key]
        if isinstance(value, float):
            req(abs(float(got) - value) < 1e-15, f"{name} metric {key} changed: {got}")
        else:
            req(int(got) == value, f"{name} metric {key} changed: {got}")


def group_structure(groups: list[str], positive: np.ndarray) -> dict[str, int]:
    by_group: dict[str, list[bool]] = defaultdict(list)
    for g, y in zip(groups, positive.tolist()):
        by_group[str(g)].append(bool(y))
    return {
        "groups": len(by_group),
        "positive_families": int(positive.sum()),
        "nonpositive_families": int((~positive).sum()),
        "positive_class_groups": sum(any(v) for v in by_group.values()),
        "nonpositive_class_groups": sum(any(not y for y in v) for v in by_group.values()),
        "mixed_class_groups": sum(any(v) and any(not y for y in v) for v in by_group.values()),
    }


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
    fisher_parent = np.load(root / "fisher_scaled.npy", allow_pickle=False)
    parent_margin = np.load(root / "parent_margin.npy", allow_pickle=False)
    payload = json.loads((root / "development_labels_and_memberships.json").read_text())

    req(X.shape == (EXPECTED_HARD, FEATURE_DIM) and np.isfinite(X).all(), "fixture feature matrix invalid")
    req(cm.shape == (EXPECTED_HARD, 8) and np.isfinite(cm).all(), "fixture centroid matrix invalid")
    req(positive.shape == (EXPECTED_HARD,) and positive.dtype == np.bool_, "fixture positive vector invalid")
    req(fisher_parent.shape == (EXPECTED_HARD,) and np.isfinite(fisher_parent).all(), "fixture Fisher score invalid")
    req(parent_margin.shape == (EXPECTED_HARD,) and np.isfinite(parent_margin).all(), "fixture parent margin invalid")
    req(parent.array_sha(X) == EXPECTED_FEATURE_SHA, "fixture feature array hash mismatch")
    req(parent.array_sha(fisher_parent) == EXPECTED_FISHER_SCALED_SHA, "fixture Fisher array hash mismatch")
    req(parent.array_sha(parent_margin) == EXPECTED_PARENT_MARGIN_SHA, "fixture parent margin array hash mismatch")

    hard = payload["hard_families"]
    hard_order = [str(x) for x in payload["hard_order"]]
    ids = [str(x) for x in payload["ids"]]
    groups = [str(x) for x in payload["groups"]]
    truths = {str(k): v for k, v in payload["truths"].items()}
    eligible = payload["eligible"]
    req(len(hard) == len(hard_order) == len(ids) == len(groups) == EXPECTED_HARD, "fixture family payload length changed")
    req([str(f["family_id"]) for f in hard] == ids, "fixture family IDs changed")
    req(parent.order_sha(hard_order) == EXPECTED_HARD_ORDER_SHA and set(hard_order) == set(ids), "fixture hard order invalid")
    req(np.array_equal(positive, np.asarray([bool(truths[fid]["positive"]) for fid in ids], dtype=bool)), "fixture positive/truth mismatch")
    folds = np.asarray([q.v1.deterministic_fold(g) for g in groups], dtype=np.int64)
    req(np.array_equal(folds, folds_saved), "fixture fold assignment changed")
    req(set(folds.tolist()) == set(range(5)), "fixture does not span five folds")
    structure = group_structure(groups, positive)
    req(structure == EXPECTED_GROUP_STRUCTURE, f"fixture group structure changed: {structure}")

    return {
        "manifest": manifest,
        "X": X,
        "cm": cm,
        "positive": positive,
        "folds": folds,
        "fisher_parent": fisher_parent,
        "parent_margin": parent_margin,
        "hard": hard,
        "hard_order": hard_order,
        "ids": ids,
        "groups": groups,
        "truths": truths,
        "eligible": eligible,
        "group_structure": structure,
    }


def class_group_prototypes(
    ztr: np.ndarray,
    train_groups: list[str],
    train_positive: np.ndarray,
    class_value: bool,
) -> tuple[np.ndarray, list[str], dict[str, int]]:
    by_group: dict[str, list[int]] = defaultdict(list)
    for local_i, (g, y) in enumerate(zip(train_groups, train_positive.tolist())):
        if bool(y) == class_value:
            by_group[str(g)].append(local_i)
    keys = sorted(by_group)
    req(len(keys) >= 2, f"too few {'positive' if class_value else 'nonpositive'} class-groups")
    prototypes = np.vstack([np.mean(ztr[by_group[g]], axis=0) for g in keys])
    req(prototypes.shape == (len(keys), FEATURE_DIM) and np.isfinite(prototypes).all(), "invalid class-group prototype matrix")
    sizes = [len(by_group[g]) for g in keys]
    diag = {
        "groups": len(keys),
        "families": int(sum(sizes)),
        "collapsed_duplicates": int(sum(sizes) - len(keys)),
        "max_families_in_one_class_group": int(max(sizes)),
    }
    return prototypes, keys, diag


def oof_group_balanced_fisher(
    X: np.ndarray,
    positive: np.ndarray,
    groups: list[str],
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    folds = np.asarray([q.v1.deterministic_fold(g) for g in groups], dtype=int)
    req(set(folds.tolist()) == set(range(5)), "five-fold assignment changed")
    score = np.zeros(len(X), dtype=float)
    diagnostics: list[dict[str, Any]] = []

    for fold in range(5):
        train = folds != fold
        test = folds == fold
        req(train.any() and test.any(), f"empty fold {fold}")
        global_train_idx = np.where(train)[0]
        global_test_idx = np.where(test)[0]
        train_group_set = {groups[i] for i in global_train_idx.tolist()}
        test_group_set = {groups[i] for i in global_test_idx.tolist()}
        req(train_group_set.isdisjoint(test_group_set), f"group leakage fold {fold}")
        req(positive[train].any() and (~positive[train]).any(), f"fold {fold} lacks both classes")

        mu = np.mean(X[train], axis=0)
        sd = np.std(X[train], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        ztr = (X[train] - mu[None, :]) / scale[None, :]
        zte = (X[test] - mu[None, :]) / scale[None, :]
        req(np.isfinite(ztr).all() and np.isfinite(zte).all(), f"nonfinite z-space fold {fold}")

        train_groups_ordered = [groups[i] for i in global_train_idx.tolist()]
        train_positive = positive[train]
        P, positive_group_keys, pdiag = class_group_prototypes(ztr, train_groups_ordered, train_positive, True)
        N, nonpositive_group_keys, ndiag = class_group_prototypes(ztr, train_groups_ordered, train_positive, False)
        mixed_train_groups = len(set(positive_group_keys).intersection(nonpositive_group_keys))

        mu_pos = np.mean(P, axis=0)
        mu_neg = np.mean(N, axis=0)
        lw_pos = LedoitWolf(assume_centered=False, store_precision=False).fit(P)
        lw_neg = LedoitWolf(assume_centered=False, store_precision=False).fit(N)
        cov_pos = np.asarray(lw_pos.covariance_, dtype=float)
        cov_neg = np.asarray(lw_neg.covariance_, dtype=float)
        for name, cov, shrink in (
            ("positive", cov_pos, float(lw_pos.shrinkage_)),
            ("nonpositive", cov_neg, float(lw_neg.shrinkage_)),
        ):
            req(cov.shape == (FEATURE_DIM, FEATURE_DIM), f"{name} covariance shape changed fold {fold}")
            req(np.isfinite(cov).all(), f"nonfinite {name} covariance fold {fold}")
            req(np.allclose(cov, cov.T, rtol=0.0, atol=1e-12), f"nonsymmetric {name} covariance fold {fold}")
            req(math.isfinite(shrink) and 0.0 <= shrink <= 1.0, f"invalid {name} shrinkage fold {fold}")

        pooled = 0.5 * (cov_pos + cov_neg)
        req(np.isfinite(pooled).all() and np.allclose(pooled, pooled.T, rtol=0.0, atol=1e-12), f"invalid pooled covariance fold {fold}")
        eig = np.linalg.eigvalsh(pooled)
        req(np.isfinite(eig).all() and float(np.min(eig)) > 0.0, f"pooled covariance not positive definite fold {fold}")
        direction = np.linalg.solve(pooled, mu_pos - mu_neg)
        midpoint = 0.5 * (mu_pos + mu_neg)
        req(np.isfinite(direction).all() and float(np.linalg.norm(direction)) > 0.0, f"invalid Fisher direction fold {fold}")

        for j, global_i in enumerate(global_test_idx.tolist()):
            score[global_i] = float(np.dot(zte[j] - midpoint, direction))

        diagnostics.append({
            "fold": fold,
            "train_examples": int(train.sum()),
            "test_examples": int(test.sum()),
            "train_groups": len(train_group_set),
            "test_groups": len(test_group_set),
            "zero_variance_features": int(np.sum(sd == 0.0)),
            "positive_prototypes": pdiag,
            "nonpositive_prototypes": ndiag,
            "mixed_class_training_groups": mixed_train_groups,
            "positive_ledoit_wolf_shrinkage": float(lw_pos.shrinkage_),
            "nonpositive_ledoit_wolf_shrinkage": float(lw_neg.shrinkage_),
            "pooled_min_eigenvalue": float(np.min(eig)),
            "pooled_max_eigenvalue": float(np.max(eig)),
            "fisher_direction_norm": float(np.linalg.norm(direction)),
        })

    req(np.isfinite(score).all(), "nonfinite group-balanced Fisher OOF score")
    return score, diagnostics


def main() -> int:
    a = args()
    a.output.mkdir(parents=True, exist_ok=True)
    req(parent.sha(a.quality_source) == parent.QUALITY_SHA, "active GMN ranker source changed")
    fx = load_fixture(a.fixture_root)

    ids = fx["ids"]
    hard_order = fx["hard_order"]
    hard = fx["hard"]
    truths = fx["truths"]
    eligible = fx["eligible"]
    cm = fx["cm"]
    fisher_parent_score = fx["fisher_parent"]
    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}
    tie = [(hard_rank[fid], fid) for fid in ids]

    # Reproduce the exact binding Fisher parent ranking from the immutable fixture before successor interpretation.
    fisher_idx = q.diversity_order(fisher_parent_score, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    fisher_local_order = [ids[i] for i in fisher_idx]
    fisher_fused_order = parent.equal_rank_fusion(hard_order, fisher_local_order)
    fisher_metrics = q.v1.monotone_metrics(hard, fisher_fused_order, truths, eligible)
    verify_metrics("Fisher parent", fisher_metrics, EXPECTED_FISHER_METRICS)

    group_raw, fold_diag = oof_group_balanced_fisher(fx["X"], fx["positive"], fx["groups"])
    fisher_scale = float(np.median(np.abs(fisher_parent_score)))
    group_scale = float(np.median(np.abs(group_raw)))
    req(math.isfinite(fisher_scale) and fisher_scale > 0.0, "invalid Fisher parent typical score")
    req(math.isfinite(group_scale) and group_scale > 0.0, "invalid group-balanced typical score")
    unit_factor = float(fisher_scale / group_scale)
    req(math.isfinite(unit_factor) and unit_factor > 0.0, "invalid group-balanced unit factor")
    group_scaled = group_raw * unit_factor
    req(np.isfinite(group_scaled).all(), "nonfinite scaled group-balanced score")

    idx = q.diversity_order(group_scaled, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    local_order = [ids[i] for i in idx]
    fused_order = parent.equal_rank_fusion(hard_order, local_order)
    candidate = q.v1.monotone_metrics(hard, fused_order, truths, eligible)
    req(int(candidate["qualified_matches"]) == EXPECTED_FISHER_METRICS["qualified_matches"], "qualified universe changed")

    gates = {
        "recovered_at_100_strictly_above_fisher_parent": int(candidate["recovered_at_100"]) > EXPECTED_FISHER_METRICS["recovered_at_100"],
        "recovered_at_50_not_below_fisher_parent": int(candidate["recovered_at_50"]) >= EXPECTED_FISHER_METRICS["recovered_at_50"],
        "top100_precision_not_below_fisher_parent": float(candidate["top100_dominant_precision"]) >= EXPECTED_FISHER_METRICS["top100_dominant_precision"],
        "mrr_not_below_fisher_parent": float(candidate["mrr"]) >= EXPECTED_FISHER_METRICS["mrr"],
        "qualified_count_identical": int(candidate["qualified_matches"]) == EXPECTED_FISHER_METRICS["qualified_matches"],
    }
    passed = all(gates.values())
    verdict = "PASS_GMN_GROUP_BALANCED_FISHER_OOF" if passed else "FAIL_GMN_GROUP_BALANCED_FISHER_OOF"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_GROUP_BALANCED_FISHER_SUCCESSOR_ONLY",
        "first_valid_outcome_binding": True,
        "candidate_count": EXPECTED_HARD,
        "feature_dimension": FEATURE_DIM,
        "fixture_verdict": fx["manifest"]["verdict"],
        "feature_matrix_sha256": parent.array_sha(fx["X"]),
        "hard_order_sha256": parent.order_sha(hard_order),
        "parent_margin_sha256": parent.array_sha(fx["parent_margin"]),
        "fisher_parent_scaled_sha256": parent.array_sha(fisher_parent_score),
        "group_structure": fx["group_structure"],
        "group_raw_sha256": parent.array_sha(group_raw),
        "group_scaled_sha256": parent.array_sha(group_scaled),
        "fisher_parent_median_absolute_score": fisher_scale,
        "group_raw_median_absolute_score": group_scale,
        "unit_factor": unit_factor,
        "mechanism": "class-conditional OOF group-centroid balanced shrinkage Fisher",
        "prototype_rule": "one arithmetic-mean z-space prototype per (OOF group,recoverability class); mixed groups contribute one prototype to each represented class",
        "heldout_unit": "individual candidate family",
        "covariance": "separate positive/nonpositive LedoitWolf on prototypes then equal 0.5/0.5 pooling",
        "strict_whole_shower_oof": True,
        "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
        "fusion": "equal rank-sum with immutable P19 hard order",
        "fisher_parent": parent.metric_subset(fisher_metrics),
        "candidate": parent.metric_subset(candidate),
        "pass_gates": gates,
        "fold_diagnostics": fold_diag,
        "prototype_statistic_search": False,
        "prototype_weight_search": False,
        "group_weight_search": False,
        "mixed_group_treatment_search": False,
        "prototype_family_blend_search": False,
        "class_prior_search": False,
        "covariance_estimator_search": False,
        "regularization_search": False,
        "group_size_feature_used": False,
        "feature_search": False,
        "dimensionality_reduction_search": False,
        "scale_statistic_search": False,
        "unit_transform_search": False,
        "threshold_search": False,
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
    out = a.output / "GMN_GROUP_BALANCED_FISHER_OOF_RESULT.json"
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
        "group_structure": fx["group_structure"],
        "unit_factor": unit_factor,
        "group_scaled_sha256": parent.array_sha(group_scaled),
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
