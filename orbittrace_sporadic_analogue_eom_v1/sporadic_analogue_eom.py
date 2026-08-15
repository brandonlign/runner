from __future__ import annotations

from collections import defaultdict
from typing import Iterable

import numpy as np
from scipy.spatial import cKDTree

import recurrent_eom as parent

K_NEIGHBOURS = 10
ANALOGUE_OFFSETS_DEG = tuple(float(x) for x in range(60, 301, 10))
TOL = 1e-12
MASS_REL_TOL = 1e-12


def bounded_contrast_weight(contrast: np.ndarray | float) -> np.ndarray | float:
    c = np.asarray(contrast, dtype=float)
    if np.any(~np.isfinite(c)) or np.any(c <= 0.0):
        raise ValueError("density contrast must be finite and positive")
    w = 2.0 * c / (1.0 + c)
    if np.isscalar(contrast):
        return float(w)
    return w


def _geo_matrix_from_arrays(sol_deg: np.ndarray, lon_deg: np.ndarray, lat_deg: np.ndarray, vg: np.ndarray) -> np.ndarray:
    sol = np.radians(np.asarray(sol_deg, dtype=float))
    lon = np.radians(np.asarray(lon_deg, dtype=float))
    lat = np.radians(np.asarray(lat_deg, dtype=float))
    speed = np.asarray(vg, dtype=float)
    return np.column_stack((
        np.cos(sol),
        np.sin(sol),
        np.sin(lon) * np.cos(lat),
        np.cos(lon) * np.cos(lat),
        np.sin(lat),
        speed / 72.0,
    ))


def compute_sporadic_analogue_weights(
    events: list[dict],
    X: np.ndarray,
    years: Iterable[int],
    blind: tuple[float, float] = (20.0, 55.0),
) -> tuple[np.ndarray, dict[str, dict[str, float | int]]]:
    """Compute label-free survey-local sporadic contrast weights.

    For each observing year, the actual 10th-other-neighbour radius is compared
    with the median 10th-neighbour radius of the same Sun-centred radiant/speed
    moved through the fixed +60..+300 degree seasonal analogue grid. Analogues
    that fall inside the protected solar-longitude interval are discarded before
    querying the target-excluded same-year tree.
    """
    years_arr = np.asarray(list(years), dtype=np.int64)
    if X.shape != (len(events), 6):
        raise ValueError(f"X shape {X.shape} does not match {len(events)} events")
    if years_arr.shape != (len(events),):
        raise ValueError("year vector does not align with events")
    if tuple(sorted(int(y) for y in np.unique(years_arr))) != (2022, 2023):
        raise ValueError("frozen analogue method requires exactly GMN 2022 and 2023")

    sol_all = np.asarray([float(e["sol"]) % 360.0 for e in events], dtype=float)
    lon_all = np.asarray([float(e["lon"]) for e in events], dtype=float)
    lat_all = np.asarray([float(e["lat"]) for e in events], dtype=float)
    vg_all = np.asarray([float(e["vg"]) for e in events], dtype=float)
    if np.any(~np.isfinite(np.column_stack((sol_all, lon_all, lat_all, vg_all)))):
        raise ValueError("non-finite event geometry")

    out = np.empty(len(events), dtype=np.float64)
    summary: dict[str, dict[str, float | int]] = {}
    low, high = map(float, blind)

    for year in (2022, 2023):
        idx = np.flatnonzero(years_arr == year)
        Xi = np.asarray(X[idx], dtype=np.float64)
        tree = cKDTree(Xi)

        # Query only the (k+1)-th neighbour: self is neighbour 1 at distance 0.
        actual_dist, _ = tree.query(Xi, k=[K_NEIGHBOURS + 1], workers=-1)
        r_actual = np.asarray(actual_dist[:, 0], dtype=np.float64)
        if np.any(~np.isfinite(r_actual)) or np.any(r_actual <= 0.0):
            raise RuntimeError(f"invalid actual kNN radius in {year}")

        n = len(idx)
        analog = np.full((n, len(ANALOGUE_OFFSETS_DEG)), np.nan, dtype=np.float64)
        sol = sol_all[idx]
        lon = lon_all[idx]
        lat = lat_all[idx]
        vg = vg_all[idx]

        for j, delta in enumerate(ANALOGUE_OFFSETS_DEG):
            shifted = (sol + delta) % 360.0
            valid = ~((shifted >= low) & (shifted <= high))
            if not np.any(valid):
                raise RuntimeError(f"all analogues blocked for {year} delta={delta}")
            q = _geo_matrix_from_arrays(shifted[valid], lon[valid], lat[valid], vg[valid])
            dist, _ = tree.query(q, k=[K_NEIGHBOURS], workers=-1)
            kth = np.asarray(dist[:, 0], dtype=np.float64)
            if np.any(~np.isfinite(kth)) or np.any(kth <= 0.0):
                raise RuntimeError(f"invalid analogue kNN radius in {year} delta={delta}")
            analog[valid, j] = kth

        valid_counts = np.sum(np.isfinite(analog), axis=1)
        if np.any(valid_counts < 20):
            raise RuntimeError(f"too few unprotected seasonal analogues in {year}: min={int(valid_counts.min())}")
        r_bg = np.nanmedian(analog, axis=1)
        if np.any(~np.isfinite(r_bg)) or np.any(r_bg <= 0.0):
            raise RuntimeError(f"invalid analogue background radius in {year}")

        contrast = r_bg / r_actual
        weight = np.asarray(bounded_contrast_weight(contrast), dtype=np.float64)
        if np.any(~np.isfinite(weight)) or np.any(weight <= 0.0) or np.any(weight >= 2.0):
            raise RuntimeError(f"invalid bounded analogue weight in {year}")
        out[idx] = weight

        summary[str(year)] = {
            "event_count": int(n),
            "min_valid_analogues": int(valid_counts.min()),
            "max_valid_analogues": int(valid_counts.max()),
            "mean_weight": float(np.mean(weight)),
            "median_weight": float(np.median(weight)),
            "min_weight": float(np.min(weight)),
            "max_weight": float(np.max(weight)),
            "mean_contrast": float(np.mean(contrast)),
            "median_contrast": float(np.median(contrast)),
        }

    return out, summary


