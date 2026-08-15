#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from hdbscan._hdbscan_tree import compute_stability

import recurrent_eom as parent
from density_synchronous_eom import TOL, density_synchronous_stability

DTYPE = np.dtype([
    ("parent", np.int64),
    ("child", np.int64),
    ("lambda_val", np.float64),
    ("child_size", np.int64),
])


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def close(a: float, b: float) -> bool:
    return bool(np.isclose(float(a), float(b), rtol=TOL, atol=TOL))


def array_sha(a: np.ndarray) -> str:
    return hashlib.sha256(a.tobytes()).hexdigest()


def identical_curve_fixture() -> tuple[np.ndarray, np.ndarray]:
    years = np.asarray([2022, 2022, 2022, 2022, 2023, 2023, 2023, 2023], dtype=np.int64)
    rows = [
        (8, 0, 1.0, 1), (8, 4, 1.0, 1),
        (8, 1, 2.0, 1), (8, 5, 2.0, 1),
        (8, 2, 3.0, 1), (8, 6, 3.0, 1),
        (8, 3, 4.0, 1), (8, 7, 4.0, 1),
    ]
    return np.asarray(rows, dtype=DTYPE), years


def crossing_curve_fixture() -> tuple[np.ndarray, np.ndarray]:
    years = np.asarray([2022, 2022, 2022, 2022, 2023, 2023, 2023, 2023], dtype=np.int64)
    rows = [
        (8, 0, 1.0, 1),
        (8, 4, 2.0, 1), (8, 5, 2.0, 1),
        (8, 1, 3.0, 1), (8, 2, 3.0, 1), (8, 3, 3.0, 1),
        (8, 6, 4.0, 1), (8, 7, 4.0, 1),
    ]
    return np.asarray(rows, dtype=DTYPE), years


