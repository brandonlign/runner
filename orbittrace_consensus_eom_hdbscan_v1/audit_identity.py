#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

from orbittrace_consensus_eom_hdbscan_v1.consensus_eom import consensus_selected_nodes, labels_from_selected_nodes
from orbittrace_recurrent_eom_hdbscan_v1.recurrent_eom import eom_labels, recurrent_stability, selected_eom_nodes

HERE = Path(__file__).resolve().parent


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def partition(labels: np.ndarray) -> tuple[tuple[int, ...], ...]:
    groups = []
    for lab in sorted(int(x) for x in np.unique(labels) if int(x) >= 0):
        groups.append(tuple(np.flatnonzero(labels == lab).tolist()))
    return tuple(sorted(groups))


def part_sha(labels: np.ndarray) -> str:
    return hashlib.sha256(json.dumps(partition(labels), separators=(",", ":")).encode()).hexdigest()


def make_case(seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    centers = np.asarray([
        [-3.0, -1.0],
        [-1.2, 2.8],
        [2.2, 2.0],
        [3.4, -2.3],
        [0.1, -3.2],
    ])
    blocks = []
    years = []
    for j, center in enumerate(centers):
        n = 64 + 4 * j
        x = rng.normal(center, [0.28 + 0.02 * j, 0.24 + 0.015 * j], size=(n, 2))
        blocks.append(x)
        # Deterministic balanced recurrence, not a label/truth field.
        yy = np.asarray([2022 if i % 2 == 0 else 2023 for i in range(n)], dtype=np.int64)
        rng.shuffle(yy)
        years.append(yy)
    # Add low-density background to exercise noise ancestry.
    bg = rng.uniform([-5.5, -5.0], [5.5, 5.0], size=(90, 2))
    blocks.append(bg)
    years.append(np.asarray([2022 if i % 2 == 0 else 2023 for i in range(len(bg))], dtype=np.int64))
    return np.vstack(blocks), np.concatenate(years)


def run_case(seed: int) -> dict:
    X, years = make_case(seed)
    model = hdbscan.HDBSCAN(
        min_cluster_size=10,
        min_samples=10,
        metric="euclidean",
        cluster_selection_method="eom",
        cluster_selection_epsilon=0.0,
        allow_single_cluster=False,
        prediction_data=False,
    ).fit(X)
    tree = model.condensed_tree_._raw_tree
    ordinary = compute_stability(tree)
    ordinary_nodes = selected_eom_nodes(tree, ordinary)
    ordinary_labels = eom_labels(tree, ordinary)
    ordinary_custom = labels_from_selected_nodes(tree, ordinary_nodes)
    require(partition(ordinary_labels) == partition(model.labels_), f"seed {seed}: frozen ordinary custom path diverged from HDBSCAN")
    require(partition(ordinary_custom) == partition(ordinary_labels), f"seed {seed}: ancestor labeller diverged on ordinary EOM")

    recurrent, annual = recurrent_stability(tree, years)
    recurrent_nodes = selected_eom_nodes(tree, recurrent)
    recurrent_labels = eom_labels(tree, recurrent)
    recurrent_custom = labels_from_selected_nodes(tree, recurrent_nodes)
    require(partition(recurrent_custom) == partition(recurrent_labels), f"seed {seed}: ancestor labeller diverged on recurrent EOM")

    # When both annual components are literally the same positive scalar EOM,
    # componentwise consensus must collapse to the standard scalar decision.
    root = int(tree["parent"].min())
    require(all(float(v) > 0.0 for k, v in ordinary.items() if int(float(k)) != root), f"seed {seed}: synthetic scalar-reduction case contains zero-stability nonroot")
    duplicated = {int(float(k)): (float(v), float(v)) for k, v in ordinary.items()}
    consensus_scalar_nodes = consensus_selected_nodes(tree, duplicated)
    require(consensus_scalar_nodes == ordinary_nodes, f"seed {seed}: componentwise selector does not reduce to scalar EOM")
    consensus_scalar_labels = labels_from_selected_nodes(tree, consensus_scalar_nodes)
    require(partition(consensus_scalar_labels) == partition(ordinary_labels), f"seed {seed}: scalar-reduced consensus partition differs")

    consensus_nodes = consensus_selected_nodes(tree, annual)
    consensus_labels = labels_from_selected_nodes(tree, consensus_nodes)
    require(all(np.all(np.asarray(annual[n], dtype=float) > 0.0) for n in consensus_nodes), f"seed {seed}: consensus selected nonrecurrent node")

    return {
        "seed": seed,
        "points": int(len(X)),
        "ordinary_selected_nodes": len(ordinary_nodes),
        "recurrent_selected_nodes": len(recurrent_nodes),
        "consensus_selected_nodes": len(consensus_nodes),
        "ordinary_partition_sha256": part_sha(ordinary_labels),
        "ordinary_custom_partition_sha256": part_sha(ordinary_custom),
        "recurrent_partition_sha256": part_sha(recurrent_labels),
        "recurrent_custom_partition_sha256": part_sha(recurrent_custom),
        "scalar_reduced_consensus_partition_sha256": part_sha(consensus_scalar_labels),
        "consensus_partition_sha256": part_sha(consensus_labels),
    }


def main() -> int:
    cases = [run_case(seed) for seed in (1701, 2203, 9147)]
    result = {
        "verdict": "PASS_CONSENSUS_EOM_HDBSCAN_V1_ZERO_TRUTH_IDENTITY_AUDIT",
        "synthetic_only": True,
        "cases": cases,
        "ordinary_hdbscan_partition_identity": True,
        "ordinary_selected_node_ancestor_labeller_identity": True,
        "recurrent_selected_node_ancestor_labeller_identity": True,
        "componentwise_reduces_to_scalar_eom_when_components_identical": True,
        "consensus_requires_positive_stability_both_years": True,
        "scientific_labels_accessed": False,
        "gmn_catalogue_accessed": False,
        "sonotaco_accessed": False,
        "efn_accessed": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = HERE / "output"
    out.mkdir(parents=True, exist_ok=True)
    (out / "CONSENSUS_EOM_ZERO_TRUTH_AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
