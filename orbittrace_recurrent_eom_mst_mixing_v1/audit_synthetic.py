#!/usr/bin/env python3
from __future__ import annotations

import json

import numpy as np

from mst_year_mixing import cluster_mixing_stats, mixed_score


def req(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def edge_array(pairs: list[tuple[int, int]]) -> np.ndarray:
    return np.asarray([[u, v, float(i + 1)] for i, (u, v) in enumerate(pairs)], dtype=float)


def main() -> int:
    # One 8-point cluster with balanced 4/4 year counts. Both fixtures use the
    # same path graph; only fixed year labels differ.
    labels = np.zeros(8, dtype=int)
    path = edge_array([(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)])

    segregated_years = np.asarray([2022, 2022, 2022, 2022, 2023, 2023, 2023, 2023])
    interleaved_years = np.asarray([2022, 2023, 2022, 2023, 2022, 2023, 2022, 2023])

    seg = cluster_mixing_stats(labels, segregated_years, path)[0]
    mix = cluster_mixing_stats(labels, interleaved_years, path)[0]

    req(seg.member_count == mix.member_count == 8, "member count changed")
    req(seg.year_counts == mix.year_counts == (4, 4), "annual counts changed")
    req(seg.internal_edges == mix.internal_edges == 7, "path internal edge count wrong")
    req(seg.cross_year_edges == 1, "segregated path should have one cross-year boundary")
    req(mix.cross_year_edges == 7, "interleaved path should have all cross-year edges")
    req(abs(seg.expected_cross_year_edges - 4.0) < 1e-15, "fixed-count null expectation wrong")
    req(abs(mix.expected_cross_year_edges - 4.0) < 1e-15, "null expectation must ignore arrangement")
    req(abs(seg.mixing_enrichment - 0.25) < 1e-15, "segregated enrichment wrong")
    req(abs(mix.mixing_enrichment - 1.75) < 1e-15, "interleaved enrichment wrong")
    req(mix.mixing_enrichment > seg.mixing_enrichment, "interleaving must score higher")

    # Edge-order and edge-weight invariance: weights are intentionally ignored.
    reversed_edges = path[::-1].copy()
    reversed_edges[:, 2] *= 1000.0
    mix_reordered = cluster_mixing_stats(labels, interleaved_years, reversed_edges)[0]
    req(mix_reordered == mix, "mixing statistic changed under edge order/weight mutation")

    # Year-name swap invariance.
    swapped = np.where(interleaved_years == 2022, 2023, 2022)
    mix_swapped = cluster_mixing_stats(labels, swapped, path)[0]
    req(mix_swapped == mix, "mixing statistic changed under year-name swap")

    # Two compact clusters; between-cluster edges must be ignored.
    labels2 = np.asarray([0, 0, 0, 0, 1, 1, 1, 1])
    years2 = np.asarray([2022, 2023, 2022, 2023, 2022, 2022, 2023, 2023])
    edges2 = edge_array([(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)])
    stats2 = cluster_mixing_stats(labels2, years2, edges2)
    req(stats2[0].internal_edges == 3, "cluster 0 internal edge count wrong")
    req(stats2[1].internal_edges == 3, "cluster 1 internal edge count wrong")
    req(stats2[0].cross_year_edges == 3, "cluster 0 cross-year count wrong")
    req(stats2[1].cross_year_edges == 1, "cluster 1 cross-year count wrong")

    # Product score is exactly the frozen rule.
    req(abs(mixed_score(0.2, 1.75) - 0.35) < 1e-15, "mixed score formula changed")
    req(mixed_score(0.0, 100.0) == 0.0, "zero recurrent stability must remain zero")

    result = {
        "verdict": "PASS_RECURRENT_EOM_MST_YEAR_MIXING_V1_SYNTHETIC_AUDIT",
        "segregated": seg.__dict__,
        "interleaved": mix.__dict__,
        "assertions": {
            "fixed_count_null": True,
            "interleaving_direction": True,
            "edge_order_invariance": True,
            "edge_weight_invariance": True,
            "year_swap_invariance": True,
            "between_cluster_edges_ignored": True,
            "exact_product_score": True,
        },
        "scientific_data_access": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
