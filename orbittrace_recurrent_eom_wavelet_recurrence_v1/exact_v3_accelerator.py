from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np
from scipy.spatial import cKDTree

METHOD_ID = "orbittrace_multi_anchor_wavelet_energy_v3_exact_accelerator"
ANGULAR_PROBE_DEG = 4.0
SPEED_PROBE_FRACTION = 0.10
TRUNCATION_RADIUS = 4.0
KERNEL_DIMENSION = 3.0
TOP_ANCHORS = 4

_ANGULAR_PROBE_RAD = math.radians(ANGULAR_PROBE_DEG)
_MAX_ANGULAR_RAD = TRUNCATION_RADIUS * _ANGULAR_PROBE_RAD
_MAX_CHORD = 2.0 * math.sin(0.5 * _MAX_ANGULAR_RAD)
# Search radius is intentionally a tiny superset. The original r^2 test below
# is authoritative, so this cannot add a nonzero contribution.
_TREE_RADIUS = _MAX_CHORD + 1e-12


def _finite_vector(values: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or len(array) < 4 or not np.all(np.isfinite(array)):
        raise ValueError(f"invalid {name}")
    return array


def _radiant_vectors(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
    lon = np.radians(lon_deg)
    lat = np.radians(lat_deg)
    vectors = np.column_stack((
        np.cos(lat) * np.cos(lon),
        np.cos(lat) * np.sin(lon),
        np.sin(lat),
    ))
    if not np.all(np.isfinite(vectors)):
        raise ValueError("invalid radiant vectors")
    return vectors


def wavelet_coefficients_from_arrays(
    sun_centered_longitude_deg: Sequence[float] | np.ndarray,
    ecliptic_latitude_deg: Sequence[float] | np.ndarray,
    geocentric_speed_km_s: Sequence[float] | np.ndarray,
) -> np.ndarray:
    lon = _finite_vector(sun_centered_longitude_deg, "longitude")
    lat = _finite_vector(ecliptic_latitude_deg, "latitude")
    speed = _finite_vector(geocentric_speed_km_s, "speed")
    if not (len(lon) == len(lat) == len(speed)) or np.any(speed <= 0.0):
        raise ValueError("shape mismatch or invalid speed")

    vectors = _radiant_vectors(lon, lat)
    tree = cKDTree(vectors)
    coefficients = np.zeros(len(speed), dtype=np.float64)

    for j in range(len(speed)):
        neighbors = tree.query_ball_point(vectors[j], r=_TREE_RADIUS)
        if not neighbors:
            continue
        idx = np.asarray(sorted(int(i) for i in neighbors if int(i) != j), dtype=np.int64)
        if idx.size == 0:
            continue

        # Exact frozen v3 geometry, evaluated only on the angular-support
        # superset guaranteed to contain every possible nonzero contribution.
        cosine = np.clip(vectors[idx] @ vectors[j], -1.0, 1.0)
        angular = np.arccos(cosine)
        angular_term = (angular / _ANGULAR_PROBE_RAD) ** 2
        test_speed_scale = SPEED_PROBE_FRACTION * speed[j]
        speed_term = ((speed[idx] - speed[j]) / test_speed_scale) ** 2
        r2 = np.maximum(angular_term + speed_term, 0.0)
        mask = r2 <= TRUNCATION_RADIUS ** 2
        if not np.any(mask):
            continue
        rr = r2[mask]
        weights = (KERNEL_DIMENSION - rr) * np.exp(-0.5 * rr)
        coefficients[j] = float(np.sum(weights))

    if coefficients.ndim != 1 or not np.all(np.isfinite(coefficients)):
        raise ValueError("invalid coefficients")
    return coefficients


def episode_score_details(episode: Any) -> dict[str, Any]:
    coefficients = wavelet_coefficients_from_arrays(episode.sun_lon, episode.ecl_lat, episode.vg)
    positive = np.maximum(coefficients, 0.0)
    top_count = min(TOP_ANCHORS, len(positive))
    indices = np.argpartition(positive, -top_count)[-top_count:]
    order = indices[np.argsort(positive[indices])[::-1]]
    values = positive[order]
    if top_count < TOP_ANCHORS:
        values = np.pad(values, (0, TOP_ANCHORS - top_count))
    score = float(np.sqrt(np.sum(values * values)))
    if not math.isfinite(score):
        raise ValueError("non-finite energy")
    return {
        "score": score,
        "brown_peak": float(np.max(coefficients)),
        "top_anchor_indices": [int(index) for index in order],
        "top_positive_coefficients": [float(value) for value in values],
    }


def multi_anchor_energy_episode_score(episode: Any) -> float:
    return float(episode_score_details(episode)["score"])
