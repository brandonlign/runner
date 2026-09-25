"""OrbitTrace multiscale consensus contrast, version 2.

A target-free sparse-stream episode statistic. Real stream evidence is required to
persist across adjacent physical scales and across several observed-event anchors.
No labels, OrbitTrace values, or predecessor result values enter the score.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np

METHOD_ID = "orbittrace_multiscale_consensus_v2"
SCALE_BANK = (
    (2.0, 0.050),
    (3.0, 0.075),
    (4.0, 0.100),
    (6.0, 0.150),
)
ADJACENT_SCALE_PAIRS = ((0, 1), (1, 2), (2, 3))
TRUNCATION_RADIUS = 4.0
KERNEL_DIMENSION = 3.0
TOP_ANCHORS = 4
ROBUST_SCALE_CONSTANT = 1.4826
NUMERIC_FLOOR = 1e-10


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


def _radius_squared(
    lon_deg: Sequence[float] | np.ndarray,
    lat_deg: Sequence[float] | np.ndarray,
    speed_km_s: Sequence[float] | np.ndarray,
    angular_scale_deg: float,
    speed_scale_fraction: float,
) -> np.ndarray:
    lon = _finite_vector(lon_deg, "longitude")
    lat = _finite_vector(lat_deg, "latitude")
    speed = _finite_vector(speed_km_s, "speed")
    if not (len(lon) == len(lat) == len(speed)) or np.any(speed <= 0.0):
        raise ValueError("shape mismatch or invalid speed")

    vectors = _radiant_vectors(lon, lat)
    cosine = np.clip(vectors @ vectors.T, -1.0, 1.0)
    angular = np.arccos(cosine)
    angular_term = (angular / math.radians(float(angular_scale_deg))) ** 2

    # Fractional/log-speed separation is symmetric between the two events.
    delta_log_speed = np.log(speed)[:, None] - np.log(speed)[None, :]
    speed_term = (delta_log_speed / float(speed_scale_fraction)) ** 2

    r2 = np.maximum(angular_term + speed_term, 0.0)
    np.fill_diagonal(r2, 0.0)
    if r2.shape != (len(speed), len(speed)) or not np.all(np.isfinite(r2)):
        raise ValueError("invalid radius matrix")
    return r2


def _mexican_hat_coefficients(r2: np.ndarray) -> np.ndarray:
    radius_squared = np.asarray(r2, dtype=np.float64)
    if radius_squared.ndim != 2 or radius_squared.shape[0] != radius_squared.shape[1]:
        raise ValueError("radius matrix must be square")
    weights = (KERNEL_DIMENSION - radius_squared) * np.exp(-0.5 * radius_squared)
    weights = np.where(radius_squared <= TRUNCATION_RADIUS ** 2, weights, 0.0)
    np.fill_diagonal(weights, 0.0)
    coefficients = weights.sum(axis=0)
    if coefficients.ndim != 1 or not np.all(np.isfinite(coefficients)):
        raise ValueError("invalid coefficients")
    return coefficients


def _robust_z(values: np.ndarray) -> np.ndarray:
    x = np.asarray(values, dtype=np.float64)
    if x.ndim != 1 or len(x) < 4 or not np.all(np.isfinite(x)):
        raise ValueError("invalid robust-normalization input")
    center = float(np.median(x))
    mad = float(np.median(np.abs(x - center)))
    scale = ROBUST_SCALE_CONSTANT * mad
    if not math.isfinite(scale) or scale <= NUMERIC_FLOOR:
        scale = float(np.std(x, ddof=1)) if len(x) > 1 else 0.0
    if not math.isfinite(scale) or scale <= NUMERIC_FLOOR:
        scale = 1.0
    z = (x - center) / scale
    if not np.all(np.isfinite(z)):
        raise ValueError("non-finite robust z scores")
    return z


def episode_score_details(episode: Any) -> dict[str, Any]:
    lon = _finite_vector(episode.sun_lon, "sun_lon")
    lat = _finite_vector(episode.ecl_lat, "ecl_lat")
    speed = _finite_vector(episode.vg, "vg")
    if not (len(lon) == len(lat) == len(speed)):
        raise ValueError("episode shape mismatch")

    z_by_scale: list[np.ndarray] = []
    for angular_scale_deg, speed_scale_fraction in SCALE_BANK:
        r2 = _radius_squared(lon, lat, speed, angular_scale_deg, speed_scale_fraction)
        z_by_scale.append(_robust_z(_mexican_hat_coefficients(r2)))
    z = np.vstack(z_by_scale)

    pair_contrasts = np.vstack([
        (z[left] + z[right]) / math.sqrt(2.0)
        for left, right in ADJACENT_SCALE_PAIRS
    ])
    anchor_evidence = np.max(pair_contrasts, axis=0)
    top_count = min(TOP_ANCHORS, len(anchor_evidence))
    top_indices = np.argpartition(anchor_evidence, -top_count)[-top_count:]
    top_values = np.sort(anchor_evidence[top_indices])[::-1]
    score = float(np.mean(top_values))
    if not math.isfinite(score):
        raise ValueError("non-finite episode score")
    return {
        "score": score,
        "top_anchor_indices": [int(index) for index in top_indices[np.argsort(anchor_evidence[top_indices])[::-1]]],
        "top_anchor_values": [float(value) for value in top_values],
    }


def multiscale_consensus_episode_score(episode: Any) -> float:
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
    clustered_score = multiscale_consensus_episode_score(clustered)
    dispersed_score = multiscale_consensus_episode_score(dispersed)

    shifted = build(True)
    shifted.sun_lon = shifted.sun_lon + 360.0
    shifted_score = multiscale_consensus_episode_score(shifted)

    permuted = build(True)
    order = np.arange(32)[::-1]
    for name in ("sun_lon", "ecl_lat", "vg"):
        setattr(permuted, name, np.asarray(getattr(permuted, name))[order])
    permuted_score = multiscale_consensus_episode_score(permuted)

    return {
        "cluster_exceeds_dispersed": clustered_score > dispersed_score,
        "longitude_wrap_invariant": math.isclose(clustered_score, shifted_score, abs_tol=1e-10, rel_tol=0.0),
        "permutation_invariant": math.isclose(clustered_score, permuted_score, abs_tol=1e-10, rel_tol=0.0),
        "finite_score": math.isfinite(clustered_score),
        "frozen_scale_bank": SCALE_BANK == ((2.0, 0.050), (3.0, 0.075), (4.0, 0.100), (6.0, 0.150)),
        "frozen_pairing": ADJACENT_SCALE_PAIRS == ((0, 1), (1, 2), (2, 3)),
        "frozen_top_anchor_count": TOP_ANCHORS == 4,
        "frozen_kernel": TRUNCATION_RADIUS == 4.0 and KERNEL_DIMENSION == 3.0,
    }
