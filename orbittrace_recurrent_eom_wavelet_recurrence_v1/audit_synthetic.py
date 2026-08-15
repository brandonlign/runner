#!/usr/bin/env python3
from __future__ import annotations

import json
import math

import numpy as np

import multi_anchor_energy_v3 as v3
from wavelet_recurrence import MIN_ANNUAL_MEMBERS, METHOD_ID, candidate_wavelet_recurrence


def cluster(year: int, lon_shift: float = 0.0) -> list[dict[str, float | int]]:
    return [
        {"year": year, "sun_lon": 179.6 + lon_shift, "ecl_lat": 10.0, "vg": 40.0},
        {"year": year, "sun_lon": -179.8 + lon_shift, "ecl_lat": 10.2, "vg": 40.2},
        {"year": year, "sun_lon": 179.9 + lon_shift, "ecl_lat": 9.8, "vg": 39.9},
        {"year": year, "sun_lon": -179.5 + lon_shift, "ecl_lat": 10.1, "vg": 40.1},
        {"year": year, "sun_lon": 179.7 + lon_shift, "ecl_lat": 9.9, "vg": 40.05},
    ]


def dispersed(year: int) -> list[dict[str, float | int]]:
    return [
        {"year": year, "sun_lon": -150.0, "ecl_lat": -50.0, "vg": 15.0},
        {"year": year, "sun_lon": -50.0, "ecl_lat": -15.0, "vg": 30.0},
        {"year": year, "sun_lon": 50.0, "ecl_lat": 20.0, "vg": 45.0},
        {"year": year, "sun_lon": 150.0, "ecl_lat": 55.0, "vg": 60.0},
        {"year": year, "sun_lon": 90.0, "ecl_lat": -35.0, "vg": 25.0},
    ]


def direct_energy(rows: list[dict[str, float | int]]) -> float:
    class Episode:
        pass

    episode = Episode()
    episode.sun_lon = np.asarray([float(row["sun_lon"]) for row in rows])
    episode.ecl_lat = np.asarray([float(row["ecl_lat"]) for row in rows])
    episode.vg = np.asarray([float(row["vg"]) for row in rows])
    return float(v3.multi_anchor_energy_episode_score(episode))


def main() -> int:
    recurrent_rows = cluster(2022) + cluster(2023)
    recurrent = candidate_wavelet_recurrence(recurrent_rows, v3)
    mixed = candidate_wavelet_recurrence(cluster(2022) + dispersed(2023), v3)

    swapped = [dict(row, year=2023 if int(row["year"]) == 2022 else 2022) for row in recurrent_rows]
    swapped_stat = candidate_wavelet_recurrence(swapped, v3)

    perm = list(reversed(recurrent_rows))
    perm_stat = candidate_wavelet_recurrence(perm, v3)

    sparse = candidate_wavelet_recurrence(cluster(2022) + cluster(2023)[:3], v3)
    wrap = candidate_wavelet_recurrence(cluster(2022, 360.0) + cluster(2023, -360.0), v3)

    tests = {
        "method_id": METHOD_ID == "orbittrace_recurrent_eom_wavelet_recurrence_v1",
        "minimum_annual_members_is_frozen_v3_minimum": MIN_ANNUAL_MEMBERS == 4,
        "exact_v3_2022_energy": math.isclose(recurrent.annual_energy_2022, direct_energy(cluster(2022)), rel_tol=0.0, abs_tol=1e-12),
        "exact_v3_2023_energy": math.isclose(recurrent.annual_energy_2023, direct_energy(cluster(2023)), rel_tol=0.0, abs_tol=1e-12),
        "recurrence_is_exact_annual_minimum": math.isclose(recurrent.recurrence_score, min(recurrent.annual_energy_2022, recurrent.annual_energy_2023), rel_tol=0.0, abs_tol=1e-12),
        "two_year_cluster_beats_one_year_dispersed": recurrent.recurrence_score > mixed.recurrence_score,
        "year_swap_invariant": math.isclose(recurrent.recurrence_score, swapped_stat.recurrence_score, rel_tol=0.0, abs_tol=1e-12),
        "permutation_invariant": math.isclose(recurrent.recurrence_score, perm_stat.recurrence_score, rel_tol=0.0, abs_tol=1e-12),
        "under_four_in_one_year_zeroes_recurrence": sparse.recurrence_score == 0.0 and sparse.annual_energy_2023 == 0.0,
        "longitude_wrap_invariant": math.isclose(recurrent.recurrence_score, wrap.recurrence_score, rel_tol=0.0, abs_tol=1e-10),
        "frozen_v3_constants": (
            v3.ANGULAR_PROBE_DEG == 4.0
            and v3.SPEED_PROBE_FRACTION == 0.10
            and v3.TRUNCATION_RADIUS == 4.0
            and v3.KERNEL_DIMENSION == 3.0
            and v3.TOP_ANCHORS == 4
        ),
    }
    passed = all(tests.values())
    payload = {
        "verdict": "PASS_RECURRENT_EOM_WAVELET_RECURRENCE_V1_SYNTHETIC_AUDIT" if passed else "FAIL_RECURRENT_EOM_WAVELET_RECURRENCE_V1_SYNTHETIC_AUDIT",
        "tests": tests,
        "clustered_score": recurrent.recurrence_score,
        "mixed_score": mixed.recurrence_score,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
