#!/usr/bin/env python3
from __future__ import annotations

import json

import numpy as np

from knn_year_mixing import candidate_knn_mixing, mixed_score


def req(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    # Same fixed geometry, different year assignments. On a one-dimensional
    # local graph, alternating labels should mix more strongly than segregated
    # labels at the same fixed 4/4 annual counts.
    X = np.column_stack([
        np.arange(8, dtype=float),
        np.zeros(8),
        np.zeros(8),
        np.zeros(8),
        np.zeros(8),
        np.zeros(8),
    ])
    segregated = np.asarray([2022, 2022, 2022, 2022, 2023, 2023, 2023, 2023])
    interleaved = np.asarray([2022, 2023, 2022, 2023, 2022, 2023, 2022, 2023])
    seg = candidate_knn_mixing(X, segregated, k_base=2)
    mix = candidate_knn_mixing(X, interleaved, k_base=2)
    req(seg.member_count == mix.member_count == 8, "member count changed")
    req(seg.year_counts == mix.year_counts == (4, 4), "fixed annual counts changed")
    req(seg.k == mix.k == 2, "synthetic k changed")
    req(seg.directed_edges == mix.directed_edges == 16, "directed edge count wrong")
    req(abs(seg.expected_cross_year_edges - mix.expected_cross_year_edges) < 1e-15,
        "fixed-count null expectation depends on label arrangement")
    req(mix.cross_year_edges > seg.cross_year_edges, "alternating years should create more local cross-year edges")
    req(mix.mixing_enrichment > seg.mixing_enrichment, "alternating years should receive higher enrichment")

    # Swapping year names cannot change the statistic.
    swapped = np.where(interleaved == 2022, 2023, 2022)
    mix_swapped = candidate_knn_mixing(X, swapped, k_base=2)
    req(mix_swapped == mix, "year-name swap changed the mixing statistic")

    # With a complete directed graph (k=n-1), observed and fixed-count expected
    # cross-year edge counts are identical for every arrangement, so M=1.
    X5 = np.column_stack([
        np.asarray([0.0, 1.0, 2.0, 4.0, 8.0]),
        np.zeros(5), np.zeros(5), np.zeros(5), np.zeros(5), np.zeros(5),
    ])
    years5 = np.asarray([2022, 2022, 2023, 2023, 2023])
    complete = candidate_knn_mixing(X5, years5, k_base=10)
    req(complete.k == 4 and complete.directed_edges == 20, "complete-graph fixture changed")
    req(abs(complete.mixing_enrichment - 1.0) < 1e-15, "complete directed graph must have enrichment exactly one")

    # One-year candidates are explicitly assigned zero enrichment, not NaN or
    # an inferred pseudo-signal.
    one_year = candidate_knn_mixing(X5, np.full(5, 2022), k_base=10)
    req(one_year.year_counts == (5, 0), "one-year count encoding changed")
    req(one_year.expected_cross_year_edges == 0.0, "one-year null expectation must be zero")
    req(one_year.mixing_enrichment == 0.0, "one-year candidate must receive zero enrichment")

    req(abs(mixed_score(0.2, 1.75) - 0.35) < 1e-15, "frozen product score changed")
    req(mixed_score(0.0, 100.0) == 0.0, "zero recurrent stability must remain zero")

    result = {
        "verdict": "PASS_RECURRENT_EOM_KNN_YEAR_MIXING_V1_SYNTHETIC_AUDIT",
        "segregated": seg.__dict__,
        "interleaved": mix.__dict__,
        "complete_graph": complete.__dict__,
        "one_year": one_year.__dict__,
        "assertions": {
            "interleaving_direction": True,
            "fixed_count_expectation": True,
            "year_swap_invariance": True,
            "complete_graph_null_identity": True,
            "one_year_zero_enrichment": True,
            "exact_product_score": True,
        },
        "scientific_data_access": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
