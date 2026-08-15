from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DriftBIC:
    identifiable: bool
    n_years: tuple[int, int]
    bic_shared: float | None
    bic_separate: float | None
    delta_bic: float | None
    shared_weight: float


@dataclass
class TreeStats:
    root: int
    node_ids: np.ndarray
    n: np.ndarray          # [node, year]
    sum_u: np.ndarray      # [node, year]
    sum_u2: np.ndarray     # [node, year]
    sum_y: np.ndarray      # [node, year, response]
    sum_uy: np.ndarray     # [node, year, response]
    sum_y2: np.ndarray     # [node, year, response]

    def index(self, node: int) -> int:
        i = int(node) - self.root
        if i < 0 or i >= len(self.node_ids) or int(self.node_ids[i]) != int(node):
            raise KeyError(f"cluster node {node} is outside compact tree-stat range")
        return i


def physical_predictor_and_response(
    sol_deg: np.ndarray,
    sun_lon_deg: np.ndarray,
    ecl_lat_deg: np.ndarray,
    vg_km_s: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    sol = np.asarray(sol_deg, dtype=np.float64)
    lon = np.deg2rad(np.asarray(sun_lon_deg, dtype=np.float64))
    lat = np.deg2rad(np.asarray(ecl_lat_deg, dtype=np.float64))
    vg = np.asarray(vg_km_s, dtype=np.float64)
    if not (sol.shape == lon.shape == lat.shape == vg.shape):
        raise ValueError("physical input arrays must be aligned")
    if sol.ndim != 1:
        raise ValueError("physical input arrays must be one-dimensional")
    if not (np.all(np.isfinite(sol)) and np.all(np.isfinite(lon)) and np.all(np.isfinite(lat)) and np.all(np.isfinite(vg))):
        raise ValueError("non-finite physical input")
    if np.any(vg <= 0.0):
        raise ValueError("geocentric speed must be strictly positive")

    # The protected [20,55] interval is already removed by the caller. Unwrap
    # the remaining 325-degree arc from 55 degrees and retain the preregistered
    # /10 numerical scaling. This scaling cannot alter OLS fitted values/BIC.
    u = np.mod(sol - 55.0, 360.0) / 10.0
    c = np.cos(lat)
    Y = np.column_stack((
        c * np.cos(lon),
        c * np.sin(lon),
        np.sin(lat),
        np.log(vg),
    ))
    return u, Y


def aggregate_tree_stats(
    tree: np.ndarray,
    years: np.ndarray,
    u: np.ndarray,
    Y: np.ndarray,
) -> TreeStats:
    years_arr = np.asarray(years, dtype=np.int64)
    u_arr = np.asarray(u, dtype=np.float64)
    y_arr = np.asarray(Y, dtype=np.float64)
    root = int(tree["parent"].min())
    if years_arr.shape != (root,) or u_arr.shape != (root,) or y_arr.shape != (root, 4):
        raise ValueError(
            f"point arrays must align to condensed-tree point count {root}; "
            f"got years={years_arr.shape}, u={u_arr.shape}, Y={y_arr.shape}"
        )
    year_values = tuple(sorted(int(y) for y in np.unique(years_arr)))
    if len(year_values) != 2:
        raise ValueError(f"exactly two observing years required, got {year_values}")
    y_index = {y: i for i, y in enumerate(year_values)}

    cluster_nodes: set[int] = set(int(x) for x in tree["parent"])
    for child, child_size, parent in zip(tree["child"], tree["child_size"], tree["parent"]):
        c = int(child)
        p = int(parent)
        if int(child_size) > 1:
            if c <= p:
                raise RuntimeError(f"condensed-tree cluster topology changed: parent={p}, child={c}")
            cluster_nodes.add(c)
    max_node = max(cluster_nodes)
    expected = np.arange(root, max_node + 1, dtype=np.int64)
    if set(expected.tolist()) != cluster_nodes:
        missing = sorted(set(expected.tolist()) - cluster_nodes)[:10]
        raise RuntimeError(f"cluster node IDs are no longer contiguous from root; missing={missing}")
    m = len(expected)

    n = np.zeros((m, 2), dtype=np.int64)
    sum_u = np.zeros((m, 2), dtype=np.float64)
    sum_u2 = np.zeros((m, 2), dtype=np.float64)
    sum_y = np.zeros((m, 2, 4), dtype=np.float64)
    sum_uy = np.zeros((m, 2, 4), dtype=np.float64)
    sum_y2 = np.zeros((m, 2, 4), dtype=np.float64)

    point_mask = np.asarray(tree["child_size"] == 1)
    point_rows = tree[point_mask]
    parents = np.asarray(point_rows["parent"], dtype=np.int64) - root
    points = np.asarray(point_rows["child"], dtype=np.int64)
    if np.any(points < 0) or np.any(points >= root):
        raise RuntimeError("point child outside input point range")
    yi = np.asarray([y_index[int(y)] for y in years_arr[points]], dtype=np.int64)
    pu = u_arr[points]
    py = y_arr[points]

    np.add.at(n, (parents, yi), 1)
    np.add.at(sum_u, (parents, yi), pu)
    np.add.at(sum_u2, (parents, yi), pu * pu)
    np.add.at(sum_y, (parents, yi), py)
    np.add.at(sum_uy, (parents, yi), pu[:, None] * py)
    np.add.at(sum_y2, (parents, yi), py * py)

    cluster_rows = tree[np.asarray(tree["child_size"] > 1)]
    # HDBSCAN condensed cluster IDs are topological. Add every child's complete
    # sufficient statistics into its parent from highest child ID downward.
    order = np.argsort(np.asarray(cluster_rows["child"], dtype=np.int64))[::-1]
    for row in cluster_rows[order]:
        p = int(row["parent"]) - root
        c = int(row["child"]) - root
        n[p] += n[c]
        sum_u[p] += sum_u[c]
        sum_u2[p] += sum_u2[c]
        sum_y[p] += sum_y[c]
        sum_uy[p] += sum_uy[c]
        sum_y2[p] += sum_y2[c]

    return TreeStats(
        root=root,
        node_ids=expected,
        n=n,
        sum_u=sum_u,
        sum_u2=sum_u2,
        sum_y=sum_y,
        sum_uy=sum_uy,
        sum_y2=sum_y2,
    )


def _rss_from_stats(
    n: int,
    sum_u: float,
    sum_u2: float,
    sum_y: np.ndarray,
    sum_uy: np.ndarray,
    sum_y2: np.ndarray,
) -> tuple[np.ndarray, float]:
    if n < 1:
        raise ValueError("cannot fit empty sufficient statistics")
    sxx = float(sum_u2) - float(sum_u) * float(sum_u) / float(n)
    if not np.isfinite(sxx) or sxx <= 0.0:
        raise ValueError(f"linear design is singular: n={n}, Sxx={sxx}")
    sy = np.asarray(sum_y, dtype=np.float64)
    suy = np.asarray(sum_uy, dtype=np.float64)
    sy2 = np.asarray(sum_y2, dtype=np.float64)
    sxy = suy - float(sum_u) * sy / float(n)
    syy = sy2 - sy * sy / float(n)
    rss = syy - (sxy * sxy) / sxx
    if not np.all(np.isfinite(rss)):
        raise ValueError(f"non-finite OLS RSS: {rss}")
    return rss, sxx


def stable_logistic_half_delta(delta_bic: float) -> float:
    x = float(delta_bic) / 2.0
    if not np.isfinite(x):
        raise ValueError(f"non-finite Delta BIC: {delta_bic}")
    if x >= 0.0:
        z = float(np.exp(-x))
        return 1.0 / (1.0 + z)
    z = float(np.exp(x))
    return z / (1.0 + z)


def node_drift_bic(stats: TreeStats, node: int) -> DriftBIC:
    i = stats.index(int(node))
    n0 = int(stats.n[i, 0])
    n1 = int(stats.n[i, 1])
    if n0 < 3 or n1 < 3:
        return DriftBIC(False, (n0, n1), None, None, None, 0.0)

    # Annual fits must each have at least one residual degree of freedom and a
    # nonsingular [1,u] design.
    annual_rss: list[np.ndarray] = []
    for yi, ny in enumerate((n0, n1)):
        try:
            rss, _sxx = _rss_from_stats(
                ny,
                float(stats.sum_u[i, yi]),
                float(stats.sum_u2[i, yi]),
                stats.sum_y[i, yi],
                stats.sum_uy[i, yi],
                stats.sum_y2[i, yi],
            )
        except ValueError:
            return DriftBIC(False, (n0, n1), None, None, None, 0.0)
        annual_rss.append(rss)

    N = n0 + n1
    pooled_sum_u = float(stats.sum_u[i].sum())
    pooled_sum_u2 = float(stats.sum_u2[i].sum())
    pooled_sum_y = stats.sum_y[i].sum(axis=0)
    pooled_sum_uy = stats.sum_uy[i].sum(axis=0)
    pooled_sum_y2 = stats.sum_y2[i].sum(axis=0)
    try:
        rss_shared, _ = _rss_from_stats(
            N, pooled_sum_u, pooled_sum_u2, pooled_sum_y, pooled_sum_uy, pooled_sum_y2
        )
    except ValueError:
        return DriftBIC(False, (n0, n1), None, None, None, 0.0)
    rss_sep = annual_rss[0] + annual_rss[1]

    # The frozen protocol deliberately fails closed on exact/nonpositive RSS
    # rather than introducing a scientific epsilon or floor.
    if np.any(rss_shared <= 0.0) or np.any(rss_sep <= 0.0):
        raise RuntimeError(
            f"nonpositive identifiable-node RSS for node {node}: shared={rss_shared}, separate={rss_sep}"
        )

    bic_shared = float(N * np.log(rss_shared / float(N)).sum() + 12.0 * np.log(float(N)))
    bic_separate = float(N * np.log(rss_sep / float(N)).sum() + 20.0 * np.log(float(N)))
    if not np.isfinite(bic_shared) or not np.isfinite(bic_separate):
        raise RuntimeError(f"non-finite BIC for node {node}: {bic_shared}, {bic_separate}")
    delta = float(bic_separate - bic_shared)
    weight = stable_logistic_half_delta(delta)
    if not np.isfinite(weight) or not (0.0 <= weight <= 1.0):
        raise RuntimeError(f"invalid shared-model weight for node {node}: {weight}")
    return DriftBIC(True, (n0, n1), bic_shared, bic_separate, delta, float(weight))


def shared_drift_stability(
    recurrent_stability: dict[float, float],
    stats: TreeStats,
) -> tuple[dict[float, float], dict[int, DriftBIC]]:
    out: dict[float, float] = {}
    evidence: dict[int, DriftBIC] = {}
    for key, rec in recurrent_stability.items():
        node = int(key)
        ev = node_drift_bic(stats, node)
        evidence[node] = ev
        value = float(rec) * float(ev.shared_weight)
        if not np.isfinite(value) or value < 0.0:
            raise RuntimeError(f"invalid shared-drift stability for node {node}: {value}")
        out[float(node)] = value
    return out, evidence
