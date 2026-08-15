from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class MixingStat:
    member_count: int
    year_counts: tuple[int, int]
    internal_edges: int
    cross_year_edges: int
    expected_cross_year_edges: float
    mixing_enrichment: float


def cluster_mixing_stats(
    labels: Iterable[int],
    years: Iterable[int],
    mst_edges: np.ndarray,
) -> dict[int, MixingStat]:
    """Compute fixed-count cross-year mixing on an already-fitted HDBSCAN MST.

    `labels` are the compact recurrent-EOM flat labels. Only MST edges whose two
    endpoints share the same nonnegative recurrent label contribute. The null
    conditions on each cluster's fixed graph and annual counts, so every
    internal edge has cross-year probability 2*n1*n2/[n*(n-1)].
    """
    lab = np.asarray(list(labels), dtype=np.int64)
    yrs = np.asarray(list(years), dtype=np.int64)
    if lab.ndim != 1 or yrs.shape != lab.shape:
        raise ValueError("labels and years must be aligned one-dimensional arrays")
    year_values = tuple(sorted(int(y) for y in np.unique(yrs)))
    if len(year_values) != 2:
        raise ValueError(f"exactly two observing years are required, got {year_values}")

    edges = np.asarray(mst_edges)
    if edges.ndim != 2 or edges.shape[1] < 2:
        raise ValueError(f"MST edge array must have at least two columns, got {edges.shape}")

    positive = sorted(int(x) for x in np.unique(lab) if int(x) >= 0)
    n_by_label = {k: int(np.sum(lab == k)) for k in positive}
    year_counts = {
        k: (
            int(np.sum((lab == k) & (yrs == year_values[0]))),
            int(np.sum((lab == k) & (yrs == year_values[1]))),
        )
        for k in positive
    }
    internal = {k: 0 for k in positive}
    cross = {k: 0 for k in positive}

    for row in edges:
        u_float = float(row[0])
        v_float = float(row[1])
        if not u_float.is_integer() or not v_float.is_integer():
            raise ValueError(f"nonintegral MST endpoint: {u_float}, {v_float}")
        u = int(u_float)
        v = int(v_float)
        if not (0 <= u < len(lab) and 0 <= v < len(lab)):
            raise ValueError(f"MST endpoint outside pooled event range: {u}, {v}")
        lu = int(lab[u])
        lv = int(lab[v])
        if lu >= 0 and lu == lv:
            internal[lu] += 1
            if int(yrs[u]) != int(yrs[v]):
                cross[lu] += 1

    out: dict[int, MixingStat] = {}
    for k in positive:
        n = n_by_label[k]
        n1, n2 = year_counts[k]
        m = int(internal[k])
        x = int(cross[k])
        if n1 + n2 != n:
            raise RuntimeError(f"annual count mismatch for label {k}: {n1}+{n2}!={n}")
        if not (0 <= x <= m):
            raise RuntimeError(f"invalid cross/internal edge counts for label {k}: {x}/{m}")
        if n < 2 or m == 0 or n1 == 0 or n2 == 0:
            mu = 0.0
            enrichment = 0.0
        else:
            q = (2.0 * float(n1) * float(n2)) / (float(n) * float(n - 1))
            mu = float(m) * q
            if not np.isfinite(mu) or mu <= 0.0:
                raise RuntimeError(f"invalid expected cross-year edge count for label {k}: {mu}")
            enrichment = float(x) / mu
        if not np.isfinite(enrichment) or enrichment < 0.0:
            raise RuntimeError(f"invalid mixing enrichment for label {k}: {enrichment}")
        out[k] = MixingStat(
            member_count=n,
            year_counts=(n1, n2),
            internal_edges=m,
            cross_year_edges=x,
            expected_cross_year_edges=float(mu),
            mixing_enrichment=float(enrichment),
        )
    return out


def mixed_score(recurrent_stability: float, mixing_enrichment: float) -> float:
    score = float(recurrent_stability) * float(mixing_enrichment)
    if not np.isfinite(score) or score < 0.0:
        raise ValueError(f"invalid recurrent/MST mixing score: {score}")
    return score
