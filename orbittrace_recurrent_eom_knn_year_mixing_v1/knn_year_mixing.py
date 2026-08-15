from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree


@dataclass(frozen=True)
class KNNMixingStat:
    member_count: int
    year_counts: tuple[int, int]
    k: int
    directed_edges: int
    cross_year_edges: int
    expected_cross_year_edges: float
    mixing_enrichment: float


def candidate_knn_mixing(
    X: np.ndarray,
    years: np.ndarray,
    *,
    k_base: int = 10,
) -> KNNMixingStat:
    """Return fixed-count cross-year mixing on a directed within-candidate kNN graph.

    The scientific runner fixes k_base=10. This argument exists only so the
    zero-truth synthetic audit can exercise the same implementation on small
    fixtures. Input row order is treated as authoritative for deterministic
    nearest-neighbor tie handling.
    """
    arr = np.asarray(X, dtype=np.float64)
    yrs = np.asarray(years, dtype=np.int64)
    if arr.ndim != 2 or arr.shape[0] < 2:
        raise ValueError(f"X must be a 2D array with at least two rows, got {arr.shape}")
    if yrs.ndim != 1 or yrs.shape[0] != arr.shape[0]:
        raise ValueError("years must be one-dimensional and aligned with X")
    if not np.all(np.isfinite(arr)):
        raise ValueError("X contains non-finite values")
    if int(k_base) != k_base or int(k_base) <= 0:
        raise ValueError(f"k_base must be a positive integer, got {k_base}")

    year_values = tuple(sorted(int(y) for y in np.unique(yrs)))
    if len(year_values) > 2:
        raise ValueError(f"at most two observing years are allowed, got {year_values}")

    n = int(arr.shape[0])
    k = min(int(k_base), n - 1)
    tree = cKDTree(arr)
    _dist, raw_idx = tree.query(arr, k=k + 1, workers=1)
    idx = np.asarray(raw_idx, dtype=np.int64)
    if idx.ndim == 1:
        idx = idx.reshape(n, -1)
    if idx.shape[0] != n:
        raise RuntimeError(f"unexpected cKDTree query shape: {idx.shape}")

    neighbors = np.empty((n, k), dtype=np.int64)
    for i in range(n):
        chosen: list[int] = []
        for j in idx[i].tolist():
            jj = int(j)
            if jj == i:
                continue
            if not 0 <= jj < n:
                raise RuntimeError(f"neighbor index outside candidate: {jj} for n={n}")
            chosen.append(jj)
            if len(chosen) == k:
                break
        if len(chosen) != k:
            raise RuntimeError(f"failed to obtain {k} non-self neighbors for row {i}: {chosen}")
        neighbors[i] = np.asarray(chosen, dtype=np.int64)

    m = int(n * k)
    if m != int(neighbors.size):
        raise RuntimeError("directed edge count changed")
    rows = np.repeat(np.arange(n, dtype=np.int64), k)
    cols = neighbors.reshape(-1)
    if np.any(rows == cols):
        raise RuntimeError("self edge survived kNN construction")
    if np.any(cols < 0) or np.any(cols >= n):
        raise RuntimeError("kNN endpoint escaped candidate")

    x = int(np.sum(yrs[rows] != yrs[cols]))
    counts = tuple(int(np.sum(yrs == y)) for y in year_values)
    if len(counts) == 1:
        n1, n2 = counts[0], 0
    elif len(counts) == 2:
        n1, n2 = counts
    else:
        raise RuntimeError("candidate has no observing-year labels")
    if n1 + n2 != n:
        raise RuntimeError(f"year counts do not sum to candidate size: {n1}+{n2}!={n}")

    if n1 == 0 or n2 == 0:
        mu = 0.0
        enrichment = 0.0
    else:
        q = (2.0 * float(n1) * float(n2)) / (float(n) * float(n - 1))
        mu = float(m) * q
        if not np.isfinite(mu) or mu <= 0.0:
            raise RuntimeError(f"invalid fixed-count expectation: {mu}")
        enrichment = float(x) / mu

    if not np.isfinite(enrichment) or enrichment < 0.0:
        raise RuntimeError(f"invalid mixing enrichment: {enrichment}")
    if not 0 <= x <= m:
        raise RuntimeError(f"invalid cross-year edge count: {x}/{m}")

    return KNNMixingStat(
        member_count=n,
        year_counts=(n1, n2),
        k=k,
        directed_edges=m,
        cross_year_edges=x,
        expected_cross_year_edges=float(mu),
        mixing_enrichment=float(enrichment),
    )


def mixed_score(recurrent_stability: float, mixing_enrichment: float) -> float:
    score = float(recurrent_stability) * float(mixing_enrichment)
    if not np.isfinite(score) or score < 0.0:
        raise ValueError(f"invalid recurrent/kNN mixing score: {score}")
    return score
