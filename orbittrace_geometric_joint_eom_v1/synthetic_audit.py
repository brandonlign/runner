#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import hdbscan
import numpy as np
from hdbscan._hdbscan_tree import compute_stability

import recurrent_eom as reom
from geometric_joint_eom import geometric_joint_stability


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def tree_sha(tree: np.ndarray) -> str:
    return hashlib.sha256(tree.tobytes()).hexdigest()


def main() -> int:
    rng = np.random.default_rng(20260819)
    # Three compact structures, each represented in both observing years.
    centers = np.asarray([[0.0, 0.0], [4.0, 0.5], [-3.5, 3.0]], dtype=float)
    xs: list[np.ndarray] = []
    ys: list[int] = []
    for year, offset in ((2013, np.asarray([0.0, 0.0])), (2014, np.asarray([0.08, -0.05]))):
        for c in centers:
            block = rng.normal(loc=c + offset, scale=0.22, size=(35, 2))
            xs.append(block)
            ys.extend([year] * len(block))
    X = np.vstack(xs)
    years = np.asarray(ys, dtype=np.int64)

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
    before = tree_sha(tree)

    joint, ordinary, recurrent, annual = geometric_joint_stability(tree, years)
    after = tree_sha(tree)
    req(before == after, "joint kernel mutated condensed hierarchy")
    req(set(joint) == set(ordinary) == set(recurrent), "node universe mismatch")
    req(all(np.isfinite(v) and v >= 0.0 for v in joint.values()), "invalid joint stability")

    swapped, ordinary2, recurrent2, annual2 = geometric_joint_stability(tree, years[::-1])
    req(ordinary == ordinary2, "ordinary stability changed under year swap")
    req(np.allclose([joint[k] for k in joint], [swapped[k] for k in joint], rtol=0.0, atol=1e-15), "joint score is not year-swap invariant")
    req(np.allclose([recurrent[k] for k in recurrent], [recurrent2[k] for k in recurrent], rtol=0.0, atol=1e-15), "recurrent score is not year-swap invariant")

    # Positive separate rescaling of the two axes must change all geometric
    # scores by the same factor and leave EOM node selection unchanged.
    a, b = 7.0, 0.13
    scaled = {k: float(np.sqrt((a * ordinary[k]) * (b * recurrent[k]))) for k in joint}
    factor = float(np.sqrt(a * b))
    req(np.allclose([scaled[k] for k in joint], [factor * joint[k] for k in joint], rtol=1e-14, atol=1e-14), "separate scale invariance failed")
    req(reom.selected_eom_nodes(tree, joint) == reom.selected_eom_nodes(tree, scaled), "selection changed under positive axis rescaling")

    # If the two axes are proportional, their geometric quality is only a
    # positive global rescaling of ordinary EOM and must reproduce its cut.
    prop = {k: 11.0 * ordinary[k] for k in ordinary}
    prop_joint = {k: float(np.sqrt(ordinary[k] * prop[k])) for k in ordinary}
    req(reom.selected_eom_nodes(tree, ordinary) == reom.selected_eom_nodes(tree, prop_joint), "proportional-map identity failed")

    result = {
        "verdict": "PASS_GEOMETRIC_JOINT_EOM_V1_SYNTHETIC_AUDIT",
        "tests": {
            "finite_nonnegative": True,
            "hierarchy_nonmutation": True,
            "year_swap_invariance": True,
            "positive_axis_rescaling_invariance": True,
            "proportional_map_identity": True,
        },
        "selected_nodes": list(reom.selected_eom_nodes(tree, joint)),
        "scientific_data_access": False,
        "gmn_access": False,
        "sonotaco_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
    }
    Path("GEOMETRIC_JOINT_EOM_V1_SYNTHETIC_AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
