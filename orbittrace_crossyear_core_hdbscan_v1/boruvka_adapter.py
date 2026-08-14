from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from hdbscan._hdbscan_boruvka import KDTreeBoruvkaAlgorithm
from sklearn.neighbors import KDTree


K_INHERITED = 10


@dataclass(frozen=True)
class CrossYearNeighborTable:
    distances: np.ndarray
    indices: np.ndarray
    core_distances: np.ndarray


def _validate(X: np.ndarray, years: Sequence[int], ids: Sequence[str], k: int) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    X = np.ascontiguousarray(np.asarray(X, dtype=np.float64))
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


def _resolve_one_query(
    tree: KDTree,
    query: np.ndarray,
    opposite_global: np.ndarray,
    ids: tuple[str, ...],
    *,
    k: int,
) -> tuple[np.ndarray, np.ndarray]:
    n_opp = int(opposite_global.shape[0])
    probe_k = min(n_opp, k + 1)
    d, j = tree.query(query.reshape(1, -1), k=probe_k, dualtree=False, breadth_first=True)
    d = np.asarray(d[0], dtype=np.float64)
    j = np.asarray(j[0], dtype=np.int64)

    boundary_tie = probe_k > k and d[k - 1] == d[k]
    if boundary_tie:
        radius = np.nextafter(d[k - 1], np.inf)
        js_obj, ds_obj = tree.query_radius(
            query.reshape(1, -1),
            r=radius,
            return_distance=True,
            sort_results=False,
        )
        local = np.asarray(js_obj[0], dtype=np.int64)
        dist = np.asarray(ds_obj[0], dtype=np.float64)
    else:
        local = j
        dist = d

    rows = [
        (float(dist[pos]), ids[int(opposite_global[int(local[pos])])], int(opposite_global[int(local[pos])]))
        for pos in range(len(local))
    ]
    rows.sort(key=lambda row: (row[0], row[1]))
    if len(rows) < k:
        raise RuntimeError("opposite-year neighbor query returned fewer than k points")
    chosen = rows[:k]
    return (
        np.asarray([row[0] for row in chosen], dtype=np.float64),
        np.asarray([row[2] for row in chosen], dtype=np.int64),
    )


def build_crossyear_neighbor_table(
    X: np.ndarray,
    years: Sequence[int],
    ids: Sequence[str],
    *,
    k: int = K_INHERITED,
    leaf_size: int = 40,
) -> CrossYearNeighborTable:
    X, y, ids_t = _validate(X, years, ids, k)
    n = X.shape[0]
    distances = np.empty((n, k + 1), dtype=np.float64)
    indices = np.empty((n, k + 1), dtype=np.int64)
    distances[:, 0] = 0.0
    indices[:, 0] = np.arange(n, dtype=np.int64)

    year_values = tuple(sorted(int(v) for v in np.unique(y)))
    for yr in year_values:
        src = np.flatnonzero(y == yr)
        opp = np.flatnonzero(y != yr)
        tree = KDTree(X[opp], metric="euclidean", leaf_size=int(leaf_size))

        # A fast batch query gives the common non-boundary-tie case. Exact ID
        # tie resolution is repaired row-by-row only when the kth boundary is tied.
        probe_k = min(len(opp), k + 1)
        d_batch, j_batch = tree.query(X[src], k=probe_k, dualtree=True, breadth_first=True)
        for row_pos, global_i in enumerate(src):
            d = np.asarray(d_batch[row_pos], dtype=np.float64)
            j = np.asarray(j_batch[row_pos], dtype=np.int64)
            boundary_tie = probe_k > k and d[k - 1] == d[k]
            if boundary_tie:
                chosen_d, chosen_i = _resolve_one_query(tree, X[global_i], opp, ids_t, k=k)
            else:
                rows = [
                    (float(d[pos]), ids_t[int(opp[int(j[pos])])], int(opp[int(j[pos])]))
                    for pos in range(len(j))
                ]
                rows.sort(key=lambda row: (row[0], row[1]))
                chosen = rows[:k]
                chosen_d = np.asarray([r[0] for r in chosen], dtype=np.float64)
                chosen_i = np.asarray([r[2] for r in chosen], dtype=np.int64)
            distances[global_i, 1:] = chosen_d
            indices[global_i, 1:] = chosen_i

    core = distances[:, k].copy()
    return CrossYearNeighborTable(distances=distances, indices=indices, core_distances=core)


class _FrozenCrossYearCoreQuery:
    """Minimal tree-like proxy consumed by HDBSCAN's exact Boruvka engine.

    HDBSCAN uses the passed object's `.data` to build its own spatial KDTree,
    and calls `.query()` only to initialize core distances / safe first-round
    edges. We provide self + exact opposite-year kNN rows, while the subsequent
    dual-tree Boruvka traversal remains HDBSCAN's unmodified exact search over
    the pooled GEO6 coordinates.
    """

    def __init__(self, X: np.ndarray, table: CrossYearNeighborTable) -> None:
        self.data = np.ascontiguousarray(np.asarray(X, dtype=np.float64))
        self._distances = np.ascontiguousarray(table.distances, dtype=np.float64)
        self._indices = np.ascontiguousarray(table.indices, dtype=np.int64)

    def query(self, data, k, dualtree=True, breadth_first=True):
        q = np.asarray(data, dtype=np.float64)
        if q.shape != self.data.shape or not np.array_equal(q, self.data):
            raise RuntimeError(
                "cross-year core proxy only permits the exact pooled full-data query; "
                "Boruvka must run with n_jobs=1"
            )
        if int(k) != self._distances.shape[1]:
            raise RuntimeError(f"unexpected core query k={k}")
        return self._distances.copy(), self._indices.copy()


def exact_crossyear_boruvka_mst(
    X: np.ndarray,
    years: Sequence[int],
    ids: Sequence[str],
    *,
    k: int = K_INHERITED,
    leaf_size: int = 40,
) -> tuple[CrossYearNeighborTable, np.ndarray]:
    X, y, ids_t = _validate(X, years, ids, k)
    table = build_crossyear_neighbor_table(X, y, ids_t, k=k, leaf_size=leaf_size)
    proxy = _FrozenCrossYearCoreQuery(X, table)
    algorithm = KDTreeBoruvkaAlgorithm(
        proxy,
        min_samples=int(k),
        metric="euclidean",
        leaf_size=int(leaf_size),
        alpha=1.0,
        approx_min_span_tree=False,
        n_jobs=1,
    )
    mst = np.asarray(algorithm.spanning_tree(), dtype=np.float64)
    if mst.shape != (X.shape[0] - 1, 3):
        raise RuntimeError(f"unexpected Boruvka MST shape {mst.shape}")
    return table, mst
