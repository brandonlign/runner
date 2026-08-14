#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import hdbscan
import numpy as np

from recurrent_eom import (
    eom_labels,
    parent_labels_through_custom_path,
    recurrent_stability,
    selected_eom_nodes,
)
from hdbscan._hdbscan_tree import compute_stability


def canonical_partition(labels: np.ndarray) -> tuple[tuple[int, ...], ...]:
    groups = []
    for lab in sorted(int(x) for x in np.unique(labels) if int(x) >= 0):
        groups.append(tuple(np.flatnonzero(labels == lab).tolist()))
    return tuple(sorted(groups))


def main() -> int:
    rng = np.random.default_rng(20260814)
    # Synthetic only: three recurring blobs plus year-specific nuisance blobs and noise.
    recurring = np.asarray([[-4.0, -2.0], [0.0, 3.0], [4.0, -1.0]])
    xs = []
    ys = []
    for year, shift in ((2022, np.asarray([0.00, 0.00])), (2023, np.asarray([0.12, -0.08]))):
        for center in recurring:
            xs.append(rng.normal(center + shift, 0.35, size=(45, 2)))
            ys.extend([year] * 45)
        nuisance = np.asarray([7.0, 5.0]) if year == 2022 else np.asarray([-7.0, 5.0])
        xs.append(rng.normal(nuisance, 0.28, size=(35, 2)))
        ys.extend([year] * 35)
        xs.append(rng.uniform(-9, 9, size=(30, 2)))
        ys.extend([year] * 30)
    X = np.vstack(xs)
    years = np.asarray(ys, dtype=np.int64)

    parent = hdbscan.HDBSCAN(
        min_cluster_size=10,
        min_samples=10,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = parent.condensed_tree_._raw_tree

    custom_parent = parent_labels_through_custom_path(tree)
    if canonical_partition(parent.labels_) != canonical_partition(custom_parent):
        raise RuntimeError("ordinary HDBSCAN labels do not reproduce through custom EOM path")

    ordinary = compute_stability(tree)
    ordinary_nodes = selected_eom_nodes(tree, ordinary)
    recurrent, annual = recurrent_stability(tree, years)
    recurrent_labels = eom_labels(tree, recurrent)
    recurrent_nodes = selected_eom_nodes(tree, recurrent)

    if recurrent_labels.shape != parent.labels_.shape:
        raise RuntimeError("recurrent label vector shape changed")
    if not all(np.isfinite(v) and v >= 0.0 for v in recurrent.values()):
        raise RuntimeError("recurrent stability is nonfinite or negative")

    out = {
        "verdict": "PASS_RECURRENT_EOM_HDBSCAN_IDENTITY_AUDIT",
        "scientific_endpoint": False,
        "synthetic_only": True,
        "hdbscan_version": hdbscan.__version__,
        "points": int(X.shape[0]),
        "ordinary_partition_sha256": hashlib.sha256(repr(canonical_partition(parent.labels_)).encode()).hexdigest(),
        "custom_parent_partition_sha256": hashlib.sha256(repr(canonical_partition(custom_parent)).encode()).hexdigest(),
        "ordinary_selected_nodes": list(ordinary_nodes),
        "recurrent_selected_nodes": list(recurrent_nodes),
        "mechanism_active_on_synthetic": ordinary_nodes != recurrent_nodes,
        "annual_stability_cluster_count": len(annual),
        "target_information_access": False,
        "target_region_events_accessed": False,
        "sonotaco_2013_2014_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    Path("identity_audit.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
