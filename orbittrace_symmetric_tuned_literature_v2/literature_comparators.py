"""Frozen comparator primitives for the OrbitTrace literature benchmark.

This module contains no benchmark tuning or data-loading side effects. Its public
functions are deterministic and shared by development and independent runs.
"""
from __future__ import annotations

from typing import Any, Iterable, Sequence

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors

SUGAR_MIN_SAMPLES = 5
SUGAR_EPS_PERCENTILE = 23.0
RUD2014_MIN_MEMBERS = 6
SPARSE_ADAPTED_MIN_MEMBERS = 4
RUD2014_DSH_THRESHOLD = 0.05


def wrap_pi(value: np.ndarray | float) -> np.ndarray:
    return (np.asarray(value, dtype=np.float64) + np.pi) % (2.0 * np.pi) - np.pi


def sugar_feature_matrix_from_arrays(
    solar_longitude_deg: Sequence[float] | np.ndarray,
    sun_centered_ecliptic_longitude_deg: Sequence[float] | np.ndarray,
    ecliptic_latitude_deg: Sequence[float] | np.ndarray,
    geocentric_speed_km_s: Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Return Sugar et al.'s published six-dimensional input vector."""
    sol = np.radians(np.asarray(solar_longitude_deg, dtype=np.float64))
    lon = np.radians(np.asarray(sun_centered_ecliptic_longitude_deg, dtype=np.float64))
    lat = np.radians(np.asarray(ecliptic_latitude_deg, dtype=np.float64))
    vg = np.asarray(geocentric_speed_km_s, dtype=np.float64)
    if not (sol.shape == lon.shape == lat.shape == vg.shape):
        raise ValueError("Sugar feature arrays must have identical shapes")
    matrix = np.column_stack(
        (
            np.cos(sol),
            np.sin(sol),
            np.sin(lon) * np.cos(lat),
            np.cos(lon) * np.cos(lat),
            np.sin(lat),
            vg / 72.0,
        )
    )
    if matrix.ndim != 2 or matrix.shape[1] != 6 or not np.all(np.isfinite(matrix)):
        raise ValueError("invalid Sugar feature matrix")
    return matrix


def sugar_feature_matrix_for_episode(episode: Any) -> np.ndarray:
    sol = (float(episode.center_sol) + np.asarray(episode.rel_sol, dtype=np.float64)) % 360.0
    return sugar_feature_matrix_from_arrays(sol, episode.sun_lon, episode.ecl_lat, episode.vg)


def sugar_transferred_epsilon(feature_matrix: np.ndarray) -> tuple[float, np.ndarray]:
    """Apply the published fourth-nearest-neighbour / 23rd-percentile rule.

    sklearn includes each point itself at zero distance, so column four of a
    five-neighbour query is the fourth non-self neighbour.
    """
    features = np.asarray(feature_matrix, dtype=np.float64)
    if features.ndim != 2 or features.shape[1] != 6 or len(features) < 5:
        raise ValueError("Sugar epsilon requires at least five six-dimensional events")
    model = NearestNeighbors(n_neighbors=5, algorithm="auto", n_jobs=-1)
    distances = model.fit(features).kneighbors(features, return_distance=True)[0][:, 4]
    epsilon = float(np.percentile(distances, SUGAR_EPS_PERCENTILE))
    if not np.isfinite(epsilon) or epsilon <= 0.0:
        raise ValueError(f"invalid transferred Sugar epsilon: {epsilon}")
    return epsilon, distances


def largest_dbscan_cluster(feature_matrix: np.ndarray, epsilon: float, min_samples: int) -> int:
    labels = DBSCAN(eps=float(epsilon), min_samples=int(min_samples), metric="euclidean").fit_predict(
        np.asarray(feature_matrix, dtype=np.float64)
    )
    valid = labels[labels >= 0]
    if not len(valid):
        return 0
    return int(np.bincount(valid).max())


def sugar_episode_score(episode: Any, epsilon: float) -> float:
    return float(largest_dbscan_cluster(sugar_feature_matrix_for_episode(episode), epsilon, SUGAR_MIN_SAMPLES))


def pairwise_dsh(
    q_au: Sequence[float] | np.ndarray,
    eccentricity: Sequence[float] | np.ndarray,
    inclination_deg: Sequence[float] | np.ndarray,
    perihelion_argument_deg: Sequence[float] | np.ndarray,
    ascending_node_deg: Sequence[float] | np.ndarray,
) -> np.ndarray:
    """Vectorized Southworth-Hawkins orbital dissimilarity matrix.

    Node differences are wrapped to [-pi, pi], carrying the required sign in
    the perihelion-longitude term. Trigonometric arguments are clipped only for
    floating-point roundoff. D_SH is mathematically symmetric; the final matrix
    is explicitly averaged with its transpose to remove branch-level roundoff.
    """
    q = np.asarray(q_au, dtype=np.float64)
    e = np.asarray(eccentricity, dtype=np.float64)
    inc = np.radians(np.asarray(inclination_deg, dtype=np.float64))
    peri = np.radians(np.asarray(perihelion_argument_deg, dtype=np.float64))
    node = np.radians(np.asarray(ascending_node_deg, dtype=np.float64))
    if not (q.shape == e.shape == inc.shape == peri.shape == node.shape):
        raise ValueError("D_SH arrays must have identical shapes")
    if q.ndim != 1 or len(q) < 2:
        raise ValueError("D_SH requires one-dimensional arrays")
    if not np.all(np.isfinite(np.column_stack((q, e, inc, peri, node)))):
        raise ValueError("non-finite orbital element in D_SH input")

    i1 = inc[:, None]
    i2 = inc[None, :]
    node_delta = wrap_pi(node[None, :] - node[:, None])
    cos_i = np.cos(i1) * np.cos(i2) + np.sin(i1) * np.sin(i2) * np.cos(node_delta)
    mutual_i = np.arccos(np.clip(cos_i, -1.0, 1.0))

    denominator = np.cos(0.5 * mutual_i)
    numerator = np.cos(0.5 * (i1 + i2)) * np.sin(0.5 * node_delta)
    ratio = np.divide(
        numerator,
        denominator,
        out=np.zeros_like(numerator),
        where=np.abs(denominator) > 1e-15,
    )
    peri_delta = wrap_pi(
        peri[None, :] - peri[:, None]
        + 2.0 * np.arcsin(np.clip(ratio, -1.0, 1.0))
    )

    q_delta = q[:, None] - q[None, :]
    e_delta = e[:, None] - e[None, :]
    plane = 2.0 * np.sin(0.5 * mutual_i)
    peri_term = 0.5 * (e[:, None] + e[None, :]) * 2.0 * np.sin(0.5 * peri_delta)
    squared = q_delta * q_delta + e_delta * e_delta + plane * plane + peri_term * peri_term
    distance = np.sqrt(np.maximum(squared, 0.0))
    if not np.all(np.isfinite(distance)):
        raise ValueError("non-finite D_SH matrix")
    distance = 0.5 * (distance + distance.T)
    np.fill_diagonal(distance, 0.0)
    if not np.allclose(distance, distance.T, atol=0.0, rtol=0.0):
        raise ValueError("failed to enforce D_SH symmetry")
    return distance


class _UnionFind:
    def __init__(self, size: int):
        self.parent = np.arange(size, dtype=np.int32)
        self.count = np.ones(size, dtype=np.int32)

    def find(self, value: int) -> int:
        parent = self.parent
        root = int(value)
        while int(parent[root]) != root:
            root = int(parent[root])
        while int(parent[value]) != value:
            nxt = int(parent[value])
            parent[value] = root
            value = nxt
        return root

    def union(self, left: int, right: int) -> int:
        a = self.find(left)
        b = self.find(right)
        if a == b:
            return int(self.count[a])
        if self.count[a] < self.count[b] or (self.count[a] == self.count[b] and a > b):
            a, b = b, a
        self.parent[b] = a
        self.count[a] += self.count[b]
        return int(self.count[a])


def single_link_birth_threshold(distance: np.ndarray, minimum_members: int) -> float:
    """Return the first single-link distance producing the requested component size."""
    matrix = np.asarray(distance, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("single-link input must be square")
    n = matrix.shape[0]
    target = int(minimum_members)
    if target < 2 or target > n:
        raise ValueError("invalid single-link target")
    upper_i, upper_j = np.triu_indices(n, k=1)
    values = matrix[upper_i, upper_j]
    order = np.lexsort((upper_j, upper_i, values))
    forest = _UnionFind(n)
    for index in order:
        size = forest.union(int(upper_i[index]), int(upper_j[index]))
        if size >= target:
            threshold = float(values[index])
            if not np.isfinite(threshold):
                raise ValueError("non-finite single-link threshold")
            return threshold
    raise RuntimeError("single-link target was never reached")


def dsh_episode_scores(episode: Any) -> dict[str, float]:
    distance = pairwise_dsh(
        episode.orbit_q,
        episode.orbit_e,
        episode.orbit_incl,
        episode.orbit_peri,
        episode.orbit_node,
    )
    threshold6 = single_link_birth_threshold(distance, RUD2014_MIN_MEMBERS)
    threshold4 = single_link_birth_threshold(distance, SPARSE_ADAPTED_MIN_MEMBERS)
    return {
        "rudawska2014_dsh6": -threshold6,
        "dsh4_sparse_adaptation": -threshold4,
    }


def conservative_rank_pvalue(score: float, calibration_scores: Sequence[float] | np.ndarray) -> float:
    calibration = np.asarray(calibration_scores, dtype=np.float64)
    if not len(calibration):
        raise ValueError("empty calibration panel")
    return float((1 + np.sum(calibration >= float(score))) / (len(calibration) + 1))


def rate(values: Iterable[float], alpha: float) -> float:
    array = np.asarray(list(values), dtype=np.float64)
    return float(np.mean(array <= float(alpha))) if len(array) else float("nan")
