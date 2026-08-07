"""OrbitTrace multi-anchor wavelet energy, version 3.

Uses the exact frozen Brown-family sparse-episode matched-filter geometry, but
replaces the single-maximum episode aggregation with the L2 energy of the four
strongest positive leave-one-out anchor coefficients.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np

METHOD_ID = "orbittrace_multi_anchor_wavelet_energy_v3"
ANGULAR_PROBE_DEG = 4.0
SPEED_PROBE_FRACTION = 0.10
TRUNCATION_RADIUS = 4.0
KERNEL_DIMENSION = 3.0
TOP_ANCHORS = 4


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


def pairwise_dimensionless_radius_squared(
    sun_centered_longitude_deg: Sequence[float] | np.ndarray,
    ecliptic_latitude_deg: Sequence[float] | np.ndarray,
    geocentric_speed_km_s: Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Exact frozen Brown-family episode radius used by the comparator.

    Rows are contributing events and columns are test locations. Speed is scaled
    by 10% of the test-location speed, matching the frozen comparator exactly.
    """
    lon = _finite_vector(sun_centered_longitude_deg, "longitude")
    lat = _finite_vector(ecliptic_latitude_deg, "latitude")
    speed = _finite_vector(geocentric_speed_km_s, "speed")
    if not (len(lon) == len(lat) == len(speed)) or np.any(speed <= 0.0):
        raise ValueError("shape mismatch or invalid speed")

    vectors = _radiant_vectors(lon, lat)
    cosine = np.clip(vectors @ vectors.T, -1.0, 1.0)
    angular = np.arccos(cosine)
    angular_term = (angular / math.radians(ANGULAR_PROBE_DEG)) ** 2

    test_speed_scale = SPEED_PROBE_FRACTION * speed[None, :]
    speed_term = ((speed[:, None] - speed[None, :]) / test_speed_scale) ** 2

    r2 = np.maximum(angular_term + speed_term, 0.0)
    np.fill_diagonal(r2, 0.0)
    if r2.shape != (len(speed), len(speed)) or not np.all(np.isfinite(r2)):
        raise ValueError("invalid radius matrix")
    return r2


def wavelet_coefficients_from_arrays(
    sun_centered_longitude_deg: Sequence[float] | np.ndarray,
    ecliptic_latitude_deg: Sequence[float] | np.ndarray,
    geocentric_speed_km_s: Sequence[float] | np.ndarray,
) -> np.ndarray:
    r2 = pairwise_dimensionless_radius_squared(
        sun_centered_longitude_deg,
        ecliptic_latitude_deg,
        geocentric_speed_km_s,
    )
    weights = (KERNEL_DIMENSION - r2) * np.exp(-0.5 * r2)
    weights = np.where(r2 <= TRUNCATION_RADIUS ** 2, weights, 0.0)
    np.fill_diagonal(weights, 0.0)
    coefficients = weights.sum(axis=0)
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


def self_test() -> dict[str, bool]:
    class Episode:
        pass

    def build(clustered: bool) -> Any:
        episode = Episode()
        episode.sun_lon = np.linspace(-170.0, 170.0, 32)
        episode.ecl_lat = np.linspace(-55.0, 55.0, 32)
        episode.vg = np.linspace(15.0, 65.0, 32)
        if clustered:
            episode.sun_lon[:4] = np.array([179.6, -179.8, 179.9, -179.5])
            episode.ecl_lat[:4] = np.array([10.0, 10.2, 9.8, 10.1])
            episode.vg[:4] = np.array([40.0, 40.2, 39.9, 40.1])
        else:
            episode.sun_lon[:4] = np.array([-150.0, -50.0, 50.0, 150.0])
            episode.ecl_lat[:4] = np.array([-50.0, -15.0, 20.0, 55.0])
            episode.vg[:4] = np.array([15.0, 30.0, 45.0, 60.0])
        return episode

    clustered = build(True)
    dispersed = build(False)
    clustered_details = episode_score_details(clustered)
    dispersed_details = episode_score_details(dispersed)

    shifted = build(True)
    shifted.sun_lon = shifted.sun_lon + 360.0
    shifted_score = multi_anchor_energy_episode_score(shifted)

    permuted = build(True)
    order = np.arange(32)[::-1]
    for name in ("sun_lon", "ecl_lat", "vg"):
        setattr(permuted, name, np.asarray(getattr(permuted, name))[order])
    permuted_score = multi_anchor_energy_episode_score(permuted)

    single = np.array([5.0, -1.0, -2.0, -3.0])
    single_energy = float(np.sqrt(np.sum(np.sort(np.maximum(single, 0.0))[-4:] ** 2)))

    return {
        "cluster_exceeds_dispersed": clustered_details["score"] > dispersed_details["score"],
        "energy_contains_brown_peak": clustered_details["score"] >= max(0.0, clustered_details["brown_peak"]),
        "single_positive_reduces_to_peak": math.isclose(single_energy, 5.0, abs_tol=1e-12, rel_tol=0.0),
        "longitude_wrap_invariant": math.isclose(clustered_details["score"], shifted_score, abs_tol=1e-10, rel_tol=0.0),
        "permutation_invariant": math.isclose(clustered_details["score"], permuted_score, abs_tol=1e-10, rel_tol=0.0),
        "frozen_brown_geometry": (
            ANGULAR_PROBE_DEG == 4.0
            and SPEED_PROBE_FRACTION == 0.10
            and TRUNCATION_RADIUS == 4.0
            and KERNEL_DIMENSION == 3.0
        ),
        "frozen_top_anchor_count": TOP_ANCHORS == 4,
    }
