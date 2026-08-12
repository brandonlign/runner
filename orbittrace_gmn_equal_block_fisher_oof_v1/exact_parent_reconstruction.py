#!/usr/bin/env python3
"""Engineering provenance helper matching the valid QDA Fisher reconstruction order."""
from __future__ import annotations

import math
from typing import Any

import numpy as np
from sklearn.covariance import LedoitWolf

from orbittrace_gmn_v31_principle_local_geometry_oof_v1 import run_development as parent

q = parent.q
FEATURE_DIM = 23


def oof_parent_and_fisher_exact(
    X: np.ndarray,
    positive: np.ndarray,
    groups: list[str],
) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    folds = np.asarray([q.v1.deterministic_fold(g) for g in groups], dtype=int)
    parent.req(set(folds.tolist()) == set(range(5)), "five-fold assignment changed")
    parent_margin = np.zeros(len(X), dtype=float)
    fisher_raw = np.zeros(len(X), dtype=float)
    diag: list[dict[str, Any]] = []

    for fold in range(5):
        train = folds != fold
        test = folds == fold
        parent.req(train.any() and test.any(), f"empty fold {fold}")
        train_groups = {groups[i] for i in np.where(train)[0]}
        test_groups = {groups[i] for i in np.where(test)[0]}
        parent.req(train_groups.isdisjoint(test_groups), f"group leakage fold {fold}")
        parent.req(positive[train].any() and (~positive[train]).any(), f"fold {fold} lacks both classes")

        mu = np.mean(X[train], axis=0)
        sd = np.std(X[train], axis=0, ddof=0)
        scale = sd.copy()
        scale[scale == 0.0] = 1.0
        ztr = (X[train] - mu[None, :]) / scale[None, :]
        zte = (X[test] - mu[None, :]) / scale[None, :]
        parent.req(np.isfinite(ztr).all() and np.isfinite(zte).all(), f"nonfinite z-space fold {fold}")

        pos = positive[train]
        neg = ~pos
        P = ztr[pos]
        N = ztr[neg]
        parent.req(len(P) >= 2 and len(N) >= 2, f"insufficient class references fold {fold}")
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
            parent.req(cov.shape == (FEATURE_DIM, FEATURE_DIM), f"{name} covariance shape changed fold {fold}")
            parent.req(np.isfinite(cov).all(), f"nonfinite {name} covariance fold {fold}")
            parent.req(np.allclose(cov, cov.T, rtol=0.0, atol=1e-12), f"nonsymmetric {name} covariance fold {fold}")
            evals = np.linalg.eigvalsh(cov)
            parent.req(np.isfinite(evals).all() and float(np.min(evals)) > 0.0, f"{name} covariance not positive definite fold {fold}")
            parent.req(math.isfinite(shrink) and 0.0 <= shrink <= 1.0, f"invalid {name} shrinkage fold {fold}")

        pooled = 0.5 * (cov_pos + cov_neg)
        pooled_eigs = np.linalg.eigvalsh(pooled)
        parent.req(np.isfinite(pooled_eigs).all() and float(np.min(pooled_eigs)) > 0.0, f"Fisher pooled covariance invalid fold {fold}")
        direction = np.linalg.solve(pooled, mu_pos - mu_neg)
        midpoint = 0.5 * (mu_pos + mu_neg)
        parent.req(np.isfinite(direction).all() and float(np.linalg.norm(direction)) > 0.0, f"invalid Fisher direction fold {fold}")

        # Reproduce the valid QDA run's linear-algebra call order before held-out Fisher scoring.
        sign_pos, logdet_pos = np.linalg.slogdet(cov_pos)
        sign_neg, logdet_neg = np.linalg.slogdet(cov_neg)
        parent.req(float(sign_pos) > 0.0 and float(sign_neg) > 0.0, f"nonpositive covariance determinant fold {fold}")
        parent.req(math.isfinite(float(logdet_pos)) and math.isfinite(float(logdet_neg)), f"nonfinite covariance logdet fold {fold}")
        precision_pos = np.linalg.inv(cov_pos)
        precision_neg = np.linalg.inv(cov_neg)
        parent.req(np.isfinite(precision_pos).all() and np.isfinite(precision_neg).all(), f"nonfinite covariance precision fold {fold}")

        test_indices = np.where(test)[0]
        for j, global_i in enumerate(test_indices.tolist()):
            point = zte[j]
            dpos = float(np.min(np.linalg.norm(P - point[None, :], axis=1)))
            dneg = float(np.min(np.linalg.norm(N - point[None, :], axis=1)))
            parent_margin[global_i] = dneg - dpos
            fisher_raw[global_i] = float(np.dot(point - midpoint, direction))

        diag.append({
            "fold": fold,
            "train_examples": int(train.sum()),
            "test_examples": int(test.sum()),
            "positive_references": int(pos.sum()),
            "nonpositive_references": int(neg.sum()),
            "zero_variance_features": int(np.sum(sd == 0.0)),
            "positive_ledoit_wolf_shrinkage": float(lw_pos.shrinkage_),
            "nonpositive_ledoit_wolf_shrinkage": float(lw_neg.shrinkage_),
            "pooled_min_eigenvalue": float(np.min(pooled_eigs)),
            "pooled_max_eigenvalue": float(np.max(pooled_eigs)),
        })

    parent.req(np.isfinite(parent_margin).all(), "nonfinite reconstructed parent margin")
    parent.req(np.isfinite(fisher_raw).all(), "nonfinite reconstructed Fisher score")
    return parent_margin, fisher_raw, diag
