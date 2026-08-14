from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from hdbscan._hdbscan_linkage import label
from hdbscan._hdbscan_tree import condense_tree


K_INHERITED = 10
MIN_CLUSTER_SIZE_INHERITED = 10


@dataclass(frozen=True)
class DenseReferenceResult:
    core_distances: np.ndarray
    mutual_reachability: np.ndarray
    mst_edges: np.ndarray
    single_linkage_tree: np.ndarray
    condensed_tree: np.ndarray


def _validate(X: np.ndarray, years: Sequence[int], ids: Sequence[str], k: int) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(years, dtype=np.int64)
    ids_t = tuple(str(v) for v in ids)
    if X.ndim != 2 or X.shape[0] == 0:
        raise ValueError("X must be a non-empty 2D array")
    if not np.all(np.isfinite(X)):
        raise ValueError("X contains non-finite values")
    if y.shape != (X.shape[0],):
        raise ValueError("years must align with rows")
    if len(ids_t) != X.shape[0] or len(set(ids_t)) != len(ids_t):
        raise ValueError("ids must be unique and align with rows")
    year_values = tuple(sorted(int(v) for v in np.unique(y)))
    if len(year_values) != 2:
        raise ValueError(f"exactly two years required, got {year_values}")
    if k <= 0:
        raise ValueError("k must be positive")
    for yr in year_values:
        if int(np.sum(y == yr)) < k:
            raise ValueError(f"year {yr} has fewer than k={k} points")
    return X, y, ids_t


def pairwise_euclidean(X: np.ndarray) -> np.ndarray:
    diff = X[:, None, :] - X[None, :, :]
    d2 = np.einsum("ijk,ijk->ij", diff, diff)
    np.maximum(d2, 0.0, out=d2)
    return np.sqrt(d2, dtype=np.float64)


def opposite_year_core_distances(
    X: np.ndarray,
    years: Sequence[int],
    ids: Sequence[str],
    *,
    k: int = K_INHERITED,
) -> np.ndarray:
    X, y, ids_t = _validate(X, years, ids, k)
    D = pairwise_euclidean(X)
    out = np.empty(X.shape[0], dtype=np.float64)
    for i in range(X.shape[0]):
        js = np.flatnonzero(y != y[i])
        ordered = sorted((float(D[i, j]), ids_t[j], int(j)) for j in js)
        out[i] = ordered[k - 1][0]
    return out


def crossyear_mutual_reachability(
    X: np.ndarray,
    years: Sequence[int],
    ids: Sequence[str],
    *,
    k: int = K_INHERITED,
) -> tuple[np.ndarray, np.ndarray]:
    X, y, ids_t = _validate(X, years, ids, k)
    D = pairwise_euclidean(X)
    core = opposite_year_core_distances(X, y, ids_t, k=k)
    mrd = np.maximum(D, core[:, None])
    mrd = np.maximum(mrd, core[None, :])
    np.fill_diagonal(mrd, 0.0)
    return core, mrd


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def deterministic_dense_mst(mrd: np.ndarray, ids: Sequence[str]) -> np.ndarray:
    mrd = np.asarray(mrd, dtype=np.float64)
    ids_t = tuple(str(v) for v in ids)
    n = mrd.shape[0]
    if mrd.shape != (n, n) or n == 0:
        raise ValueError("mrd must be non-empty square matrix")
    if len(ids_t) != n or len(set(ids_t)) != n:
        raise ValueError("ids must be unique and align with mrd")
    if not np.allclose(mrd, mrd.T, rtol=0.0, atol=0.0):
        raise ValueError("mrd must be exactly symmetric")
    if np.any(mrd < 0) or not np.all(np.isfinite(mrd)):
        raise ValueError("mrd must be finite and nonnegative")

    edges: list[tuple[float, str, str, int, int]] = []
    for i in range(n):
        for j in range(i + 1, n):
            lo_id, hi_id = sorted((ids_t[i], ids_t[j]))
            edges.append((float(mrd[i, j]), lo_id, hi_id, i, j))
    edges.sort(key=lambda row: (row[0], row[1], row[2]))

    uf = _UnionFind(n)
    chosen: list[tuple[int, int, float]] = []
    for w, _lo, _hi, i, j in edges:
        if uf.union(i, j):
            chosen.append((i, j, w))
            if len(chosen) == n - 1:
                break
    if len(chosen) != n - 1:
        raise RuntimeError("failed to construct spanning tree")
    return np.asarray(chosen, dtype=np.float64)


def dense_reference(
    X: np.ndarray,
    years: Sequence[int],
    ids: Sequence[str],
    *,
    k: int = K_INHERITED,
    min_cluster_size: int = MIN_CLUSTER_SIZE_INHERITED,
) -> DenseReferenceResult:
    X, y, ids_t = _validate(X, years, ids, k)
    core, mrd = crossyear_mutual_reachability(X, y, ids_t, k=k)
    mst = deterministic_dense_mst(mrd, ids_t)
    # HDBSCAN's linkage builder consumes an MST edge list sorted by weight.
    mst_for_linkage = mst[np.lexsort((mst[:, 1], mst[:, 0], mst[:, 2]))]
    single = label(mst_for_linkage)
    condensed = condense_tree(single, int(min_cluster_size))
    return DenseReferenceResult(
        core_distances=core,
        mutual_reachability=mrd,
        mst_edges=mst,
        single_linkage_tree=np.asarray(single),
        condensed_tree=np.asarray(condensed),
    )
