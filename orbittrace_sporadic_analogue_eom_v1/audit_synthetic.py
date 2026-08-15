#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from hdbscan._hdbscan_tree import compute_stability

from density_synchronous_eom import density_synchronous_stability
from sporadic_analogue_eom import (
    ANALOGUE_OFFSETS_DEG,
    K_NEIGHBOURS,
    bounded_contrast_weight,
    sporadic_analogue_stability,
)

DTYPE = np.dtype([
    ("parent", np.int64),
    ("child", np.int64),
    ("lambda_val", np.float64),
    ("child_size", np.int64),
])
TOL = 1e-12


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def close(a: float, b: float) -> bool:
    return bool(np.isclose(float(a), float(b), rtol=TOL, atol=TOL))


def tree_sha(a: np.ndarray) -> str:
    return hashlib.sha256(a.tobytes()).hexdigest()


def fixture() -> tuple[np.ndarray, np.ndarray]:
    years = np.asarray([2022, 2022, 2022, 2022, 2023, 2023, 2023, 2023], dtype=np.int64)
    rows = [
        (8, 9, 1.0, 4), (8, 10, 1.0, 4),
        (9, 0, 2.0, 1), (9, 4, 2.0, 1),
        (9, 1, 3.0, 1), (9, 5, 3.0, 1),
        (10, 2, 2.5, 1), (10, 6, 2.5, 1),
        (10, 3, 3.5, 1), (10, 7, 3.5, 1),
    ]
    return np.asarray(rows, dtype=DTYPE), years


def main() -> int:
    req(K_NEIGHBOURS == 10, "k drifted from inherited HDBSCAN min_samples")
    req(ANALOGUE_OFFSETS_DEG == tuple(float(x) for x in range(60, 301, 10)), "analogue grid changed")
    req(len(ANALOGUE_OFFSETS_DEG) == 25, "published analogue count changed")

    # Fixed bounded transform identities.
    req(close(bounded_contrast_weight(1.0), 1.0), "unit contrast identity failed")
    req(close(bounded_contrast_weight(3.0), 1.5), "contrast=3 weight changed")
    req(close(bounded_contrast_weight(1.0 / 3.0), 0.5), "reciprocal contrast weight changed")
    for c in (0.1, 0.25, 0.5, 2.0, 4.0, 10.0):
        req(close(bounded_contrast_weight(c) + bounded_contrast_weight(1.0 / c), 2.0), f"reciprocal symmetry failed {c}")

    tree, years = fixture()
    before = tree.copy()
    ordinary_before = compute_stability(tree)

    # Exact identity to the current density-synchronous champion when all
    # local background contrasts are neutral (all weights = 1).
    champion, _annual, _reconstructed = density_synchronous_stability(tree, years)
    neutral = sporadic_analogue_stability(tree, years, np.ones(len(years), dtype=float))
    req(set(champion) == set(neutral), "neutral-weight node universe mismatch")
    for node in champion:
        req(close(champion[node], neutral[node]), f"neutral-weight identity failed for node {node}")

    # Survey-local significance must be able to change hierarchy-node quality
    # without changing the hierarchy itself. Upweight node-9 descendants in
    # both years and downweight node-10 descendants symmetrically.
    weights = np.asarray([1.5, 1.5, 0.5, 0.5, 1.5, 1.5, 0.5, 0.5], dtype=float)
    weighted = sporadic_analogue_stability(tree, years, weights)
    req(weighted[9.0] > neutral[9.0] + TOL, "upweighted recurrent node did not gain quality")
    req(weighted[10.0] < neutral[10.0] - TOL, "downweighted recurrent node did not lose quality")

    # Year-swap invariance when the same event weights move with the event.
    swapped_years = np.where(years == 2022, 2023, 2022).astype(np.int64)
    swapped = sporadic_analogue_stability(tree.copy(), swapped_years, weights.copy())
    req(set(swapped) == set(weighted), "year swap changed node universe")
    for node in weighted:
        req(close(swapped[node], weighted[node]), f"year-swap invariance failed for node {node}")

    # Row-order ties cannot matter.
    perm = np.arange(len(tree))
    for lam in np.unique(tree["lambda_val"]):
        idx = np.flatnonzero(tree["lambda_val"] == lam)
        perm[idx] = idx[::-1]
    permuted = tree[perm].copy()
    tied = sporadic_analogue_stability(permuted, years, weights)
    for node in weighted:
        req(close(tied[node], weighted[node]), f"tie permutation changed node {node}")

    req(np.array_equal(tree, before), "kernel mutated condensed tree")
    req(compute_stability(tree) == ordinary_before, "ordinary HDBSCAN stability changed")

    result = {
        "verdict": "PASS_SPORADIC_ANALOGUE_EOM_V1_SYNTHETIC_AUDIT",
        "scientific_data_access": False,
        "gmn_access": False,
        "sonotaco_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "tests": {
            "published_25_analogue_grid_frozen": True,
            "inherited_k10_frozen": True,
            "bounded_transform_unit_identity": True,
            "bounded_transform_reciprocal_symmetry": True,
            "neutral_weight_exact_champion_identity": True,
            "hierarchy_quality_responds_to_local_contrast": True,
            "year_swap_invariance": True,
            "tie_permutation_invariance": True,
            "tree_nonmutation": True,
            "ordinary_stability_nonmutation": True,
        },
        "fixture": {
            "tree_sha256": tree_sha(tree),
            "neutral_node9": neutral[9.0],
            "weighted_node9": weighted[9.0],
            "neutral_node10": neutral[10.0],
            "weighted_node10": weighted[10.0],
        },
    }
    out = Path("output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "SPORADIC_ANALOGUE_EOM_V1_SYNTHETIC_AUDIT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
