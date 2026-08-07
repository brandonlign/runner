"""OrbitTrace adaptive local-likelihood episode core, version 1.

This is a new OrbitTrace-developed method. It is intentionally isolated from all
frozen predecessor implementations. The score is label-free and target-free.

For each observed event and each preregistered angular/speed scale, the method:
1. forms an uncertainty-broadened radiant/log-speed distance;
2. estimates local background from an outer shell;
3. computes a one-sided Poisson count likelihood for a compact core excess; and
4. adds positive within-core concentration evidence relative to a uniform core.

The episode score is the maximum local score across anchors and the fixed scale
bank. Empirical Mondrian calibration is applied by the external frozen benchmark
runner, so the scale maximization is calibrated as part of the statistic.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np

METHOD_ID = "orbittrace_adaptive_local_likelihood_v1"
SCALE_BANK = (
    (2.0, 0.050),
    (3.0, 0.075),
    (4.0, 0.100),
    (6.0, 0.150),
)
CORE_RADIUS = math.sqrt(3.0)
OUTER_RADIUS = 4.0
MIN_CORE_MEMBERS = 3
BACKGROUND_PSEUDOCOUNT = 0.5
ANGULAR_UNCERTAINTY_FLOOR_DEG = 0.05
SPEED_UNCERTAINTY_FLOOR_KM_S = 0.05


def _finite_vector(values: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or len(array) < 4 or not np.all(np.isfinite(array)):
        raise ValueError(f"invalid {name}")
    return array


def _radiant_vectors(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
    lon = np.radians(lon_deg)
    lat = np.radians(lat_deg)
    vectors = np.column_stack(
        (
            np.cos(lat) * np.cos(lon),
            np.cos(lat) * np.sin(lon),
            np.sin(lat),
        )
    )
    if not np.all(np.isfinite(vectors)):
        raise ValueError("invalid radiant vectors")
    return vectors


def _angular_sigma_deg(episode: Any) -> np.ndarray:
    ra_sd = _finite_vector(episode.ra_sd, "ra_sd")
    dec_sd = _finite_vector(episode.dec_sd, "dec_sd")
    dec = _finite_vector(episode.dec, "dec")
    if not (len(ra_sd) == len(dec_sd) == len(dec)):
        raise ValueError("angular-uncertainty shape mismatch")
    projected_ra = ra_sd * np.cos(np.radians(dec))
    sigma = np.sqrt(projected_ra * projected_ra + dec_sd * dec_sd)
    return np.maximum(sigma, ANGULAR_UNCERTAINTY_FLOOR_DEG)


def _distance_matrix(episode: Any, angular_scale_deg: float, speed_scale_fraction: float) -> np.ndarray:
    lon = _finite_vector(episode.sun_lon, "sun_lon")
    lat = _finite_vector(episode.ecl_lat, "ecl_lat")
    speed = _finite_vector(episode.vg, "vg")
    speed_sd = _finite_vector(episode.vg_sd, "vg_sd")
    if not (len(lon) == len(lat) == len(speed) == len(speed_sd)):
        raise ValueError("episode shape mismatch")
    if np.any(speed <= 0.0) or np.any(speed_sd < 0.0):
        raise ValueError("invalid speed or speed uncertainty")

    vectors = _radiant_vectors(lon, lat)
    cosine = np.clip(vectors @ vectors.T, -1.0, 1.0)
    angular = np.arccos(cosine)

    angular_sigma = np.radians(_angular_sigma_deg(episode))
    angular_scale = math.radians(float(angular_scale_deg))
    angular_variance = (
        angular_scale * angular_scale
        + angular_sigma[:, None] ** 2
        + angular_sigma[None, :] ** 2
    )

    log_speed = np.log(speed)
    delta_log_speed = log_speed[:, None] - log_speed[None, :]
    fractional_sigma = np.maximum(speed_sd, SPEED_UNCERTAINTY_FLOOR_KM_S) / speed
    speed_variance = (
        float(speed_scale_fraction) ** 2
        + fractional_sigma[:, None] ** 2
        + fractional_sigma[None, :] ** 2
    )

    radius_squared = angular * angular / angular_variance + delta_log_speed * delta_log_speed / speed_variance
    radius_squared = np.maximum(radius_squared, 0.0)
    np.fill_diagonal(radius_squared, np.inf)
    if radius_squared.shape != (len(speed), len(speed)) or np.any(np.isnan(radius_squared)):
        raise ValueError("invalid adaptive distance matrix")
    return radius_squared


def _gaussian_ball_probability(radius: float) -> float:
    r = float(radius)
    return math.erf(r / math.sqrt(2.0)) - math.sqrt(2.0 / math.pi) * r * math.exp(-0.5 * r * r)


def _anchor_score(radius_squared: np.ndarray, anchor: int) -> float:
    r2 = radius_squared[:, anchor]
    core2 = CORE_RADIUS * CORE_RADIUS
    outer2 = OUTER_RADIUS * OUTER_RADIUS
    core_mask = r2 < core2
    shell_mask = (r2 >= core2) & (r2 <= outer2)

    k = int(np.count_nonzero(core_mask))
    if k < MIN_CORE_MEMBERS:
        return 0.0
    shell = int(np.count_nonzero(shell_mask))

    core_volume = CORE_RADIUS ** 3
    shell_volume = OUTER_RADIUS ** 3 - CORE_RADIUS ** 3
    expected_core = (shell + BACKGROUND_PSEUDOCOUNT) * core_volume / shell_volume
    expected_core = max(expected_core, 1e-12)

    if k > expected_core:
        count_llr = k * math.log(k / expected_core) - k + expected_core
    else:
        count_llr = 0.0

    gaussian_mass = _gaussian_ball_probability(CORE_RADIUS)
    uniform_core_volume = (4.0 / 3.0) * math.pi * CORE_RADIUS ** 3
    log_ratio_constant = (
        math.log(uniform_core_volume)
        - 1.5 * math.log(2.0 * math.pi)
        - math.log(gaussian_mass)
    )
    shape_llr = float(np.sum(log_ratio_constant - 0.5 * r2[core_mask]))
    return float(max(0.0, count_llr + max(0.0, shape_llr)))


def episode_score_details(episode: Any) -> dict[str, Any]:
    best_score = 0.0
    best_anchor = -1
    best_scale = None
    for angular_scale_deg, speed_scale_fraction in SCALE_BANK:
        r2 = _distance_matrix(episode, angular_scale_deg, speed_scale_fraction)
        for anchor in range(r2.shape[1]):
            score = _anchor_score(r2, anchor)
            if score > best_score:
                best_score = score
                best_anchor = int(anchor)
                best_scale = (float(angular_scale_deg), float(speed_scale_fraction))
    return {
        "score": float(best_score),
        "anchor": best_anchor,
        "scale": best_scale,
    }


def adaptive_likelihood_episode_score(episode: Any) -> float:
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
        episode.dec = episode.ecl_lat.copy()
        episode.ra_sd = np.full(32, 0.15)
        episode.dec_sd = np.full(32, 0.15)
        episode.vg_sd = np.full(32, 0.20)
        return episode

    clustered = build(True)
    dispersed = build(False)
    clustered_score = adaptive_likelihood_episode_score(clustered)
    dispersed_score = adaptive_likelihood_episode_score(dispersed)

    shifted = build(True)
    shifted.sun_lon = shifted.sun_lon + 360.0
    shifted_score = adaptive_likelihood_episode_score(shifted)

    permuted = build(True)
    order = np.arange(32)[::-1]
    for name in ("sun_lon", "ecl_lat", "vg", "dec", "ra_sd", "dec_sd", "vg_sd"):
        setattr(permuted, name, np.asarray(getattr(permuted, name))[order])
    permuted_score = adaptive_likelihood_episode_score(permuted)

    return {
        "cluster_exceeds_dispersed": clustered_score > dispersed_score,
        "longitude_wrap_invariant": math.isclose(clustered_score, shifted_score, abs_tol=1e-10, rel_tol=0.0),
        "permutation_invariant": math.isclose(clustered_score, permuted_score, abs_tol=1e-10, rel_tol=0.0),
        "finite_nonnegative": math.isfinite(clustered_score) and clustered_score >= 0.0,
        "frozen_scale_bank": SCALE_BANK == ((2.0, 0.050), (3.0, 0.075), (4.0, 0.100), (6.0, 0.150)),
        "frozen_geometry": (
            math.isclose(CORE_RADIUS, math.sqrt(3.0))
            and OUTER_RADIUS == 4.0
            and MIN_CORE_MEMBERS == 3
            and BACKGROUND_PSEUDOCOUNT == 0.5
        ),
    }
