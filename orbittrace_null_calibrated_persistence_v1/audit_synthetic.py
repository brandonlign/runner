#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from null_calibration import (
    METHOD_ID,
    NULL_REPLICATES,
    calibrate_candidates,
    pareto_tail_rate,
    permuted_solar_longitude_matrix,
    replicate_seed,
)


def req(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def main() -> int:
    years = np.asarray([2022] * 6 + [2023] * 6, dtype=np.int64)
    sols = np.asarray([1, 5, 9, 60, 90, 120, 2, 6, 10, 70, 100, 130], dtype=float)
    lat = np.linspace(-0.4, 0.4, 12)
    lon = np.linspace(-1.0, 1.0, 12)
    vg = np.linspace(15.0, 55.0, 12)
    rsol = np.radians(sols)
    X = np.column_stack((
        np.cos(rsol), np.sin(rsol),
        np.sin(lon) * np.cos(lat),
        np.cos(lon) * np.cos(lat),
        np.sin(lat), vg / 72.0,
    ))

    X0, report0 = permuted_solar_longitude_matrix(X, sols, years, 0)
    X0b, report0b = permuted_solar_longitude_matrix(X, sols, years, 0)
    X1, report1 = permuted_solar_longitude_matrix(X, sols, years, 1)
    req(np.array_equal(X0, X0b), "replicate 0 is not deterministic")
    req(report0 == report0b, "replicate report is not deterministic")
    req(not np.array_equal(X0[:, :2], X1[:, :2]), "different frozen seeds produced identical null")
    req(np.array_equal(X0[:, 2:], X[:, 2:]), "replicate changed radiant/speed columns")
    req(np.array_equal(X1[:, 2:], X[:, 2:]), "replicate 1 changed radiant/speed columns")
    for year in (2022, 2023):
        idx = np.flatnonzero(years == year)
        recovered0 = (np.degrees(np.arctan2(X0[idx, 1], X0[idx, 0])) % 360.0)
        recovered1 = (np.degrees(np.arctan2(X1[idx, 1], X1[idx, 0])) % 360.0)
        req(np.allclose(np.sort(recovered0), np.sort(sols[idx]), atol=1e-12, rtol=0.0), f"rep0 sol multiset changed for {year}")
        req(np.allclose(np.sort(recovered1), np.sort(sols[idx]), atol=1e-12, rtol=0.0), f"rep1 sol multiset changed for {year}")

    req(len({replicate_seed(i) for i in range(NULL_REPLICATES)}) == NULL_REPLICATES, "frozen null seeds are not unique")

    null_fixture = [
        [(10, 1.0), (20, 2.0), (40, 3.0)],
        [(12, 1.2), (22, 2.2), (42, 3.2)],
    ]
    # Expand deterministically to the frozen 16 replicates without adding any
    # scientific behavior to the fixture.
    nulls = [list(null_fixture[i % 2]) for i in range(NULL_REPLICATES)]

    p_weak, _, _ = pareto_tail_rate(10, 1.0, nulls[0])
    p_mid, _, _ = pareto_tail_rate(20, 2.0, nulls[0])
    p_strong, _, _ = pareto_tail_rate(50, 4.0, nulls[0])
    req(p_strong < p_mid <= p_weak, "Pareto tail rate does not reward joint size/persistence surprise")

    candidates = [
        {"family_id": "weak", "member_count": 10, "synchronous_stability": 1.0, "ordinary_stability": 1.0},
        {"family_id": "mid", "member_count": 20, "synchronous_stability": 2.0, "ordinary_stability": 2.0},
        {"family_id": "strong", "member_count": 50, "synchronous_stability": 4.0, "ordinary_stability": 3.0},
    ]
    ranked = calibrate_candidates(candidates, nulls)
    req([r["family_id"] for r in ranked] == ["strong", "mid", "weak"], "null-calibrated ranking fixture failed")
    ranked2 = calibrate_candidates(candidates, nulls)
    req(ranked == ranked2, "null-calibrated ranking is not deterministic")

    result = {
        "verdict": "PASS_NULL_CALIBRATED_PERSISTENCE_V1_SYNTHETIC_AUDIT",
        "method_id": METHOD_ID,
        "null_replicates": NULL_REPLICATES,
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
        "tests": {
            "deterministic_permutation": True,
            "unique_frozen_seeds": True,
            "within_year_solar_longitude_multiset_preserved": True,
            "radiant_speed_columns_unchanged": True,
            "different_replicates_differ": True,
            "pareto_joint_monotonicity": True,
            "candidate_ranking_deterministic": True,
        },
        "replicate0": report0,
        "replicate1": report1,
        "fixture_tail_rates": {
            "weak": p_weak,
            "mid": p_mid,
            "strong": p_strong,
        },
    }
    out = Path("output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "NULL_CALIBRATED_PERSISTENCE_V1_SYNTHETIC_AUDIT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
