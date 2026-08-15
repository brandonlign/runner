#!/usr/bin/env python3
from __future__ import annotations

import json
import math

import numpy as np

import exact_v3_accelerator as accel
import multi_anchor_energy_v3 as direct

ABS_TOL = 2e-10


class Episode:
    pass


def episode(lon: np.ndarray, lat: np.ndarray, vg: np.ndarray) -> Episode:
    out = Episode()
    out.sun_lon = np.asarray(lon, dtype=np.float64)
    out.ecl_lat = np.asarray(lat, dtype=np.float64)
    out.vg = np.asarray(vg, dtype=np.float64)
    return out


def compare(name: str, e: Episode) -> dict[str, object]:
    direct_coeff = direct.wavelet_coefficients_from_arrays(e.sun_lon, e.ecl_lat, e.vg)
    accel_coeff = accel.wavelet_coefficients_from_arrays(e.sun_lon, e.ecl_lat, e.vg)
    direct_score = float(direct.multi_anchor_energy_episode_score(e))
    accel_score = float(accel.multi_anchor_energy_episode_score(e))
    max_coeff_abs = float(np.max(np.abs(direct_coeff - accel_coeff)))
    score_abs = abs(direct_score - accel_score)
    return {
        "name": name,
        "n": int(len(e.vg)),
        "max_coefficient_abs_difference": max_coeff_abs,
        "score_abs_difference": score_abs,
        "pass": bool(max_coeff_abs <= ABS_TOL and score_abs <= ABS_TOL),
    }


def main() -> int:
    rng = np.random.default_rng(20260815)
    fixtures: list[tuple[str, Episode]] = []

    fixtures.append(("wrap_cluster", episode(
        np.array([179.6, -179.8, 179.9, -179.5, 170.0, -170.0, 0.0, 90.0]),
        np.array([10.0, 10.2, 9.8, 10.1, 15.0, -10.0, 45.0, -45.0]),
        np.array([40.0, 40.2, 39.9, 40.1, 38.0, 42.0, 20.0, 65.0]),
    )))
    fixtures.append(("dense_128", episode(
        42.0 + rng.normal(0.0, 3.0, 128),
        -12.0 + rng.normal(0.0, 2.0, 128),
        36.0 + rng.normal(0.0, 1.5, 128),
    )))
    fixtures.append(("dispersed_127", episode(
        rng.uniform(-180.0, 180.0, 127),
        rng.uniform(-75.0, 75.0, 127),
        rng.uniform(12.0, 70.0, 127),
    )))
    fixtures.append(("mixed_257", episode(
        np.concatenate([15.0 + rng.normal(0.0, 2.5, 80), rng.uniform(-180.0, 180.0, 177)]),
        np.concatenate([25.0 + rng.normal(0.0, 2.0, 80), rng.uniform(-70.0, 70.0, 177)]),
        np.concatenate([48.0 + rng.normal(0.0, 2.0, 80), rng.uniform(12.0, 70.0, 177)]),
    )))
    fixtures.append(("near_support_boundary", episode(
        np.array([0.0, 15.999999999, 16.000000001, -15.999999999, -16.000000001, 30.0, 60.0, 90.0]),
        np.zeros(8),
        np.array([40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0, 40.0]),
    )))

    for n in (4, 5, 16, 32, 64):
        fixtures.append((f"random_{n}", episode(
            rng.uniform(-180.0, 180.0, n),
            rng.uniform(-80.0, 80.0, n),
            rng.uniform(10.0, 72.0, n),
        )))

    comparisons = [compare(name, e) for name, e in fixtures]
    tests = {
        "method_constants_identical": (
            accel.ANGULAR_PROBE_DEG == direct.ANGULAR_PROBE_DEG
            and accel.SPEED_PROBE_FRACTION == direct.SPEED_PROBE_FRACTION
            and accel.TRUNCATION_RADIUS == direct.TRUNCATION_RADIUS
            and accel.KERNEL_DIMENSION == direct.KERNEL_DIMENSION
            and accel.TOP_ANCHORS == direct.TOP_ANCHORS
        ),
        "direct_v3_self_test": all(direct.self_test().values()),
        "all_fixture_coefficients_and_scores_match": all(bool(row["pass"]) for row in comparisons),
        "support_radius_is_superset": accel._TREE_RADIUS > 2.0 * math.sin(0.5 * math.radians(16.0)),
    }
    passed = all(tests.values())
    payload = {
        "verdict": "PASS_EXACT_V3_ACCELERATOR_AUDIT" if passed else "FAIL_EXACT_V3_ACCELERATOR_AUDIT",
        "absolute_tolerance": ABS_TOL,
        "tests": tests,
        "comparisons": comparisons,
        "max_coefficient_abs_difference": max(float(row["max_coefficient_abs_difference"]) for row in comparisons),
        "max_score_abs_difference": max(float(row["score_abs_difference"]) for row in comparisons),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
