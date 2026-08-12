#!/usr/bin/env python3
"""Target-excluded GMN balanced shrinkage Fisher architectural successor."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.covariance import LedoitWolf

from orbittrace_gmn_v31_principle_local_geometry_oof_v1 import run_development as parent

q = parent.q
YEARS = parent.YEARS
MONTH_KEYS = parent.MONTH_KEYS
BLIND = parent.BLIND
EXPECTED_HARD = parent.EXPECTED_HARD
FEATURE_DIM = parent.FEATURE_DIM
DIVERSITY_LAMBDA = parent.DIVERSITY_LAMBDA
DIVERSITY_SCALE = parent.DIVERSITY_SCALE
PARENT_MARGIN_SHA = "f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd"
PARENT_METRICS = {
    "recovered_at_100": 66,
    "recovered_at_50": 41,
    "top100_dominant_precision": 0.7229521515453452,
    "mrr": 0.050244164168646674,
    "qualified_matches": 95,
}
CORPUS = "orbittrace-gmn-balanced-shrinkage-fisher-oof-v1"


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    for name in (
        "quality_source",
        "support_source_parts",
        "candidate_payload",
        "baseline_payload",
        "scorer_parts",
        "v8_result_json",
        "p19_prelabel_json",
        "output",
    ):
        p.add_argument("--" + name.replace("_", "-"), dest=name, type=Path, required=True)
    return p.parse_args()


def oof_parent_and_fisher(
    X: np.ndarray,
    y: np.ndarray,
    groups: list[str],
) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    folds = np.asarray([q.v1.deterministic_fold(group) for group in groups], dtype=int)
    parent.req(set(folds.tolist()) == set(range(5)), "five-fold assignment changed")
    parent_margin = np.zeros(len(X), dtype=float)
    fisher = np.zeros(len(X), dtype=float)
    diag: list[dict[str, Any]] = []

    for fold in range(5):
        train = folds != fold
        test = folds == fold
        parent.req(train.any() and test.any(), f"empty fold {fold}")
        train_groups = {groups[i] for i in np.where(train)[0]}
        test_groups = {groups[i] for i in np.where(test)[0]}
        parent.req(train_groups.isdisjoint(test_groups), f"group leakage fold {fold}")
        parent.req(y[train].any() and (~y[train]).any(), f"fold {fold} lacks both reference classes")

        mu = np.mean(X[train], axis=0)
        sd = np.std(X[train], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        ztr = (X[train] - mu[None, :]) / scale[None, :]
        zte = (X[test] - mu[None, :]) / scale[None, :]
        parent.req(np.isfinite(ztr).all() and np.isfinite(zte).all(), f"nonfinite z-space fold {fold}")

        pos = y[train]
        neg = ~pos
        P = ztr[pos]
        N = ztr[neg]
        parent.req(len(P) >= 2 and len(N) >= 2, f"insufficient class references fold {fold}")

        mu_pos = np.mean(P, axis=0)
        mu_neg = np.mean(N, axis=0)
        parent.req(np.isfinite(mu_pos).all() and np.isfinite(mu_neg).all(), f"nonfinite class means fold {fold}")

        lw_pos = LedoitWolf(assume_centered=False, store_precision=False).fit(P)
        lw_neg = LedoitWolf(assume_centered=False, store_precision=False).fit(N)
        cov_pos = np.asarray(lw_pos.covariance_, dtype=float)
        cov_neg = np.asarray(lw_neg.covariance_, dtype=float)
        for name, cov, shrink in (
            ("positive", cov_pos, float(lw_pos.shrinkage_)),
            ("nonpositive", cov_neg, float(lw_neg.shrinkage_)),
        ):
            parent.req(cov.shape == (FEATURE_DIM, FEATURE_DIM), f"{name} covariance shape changed fold {fold}")
            parent.req(np.isfinite(cov).all(), f"nonfinite {name} covariance fold {fold}")
            parent.req(np.allclose(cov, cov.T, rtol=0.0, atol=1e-12), f"nonsymmetric {name} covariance fold {fold}")
            parent.req(math.isfinite(shrink) and 0.0 <= shrink <= 1.0, f"invalid {name} shrinkage fold {fold}")

        pooled = 0.5 * (cov_pos + cov_neg)
        parent.req(np.isfinite(pooled).all(), f"nonfinite equal-class pooled covariance fold {fold}")
        parent.req(np.allclose(pooled, pooled.T, rtol=0.0, atol=1e-12), f"nonsymmetric pooled covariance fold {fold}")
        evals = np.linalg.eigvalsh(pooled)
        parent.req(np.isfinite(evals).all() and float(np.min(evals)) > 0.0, f"pooled covariance not positive definite fold {fold}")

        delta = mu_pos - mu_neg
        direction = np.linalg.solve(pooled, delta)
        midpoint = 0.5 * (mu_pos + mu_neg)
        parent.req(np.isfinite(direction).all() and np.isfinite(midpoint).all(), f"nonfinite Fisher geometry fold {fold}")
        parent.req(float(np.linalg.norm(direction)) > 0.0, f"zero Fisher direction fold {fold}")

        test_indices = np.where(test)[0]
        for j, global_i in enumerate(test_indices.tolist()):
            point = zte[j]
            # Bit-for-bit successful-parent provenance calculation.
            dpos = float(np.min(np.linalg.norm(P - point[None, :], axis=1)))
            dneg = float(np.min(np.linalg.norm(N - point[None, :], axis=1)))
            parent_margin[global_i] = dneg - dpos
            fisher[global_i] = float(np.dot(point - midpoint, direction))

        diag.append({
            "fold": fold,
            "train_examples": int(train.sum()),
            "test_examples": int(test.sum()),
            "positive_references": int(pos.sum()),
            "nonpositive_references": int(neg.sum()),
            "zero_variance_features": int(np.sum(sd == 0.0)),
            "train_group_count": len(train_groups),
            "test_group_count": len(test_groups),
            "positive_ledoit_wolf_shrinkage": float(lw_pos.shrinkage_),
            "nonpositive_ledoit_wolf_shrinkage": float(lw_neg.shrinkage_),
            "pooled_min_eigenvalue": float(np.min(evals)),
            "pooled_max_eigenvalue": float(np.max(evals)),
            "class_mean_distance": float(np.linalg.norm(delta)),
            "fisher_direction_norm": float(np.linalg.norm(direction)),
        })

    parent.req(np.isfinite(parent_margin).all(), "nonfinite parent OOF margin")
    parent.req(np.isfinite(fisher).all(), "nonfinite Fisher OOF score")
    return parent_margin, fisher, diag


def main() -> int:
    a = args()
    a.output.mkdir(parents=True, exist_ok=True)
    parent.req(parent.sha(a.quality_source) == parent.QUALITY_SHA, "active GMN ranker source changed")
    parent.req(parent.sha(a.v8_result_json) == parent.V8_RESULT_SHA, "v8 result changed")
    parent.req(parent.sha(a.p19_prelabel_json) == parent.P19_PRELABEL_SHA, "P19 hard-family prelabel changed")

    payload = json.loads(a.p19_prelabel_json.read_text())
    hard = payload["hard_families"]
    hard_order = [str(x) for x in payload["hard_order"]]
    parent.req(len(hard) == EXPECTED_HARD and len(hard_order) == EXPECTED_HARD, "hard family count changed")
    ids = [str(f["family_id"]) for f in hard]
    parent.req(len(set(ids)) == EXPECTED_HARD and set(ids) == set(hard_order), "hard family identity changed")
    hard_rank = {fid: i + 1 for i, fid in enumerate(hard_order)}

    q.v1.mult.YEARS = YEARS
    q.v1.mult.MONTH_KEYS = MONTH_KEYS
    q.v1.mult.TOP_K = 100
    runtime = q.v1.mult.load_frozen_runtime()
    support = runtime.load_support_module(a.support_source_parts)
    support.YEARS = YEARS
    support.MONTH_KEYS = MONTH_KEYS
    support.CORPUS = CORPUS
    support.RANKING_VARIANTS = ("persistence",)
    parent.req(float(support.BLIND_LOW) == BLIND[0] and float(support.BLIND_HIGH) == BLIND[1], "blind interval changed")
    setattr(a, "fixed4_baseline_json", a.v8_result_json)
    _candidate, base, _scorer = support.load_sources(a)
    scan_by_year, _calibration_by_year, hidden_labels, sources = support.parse_catalogue(base)
    parent.req(sorted(scan_by_year) == list(YEARS), "GMN year universe changed")
    parent.req([row["key"] for row in sources] == list(MONTH_KEYS), "GMN month panel changed")

    # Protected-data barrier before representation or truth interpretation.
    for year in YEARS:
        for row in scan_by_year[year]:
            _ = parent.event_sol(row)
    for family in hard:
        for year in YEARS:
            centroid = family.get("centroids", {}).get(str(year))
            parent.req(centroid is not None, f"missing centroid for {family['family_id']} {year}")
            csol = float(centroid["sol"]) % 360.0
            parent.req(not (BLIND[0] <= csol <= BLIND[1]), f"protected centroid reached diagnostic: {family['family_id']} {year}")

    lookup = q.v2.event_lookup(scan_by_year)
    cm = q.centroid_matrix(hard)
    parent.req(cm.shape == (EXPECTED_HARD, 8) and np.isfinite(cm).all(), "centroid matrix changed")
    nf = q.neighbor_features(cm)
    parent.req(nf.shape == (EXPECTED_HARD, 6) and np.isfinite(nf).all(), "neighbor matrix changed")
    X = np.asarray([
        parent.intrinsic_features(family, hard_rank, lookup, support, base, nf[i])
        for i, family in enumerate(hard)
    ], dtype=float)
    parent.req(X.shape == (EXPECTED_HARD, FEATURE_DIM) and np.isfinite(X).all(), "intrinsic feature matrix invalid")

    np.save(a.output / "GMN_BALANCED_SHRINKAGE_FISHER_INTRINSIC_FEATURES.npy", X, allow_pickle=False)
    prelabel = {
        "scope": "GMN 2022/2023 target-excluded balanced shrinkage Fisher architectural successor",
        "candidate_count": EXPECTED_HARD,
        "feature_dimension": FEATURE_DIM,
        "feature_matrix_sha256": parent.array_sha(X),
        "hard_order_sha256": parent.order_sha(hard_order),
        "representation_changed_from_parent": False,
        "truth_interpreted_for_feature_construction": False,
        "blind_exclusion": list(BLIND),
        "sonotaco_2013_2014_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    prelabel_path = a.output / "GMN_BALANCED_SHRINKAGE_FISHER_PRELABEL.json"
    prelabel_path.write_text(json.dumps(prelabel, indent=2, sort_keys=True, allow_nan=False) + "\n")
    prelabel_sha = parent.sha(prelabel_path)

    # Development truth begins only after the fixed representation is sealed.
    eligible = q.v1.eligible_labels(hidden_labels)
    by_id = {str(f["family_id"]): f for f in hard}
    truths = {fid: q.v1.family_truth(by_id[fid], hidden_labels, eligible) for fid in ids}
    y = np.asarray([bool(truths[fid]["positive"]) for fid in ids], dtype=bool)
    parent.req(y.any() and (~y).any(), "recoverability reference target degenerate")
    groups: list[str] = []
    for fid in ids:
        label = truths[fid]["best_label"]
        groups.append(("SHOWER/" + str(label)) if label is not None else ("NEG/" + fid))

    parent_margin, fisher_raw, fold_diag = oof_parent_and_fisher(X, y, groups)
    parent.req(parent.array_sha(parent_margin) == PARENT_MARGIN_SHA, "parent OOF margin did not reproduce exactly")

    parent_scale = float(np.median(np.abs(parent_margin)))
    fisher_scale = float(np.median(np.abs(fisher_raw)))
    parent.req(math.isfinite(parent_scale) and parent_scale > 0.0, "invalid parent median absolute margin")
    parent.req(math.isfinite(fisher_scale) and fisher_scale > 0.0, "invalid Fisher median absolute score")
    unit_factor = float(parent_scale / fisher_scale)
    parent.req(math.isfinite(unit_factor) and unit_factor > 0.0, "invalid Fisher unit factor")
    fisher_scaled = fisher_raw * unit_factor
    parent.req(np.isfinite(fisher_scaled).all(), "nonfinite scaled Fisher score")

    tie = [(hard_rank[fid], fid) for fid in ids]

    # Exact successful-parent reconstruction first.
    parent_idx = q.diversity_order(parent_margin, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    parent_local_order = [ids[i] for i in parent_idx]
    parent_fused_order = parent.equal_rank_fusion(hard_order, parent_local_order)
    parent_metrics = q.v1.monotone_metrics(hard, parent_fused_order, truths, eligible)
    for key, expected in PARENT_METRICS.items():
        got = parent_metrics[key]
        if isinstance(expected, float):
            parent.req(abs(float(got) - expected) < 1e-15, f"parent metric {key} changed: {got}")
        else:
            parent.req(int(got) == expected, f"parent metric {key} changed: {got}")

    idx = q.diversity_order(fisher_scaled, cm, DIVERSITY_LAMBDA, DIVERSITY_SCALE, tie)
    local_order = [ids[i] for i in idx]
    fused_order = parent.equal_rank_fusion(hard_order, local_order)
    candidate = q.v1.monotone_metrics(hard, fused_order, truths, eligible)
    parent.req(int(candidate["qualified_matches"]) == PARENT_METRICS["qualified_matches"], "qualified universe changed")

    gates = {
        "recovered_at_100_strictly_above_parent": int(candidate["recovered_at_100"]) > PARENT_METRICS["recovered_at_100"],
        "recovered_at_50_not_below_parent": int(candidate["recovered_at_50"]) >= PARENT_METRICS["recovered_at_50"],
        "top100_precision_not_below_parent": float(candidate["top100_dominant_precision"]) >= PARENT_METRICS["top100_dominant_precision"],
        "mrr_not_below_parent": float(candidate["mrr"]) >= PARENT_METRICS["mrr"],
        "qualified_count_identical": int(candidate["qualified_matches"]) == PARENT_METRICS["qualified_matches"],
    }
    passed = all(gates.values())
    verdict = "PASS_GMN_BALANCED_SHRINKAGE_FISHER_OOF" if passed else "FAIL_GMN_BALANCED_SHRINKAGE_FISHER_OOF"

    result = {
        "verdict": verdict,
        "scientific_role": "TARGET_EXCLUDED_GMN_BALANCED_SHRINKAGE_FISHER_ARCHITECTURAL_SUCCESSOR_ONLY",
        "first_valid_outcome_binding": True,
        "candidate_count": EXPECTED_HARD,
        "feature_dimension": FEATURE_DIM,
        "prelabel_sha256": prelabel_sha,
        "feature_matrix_sha256": parent.array_sha(X),
        "parent_margin_sha256": parent.array_sha(parent_margin),
        "fisher_raw_sha256": parent.array_sha(fisher_raw),
        "fisher_scaled_sha256": parent.array_sha(fisher_scaled),
        "parent_median_absolute_margin": parent_scale,
        "fisher_median_absolute_score": fisher_scale,
        "unit_factor": unit_factor,
        "mechanism": "equal-class Ledoit-Wolf shrinkage Fisher discriminant",
        "positive_covariance_estimator": "LedoitWolf(assume_centered=False,store_precision=False)",
        "nonpositive_covariance_estimator": "LedoitWolf(assume_centered=False,store_precision=False)",
        "pooled_covariance": "0.5*Sigma_pos+0.5*Sigma_neg",
        "class_prior_geometry": "equal-prior midpoint",
        "strict_whole_shower_oof": True,
        "diversity": {"lambda": DIVERSITY_LAMBDA, "scale": DIVERSITY_SCALE},
        "fusion": "equal rank-sum with immutable P19 hard order",
        "parent": parent.metric_subset(parent_metrics),
        "candidate": parent.metric_subset(candidate),
        "pass_gates": gates,
        "fold_diagnostics": fold_diag,
        "class_prior_search": False,
        "covariance_estimator_search": False,
        "covariance_weight_search": False,
        "regularization_search": False,
        "solver_search": False,
        "feature_search": False,
        "dimensionality_reduction_search": False,
        "nonlinear_transform_search": False,
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
    out = a.output / "GMN_BALANCED_SHRINKAGE_FISHER_OOF_RESULT.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({
        "verdict": verdict,
        "parent100": parent_metrics["recovered_at_100"],
        "candidate100": candidate["recovered_at_100"],
        "parent50": parent_metrics["recovered_at_50"],
        "candidate50": candidate["recovered_at_50"],
        "parent_precision": parent_metrics["top100_dominant_precision"],
        "candidate_precision": candidate["top100_dominant_precision"],
        "parent_mrr": parent_metrics["mrr"],
        "candidate_mrr": candidate["mrr"],
        "qualified": candidate["qualified_matches"],
        "parent_scale": parent_scale,
        "fisher_scale": fisher_scale,
        "unit_factor": unit_factor,
        "parent_margin_sha256": parent.array_sha(parent_margin),
        "fisher_scaled_sha256": parent.array_sha(fisher_scaled),
    }, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
