#!/usr/bin/env python3
from __future__ import annotations

import math
from typing import Any

import numpy as np
from sklearn.mixture import GaussianMixture

H_SOL = 2.0 * math.sin(math.radians(5.0) / 2.0)
H_RAD = 2.0 * math.sin(math.radians(4.0) / 2.0)
H_LOGV = math.log(1.1)

N_COMPONENTS = 160
COVARIANCE_TYPE = "diag"
REG_COVAR = 1.0e-4
TOL = 1.0e-3
MAX_ITER = 500
N_INIT = 1
INIT_PARAMS = "kmeans"
RANDOM_STATE = 20260816
MIN_SUPPORT = 4


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def embedding(rows: list[dict[str, Any]]) -> np.ndarray:
    require(bool(rows), "empty row list")
    sol = np.radians(np.asarray([float(r["sol"]) for r in rows], dtype=np.float64))
    lon = np.radians(np.asarray([float(r["sun_lon"]) for r in rows], dtype=np.float64))
    lat = np.radians(np.asarray([float(r["ecl_lat"]) for r in rows], dtype=np.float64))
    vg = np.asarray([float(r["vg"]) for r in rows], dtype=np.float64)
    require(np.all(np.isfinite(sol)) and np.all(np.isfinite(lon)) and np.all(np.isfinite(lat)), "nonfinite angle")
    require(np.all(np.isfinite(vg)) and np.all(vg > 0.0), "invalid geocentric speed")
    cl = np.cos(lat)
    x = np.column_stack(
        [
            np.cos(sol) / H_SOL,
            np.sin(sol) / H_SOL,
            cl * np.cos(lon) / H_RAD,
            cl * np.sin(lon) / H_RAD,
            np.sin(lat) / H_RAD,
            np.log(vg) / H_LOGV,
        ]
    )
    require(x.shape == (len(rows), 6) and np.all(np.isfinite(x)), "invalid embedding")
    return x


def fit_ranked(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ids = [str(r["id"]) for r in rows]
    require(len(ids) == len(set(ids)), "duplicate IDs")
    x = embedding(rows)
    require(len(rows) > N_COMPONENTS, "not enough rows for fixed mixture")

    model = GaussianMixture(
        n_components=N_COMPONENTS,
        covariance_type=COVARIANCE_TYPE,
        reg_covar=REG_COVAR,
        tol=TOL,
        max_iter=MAX_ITER,
        n_init=N_INIT,
        init_params=INIT_PARAMS,
        random_state=RANDOM_STATE,
    )
    model.fit(x)
    require(bool(model.converged_), "GaussianMixture did not converge")
    require(model.covariance_type == "diag", "unexpected covariance type")
    require(model.covariances_.shape == (N_COMPONENTS, 6), "unexpected covariance shape")
    require(np.all(model.covariances_ > 0.0), "nonpositive covariance")
    require(np.all(model.weights_ > 0.0), "nonpositive mixture weight")

    labels = model.predict(x)
    require(labels.shape == (len(rows),), "invalid MAP assignment shape")

    raw: list[dict[str, Any]] = []
    for k in range(N_COMPONENTS):
        idx = np.flatnonzero(labels == k)
        if idx.size < MIN_SUPPORT:
            continue
        variances = np.asarray(model.covariances_[k], dtype=np.float64)
        score = float(model.weights_[k] / math.sqrt(float(np.prod(variances))))
        require(math.isfinite(score) and score > 0.0, "invalid peak-density score")
        event_ids = [ids[int(i)] for i in idx]
        raw.append(
            {
                "component_index": int(k),
                "event_ids": event_ids,
                "member_count": int(idx.size),
                "weight": float(model.weights_[k]),
                "diag_variances": [float(v) for v in variances],
                "peak_density_score": score,
            }
        )

    require(bool(raw), "mixture returned no reportable components")
    raw.sort(key=lambda r: (-float(r["peak_density_score"]), int(r["component_index"])))

    ranked: list[dict[str, Any]] = []
    for rank, r in enumerate(raw, 1):
        ranked.append(
            {
                "family_id": f"cmix-{int(r['component_index']):03d}",
                "rank": rank,
                **r,
            }
        )

    summary = {
        "n_events": len(rows),
        "embedding_dimensions": 6,
        "configured_components": N_COMPONENTS,
        "reportable_components": len(ranked),
        "converged": bool(model.converged_),
        "n_iter": int(model.n_iter_),
        "lower_bound": float(model.lower_bound_),
        "bic": float(model.bic(x)),
        "aic": float(model.aic(x)),
        "min_report_support": MIN_SUPPORT,
        "assignment": "hard_MAP",
        "ranking": "weight_over_sqrt_diag_covariance_determinant",
    }
    return ranked, summary