def nested_locality_fixture(sibling_shift: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    # Points 0,1,4,5 form cluster 9; points 2,3,6,7 form sibling cluster 10.
    # Internal density changes inside sibling 10 must not change local quality of node 9.
    years = np.asarray([2022, 2022, 2022, 2022, 2023, 2023, 2023, 2023], dtype=np.int64)
    rows = [
        (8, 9, 1.0, 4), (8, 10, 1.0, 4),
        (9, 0, 2.0, 1), (9, 4, 2.0, 1),
        (9, 1, 3.0, 1), (9, 5, 3.0, 1),
        (10, 2, 2.5 + sibling_shift, 1), (10, 6, 2.5 + sibling_shift, 1),
        (10, 3, 3.5 + sibling_shift, 1), (10, 7, 3.5 + sibling_shift, 1),
    ]
    return np.asarray(rows, dtype=DTYPE), years


def run_fixture(tree: np.ndarray, years: np.ndarray) -> tuple[dict[float, float], dict[int, tuple[float, float]]]:
    before = tree.copy()
    ordinary_before = compute_stability(tree)
    sync, annual, reconstructed = density_synchronous_stability(tree, years)
    req(np.array_equal(tree, before), "synchronous kernel mutated condensed tree")
    ordinary_after = compute_stability(tree)
    req(ordinary_before == ordinary_after, "ordinary HDBSCAN stability changed after synchronous kernel")
    req(set(annual) == set(reconstructed), "annual reconstruction node universe mismatch")
    for node in annual:
        req(
            np.allclose(np.asarray(annual[node]), np.asarray(reconstructed[node]), rtol=TOL, atol=TOL),
            f"annual parent identity failed for node {node}",
        )
        req(sync[float(node)] <= min(annual[node]) + TOL * max(1.0, abs(min(annual[node]))), f"upper bound failed {node}")
    return sync, annual


def main() -> int:
    # 1. Identical annual alive-mass curves: synchronous quality must equal each annual EOM.
    identical_tree, identical_years = identical_curve_fixture()
    identical_sync, identical_annual = run_fixture(identical_tree, identical_years)
    root = 8
    req(close(identical_annual[root][0], 2.5), f"unexpected annual fixture value {identical_annual[root]}")
    req(close(identical_annual[root][1], 2.5), f"unexpected annual fixture value {identical_annual[root]}")
    req(close(identical_sync[float(root)], 2.5), f"identical-curve identity failed: {identical_sync[float(root)]}")

    # 2. Crossing annual curves: integration-after-min must be strictly smaller than min-after-integration.
    crossing_tree, crossing_years = crossing_curve_fixture()
    crossing_sync, crossing_annual = run_fixture(crossing_tree, crossing_years)
    parent_min = min(crossing_annual[root])
    req(close(crossing_annual[root][0], 2.5), f"unexpected crossing annual 2022 {crossing_annual[root][0]}")
    req(close(crossing_annual[root][1], 3.0), f"unexpected crossing annual 2023 {crossing_annual[root][1]}")
    req(close(crossing_sync[float(root)], 2.25), f"unexpected synchronous crossing value {crossing_sync[float(root)]}")
    req(crossing_sync[float(root)] < parent_min - TOL, "timing-sensitivity fixture did not separate successor from parent")

    # 3. Year-swap invariance.
    swapped = np.where(crossing_years == 2022, 2023, 2022).astype(np.int64)
    swapped_sync, _swapped_annual = run_fixture(crossing_tree.copy(), swapped)
    req(close(swapped_sync[float(root)], crossing_sync[float(root)]), "year-swap invariance failed")

    # 4. Direct-row tie permutation invariance.
    perm = np.arange(len(crossing_tree))
    # Reverse rows within each lambda group without changing values.
    for lam in np.unique(crossing_tree["lambda_val"]):
        idx = np.flatnonzero(crossing_tree["lambda_val"] == lam)
        perm[idx] = idx[::-1]
    permuted_tree = crossing_tree[perm].copy()
    perm_sync, perm_annual = run_fixture(permuted_tree, crossing_years)
    req(set(perm_sync) == set(crossing_sync), "tie permutation changed node universe")
    for node in crossing_sync:
        req(close(perm_sync[node], crossing_sync[node]), f"tie permutation changed synchronous value for node {node}")
    for node in crossing_annual:
        req(np.allclose(perm_annual[node], crossing_annual[node], rtol=TOL, atol=TOL), f"tie permutation changed annual EOM {node}")

    # 5. FOSC locality: perturb a sibling cluster's internal departure levels only.
    local_a, local_years = nested_locality_fixture(0.0)
    local_b, _ = nested_locality_fixture(7.0)
    local_sync_a, _ = run_fixture(local_a, local_years)
    local_sync_b, _ = run_fixture(local_b, local_years)
    req(close(local_sync_a[9.0], local_sync_b[9.0]), "node-9 local quality changed when only sibling internals changed")
    req(not close(local_sync_a[10.0], local_sync_b[10.0]), "sibling perturbation fixture was inert")

    # 6. Exact parent annual routine is the only annual-EOM reference.
    parent_recurrent, parent_annual = parent.recurrent_stability(crossing_tree, crossing_years)
    req(close(parent_recurrent[8.0], min(parent_annual[8])), "promoted parent recurrent identity failed")

    result = {
        "verdict": "PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_SYNTHETIC_AUDIT",
        "scientific_data_access": False,
        "gmn_access": False,
        "sonotaco_access": False,
        "efn_access": False,
        "asfn_access": False,
        "amos_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "tests": {
            "annual_parent_identity": True,
            "synchronous_upper_bound": True,
            "identical_curve_identity": True,
            "density_timing_sensitivity": True,
            "year_swap_invariance": True,
            "tie_permutation_invariance": True,
            "tree_nonmutation": True,
            "ordinary_stability_nonmutation": True,
            "locality_sibling_invariance": True,
        },
        "fixtures": {
            "identical_curve": {
                "annual": list(identical_annual[root]),
                "synchronous": identical_sync[float(root)],
                "tree_sha256": array_sha(identical_tree),
            },
            "crossing_curve": {
                "annual": list(crossing_annual[root]),
                "parent_recurrent_min": parent_min,
                "synchronous": crossing_sync[float(root)],
                "tree_sha256": array_sha(crossing_tree),
            },
        },
    }
    out = Path("output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_SYNTHETIC_AUDIT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
