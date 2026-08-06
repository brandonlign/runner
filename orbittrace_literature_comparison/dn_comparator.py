"""Valsecchi-Jopek-Froeschle D_N comparator primitives.

Implements the published geocentric-variable distance with w1=w2=w3=1.
The benchmark uses the paper's single-neighbour linkage but replaces the
paper's sample-specific chance threshold with the benchmark's identical
empirical negative calibration. This module has no data-loading side effects.
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from literature_comparators import single_link_birth_threshold

EARTH_SPEED_KM_S = 29.7
OBLIQUITY_DEG = 23.4392911
DN_WEIGHTS = (1.0, 1.0, 1.0)
DN_PARITY_MEMBERS = 6
DN_SPARSE_MEMBERS = 4


def geocentric_variables(
    right_ascension_deg: Sequence[float] | np.ndarray,
    declination_deg: Sequence[float] | np.ndarray,
    geocentric_speed_km_s: Sequence[float] | np.ndarray,
    solar_longitude_deg: Sequence[float] | np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return published U, cos(theta), phi and encounter longitude variables.

    The Cartesian transformation follows Valsecchi et al. (1999), as written
    explicitly by Moorhead et al. (2016): the radiant direction is negated to
    obtain the incoming geocentric velocity vector, rotated from equatorial to
    ecliptic coordinates, then into the Earth-centred frame whose y-axis is the
    direction of Earth's motion. ``phi`` uses atan2(ux, uz) to enforce the
    correct quadrant. A constant 180-degree offset in encounter longitude would
    cancel pairwise and therefore does not affect D_N.
    """
    ra = np.radians(np.asarray(right_ascension_deg, dtype=np.float64))
    dec = np.radians(np.asarray(declination_deg, dtype=np.float64))
    vg = np.asarray(geocentric_speed_km_s, dtype=np.float64)
    encounter = np.radians(np.asarray(solar_longitude_deg, dtype=np.float64))
    if not (ra.shape == dec.shape == vg.shape == encounter.shape):
        raise ValueError("D_N observable arrays must have identical shapes")
    if ra.ndim != 1 or len(ra) < 2:
        raise ValueError("D_N requires one-dimensional arrays with at least two events")
    matrix = np.column_stack((ra, dec, vg, encounter))
    if not np.all(np.isfinite(matrix)) or np.any(vg <= 0.0):
        raise ValueError("invalid D_N observable input")

    cos_dec = np.cos(dec)
    x_eq = -cos_dec * np.cos(ra)
    y_eq = -cos_dec * np.sin(ra)
    z_eq = -np.sin(dec)

    eps = np.radians(OBLIQUITY_DEG)
    x_ecl = x_eq
    y_ecl = np.cos(eps) * y_eq + np.sin(eps) * z_eq
    z_ecl = -np.sin(eps) * y_eq + np.cos(eps) * z_eq

    cos_lam = np.cos(encounter)
    sin_lam = np.sin(encounter)
    unit_x = cos_lam * x_ecl + sin_lam * y_ecl
    unit_y = -sin_lam * x_ecl + cos_lam * y_ecl
    unit_z = z_ecl

    norm = np.sqrt(unit_x * unit_x + unit_y * unit_y + unit_z * unit_z)
    if not np.allclose(norm, 1.0, atol=2e-14, rtol=2e-14):
        raise ValueError("D_N direction transform lost unit norm")
    u = vg / EARTH_SPEED_KM_S
    cos_theta = np.clip(unit_y / norm, -1.0, 1.0)
    phi = np.arctan2(unit_x, unit_z)
    return u, cos_theta, phi, encounter


