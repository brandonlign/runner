from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np


def midrank_ecdf(values: Sequence[float]) -> np.ndarray:
    """Frozen exact-tie midrank empirical CDF.

    For each value x_i, returns (#{x_j < x_i} + 0.5 #{x_j == x_i}) / n.
    Equality is exact float equality. No tolerance or rounding is used.
    """
    x = np.asarray(values, dtype=np.float64)
    if x.ndim != 1 or x.size == 0 or not np.all(np.isfinite(x)):
        raise ValueError("values must be a non-empty finite 1D vector")

    order = np.argsort(x, kind="mergesort")
    out = np.empty(x.size, dtype=np.float64)
    start = 0
    while start < x.size:
        end = start + 1
        value = x[order[start]]
        while end < x.size and x[order[end]] == value:
            end += 1
        # start entries are strictly lower; end-start entries are exactly equal.
        q = (float(start) + 0.5 * float(end - start)) / float(x.size)
        out[order[start:end]] = q
        start = end
    return out


def rank_candidates(
    candidates: Sequence[Mapping[str, Any]],
    annual_stability: Mapping[int, Sequence[float]],
) -> list[dict[str, Any]]:
    """Order the exact promoted recurrent-EOM candidate catalogue by frozen ECDF rule."""
    if not candidates:
        raise ValueError("candidate catalogue must be non-empty")

    rows = [dict(c) for c in candidates]
    node_ids = [int(c["node_id"]) for c in rows]
    if len(set(node_ids)) != len(node_ids):
        raise ValueError("candidate node IDs must be unique")

    a0 = []
    a1 = []
    for node in node_ids:
        if node not in annual_stability:
            raise ValueError(f"annual stability missing selected node {node}")
        vals = tuple(float(v) for v in annual_stability[node])
        if len(vals) != 2 or not np.all(np.isfinite(vals)):
            raise ValueError(f"selected node {node} lacks two finite annual stability values")
        a0.append(vals[0])
        a1.append(vals[1])

    q0 = midrank_ecdf(a0)
    q1 = midrank_ecdf(a1)
    for i, row in enumerate(rows):
        row["annual_stability_2022"] = float(a0[i])
        row["annual_stability_2023"] = float(a1[i])
        row["ecdf_2022"] = float(q0[i])
        row["ecdf_2023"] = float(q1[i])
        row["worst_year_ecdf"] = float(min(q0[i], q1[i]))
        row["best_year_ecdf"] = float(max(q0[i], q1[i]))

    rows.sort(
        key=lambda c: (
            -float(c["worst_year_ecdf"]),
            -float(c["best_year_ecdf"]),
            -float(c["recurrent_stability"]),
            -float(c["ordinary_stability"]),
            -int(c["member_count"]),
            str(c["family_id"]),
        )
    )
    return rows


def canonical_membership(rows: Sequence[Mapping[str, Any]]) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(sorted(
        (str(row["family_id"]), tuple(sorted(str(x) for x in row["event_ids"])))
        for row in rows
    ))
