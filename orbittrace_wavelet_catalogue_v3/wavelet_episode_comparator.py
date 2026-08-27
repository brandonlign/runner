"""Frozen Brown-family 3D wavelet core for the OrbitTrace episode benchmark.

This is a literature-inspired sparse-episode transfer, not a reproduction of the
full Brown et al. (2010) catalogue survey. It contains no data loading, labels,
benchmark tuning, or OrbitTrace-specific values.
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np

ANGULAR_PROBE_DEG = 4.0
SPEED_PROBE_FRACTION = 0.10
TRUNCATION_RADIUS = 4.0
KERNEL_DIMENSION = 3.0


def _as_finite_vector(values: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or len(array) < 2 or not np.all(np.isfinite(array)):
        raise ValueError(f"invalid {name}")
    return array


def radiant_unit_vectors(
    sun_centered_longitude_deg: Sequence[float] | np.ndarray,
    ecliptic_latitude_deg: Sequence[float] | np.ndarray,
) -> np.ndarray:
    lon = np.radians(_as_finite_vector(sun_centered_longitude_deg, "longitude"))
    lat = np.radians(_as_finite_vector(ecliptic_latitude_deg, "latitude"))
    if lon.shape != lat.shape:
        raise ValueError("longitude and latitude shapes differ")
    vectors = np.column_stack(
        (
            np.cos(lat) * np.cos(lon),
            np.cos(lat) * np.sin(lon),
            np.sin(lat),
        )
    )
    if vectors.shape != (len(lon), 3) or not np.all(np.isfinite(vectors)):
        raise ValueError("invalid radiant vectors")
    return vectors


def pairwise_dimensionless_radius_squared(
    sun_centered_longitude_deg: Sequence[float] | np.ndarray,
    ecliptic_latitude_deg: Sequence[float] | np.ndarray,
    geocentric_speed_km_s: Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Return event-to-test-point squared distances in the frozen wavelet metric.

    Rows are contributing events and columns are test locations. The speed scale
    is ten percent of the test-location speed, matching a fractional probe.
    """
    vectors = radiant_unit_vectors(sun_centered_longitude_deg, ecliptic_latitude_deg)
    speed = _as_finite_vector(geocentric_speed_km_s, "speed")
    if len(speed) != len(vectors) or np.any(speed <= 0.0):
        raise ValueError("invalid or mismatched speeds")

    cosine = np.clip(vectors @ vectors.T, -1.0, 1.0)
    angular = np.arccos(cosine)
    angular_scale = np.radians(ANGULAR_PROBE_DEG)
    angular_term = (angular / angular_scale) ** 2

    test_speed_scale = SPEED_PROBE_FRACTION * speed[None, :]
    speed_term = ((speed[:, None] - speed[None, :]) / test_speed_scale) ** 2
    radius_squared = angular_term + speed_term
    if radius_squared.shape != (len(speed), len(speed)) or not np.all(np.isfinite(radius_squared)):
        raise ValueError("invalid wavelet radius matrix")
    radius_squared = np.maximum(radius_squared, 0.0)
    np.fill_diagonal(radius_squared, 0.0)
    return radius_squared


def mexican_hat_weights(radius_squared: np.ndarray) -> np.ndarray:
    r2 = np.asarray(radius_squared, dtype=np.float64)
    if r2.ndim != 2 or r2.shape[0] != r2.shape[1] or not np.all(np.isfinite(r2)):
        raise ValueError("wavelet radius input must be a finite square matrix")
    weights = (KERNEL_DIMENSION - r2) * np.exp(-0.5 * r2)
    weights = np.where(r2 <= TRUNCATION_RADIUS ** 2, weights, 0.0)
    np.fill_diagonal(weights, 0.0)
    if not np.all(np.isfinite(weights)):
        raise ValueError("non-finite wavelet weights")
    return weights


def wavelet_coefficients_from_arrays(
    sun_centered_longitude_deg: Sequence[float] | np.ndarray,
    ecliptic_latitude_deg: Sequence[float] | np.ndarray,
    geocentric_speed_km_s: Sequence[float] | np.ndarray,
) -> np.ndarray:
    radius_squared = pairwise_dimensionless_radius_squared(
        sun_centered_longitude_deg,
        ecliptic_latitude_deg,
        geocentric_speed_km_s,
    )
    coefficients = mexican_hat_weights(radius_squared).sum(axis=0)
    if coefficients.ndim != 1 or not np.all(np.isfinite(coefficients)):
        raise ValueError("invalid wavelet coefficients")
    return coefficients


def wavelet_episode_score(episode: Any) -> float:
    coefficients = wavelet_coefficients_from_arrays(episode.sun_lon, episode.ecl_lat, episode.vg)
    return float(np.max(coefficients))


def self_test() -> dict[str, bool]:
    background_lon = np.linspace(-175.0, 175.0, 32)
    background_lat = np.linspace(-65.0, 65.0, 32)
    background_speed = np.linspace(12.0, 68.0, 32)

    clustered_lon = background_lon.copy()
    clustered_lat = background_lat.copy()
    clustered_speed = background_speed.copy()
    clustered_lon[:4] = np.array([179.6, -179.8, 179.9, -179.5])
    clustered_lat[:4] = np.array([10.0, 10.2, 9.8, 10.1])
    clustered_speed[:4] = np.array([40.0, 40.2, 39.9, 40.1])

    dispersed_lon = background_lon.copy()
    dispersed_lat = background_lat.copy()
    dispersed_speed = background_speed.copy()
    dispersed_lon[:4] = np.array([-150.0, -50.0, 50.0, 150.0])
    dispersed_lat[:4] = np.array([-50.0, -15.0, 20.0, 55.0])
    dispersed_speed[:4] = np.array([15.0, 30.0, 45.0, 60.0])

    clustered = wavelet_coefficients_from_arrays(clustered_lon, clustered_lat, clustered_speed)
    dispersed = wavelet_coefficients_from_arrays(dispersed_lon, dispersed_lat, dispersed_speed)
    shifted = wavelet_coefficients_from_arrays(clustered_lon + 360.0, clustered_lat, clustered_speed)
    order = np.arange(len(clustered_lon))[::-1]
    permuted = wavelet_coefficients_from_arrays(
        clustered_lon[order], clustered_lat[order], clustered_speed[order]
    )

    return {
        "cluster_exceeds_dispersed": float(np.max(clustered)) > float(np.max(dispersed)),
        "longitude_wrap_invariant": np.allclose(clustered, shifted, atol=1e-12, rtol=0.0),
        "permutation_score_invariant": np.isclose(
            float(np.max(clustered)), float(np.max(permuted)), atol=1e-12, rtol=0.0
        ),
        "leave_one_out_diagonal_zero": np.allclose(
            np.diag(mexican_hat_weights(pairwise_dimensionless_radius_squared(
                clustered_lon, clustered_lat, clustered_speed
            ))),
            0.0,
            atol=0.0,
            rtol=0.0,
        ),
        "frozen_parameters": (
            ANGULAR_PROBE_DEG == 4.0
            and SPEED_PROBE_FRACTION == 0.10
            and TRUNCATION_RADIUS == 4.0
            and KERNEL_DIMENSION == 3.0
        ),
    }
