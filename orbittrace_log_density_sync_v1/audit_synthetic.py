#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from hdbscan._hdbscan_tree import compute_stability

from density_synchronous_eom import density_synchronous_stability
from log_density_sync import TOL, log_density_synchronous_stability

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
    return bool(np.isclose(float(a), float(b), rtol=1e-12, atol=1e-12))


def sha(a: np.ndarray) -> str:
    return hashlib.sha256(a.tobytes()).hexdigest()


def fixture(sibling_scale: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    # root=8; node 9 has two members from each year and is the analytic target.
    # node 10 is an independent sibling used for locality testing.
    years = np.asarray([2022, 2022, 2022, 2022, 2023, 2023, 2023, 2023], dtype=np.int64)
    rows = [
        (8, 9, 1.0, 4), (8, 10, 1.0, 4),
        (9, 0, 2.0, 1), (9, 4, 2.0, 1),
        (9, 1, 4.0, 1), (9, 5, 4.0, 1),
        (10, 2, 2.0 * sibling_scale, 1), (10, 6, 2.0 * sibling_scale, 1),
        (10, 3, 3.0 * sibling_scale, 1), (10, 7, 3.0 * sibling_scale, 1),
    ]
    return np.asarray(rows, dtype=DTYPE), years


def main() -> int:
    tree, years = fixture()
    before = tree.copy()
    ordinary_before = compute_stability(tree)
    log_score = log_density_synchronous_stability(tree, years)
    ordinary_after = compute_stability(tree)

    req(np.array_equal(tree, before), "log-density kernel mutated condensed tree")
    req(ordinary_before == ordinary_after, "ordinary HDBSCAN stability changed")
    req(log_score[8.0] == 0.0, "root score is not exactly zero")

    # Node 9: alive recurrent mass is 0.5 over lambda 1->2, then 0.25 over 2->4.
    expected_9 = 0.5 * np.log(2.0) + 0.25 * np.log(2.0)
    req(close(log_score[9.0], expected_9), f"analytic dlog integral failed: {log_score[9.0]} != {expected_9}")

    # Global multiplicative density scaling is the core intended invariance.
    scaled = tree.copy()
    scaled["lambda_val"] *= 17.0
    scaled_log = log_density_synchronous_stability(scaled, years)
    for node in (9.0, 10.0):
        req(close(log_score[node], scaled_log[node]), f"multiplicative lambda-scale invariance failed for {node}")

    # The existing raw-density champion is intentionally not invariant: non-root
    # synchronous stability scales linearly when every lambda is multiplied.
    raw, _, _ = density_synchronous_stability(tree, years)
    raw_scaled, _, _ = density_synchronous_stability(scaled, years)
    req(close(raw_scaled[9.0], 17.0 * raw[9.0]), "raw-density reference did not scale linearly")
    req(not close(raw_scaled[9.0], raw[9.0]), "synthetic distinction from raw-density champion was inert")

    # Year identity is symmetric.
    swapped_years = np.where(years == 2022, 2023, 2022).astype(np.int64)
    swapped = log_density_synchronous_stability(tree, swapped_years)
    for node in log_score:
        req(close(log_score[node], swapped[node]), f"year-swap invariance failed for {node}")

    # Permuting rows tied at the same lambda must not change scores.
    perm = np.arange(len(tree))
    for lam in np.unique(tree["lambda_val"]):
        idx = np.flatnonzero(tree["lambda_val"] == lam)
        perm[idx] = idx[::-1]
    permuted = tree[perm].copy()
    perm_score = log_density_synchronous_stability(permuted, years)
    for node in log_score:
        req(close(log_score[node], perm_score[node]), f"tie-row permutation changed node {node}")

    # Sibling-locality: changing only node 10 internals must not change node 9.
    sibling_tree, sibling_years = fixture(sibling_scale=1.5)
    sibling_score = log_density_synchronous_stability(sibling_tree, sibling_years)
    req(close(log_score[9.0], sibling_score[9.0]), "node 9 changed when only sibling internals changed")
    req(not close(log_score[10.0], sibling_score[10.0]), "sibling perturbation fixture was inert")

    result = {
        "verdict": "PASS_LOG_DENSITY_SYNCHRONOUS_EOM_V1_SYNTHETIC_AUDIT",
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
            "analytic_dlog_integral": True,
            "root_zero_without_log_offset": True,
            "multiplicative_lambda_scale_invariance": True,
            "distinct_from_raw_density_champion": True,
            "year_swap_invariance": True,
            "tie_permutation_invariance": True,
            "sibling_locality": True,
            "tree_nonmutation": True,
            "ordinary_stability_nonmutation": True,
        },
        "fixture": {
            "tree_sha256": sha(tree),
            "node9_log_score": float(log_score[9.0]),
            "node9_expected": float(expected_9),
            "node9_raw_score": float(raw[9.0]),
            "node9_raw_scaled_17x": float(raw_scaled[9.0]),
        },
    }
    out = Path("output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "LOG_DENSITY_SYNCHRONOUS_EOM_V1_SYNTHETIC_AUDIT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
