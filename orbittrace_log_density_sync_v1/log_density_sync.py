from __future__ import annotations

from collections import defaultdict
from typing import Iterable

import numpy as np

import recurrent_eom as parent_reom

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


def log_density_synchronous_stability(
    tree: np.ndarray,
    years: Iterable[int],
) -> dict[float, float]:
    """Integrate recurrent alive mass over log density rather than raw density.

    For each non-root condensed-tree node C:

        S_log(C) = integral min(A_0^C(lambda), A_1^C(lambda)) d log(lambda)

    where each A_y is the annual alive count normalized by the complete
    accessible event count for that year.  The hierarchy is not modified.

    The condensed-tree root has birth lambda zero and is excluded from HDBSCAN
    extraction when allow_single_cluster=False.  Its score is therefore fixed
    to zero rather than introducing an arbitrary positive offset inside log().
    """
    years_arr = np.asarray(list(years), dtype=np.int64)
    root = int(tree["parent"].min())
    if years_arr.shape != (root,):
        raise ValueError("year vector must align exactly with condensed-tree input points")

    values = tuple(sorted(int(y) for y in np.unique(years_arr)))
    if len(values) != 2:
        raise ValueError(f"log-density synchronous EOM requires exactly two years, got {values}")
    year_values = (int(values[0]), int(values[1]))
    totals = np.asarray([(years_arr == y).sum() for y in year_values], dtype=float)
    if np.any(totals <= 0):
        raise ValueError("both observing years must contain accessible events")

    births = parent_reom._birth_lambdas(tree)
    descendant_counts = parent_reom._descendant_year_counts(tree, years_arr)

    rows_by_parent: dict[int, list[tuple[float, int, int]]] = defaultdict(list)
    for p_raw, c_raw, lam_raw, size_raw in tree:
        p = int(p_raw)
        c = int(c_raw)
        lam = float(lam_raw)
        size = int(size_raw)
        if not np.isfinite(lam):
            raise RuntimeError(f"non-finite condensed-tree lambda for parent={p}, child={c}")
        if lam < 0.0:
            raise RuntimeError(f"negative condensed-tree lambda for parent={p}, child={c}")
        rows_by_parent[p].append((lam, c, size))

    out: dict[float, float] = {}
    for p in sorted(rows_by_parent):
        if p not in descendant_counts:
            raise RuntimeError(f"missing descendant-year counts for parent {p}")
        if p not in births:
            raise RuntimeError(f"missing birth lambda for parent {p}")

        birth = float(births[p])
        if p == root:
            if abs(birth) > TOL:
                raise RuntimeError(f"root birth lambda changed from zero: {birth}")
            out[float(p)] = 0.0
            continue
        if not np.isfinite(birth) or birth <= 0.0:
            raise RuntimeError(f"non-root node {p} has nonpositive/nonfinite birth lambda {birth}")

        alive = np.asarray(descendant_counts[p], dtype=np.int64).copy()
        if np.any(alive < 0):
            raise RuntimeError(f"negative initial alive count for parent {p}")

        previous = birth
        score = 0.0
        rows = sorted(rows_by_parent[p], key=lambda x: (x[0], x[1], x[2]))
        i = 0
        while i < len(rows):
            lam = float(rows[i][0])
            if lam < previous - TOL:
                raise RuntimeError(
                    f"condensed-tree departure precedes previous lambda for parent {p}: {lam} < {previous}"
                )
            if lam <= 0.0:
                raise RuntimeError(f"non-root node {p} reached nonpositive departure lambda {lam}")

            if lam > previous:
                dlog = float(np.log(lam / previous))
                if dlog < -TOL or not np.isfinite(dlog):
                    raise RuntimeError(f"invalid log-density interval for parent {p}: {previous} -> {lam}")
                alive_norm = alive.astype(float) / totals
                score += max(dlog, 0.0) * float(min(alive_norm[0], alive_norm[1]))

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
        if score < -TOL or not np.isfinite(score):
            raise RuntimeError(f"invalid log-density synchronous score for parent {p}: {score}")
        out[float(p)] = float(max(score, 0.0))

    expected_nodes = set(int(k) for k in parent_reom.recurrent_stability(tree, years_arr)[0])
    if set(int(k) for k in out) != expected_nodes:
        raise RuntimeError("log-density score node universe differs from recurrent-EOM node universe")
    return out
