#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from hdbscan._hdbscan_tree import compute_stability

import recurrent_eom as reom
from density_synchronous_eom import density_synchronous_stability
from stratified_core import K_YEAR, MIN_CLUSTER_SIZE, MIN_SAMPLES, condensed_tree_from_injected_core, stratified_core_distances


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def main() -> int:
    # Synthetic only. Two recurrent compact groups plus deterministic diffuse points.
    rng = np.random.default_rng(20260814)
    blocks = []
    years = []
    for year, shift in ((2022, 0.0), (2023, 0.06)):
        a = rng.normal(loc=np.array([0, 0, 0, 0, 0, 0], dtype=float) + shift, scale=0.035, size=(18, 6))
        b = rng.normal(loc=np.array([2.5, 2.5, 2.5, 2.5, 2.5, 2.5], dtype=float) - shift, scale=0.035, size=(18, 6))
        diffuse = rng.normal(loc=6.0 + shift, scale=0.8, size=(12, 6))
        blocks.extend((a, b, diffuse))
        years.extend([year] * (len(a) + len(b) + len(diffuse)))
    X = np.asarray(np.vstack(blocks), dtype=np.float64, order="C")
    y = np.asarray(years, dtype=np.int64)

    req(K_YEAR == 5, "frozen k_year changed")
    req(MIN_SAMPLES == 10 and MIN_CLUSTER_SIZE == 10, "frozen HDBSCAN size parameters changed")
    core, annual = stratified_core_distances(X, y)
    req(np.array_equal(core, np.maximum(annual["d_2022"], annual["d_2023"])), "stratified max rule failed")
    req(np.all(core >= 0.0) and np.all(np.isfinite(core)), "invalid synthetic stratified core")

    tree, linkage, mst = condensed_tree_from_injected_core(X, core)
    req(len(tree) > 0 and linkage.shape[0] == X.shape[0] - 1 and mst.shape == (X.shape[0] - 1, 3), "synthetic hierarchy failed")
    ordinary = compute_stability(tree)
    synchronous, annual_parent, annual_reconstructed = density_synchronous_stability(tree, y)
    req(set(int(k) for k in synchronous) == set(int(k) for k in ordinary), "density-sync node universe differs from hierarchy stability universe")
    req(annual_parent == annual_reconstructed, "density-sync annual reconstruction changed")
    labels = reom.eom_labels(tree, synchronous)
    nodes = reom.selected_eom_nodes(tree, synchronous)
    req(len(nodes) == len(set(int(x) for x in labels if int(x) >= 0)), "selected-node/label mapping failed")
    req(all(np.isfinite(float(v)) and float(v) >= 0.0 for v in synchronous.values()), "invalid synchronous stability")

    result = {
        "verdict": "PASS_DENSITY_SYNC_STRATIFIED_CORE_V1_ZERO_TRUTH_COMPOSITION_AUDIT",
        "synthetic_only": True,
        "synthetic_events": int(X.shape[0]),
        "balanced_k_year": K_YEAR,
        "parent_min_samples": MIN_SAMPLES,
        "min_cluster_size": MIN_CLUSTER_SIZE,
        "core_is_pointwise_annual_max": True,
        "hierarchy_constructed": True,
        "density_synchronous_scoring_constructed": True,
        "selected_nodes": len(nodes),
        "prior_injection_equivalence_pass_run": 31861223877,
        "gmn_catalogue_accessed": False,
        "scientific_labels_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_accessed": False,
        "efn_accessed": False,
        "asfn_accessed": False,
        "amos_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = Path("orbittrace_density_sync_stratified_core_v1/output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "DENSITY_SYNC_STRATIFIED_CORE_V1_ZERO_TRUTH_COMPOSITION_AUDIT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(result["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
