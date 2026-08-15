#!/usr/bin/env python3
from __future__ import annotations

import json
import numpy as np

from whitening import COV_TOL, DIM, METHOD_ID, fit_transform, fit_whitener


def main() -> int:
    rng = np.random.default_rng(20260815)
    a = rng.normal(size=(5000, DIM))
    mix = np.array([
        [3.0, 0.8, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.5, 0.2, 0.0, 0.0, 0.0],
        [0.0, 0.0, 2.0, 0.7, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.4, 0.1, 0.0],
        [0.0, 0.0, 0.0, 0.0, 1.5, 0.5],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.25],
    ])
    x = a @ mix.T + np.array([5.0, -2.0, 3.0, 7.0, -4.0, 11.0])
    z, fit, err = fit_transform(x)
    z2, fit2, err2 = fit_transform(x.copy())

    scaled = x @ np.diag([2.0, 0.5, 1.5, 3.0, 0.75, 4.0])
    zs, _, errs = fit_transform(scaled)
    d0 = np.linalg.norm(z[:200, None, :] - z[None, :200, :], axis=2)
    ds = np.linalg.norm(zs[:200, None, :] - zs[None, :200, :], axis=2)

    singular = np.column_stack([x[:, :5], x[:, 0] + x[:, 1]])
    singular_failed = False
    try:
        fit_whitener(singular)
    except ValueError:
        singular_failed = True

    tests = {
        "method_id": METHOD_ID == "orbittrace_density_sync_global_whitened_geo6_v1",
        "dimension_frozen": DIM == 6,
        "covariance_identity": err <= COV_TOL,
        "deterministic_transform": np.array_equal(z, z2) and np.array_equal(fit.matrix, fit2.matrix) and err2 == err,
        "mean_zero": float(np.max(np.abs(np.mean(z, axis=0)))) < 1e-12,
        "positive_eigenvalues": bool(np.all(fit.eigenvalues > 0.0)),
        "nonidentity_transform": not np.allclose(fit.matrix, np.eye(DIM), rtol=0.0, atol=1e-12),
        "axis_rescaling_distance_invariance": float(np.max(np.abs(d0 - ds))) < 1e-10,
        "scaled_covariance_identity": errs <= COV_TOL,
        "singular_covariance_fails_closed": singular_failed,
    }
    passed = all(tests.values())
    print(json.dumps({
        "verdict": "PASS_GLOBAL_WHITENED_GEO6_V1_SYNTHETIC_AUDIT" if passed else "FAIL_GLOBAL_WHITENED_GEO6_V1_SYNTHETIC_AUDIT",
        "tests": tests,
        "max_whitened_covariance_error": err,
        "min_eigenvalue": float(np.min(fit.eigenvalues)),
        "max_distance_rescaling_error": float(np.max(np.abs(d0-ds))),
    }, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