def _descendant_weight_sums(tree: np.ndarray, years: np.ndarray, weights: np.ndarray) -> dict[int, np.ndarray]:
    root = int(tree["parent"].min())
    if years.shape != (root,) or weights.shape != (root,):
        raise ValueError("years/weights must align exactly with condensed-tree points")
    year_values = tuple(sorted(int(y) for y in np.unique(years)))
    if year_values != (2022, 2023):
        raise ValueError(f"unexpected years {year_values}")
    y_index = {y: i for i, y in enumerate(year_values)}

    children: dict[int, list[int]] = defaultdict(list)
    cluster_nodes: set[int] = set()
    for parent_raw, child_raw in zip(tree["parent"], tree["child"]):
        p = int(parent_raw)
        c = int(child_raw)
        children[p].append(c)
        cluster_nodes.add(p)
        if c >= root:
            if c <= p:
                raise RuntimeError(f"condensed-tree topological order changed: parent={p}, child={c}")
            cluster_nodes.add(c)

    memo: dict[int, np.ndarray] = {}
    for node in sorted(cluster_nodes, reverse=True):
        out = np.zeros(2, dtype=np.float64)
        for child in children.get(node, []):
            if child < root:
                out[y_index[int(years[child])]] += float(weights[child])
            else:
                if child not in memo:
                    raise RuntimeError(f"missing weighted child {child} for parent {node}")
                out += memo[child]
        memo[node] = out
    return memo


def sporadic_analogue_stability(
    tree: np.ndarray,
    years: Iterable[int],
    weights: Iterable[float],
) -> dict[float, float]:
    """Density-synchronous EOM with survey-local sporadic-contrast alive mass."""
    years_arr = np.asarray(list(years), dtype=np.int64)
    weights_arr = np.asarray(list(weights), dtype=np.float64)
    root = int(tree["parent"].min())
    if years_arr.shape != (root,) or weights_arr.shape != (root,):
        raise ValueError("years/weights must align exactly with condensed-tree points")
    if np.any(~np.isfinite(weights_arr)) or np.any(weights_arr <= 0.0):
        raise ValueError("weights must be finite and positive")

    year_values = tuple(sorted(int(y) for y in np.unique(years_arr)))
    if year_values != (2022, 2023):
        raise ValueError(f"unexpected years {year_values}")
    totals = np.asarray([weights_arr[years_arr == y].sum() for y in year_values], dtype=np.float64)
    if np.any(totals <= 0.0):
        raise ValueError("both years must have positive total analogue weight")

    births = parent._birth_lambdas(tree)
    desc = _descendant_weight_sums(tree, years_arr, weights_arr)
    rows_by_parent: dict[int, list[tuple[float, int]]] = defaultdict(list)
    for p_raw, c_raw, lam_raw, _size_raw in tree:
        p = int(p_raw)
        c = int(c_raw)
        lam = float(lam_raw)
        if not np.isfinite(lam):
            raise RuntimeError(f"non-finite lambda for parent={p}, child={c}")
        rows_by_parent[p].append((lam, c))

    score: dict[float, float] = {}
    y_index = {y: i for i, y in enumerate(year_values)}
    for p in sorted(rows_by_parent):
        if p not in desc or p not in births:
            raise RuntimeError(f"missing node bookkeeping for {p}")
        alive = np.asarray(desc[p], dtype=np.float64).copy()
        initial_alive = alive.copy()
        mass_tol = MASS_REL_TOL * max(1.0, float(np.max(np.abs(initial_alive))))
        previous = float(births[p])
        integral = 0.0
        rows = sorted(rows_by_parent[p], key=lambda x: (x[0], x[1]))
        i = 0
        while i < len(rows):
            lam = float(rows[i][0])
            delta = lam - previous
            if delta < -TOL:
                raise RuntimeError(f"departure lambda decreased for node {p}: {lam} < {previous}")
            if delta < 0.0:
                delta = 0.0
            norm = alive / totals
            integral += delta * float(min(norm[0], norm[1]))

            departure = np.zeros(2, dtype=np.float64)
            j = i
            while j < len(rows) and float(rows[j][0]) == lam:
                child = int(rows[j][1])
                if child < root:
                    departure[y_index[int(years_arr[child])]] += float(weights_arr[child])
                else:
                    departure += desc[child]
                j += 1
            alive -= departure
            if np.any(alive < -mass_tol):
                raise RuntimeError(
                    f"negative weighted alive mass for node {p}: {alive.tolist()} below tolerance {mass_tol}"
                )
            alive[np.abs(alive) <= mass_tol] = 0.0
            previous = lam
            i = j

        if np.any(np.abs(alive) > mass_tol):
            raise RuntimeError(
                f"nonzero final weighted alive mass for node {p}: {alive.tolist()} above tolerance {mass_tol}"
            )
        if integral < -TOL or not np.isfinite(integral):
            raise RuntimeError(f"invalid analogue stability for node {p}: {integral}")
        score[float(p)] = float(max(integral, 0.0))

    return score
