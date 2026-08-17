#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import math
from typing import Any

import numpy as np
from scipy.spatial.distance import cdist
from sklearn.neighbors import NearestNeighbors

H_SOL = 2.0 * math.sin(math.radians(5.0) / 2.0)
H_RAD = 2.0 * math.sin(math.radians(4.0) / 2.0)
H_LOGV = math.log(1.1)
DIMENSION = 6
MIN_SUPPORT = 4
MAX_BASIN_FRACTION = 0.10


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise RuntimeError(msg)


def embedding(rows: list[dict[str, Any]]) -> np.ndarray:
    require(bool(rows), "empty rows")
    sol = np.radians(np.asarray([float(r["sol"]) for r in rows], dtype=np.float64))
    lon = np.radians(np.asarray([float(r["sun_lon"]) for r in rows], dtype=np.float64))
    lat = np.radians(np.asarray([float(r["ecl_lat"]) for r in rows], dtype=np.float64))
    vg = np.asarray([float(r["vg"]) for r in rows], dtype=np.float64)
    require(np.all(np.isfinite(sol)) and np.all(np.isfinite(lon)) and np.all(np.isfinite(lat)), "nonfinite angles")
    require(np.all(np.isfinite(vg)) and np.all(vg > 0.0), "invalid speed")
    cl = np.cos(lat)
    x = np.column_stack([
        np.cos(sol) / H_SOL,
        np.sin(sol) / H_SOL,
        cl * np.cos(lon) / H_RAD,
        cl * np.sin(lon) / H_RAD,
        np.sin(lat) / H_RAD,
        np.log(vg) / H_LOGV,
    ])
    require(x.shape == (len(rows), DIMENSION) and np.all(np.isfinite(x)), "invalid embedding")
    return x


def _ordered_neighbors(x: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    n = x.shape[0]
    model = NearestNeighbors(n_neighbors=k + 1, metric="euclidean", algorithm="auto", n_jobs=1).fit(x)
    distances, indices = model.kneighbors(x, return_distance=True)
    out_d = np.empty((n, k), dtype=np.float64)
    out_i = np.empty((n, k), dtype=np.int64)
    for row in range(n):
        pairs = [(float(d), int(j)) for d, j in zip(distances[row], indices[row]) if int(j) != row]
        pairs.sort(key=lambda z: (z[0], z[1]))
        require(len(pairs) >= k, "insufficient non-self neighbors")
        pairs = pairs[:k]
        out_d[row] = [p[0] for p in pairs]
        out_i[row] = [p[1] for p in pairs]
    require(np.all(out_d > 0.0), "zero nearest-neighbor distance")
    return out_d, out_i


def fit_ranked(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ids = [str(r["id"]) for r in rows]
    n = len(ids)
    require(n == len(set(ids)) and n > 4, "invalid IDs")
    x = embedding(rows)
    k = int(math.ceil(math.log2(n)))
    require(2 <= k < n, "invalid k")
    distances, neighbors = _ordered_neighbors(x, k)
    r_k = distances[:, -1]
    log_rho = -float(DIMENSION) * np.log(r_k)
    require(np.all(np.isfinite(log_rho)), "invalid density")

    parent = np.full(n, -1, dtype=np.int64)
    for i in range(n):
        for j in neighbors[i]:
            jj = int(j)
            if log_rho[jj] > log_rho[i] or (log_rho[jj] == log_rho[i] and jj < i):
                parent[i] = jj
                break

    def root_of(start: int) -> int:
        i = int(start)
        path: list[int] = []
        seen: set[int] = set()
        while parent[i] >= 0:
            require(i not in seen, "cycle in ascent forest")
            seen.add(i)
            path.append(i)
            i = int(parent[i])
        for node in path:
            parent[node] = i
        return i

    root_ids = np.asarray([root_of(i) for i in range(n)], dtype=np.int64)
    roots = np.unique(root_ids)
    require(len(roots) > 1, "density-ascent forest collapsed to one root")

    root_x = x[roots]
    root_rho = log_rho[roots]
    root_dist = cdist(root_x, root_x, metric="euclidean")
    require(np.all(np.isfinite(root_dist)), "invalid root distances")

    salience_by_root: dict[int, tuple[float, float]] = {}
    for a, root in enumerate(roots):
        higher = [b for b in range(len(roots)) if root_rho[b] > root_rho[a] or (root_rho[b] == root_rho[a] and int(roots[b]) < int(root))]
        if higher:
            delta = float(np.min(root_dist[a, higher]))
        else:
            others = [b for b in range(len(roots)) if b != a]
            require(bool(others), "single root")
            delta = float(np.max(root_dist[a, others]))
        require(math.isfinite(delta) and delta > 0.0, "invalid root separation")
        log_gamma = float(log_rho[int(root)] + math.log(delta))
        require(math.isfinite(log_gamma), "invalid salience")
        salience_by_root[int(root)] = (log_gamma, delta)

    raw: list[dict[str, Any]] = []
    max_allowed = int(math.floor(MAX_BASIN_FRACTION * n))
    for root in roots:
        rr = int(root)
        idx = np.flatnonzero(root_ids == rr)
        if idx.size < MIN_SUPPORT:
            continue
        require(idx.size <= max_allowed, "reportable basin exceeds structural max fraction")
        event_ids = [ids[int(i)] for i in idx]
        tie_hash = hashlib.sha256(("\n".join(sorted(event_ids)) + "\n").encode()).hexdigest()
        log_gamma, delta = salience_by_root[rr]
        raw.append({
            "root_index": rr,
            "event_ids": event_ids,
            "member_count": int(idx.size),
            "root_log_density": float(log_rho[rr]),
            "root_delta": float(delta),
            "log_salience": float(log_gamma),
            "tie_hash": tie_hash,
        })

    require(bool(raw), "no reportable density basins")
    raw.sort(key=lambda r: (-float(r["log_salience"]), str(r["tie_hash"])))
    ranked: list[dict[str, Any]] = []
    for rank, r in enumerate(raw, start=1):
        ranked.append({"family_id": f"ada-{str(r['tie_hash'])[:16]}", "rank": rank, **r})

    sizes = np.asarray([r["member_count"] for r in ranked], dtype=np.int64)
    summary = {
        "n_events": n,
        "k": k,
        "embedding_dimensions": DIMENSION,
        "local_root_count": int(len(roots)),
        "reportable_basin_count": len(ranked),
        "max_reportable_basin_size": int(np.max(sizes)),
        "median_reportable_basin_size": float(np.median(sizes)),
        "max_reportable_basin_fraction": float(np.max(sizes) / n),
        "density": "negative_6_log_kth_neighbor_distance",
        "parent_rule": "nearest_in_kNN_order_with_strictly_higher_density",
        "root_order": "log_density_plus_log_nearest_higher_root_distance",
    }
    return ranked, summary
