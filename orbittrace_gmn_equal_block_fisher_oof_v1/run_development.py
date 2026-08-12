#!/usr/bin/env python3
"""Fixture-backed target-excluded GMN equal-physical-block Fisher successor."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.covariance import LedoitWolf

from orbittrace_gmn_v31_principle_local_geometry_oof_v1 import run_development as parent
from orbittrace_gmn_balanced_shrinkage_fisher_oof_v1 import run_development as fisher_parent

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
BLOCKS = {
    "structural": (0, 10),
    "cohesion": (10, 17),
    "neighbor": (17, 23),
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
    parent_margin = np.load(root / "parent_margin.npy", allow_pickle=False)
    fisher_fixture = np.load(root / "fisher_scaled.npy", allow_pickle=False)
    payload = json.loads((root / "development_labels_and_memberships.json").read_text())

    req(X.shape == (EXPECTED_HARD, FEATURE_DIM) and np.isfinite(X).all(), "fixture feature matrix invalid")
    req(cm.shape == (EXPECTED_HARD, 8) and np.isfinite(cm).all(), "fixture centroid matrix invalid")
    req(positive.shape == (EXPECTED_HARD,) and positive.dtype == np.bool_, "fixture positive vector invalid")
    req(parent.array_sha(X) == EXPECTED_FEATURE_SHA, "fixture feature array hash mismatch")
    req(parent.array_sha(parent_margin) == EXPECTED_PARENT_MARGIN_SHA, "fixture parent margin array hash mismatch")
    req(parent.array_sha(fisher_fixture) == EXPECTED_FISHER_SCALED_SHA, "fixture Fisher array hash mismatch")

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
    folds = np.asarray([q.v1.deterministic_fold(g) for g in groups], dtype=int)
    req(set(folds.tolist()) == set(range(5)), "fixture fold assignment changed")

    return {
        "manifest": manifest,
        "X": X,
        "cm": cm,
        "positive": positive,
        "parent_margin": parent_margin,
        "fisher_fixture": fisher_fixture,
        "hard": hard,
        "hard_order": hard_order,
        "ids": ids,
        "groups": groups,
        "truths": truths,
        "eligible": eligible,
    }


def block_fisher_scores(X: np.ndarray, positive: np.ndarray, groups: list[str]) -> tuple[dict[str, np.ndarray], list[dict[str, Any]]]:
    folds = np.asarray([q.v1.deterministic_fold(g) for g in groups], dtype=int)
    out = {name: np.zeros(len(X), dtype=float) for name in BLOCKS}
    diagnostics: list[dict[str, Any]] = []

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
        pos = positive[train]
        neg = ~pos
        te_idx = np.where(test)[0]

        fold_diag: dict[str, Any] = {
            "fold": fold,
            "train_examples": int(train.sum()),
            "test_examples": int(test.sum()),
            "positive_references": int(pos.sum()),
            "nonpositive_references": int(neg.sum()),
            "zero_variance_features": int(np.sum(sd == 0.0)),
            "blocks": {},
        }

        for name, (lo, hi) in BLOCKS.items():
            P = ztr[pos, lo:hi]
            N = ztr[neg, lo:hi]
            mu_pos = np.mean(P, axis=0)
            mu_neg = np.mean(N, axis=0)
            lw_pos = LedoitWolf(assume_centered=False, store_precision=False).fit(P)
            lw_neg = LedoitWolf(assume_centered=False, store_precision=False).fit(N)
            cov_pos = np.asarray(lw_pos.covariance_, dtype=float)
            cov_neg = np.asarray(lw_neg.covariance_, dtype=float)
            pooled = 0.5 * (cov_pos + cov_neg)
            req(np.isfinite(pooled).all(), f"nonfinite {name} pooled covariance fold {fold}")
            req(np.allclose(pooled, pooled.T, rtol=0.0, atol=1e-12), f"nonsymmetric {name} pooled covariance fold {fold}")
            eig = np.linalg.eigvalsh(pooled)
            req(np.isfinite(eig).all() and float(np.min(eig)) > 0.0, f"non-PD {name} pooled covariance fold {fold}")
            direction = np.linalg.solve(pooled, mu_pos - mu_neg)
            midpoint = 0.5 * (mu_pos + mu_neg)
            req(np.isfinite(direction).all() and float(np.linalg.norm(direction)) > 0.0, f"invalid {name} Fisher direction fold {fold}")
            for j, global_i in enumerate(te_idx.tolist()):
                out[name][global_i] = float(np.dot(zte[j, lo:hi] - midpoint, direction))
            fold_diag["blocks"][name] = {
                "dimensions": hi - lo,
                "positive_ledoit_wolf_shrinkage": float(lw_pos.shrinkage_),
                "nonpositive_ledoit_wolf_shrinkage": float(lw_neg.shrinkage_),
                "pooled_min_eigenvalue": float(np.min(eig)),
                "pooled_max_eigenvalue": float(np.max(eig)),
                "direction_norm": float(np.linalg.norm(direction)),
            }

        diagnostics.append(fold_diag)

    for name, values in out.items():
        req(np.isfinite(values).all(), f"nonfinite {name} OOF Fisher score")
    return out, diagnostics


def main() -> int:
    a = args()
    a.output.mkdir(parents=True, exist_ok=True)
    req(parent.sha(a.quality_source) == parent.QUALITY_SHA, "active GMN ranker source changed")
    fx = load_fixture(a.fixture_root)

    X = fx["X"]
    positive = fx["positive"]
    groups = fx["groups"]

    # Exact binding Fisher parent reconstruction before successor interpretation.
    parent_margin_reconstructed, fisher_raw, fisher_diag = fisher_parent.oof_parent_and_fisher(X, positive, groups)
    req(parent.array_sha(parent_margin_reconstructed) == EXPECTED_PARENT_MARGIN_SHA, "binding parent margin did not reproduce")
    req(np.array_equal(parent_margin_reconstructed, fx["parent_margin"]), "fixture parent margin differs from exact reconstruction")
    parent_scale = float(np.median(np.abs(parent_margin_reconstructed)))
    fisher_raw_scale = float(np.median(np.abs(fisher_raw)))
    req(math.isfinite(parent_scale) and parent_scale > 0.0 and math.isfinite(fisher_raw_scale) and fisher_raw_scale > 0.0, "invalid Fisher parent scales")
    fisher_unit_factor = float(parent_scale / fisher_raw_scale)
    fisher_scaled = fisher_raw * fisher_unit_factor
    req(parent.array_sha(fisher_scaled) == EXPECTED_FISHER_SCALED_SHA, "binding Fisher scaled score did not reproduce")
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

    raw_blocks, block_diag = block_fisher_scores(X, positive, groups)
    block_scales: dict[str, float] = {}
    normalized: list[np.ndarray] = []
    for name in ("structural", "cohesion", "neighbor"):
        s = float(np.median(np.abs(raw_blocks[name])))
        req(math.isfinite(s) and s > 0.0, f"invalid {name} median absolute score")
        block_scales[name] = s
        normalized.append(raw_blocks[name] / s)
    combined_raw = np.mean(np.vstack(normalized), axis=0)
    req(combined_raw.shape == (EXPECTED_HARD,) and np.isfinite(combined_raw).all(), "invalid equal-block combined score")

    fisher_scaled_scale = float(np.median(np.abs(fisher_scaled)))
    combined_scale = float(np.median(np.abs(combined_raw)))
    req(math.isfinite(fisher_scaled_scale) and fisher_scaled_scale > 0.0, "invalid Fisher scaled magnitude")
    req(math.isfinite(combined_scale) and combined_scale > 0.0, "invalid combined score magnitude")
    unit_factor = float(fisher_scaled_scale / combined_scale)
    req(math.isfinite(unit_factor) and unit_factor > 0.0, "invalid equal-block unit factor")
    combined_scaled = combined_raw * unit_factor
    req(np.isfinite(combined_scaled).all(), "nonfinite scaled equal-block score")

    idx = q.diversity_order(combined_scaled, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
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
    verdict = "PASS_GMN_EQUAL_BLOCK_FISHER_OOF" if passed else "FAIL_GMN_EQUAL_BLOCK_FISHER_OOF"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_EQUAL_PHYSICAL_BLOCK_FISHER_SUCCESSOR_ONLY",
        "first_valid_outcome_binding": True,
        "candidate_count": EXPECTED_HARD,
        "feature_dimension": FEATURE_DIM,
        "fixture_verdict": fx["manifest"]["verdict"],
        "feature_matrix_sha256": parent.array_sha(X),
        "parent_margin_sha256": parent.array_sha(parent_margin_reconstructed),
        "fisher_parent_scaled_sha256": parent.array_sha(fisher_scaled),
        "block_raw_score_sha256": {name: parent.array_sha(raw_blocks[name]) for name in BLOCKS},
        "block_median_absolute_score": block_scales,
        "combined_raw_sha256": parent.array_sha(combined_raw),
        "combined_scaled_sha256": parent.array_sha(combined_scaled),
        "combined_unit_factor": unit_factor,
        "blocks": {name: [lo, hi] for name, (lo, hi) in BLOCKS.items()},
        "mechanism": "equal arithmetic mean of median-absolute-normalized blockwise balanced shrinkage Fisher OOF scores",
        "block_covariance": "separate positive/nonpositive LedoitWolf then equal 0.5/0.5 pooling within each frozen block",
        "block_weighting": "exact equal one-third weights",
        "strict_whole_shower_oof": True,
        "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
        "fusion": "equal rank-sum with immutable P19 hard order",
        "fisher_parent": parent.metric_subset(fisher_metrics),
        "candidate": parent.metric_subset(candidate),
        "pass_gates": gates,
        "fisher_parent_fold_diagnostics": fisher_diag,
        "block_fold_diagnostics": block_diag,
        "block_search": False,
        "block_subset_search": False,
        "block_weight_search": False,
        "combiner_search": False,
        "covariance_estimator_search": False,
        "regularization_search": False,
        "parent_block_blend_search": False,
        "feature_search": False,
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
    out = a.output / "GMN_EQUAL_BLOCK_FISHER_OOF_RESULT.json"
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
        "block_scales": block_scales,
        "combined_unit_factor": unit_factor,
        "combined_scaled_sha256": parent.array_sha(combined_scaled),
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
