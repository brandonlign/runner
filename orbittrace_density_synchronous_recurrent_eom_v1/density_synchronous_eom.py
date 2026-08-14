from __future__ import annotations

from collections import defaultdict
from typing import Iterable

import numpy as np

import recurrent_eom as parent

TOL = 1e-12


def _branch_year_counts(
    child: int,
    root: int,
    years: np.ndarray,
    year_values: tuple[int, int],
    descendant_counts: dict[int, np.ndarray],
) -> np.ndarray:
    if child < root:
        return np.asarray([int(years[child] == y) for y in year_values], dtype=np.int64)
    if child not in descendant_counts:
        raise RuntimeError(f"missing descendant-year counts for cluster child {child}")
    return np.asarray(descendant_counts[child], dtype=np.int64)


def density_synchronous_stability(
    tree: np.ndarray,
    years: Iterable[int],
) -> tuple[
    dict[float, float],
    dict[int, tuple[float, float]],
    dict[int, tuple[float, float]],
]:
    """Compute the frozen density-synchronous recurrent-EOM quality.

    The HDBSCAN hierarchy is not modified.  For each cluster node, this function
    sweeps the exact direct-child departure lambdas and integrates the pointwise
    minimum of the two annual normalized alive-mass curves.  It also reconstructs
    each annual EOM integral independently and verifies identity to the promoted
    recurrent-EOM v1 implementation.

    Returns
    -------
    synchronous:
        Mapping accepted by hdbscan._hdbscan_tree.get_clusters.
    annual_parent:
        Exact promoted-parent annual normalized EOM values per cluster.
    annual_reconstructed:
        The same annual values reconstructed by alive-curve integration, retained
        for audit/provenance.
    """
    years_arr = np.asarray(list(years), dtype=np.int64)
    root = int(tree["parent"].min())
    if years_arr.shape != (root,):
        raise ValueError("year vector must align exactly with condensed-tree input points")
    year_values = tuple(sorted(int(y) for y in np.unique(years_arr)))
    if len(year_values) != 2:
        raise ValueError(f"density-synchronous EOM requires exactly two years, got {year_values}")
    year_values = (int(year_values[0]), int(year_values[1]))
    totals_i = np.asarray([(years_arr == y).sum() for y in year_values], dtype=np.int64)
    if np.any(totals_i <= 0):
        raise ValueError("both observing years must contain accessible events")
    totals = totals_i.astype(float)

    births = parent._birth_lambdas(tree)
    descendant_counts = parent._descendant_year_counts(tree, years_arr)
    _parent_recurrent, parent_annual = parent.recurrent_stability(tree, years_arr)

    rows_by_parent: dict[int, list[tuple[float, int, int]]] = defaultdict(list)
    for p_raw, c_raw, lam_raw, size_raw in tree:
        p = int(p_raw)
        c = int(c_raw)
        lam = float(lam_raw)
        size = int(size_raw)
        if not np.isfinite(lam):
            raise RuntimeError(f"non-finite condensed-tree lambda for parent={p}, child={c}")
        rows_by_parent[p].append((lam, c, size))

    synchronous: dict[float, float] = {}
    reconstructed: dict[int, tuple[float, float]] = {}

    for p in sorted(rows_by_parent):
        if p not in descendant_counts:
            raise RuntimeError(f"missing descendant-year counts for parent {p}")
        if p not in births:
            raise RuntimeError(f"missing birth lambda for parent {p}")
        if p not in parent_annual:
            raise RuntimeError(f"missing promoted-parent annual EOM for parent {p}")

        alive = np.asarray(descendant_counts[p], dtype=np.int64).copy()
        if np.any(alive < 0):
            raise RuntimeError(f"negative initial alive count for parent {p}")
        previous = float(births[p])
        if not np.isfinite(previous):
            raise RuntimeError(f"non-finite birth lambda for parent {p}")

        annual_integral = np.zeros(2, dtype=float)
        sync_integral = 0.0
        rows = sorted(rows_by_parent[p], key=lambda x: (x[0], x[1], x[2]))
        i = 0
        while i < len(rows):
            lam = float(rows[i][0])
            delta = lam - previous
            if delta < -TOL:
                raise RuntimeError(
                    f"condensed-tree departure precedes previous lambda for parent {p}: {lam} < {previous}"
                )
            if delta < 0.0:
                delta = 0.0

            alive_norm = alive.astype(float) / totals
            annual_integral += delta * alive_norm
            sync_integral += delta * float(min(alive_norm[0], alive_norm[1]))

            departure = np.zeros(2, dtype=np.int64)
            j = i
            while j < len(rows) and float(rows[j][0]) == lam:
                _lam, child, child_size = rows[j]
                branch = _branch_year_counts(child, root, years_arr, year_values, descendant_counts)
                if int(branch.sum()) != int(child_size):
                    raise RuntimeError(
                        f"descendant accounting mismatch for parent={p}, child={child}: "
                        f"{int(branch.sum())} != {int(child_size)}"
                    )
                departure += branch
                j += 1

            alive -= departure
            if np.any(alive < 0):
                raise RuntimeError(f"negative alive count after lambda={lam} for parent {p}: {alive.tolist()}")
            previous = lam
            i = j

        if np.any(alive != 0):
            raise RuntimeError(f"nonzero final alive counts for parent {p}: {alive.tolist()}")

        expected = np.asarray(parent_annual[p], dtype=float)
        if not np.allclose(annual_integral, expected, rtol=TOL, atol=TOL):
            raise RuntimeError(
                f"annual EOM reconstruction mismatch for parent {p}: "
                f"reconstructed={annual_integral.tolist()} expected={expected.tolist()}"
            )
        upper = float(min(expected[0], expected[1]))
        if sync_integral > upper + TOL * max(1.0, abs(upper)):
            raise RuntimeError(
                f"synchronous stability exceeds promoted recurrent bound for parent {p}: "
                f"sync={sync_integral} upper={upper}"
            )
        if sync_integral < -TOL:
            raise RuntimeError(f"negative synchronous stability for parent {p}: {sync_integral}")

        synchronous[float(p)] = float(max(sync_integral, 0.0))
        reconstructed[p] = (float(annual_integral[0]), float(annual_integral[1]))

    if set(int(k) for k in synchronous) != set(int(k) for k in parent_annual):
        raise RuntimeError("synchronous stability node universe differs from promoted recurrent-EOM annual universe")

    return synchronous, parent_annual, reconstructed
