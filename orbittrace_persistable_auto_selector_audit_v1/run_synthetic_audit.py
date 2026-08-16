#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import warnings
from pathlib import Path

import numpy as np
from sklearn.metrics import adjusted_rand_score

from persistable import Persistable
from persistable.persistable_interactive import (
    compute_defaults,
    X_START_FIRST_LINE,
    Y_START_FIRST_LINE,
    X_END_FIRST_LINE,
    Y_END_FIRST_LINE,
    X_START_SECOND_LINE,
    Y_START_SECOND_LINE,
    X_END_SECOND_LINE,
    Y_END_SECOND_LINE,
    GRANULARITY_PV,
)

SEEDS = (202608160, 202608161, 202608162, 202608163)
N_DENSE = 6144
N_SPARSE = 768
MAX_GAP = 15
EPS = 1e-15
CENTERS = np.asarray([
    [2.0, 0.0, 0.0, 0.0],
    [-2.0, 0.0, 0.0, 0.0],
    [0.0, 2.0, 0.0, 0.0],
    [0.0, -2.0, 0.0, 0.0],
    [0.0, 0.0, 2.0, 0.0],
    [0.0, 0.0, -2.0, 0.0],
], dtype=float)
WEIGHTS = np.asarray([0.18, 0.15, 0.13, 0.11, 0.09, 0.07, 0.27], dtype=float)
SIGMAS = np.asarray([0.22, 0.28, 0.34, 0.40, 0.46, 0.52], dtype=float)


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def make_data(seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(np.random.PCG64(seed))
    labels = rng.choice(7, size=N_DENSE, p=WEIGHTS)
    X = np.empty((N_DENSE, 4), dtype=float)
    for j in range(6):
        ix = np.flatnonzero(labels == j)
        X[ix] = CENTERS[j] + SIGMAS[j] * rng.standard_normal((len(ix), 4))
    bg = np.flatnonzero(labels == 6)
    X[bg] = rng.uniform(-4.0, 4.0, size=(len(bg), 4))
    req(np.all(np.isfinite(X)), "nonfinite synthetic data")
    return X, labels.astype(np.int64)


def default_slices(p: Persistable):
    end_extent = np.asarray(p._find_end(), dtype=float)
    req(end_extent.shape == (2,) and np.all(np.isfinite(end_extent)) and np.all(end_extent > 0), f"invalid find_end {end_extent}")
    defaults, _bounds = compute_defaults(end_extent, p._default_granularity())
    s1 = np.asarray([defaults[X_START_FIRST_LINE], defaults[Y_START_FIRST_LINE]], dtype=float)
    e1 = np.asarray([defaults[X_END_FIRST_LINE], defaults[Y_END_FIRST_LINE]], dtype=float)
    s2 = np.asarray([defaults[X_START_SECOND_LINE], defaults[Y_START_SECOND_LINE]], dtype=float)
    e2 = np.asarray([defaults[X_END_SECOND_LINE], defaults[Y_END_SECOND_LINE]], dtype=float)
    npar = int(defaults[GRANULARITY_PV])
    req(npar >= 2, f"invalid default vineyard granularity {npar}")
    for x in (s1, e1, s2, e2):
        req(x.shape == (2,) and np.all(np.isfinite(x)), "invalid default slice")
    return end_extent, (s1, e1), (s2, e2), npar


def automatic_cluster(X: np.ndarray) -> tuple[np.ndarray, dict]:
    caught = []
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter("always")
        p = Persistable(X, n_neighbors="auto", n_jobs=1)
        end_extent, slice1, slice2, npar = default_slices(p)
        vineyard = p._linear_vineyard(slice1, slice2, npar, reduced=False, n_jobs=1)
        vines = vineyard._vineyard_to_vines()
        caught = [str(w.message) for w in ws]

    bad_neighbor_warning = any("enough neighbors" in s.lower() for s in caught)
    req(not bad_neighbor_warning, f"insufficient-neighbor warning: {caught}")
    req(len(vines) >= 3, f"too few prominence vines: {len(vines)}")
    prom = np.column_stack([np.asarray(v[1], dtype=float) for v in vines])
    req(prom.shape[0] == npar and np.all(np.isfinite(prom)) and np.all(prom >= 0), "invalid prominence matrix")

    last_gap = min(MAX_GAP, prom.shape[1] - 1)
    req(last_gap >= 2, "no nontrivial prominence gap available")
    scores = []
    curves: dict[int, np.ndarray] = {}
    denom = np.maximum(prom[:, 0], EPS)
    for gap in range(2, last_gap + 1):
        curve = np.maximum(prom[:, gap - 1] - prom[:, gap], 0.0) / denom
        req(np.all(np.isfinite(curve)), f"invalid gap curve {gap}")
        curves[gap] = curve
        scores.append((float(np.mean(curve)), gap))
    best_score = max(s[0] for s in scores)
    gap = min(g for s, g in scores if abs(s - best_score) <= 1e-15)
    curve = curves[gap]
    t = int(np.flatnonzero(np.abs(curve - np.max(curve)) <= 1e-15)[0])

    params = list(vineyard._parameters)
    req(len(params) == npar, "vineyard parameter count mismatch")
    start, end = params[t]
    start = np.asarray(start, dtype=float)
    end = np.asarray(end, dtype=float)
    req(start.shape == (2,) and end.shape == (2,) and np.all(np.isfinite(start)) and np.all(np.isfinite(end)), "invalid selected slice")

    labels = np.asarray(
        p.cluster(
            n_clusters=int(gap),
            start=start,
            end=end,
            flattening_mode="conservative",
            keep_low_persistence_clusters=False,
        ),
        dtype=np.int64,
    )
    req(labels.shape == (len(X),), "wrong output label shape")
    clusters = sorted(int(v) for v in np.unique(labels) if int(v) >= 0)
    return labels, {
        "find_end": end_extent.tolist(),
        "default_slice_1": [slice1[0].tolist(), slice1[1].tolist()],
        "default_slice_2": [slice2[0].tolist(), slice2[1].tolist()],
        "vineyard_parameters": npar,
        "prominence_vines": int(prom.shape[1]),
        "selected_gap": int(gap),
        "selected_gap_mean_normalized_separation": float(best_score),
        "selected_vineyard_index": int(t),
        "selected_gap_at_index": float(curve[t]),
        "selected_slice": [start.tolist(), end.tolist()],
        "returned_cluster_count": len(clusters),
        "noise_fraction": float(np.mean(labels < 0)),
        "warning_messages": caught,
    }


def main() -> int:
    out = Path("output")
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    all_pass = True
    for seed in SEEDS:
        X, truth = make_data(seed)
        dense, ds = automatic_cluster(X)
        sparse, ss = automatic_cluster(X[:N_SPARSE])
        cross_ari = float(adjusted_rand_score(dense[:N_SPARSE], sparse))
        truth_dense = float(adjusted_rand_score(truth, dense))
        truth_sparse = float(adjusted_rand_score(truth[:N_SPARSE], sparse))
        gates = {
            "dense_at_least_two_clusters": int(ds["returned_cluster_count"]) >= 2,
            "sparse_at_least_two_clusters": int(ss["returned_cluster_count"]) >= 2,
            "selected_gaps_in_range": 2 <= int(ds["selected_gap"]) <= MAX_GAP and 2 <= int(ss["selected_gap"]) <= MAX_GAP,
            "cluster_count_difference_at_most_two": abs(int(ds["returned_cluster_count"]) - int(ss["returned_cluster_count"])) <= 2,
            "nested_cross_scale_ari_at_least_half": cross_ari >= 0.50,
        }
        passed = all(gates.values())
        all_pass = all_pass and passed
        row = {
            "seed": seed,
            "dense": ds,
            "sparse": ss,
            "cross_scale_ari": cross_ari,
            "secondary_truth_ari_dense": truth_dense,
            "secondary_truth_ari_sparse": truth_sparse,
            "gates": gates,
            "pass": passed,
        }
        rows.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    verdict = "PASS_PERSISTABLE_AUTO_SELECTOR_SYNTHETIC_FEASIBILITY" if all_pass else "FAIL_PERSISTABLE_AUTO_SELECTOR_SYNTHETIC_FEASIBILITY"
    result = {
        "schema": "ORBITTRACE_PERSISTABLE_AUTO_SELECTOR_AUDIT_V1",
        "verdict": verdict,
        "upstream_persistable_commit": "7eb75b2e8d2fe5a18e49248aa7d1c97f829415be",
        "meteor_data_access": False,
        "target_information_access": False,
        "manual_parameter_selection": False,
        "replicates": rows,
    }
    (out / "PERSISTABLE_AUTO_SELECTOR_SYNTHETIC_AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