def pairwise_dn_from_variables(
    u: Sequence[float] | np.ndarray,
    cos_theta: Sequence[float] | np.ndarray,
    phi_rad: Sequence[float] | np.ndarray,
    encounter_longitude_rad: Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Return the published pairwise D_N matrix with all weights equal to one."""
    u = np.asarray(u, dtype=np.float64)
    ctheta = np.asarray(cos_theta, dtype=np.float64)
    phi = np.asarray(phi_rad, dtype=np.float64)
    encounter = np.asarray(encounter_longitude_rad, dtype=np.float64)
    if not (u.shape == ctheta.shape == phi.shape == encounter.shape):
        raise ValueError("D_N variable arrays must have identical shapes")
    if u.ndim != 1 or len(u) < 2:
        raise ValueError("D_N requires one-dimensional variables")
    if not np.all(np.isfinite(np.column_stack((u, ctheta, phi, encounter)))):
        raise ValueError("non-finite D_N variable")

    du = u[None, :] - u[:, None]
    dtheta = ctheta[None, :] - ctheta[:, None]
    dphi = phi[None, :] - phi[:, None]
    dlam = encounter[None, :] - encounter[:, None]

    dphi_i = 2.0 * np.sin(0.5 * dphi)
    dphi_ii = 2.0 * np.sin(0.5 * (np.pi + dphi))
    dlam_i = 2.0 * np.sin(0.5 * dlam)
    dlam_ii = 2.0 * np.sin(0.5 * (np.pi + dlam))
    w1, w2, w3 = DN_WEIGHTS
    angular = np.minimum(
        w2 * dphi_i * dphi_i + w3 * dlam_i * dlam_i,
        w2 * dphi_ii * dphi_ii + w3 * dlam_ii * dlam_ii,
    )
    squared = du * du + w1 * dtheta * dtheta + angular
    distance = np.sqrt(np.maximum(squared, 0.0))
    if not np.all(np.isfinite(distance)):
        raise ValueError("non-finite D_N matrix")
    distance = 0.5 * (distance + distance.T)
    np.fill_diagonal(distance, 0.0)
    if not np.allclose(distance, distance.T, atol=0.0, rtol=0.0):
        raise ValueError("failed to enforce D_N symmetry")
    return distance


def pairwise_dn(
    right_ascension_deg: Sequence[float] | np.ndarray,
    declination_deg: Sequence[float] | np.ndarray,
    geocentric_speed_km_s: Sequence[float] | np.ndarray,
    solar_longitude_deg: Sequence[float] | np.ndarray,
) -> np.ndarray:
    return pairwise_dn_from_variables(
        *geocentric_variables(
            right_ascension_deg,
            declination_deg,
            geocentric_speed_km_s,
            solar_longitude_deg,
        )
    )


def dn_episode_scores(episode: Any) -> dict[str, float]:
    solar_longitude = (
        float(episode.center_sol) + np.asarray(episode.rel_sol, dtype=np.float64)
    ) % 360.0
    distance = pairwise_dn(episode.ra, episode.dec, episode.vg, solar_longitude)
    return {
        "valsecchi1999_dn6": -single_link_birth_threshold(distance, DN_PARITY_MEMBERS),
        "dn4_sparse_transfer": -single_link_birth_threshold(distance, DN_SPARSE_MEMBERS),
    }


def self_test() -> dict[str, bool]:
    ra = np.array([12.0, 47.0, 130.0, 278.0, 315.0, 91.0])
    dec = np.array([-12.0, 22.0, 5.0, -41.0, 63.0, 0.5])
    vg = np.array([31.0, 44.0, 18.0, 57.0, 29.0, 36.0])
    sol = np.array([15.0, 62.0, 121.0, 188.0, 244.0, 330.0])
    variables = geocentric_variables(ra, dec, vg, sol)
    distance = pairwise_dn_from_variables(*variables)

    u = np.array([1.2, 1.2])
    ctheta = np.array([0.3, 0.3])
    phi = np.array([0.7, 0.7 + np.pi])
    encounter = np.array([1.1, 1.1 + np.pi])
    twin = pairwise_dn_from_variables(u, ctheta, phi, encounter)

    identical = pairwise_dn_from_variables(
        np.array([1.0, 1.0]), np.array([0.2, 0.2]),
        np.array([-0.4, -0.4]), np.array([2.1, 2.1])
    )
    return {
        "shape": distance.shape == (6, 6),
        "symmetric": bool(np.allclose(distance, distance.T, atol=0.0, rtol=0.0)),
        "zero_diagonal": bool(np.all(np.diag(distance) == 0.0)),
        "positive_off_diagonal": bool(np.all(distance[np.triu_indices(6, 1)] > 0.0)),
        "identical_zero": bool(np.allclose(identical, 0.0, atol=1e-14)),
        "twin_node_zero": bool(np.allclose(twin, 0.0, atol=1e-14)),
    }
