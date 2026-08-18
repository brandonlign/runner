#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

import numpy as np

import build_prelabel as frozen
import technical_lazy_local_trunk as transport


class ExactFullRadiusNeighbors(transport.LazyRadiusNeighbors):
    """Expose the exact frozen radius row lazily, with no edge pruning."""

    def __getitem__(self, i: int):
        i = int(i)
        if i < 0 or i >= self.n:
            raise IndexError(i)
        raw = self.tree.query_ball_point(
            self.z[i], r=frozen.RADIUS, p=2.0, eps=0.0, return_sorted=True
        )
        row = [int(x) for x in raw]
        frozen.req(i in row, f"self missing from exact lazy radius graph at {i}")
        frozen.req(all(0 <= j < self.n for j in row), "exact lazy radius graph index out of range")
        self.rows_served += 1
        self.entries_served += len(row)
        return row


def local_trunk_exact_full_row(
    parent_ids: list[str], event_by_id: dict[str, dict[str, Any]]
) -> tuple[list[str], dict[str, Any]]:
    # Reuse the already-frozen downstream hierarchy/membership reconstruction
    # from the transport helper, replacing only its row provider. The provider
    # here returns every exact radius neighbor, so the logical graph is exactly
    # the original frozen manual graph.
    original_cls = transport.LazyRadiusNeighbors
    transport.LazyRadiusNeighbors = ExactFullRadiusNeighbors
    try:
        return transport.local_trunk_lazy(parent_ids, event_by_id)
    finally:
        transport.LazyRadiusNeighbors = original_cls


if __name__ == "__main__":
    raise SystemExit("import-only exact full-row transport")
