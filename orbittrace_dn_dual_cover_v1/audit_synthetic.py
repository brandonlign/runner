#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from dn_dual_cover import (
    EARTH_SPEED_KM_S,
    dn_coordinates,
    dn_distance_squared_from_coordinates,
    dual_cover,
    fold_selected_cover_clusters,
)


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def row(coords: dict[str, np.ndarray], i: int) -> dict[str, float]:
    return {k: float(coords[k][i]) for k in ("u", "cos_theta", "phi", "lambda")}


def cover_pair_min_sq(cover: np.ndarray, n: int, i: int, j: int, sheet_i: int = 0) -> float:
    ii = i + sheet_i * n
    d0 = float(np.sum((cover[ii] - cover[j]) ** 2))
    d1 = float(np.sum((cover[ii] - cover[n + j]) ** 2))
    return min(d0, d1)


def main() -> int:
    rng = np.random.Generator(np.random.PCG64(20260815))
    n = 64
    sol = rng.uniform(0.0, 360.0, n)
    lon = rng.uniform(-180.0, 180.0, n)
    lat = rng.uniform(-75.0, 75.0, n)
    vg = rng.uniform(8.0, 71.0, n)

    cover, coords = dual_cover(sol, lon, lat, vg)
    req(cover.shape == (2 * n, 6), "dual-cover shape is wrong")
    req(np.allclose(coords["u"], vg / EARTH_SPEED_KM_S, rtol=0.0, atol=1e-15), "u normalization changed")

    # Independent check of the Sun-centred radiant -> D_N velocity-frame map.
    L = np.radians(lon)
    beta = np.radians(lat)
    expected_ux = np.cos(beta) * np.cos(L)
    expected_uy = np.cos(beta) * np.sin(L)
    expected_uz = -np.sin(beta)
    req(np.allclose(coords["ux_hat"], expected_ux, rtol=0.0, atol=2e-15), "Ux mapping failed")
    req(np.allclose(coords["uy_hat"], expected_uy, rtol=0.0, atol=2e-15), "Uy mapping failed")
    req(np.allclose(coords["uz_hat"], expected_uz, rtol=0.0, atol=2e-15), "Uz mapping failed")
    req(np.allclose(coords["cos_theta"], expected_uy, rtol=0.0, atol=2e-15), "cos(theta) mapping failed")

    # Exact algebraic identity: published D_N is the minimum Euclidean distance
    # across the two sheets, starting from either representative of event i.
    max_abs_err = 0.0
    max_rel_err = 0.0
    comparisons = 0
    for i in range(n):
        for j in range(i + 1, n):
            explicit = dn_distance_squared_from_coordinates(row(coords, i), row(coords, j))
            for sheet_i in (0, 1):
                lifted = cover_pair_min_sq(cover, n, i, j, sheet_i)
                err = abs(explicit - lifted)
                max_abs_err = max(max_abs_err, err)
                max_rel_err = max(max_rel_err, err / max(abs(explicit), 1e-15))
                req(np.isclose(explicit, lifted, rtol=2e-13, atol=2e-13), f"D_N dual-cover identity failed i={i} j={j} sheet={sheet_i}: {explicit} vs {lifted}")
                comparisons += 1
            reverse = dn_distance_squared_from_coordinates(row(coords, j), row(coords, i))
            req(np.isclose(explicit, reverse, rtol=0.0, atol=2e-14), "explicit D_N symmetry failed")

    # A common pi shift in encounter longitude must leave all D_N pairwise
    # distances unchanged, validating use of stored solar longitude in place of
    # Earth heliocentric encounter longitude.
    shifted_cover, shifted_coords = dual_cover(np.mod(sol + 180.0, 360.0), lon, lat, vg)
    shift_max = 0.0
    for i in range(0, n, 3):
        for j in range(i + 1, n, 5):
            before = dn_distance_squared_from_coordinates(row(coords, i), row(coords, j))
            after = dn_distance_squared_from_coordinates(row(shifted_coords, i), row(shifted_coords, j))
            shift_max = max(shift_max, abs(before - after))
            req(np.isclose(before, after, rtol=2e-14, atol=2e-14), "common pi encounter-longitude shift changed D_N")
            req(np.isclose(cover_pair_min_sq(shifted_cover, n, i, j), after, rtol=2e-13, atol=2e-13), "shifted cover no longer realizes D_N")

    # Folding audit: two mirror cover clusters with identical physical members
    # collapse to one valid physical family.
    ids = [f"E{i:02d}" for i in range(12)]
    labels = np.full(24, -1, dtype=np.int64)
    labels[np.arange(0, 10)] = 0
    labels[12 + np.arange(0, 10)] = 1
    nodes = (30, 31)
    ordinary = {30.0: 3.0, 31.0: 3.0}
    sync = {30.0: 2.0, 31.0: 2.0}
    folded, fold_audit = fold_selected_cover_clusters(labels, nodes, ids, ordinary, sync)
    req(len(folded) == 1, "mirror duplicate did not collapse to one physical family")
    req(folded[0]["event_ids"] == ids[:10], "mirror-folded membership changed")
    req(fold_audit["mirror_duplicate_cluster_count"] == 1, "mirror duplicate not reported")
    req(fold_audit["invalid_duplicate_sheet_cluster_count"] == 0, "valid mirror fixture flagged duplicate sheet")

    # Mixed-sheet parity is valid when each physical meteor appears exactly once.
    mixed_labels = np.full(24, -1, dtype=np.int64)
    mixed_labels[np.r_[np.arange(0, 5), 12 + np.arange(5, 10)]] = 0
    mixed_labels[np.r_[np.arange(5, 10), 12 + np.arange(0, 5)]] = 1
    mixed, mixed_audit = fold_selected_cover_clusters(mixed_labels, nodes, ids, ordinary, sync)
    req(len(mixed) == 1 and mixed[0]["event_ids"] == ids[:10], "mixed-sheet valid cluster did not fold correctly")
    req(mixed_audit["mirror_duplicate_cluster_count"] == 1, "mixed-sheet mirror was not deduplicated")

    # A cover cluster containing both representatives of one physical event is
    # invalid by the frozen quotient rule and must be discarded.
    bad_labels = np.full(24, -1, dtype=np.int64)
    bad_labels[np.r_[np.arange(0, 10), 12]] = 0
    bad, bad_audit = fold_selected_cover_clusters(bad_labels, (30,), ids, {30.0: 3.0}, {30.0: 2.0})
    req(len(bad) == 0, "duplicate-sheet physical cluster was emitted")
    req(bad_audit["invalid_duplicate_sheet_cluster_count"] == 1, "duplicate-sheet invalidity was not reported")

    result = {
        "verdict": "PASS_DN_DUAL_COVER_V1_SYNTHETIC_AUDIT",
        "scientific_data_access": False,
        "gmn_access": False,
        "sonotaco_access": False,
        "asfn_access": False,
        "efn_access": False,
        "amos_access": False,
        "target_information_access": False,
        "target_region_events_accessed": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
        "weights": {"w1": 1.0, "w2": 1.0, "w3": 1.0},
        "earth_speed_km_s": EARTH_SPEED_KM_S,
        "random_pair_sheet_comparisons": comparisons,
        "max_dn_squared_identity_abs_error": max_abs_err,
        "max_dn_squared_identity_relative_error": max_rel_err,
        "max_common_pi_shift_abs_error": shift_max,
        "tests": {
            "published_observable_mapping": True,
            "published_dn_exact_dual_cover_identity": True,
            "both_starting_sheets_equivalent": True,
            "explicit_dn_symmetric": True,
            "common_pi_encounter_longitude_shift_invariant": True,
            "mirror_family_deduplication": True,
            "mixed_sheet_valid_fold": True,
            "duplicate_physical_sheet_rejected": True,
            "no_fitted_weights_or_thresholds": True,
        },
        "fold_fixture": fold_audit,
        "mixed_fold_fixture": mixed_audit,
        "invalid_fold_fixture": bad_audit,
    }
    out = Path("output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "DN_DUAL_COVER_V1_SYNTHETIC_AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
