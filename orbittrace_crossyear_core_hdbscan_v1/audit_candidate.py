from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
from hdbscan._hdbscan_linkage import label
from hdbscan._hdbscan_tree import condense_tree


K_INHERITED = 10
MIN_CLUSTER_SIZE_INHERITED = 10


@dataclass(frozen=True)
class AuditCandidateResult:
    core_distances: np.ndarray
    mutual_reachability: np.ndarray
    mst_edges: np.ndarray
    single_linkage_tree: np.ndarray
    condensed_tree: np.ndarray


def _validate(X: np.ndarray, years: Sequence[int], ids: Sequence[str], k: int) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(years, dtype=np.int64)
    ids_t = tuple(str(v) for v in ids)
    if X.ndim != 2 or X.shape[0] == 0 or not np.all(np.isfinite(X)):
        raise ValueError("X must be a non-empty finite 2D array")
    if y.shape != (X.shape[0],):
        raise ValueError("years must align with X")
    if len(ids_t) != X.shape[0] or len(set(ids_t)) != len(ids_t):
        raise ValueError("ids must be unique and align with X")
    yrs = tuple(sorted(int(v) for v in np.unique(y)))
    if len(yrs) != 2:
        raise ValueError("exactly two years are required")
    if k <= 0 or any(int(np.sum(y == yr)) < k for yr in yrs):
        raise ValueError("each year must contain at least k points")
    return X, y, ids_t


def opposite_year_core_distances_kdtree(
    X: np.ndarray,
    years: Sequence[int],
    ids: Sequence[str],
    *,
    k: int = K_INHERITED,
) -> np.ndarray:
    X, y, _ids = _validate(X, years, ids, k)
    yrs = tuple(sorted(int(v) for v in np.unique(y)))
    out = np.empty(X.shape[0], dtype=np.float64)
    for yr in yrs:
        src = np.flatnonzero(y == yr)
        opp = np.flatnonzero(y != yr)
        tree = cKDTree(X[opp])
        distances, _indices = tree.query(X[src], k=k, workers=1)
        if k == 1:
            distances = distances[:, None]
        out[src] = np.asarray(distances[:, k - 1], dtype=np.float64)
    return out


def mutual_reachability_cdist(
    X: np.ndarray,
    years: Sequence[int],
    ids: Sequence[str],
    *,
    k: int = K_INHERITED,
) -> tuple[np.ndarray, np.ndarray]:
    X, y, ids_t = _validate(X, years, ids, k)
    core = opposite_year_core_distances_kdtree(X, y, ids_t, k=k)
    distances = cdist(X, X, metric="euclidean")
    mrd = np.maximum(distances, core[:, None])
    mrd = np.maximum(mrd, core[None, :])
    np.fill_diagonal(mrd, 0.0)
    return core, np.asarray(mrd, dtype=np.float64)


def deterministic_prim_mst(mrd: np.ndarray, ids: Sequence[str]) -> np.ndarray:
    mrd = np.asarray(mrd, dtype=np.float64)
    ids_t = tuple(str(v) for v in ids)
    n = mrd.shape[0]
    if mrd.shape != (n, n) or n == 0:
        raise ValueError("mrd must be non-empty and square")
    if len(ids_t) != n or len(set(ids_t)) != n:
        raise ValueError("ids must be unique and align with mrd")
    if not np.all(np.isfinite(mrd)) or np.any(mrd < 0):
        raise ValueError("mrd must be finite and nonnegative")

    start = min(range(n), key=lambda i: ids_t[i])
    in_tree = np.zeros(n, dtype=bool)
    best = np.full(n, np.inf, dtype=np.float64)
    parent = np.full(n, -1, dtype=np.int64)
    best[start] = 0.0
    chosen: list[tuple[int, int, float]] = []

    for _ in range(n):
        candidates = np.flatnonzero(~in_tree)
        u = min(candidates, key=lambda i: (float(best[i]), ids_t[i]))
        if not np.isfinite(best[u]):
            raise RuntimeError("graph is disconnected")
        in_tree[u] = True
        if parent[u] >= 0:
            chosen.append((int(parent[u]), int(u), float(best[u])))

        for v in np.flatnonzero(~in_tree):
            w = float(mrd[u, v])
            old_parent = int(parent[v])
            candidate_key = (min(ids_t[u], ids_t[v]), max(ids_t[u], ids_t[v]))
            old_key = (
                (min(ids_t[old_parent], ids_t[v]), max(ids_t[old_parent], ids_t[v]))
                if old_parent >= 0
                else ("\uffff", "\uffff")
            )
            if w < best[v] or (w == best[v] and candidate_key < old_key):
                best[v] = w
                parent[v] = u

    if len(chosen) != n - 1:
        raise RuntimeError("failed to build n-1 MST edges")
    return np.asarray(chosen, dtype=np.float64)


def audit_candidate(
    X: np.ndarray,
    years: Sequence[int],
    ids: Sequence[str],
    *,
    k: int = K_INHERITED,
    min_cluster_size: int = MIN_CLUSTER_SIZE_INHERITED,
) -> AuditCandidateResult:
    X, y, ids_t = _validate(X, years, ids, k)
    core, mrd = mutual_reachability_cdist(X, y, ids_t, k=k)
    mst = deterministic_prim_mst(mrd, ids_t)
    order = sorted(
        range(mst.shape[0]),
        key=lambda r: (
            float(mst[r, 2]),
            min(ids_t[int(mst[r, 0])], ids_t[int(mst[r, 1])]),
            max(ids_t[int(mst[r, 0])], ids_t[int(mst[r, 1])]),
        ),
    )
    single = label(np.asarray(mst[order], dtype=np.float64))
    condensed = condense_tree(single, int(min_cluster_size))
    return AuditCandidateResult(
        core_distances=core,
        mutual_reachability=mrd,
        mst_edges=mst,
        single_linkage_tree=np.asarray(single),
        condensed_tree=np.asarray(condensed),
    )
