#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

from orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom import eom_labels
from orbittrace_stratified_core_hdbscan_v1.stratified_core import (
    K_YEAR,
    condensed_tree_from_injected_core,
    standard_pooled_core_distances,
    stratified_core_distances,
)

HERE = Path(__file__).resolve().parent


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def canonical_partition(labels: np.ndarray) -> tuple[tuple[int, ...], ...]:
    out = []
    for lab in sorted(int(x) for x in np.unique(labels) if int(x) >= 0):
        out.append(tuple(np.flatnonzero(labels == lab).tolist()))
    return tuple(sorted(out))


def part_sha(labels: np.ndarray) -> str:
    payload = [list(x) for x in canonical_partition(labels)]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def brute_stratified_core(X: np.ndarray, years: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = len(X)
    d22 = np.empty(n, dtype=float)
    d23 = np.empty(n, dtype=float)
    for i in range(n):
        for y, out in ((2022, d22), (2023, d23)):
            vals = []
            for j in range(n):
                if int(years[j]) != y or j == i:
                    continue
                vals.append(float(np.linalg.norm(X[i] - X[j])))
            vals.sort()
            require(len(vals) >= K_YEAR, "brute-force synthetic year lacks k support")
            out[i] = vals[K_YEAR - 1]
    return np.maximum(d22, d23), d22, d23


def core_mechanics_case() -> dict:
    # Both years include exact coordinate duplicates; only exact event identity is
    # removed, so a duplicate event at distance zero must remain a legal neighbor.
    x22 = np.asarray([
        [0.0, 0.0], [0.0, 0.0], [0.10, 0.0], [0.20, 0.0], [0.30, 0.0], [0.40, 0.0],
        [1.5, 0.2], [1.7, 0.2], [1.9, 0.2], [2.1, 0.2], [2.3, 0.2], [2.5, 0.2],
    ])
    x23 = np.asarray([
        [0.0, 0.0], [0.0, 0.0], [0.12, 0.0], [0.22, 0.0], [0.32, 0.0], [0.42, 0.0],
        [1.45, -0.2], [1.65, -0.2], [1.85, -0.2], [2.05, -0.2], [2.25, -0.2], [2.45, -0.2],
    ])
    X = np.vstack([x22, x23]).astype(np.float64)
    years = np.asarray([2022] * len(x22) + [2023] * len(x23), dtype=np.int64)
    got, parts = stratified_core_distances(X, years)
    want, want22, want23 = brute_stratified_core(X, years)
    require(np.array_equal(got, want), "stratified core differs from brute force")
    require(np.array_equal(parts["d_2022"], want22), "2022 fifth-neighbor vector differs from brute force")
    require(np.array_equal(parts["d_2023"], want23), "2023 fifth-neighbor vector differs from brute force")
    # For event 0, event 1 is an exact-coordinate distinct identity and must count.
    require(want22[0] == 0.3, f"duplicate-coordinate self exclusion changed: {want22[0]}")
    return {
        "points": int(len(X)),
        "stratified_core_sha256": hashlib.sha256(np.asarray(got, dtype="<f8").tobytes()).hexdigest(),
        "duplicate_coordinate_other_event_counted": True,
        "exact_identity_self_excluded": True,
        "matches_bruteforce_bitwise": True,
    }


def make_cluster_case(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    centers = np.asarray([
        [-3.6, -2.0, 0.2], [-3.0, 2.6, -0.4], [-0.2, 0.1, 1.5],
        [2.8, 2.7, -0.8], [3.6, -2.2, 0.5], [0.3, -3.8, -1.1],
    ])
    blocks = []
    for j, c in enumerate(centers):
        n = 55 + 7 * j
        scale = np.asarray([0.22 + 0.02*j, 0.24 + 0.015*j, 0.18 + 0.01*j])
        blocks.append(rng.normal(c, scale, size=(n, 3)))
    blocks.append(rng.uniform([-5.2, -5.0, -2.0], [5.2, 5.0, 2.0], size=(85, 3)))
    return np.asarray(np.vstack(blocks), dtype=np.float64, order="C")


def injection_case(seed: int) -> dict:
    X = make_cluster_case(seed)
    model = hdbscan.HDBSCAN(
        min_cluster_size=10,
        min_samples=10,
        metric="euclidean",
        algorithm="boruvka_kdtree",
        leaf_size=40,
        approx_min_span_tree=True,
        core_dist_n_jobs=1,
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    standard_core = standard_pooled_core_distances(X)
    injected_tree, single, mst = condensed_tree_from_injected_core(X, standard_core)
    injected_stability = compute_stability(injected_tree)
    injected_labels = eom_labels(injected_tree, injected_stability)
    require(canonical_partition(injected_labels) == canonical_partition(model.labels_), f"seed {seed}: injected standard-core partition differs from HDBSCAN")
    return {
        "seed": seed,
        "points": int(len(X)),
        "standard_partition_sha256": part_sha(np.asarray(model.labels_, dtype=np.int64)),
        "injected_partition_sha256": part_sha(injected_labels),
        "standard_core_sha256": hashlib.sha256(np.asarray(standard_core, dtype="<f8").tobytes()).hexdigest(),
        "single_linkage_shape": list(single.shape),
        "condensed_tree_rows": int(len(injected_tree)),
        "mst_rows": int(len(mst)),
    }


def main() -> int:
    mechanics = core_mechanics_case()
    cases = [injection_case(seed) for seed in (1103, 4819, 9173)]
    require(all(c["standard_partition_sha256"] == c["injected_partition_sha256"] for c in cases), "synthetic injection identity summary failed")
    result = {
        "verdict": "PASS_STRATIFIED_CORE_HDBSCAN_V1_ZERO_TRUTH_INJECTION_AUDIT",
        "synthetic_only": True,
        "core_mechanics": mechanics,
        "injection_cases": cases,
        "balanced_k_year": 5,
        "total_parent_min_samples": 10,
        "stratified_core_is_max_of_year_fifth_other_distances": True,
        "standard_core_injection_reproduces_standard_hdbscan_partition": True,
        "gmn_catalogue_accessed": False,
        "scientific_labels_accessed": False,
        "sonotaco_accessed": False,
        "efn_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = HERE / "output"
    out.mkdir(parents=True, exist_ok=True)
    (out / "STRATIFIED_CORE_ZERO_TRUTH_INJECTION_AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
