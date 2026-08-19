#!/usr/bin/env python3
from __future__ import annotations

import math
from typing import Any

import numpy as np

import run_benchmark as benchmark


def sugar_candidate_output_exact(
    rows: list[dict[str, Any]],
    source: Any,
    percentile: float,
    clones: int,
    seed_tag: str,
) -> list[dict[str, Any]]:
    """Run the frozen Sugar uncertainty machinery exactly, varying only the
    preregistered dataset-level epsilon percentile and clone count.

    The frozen source supplies the 4th-neighbour distances, DBSCAN implementation,
    clone generator, overlap graph, and hard assignment.  Development uses a
    clone-count-scaled 10% recurrence floor; selected configurations are rerun at
    the source-native 1000-clone / 100-recurrence scale before test scoring.
    """
    sol, ra, dec, vg, ra_sd, dec_sd, vg_sd = benchmark.sugar_arrays(rows)
    observed = np.asarray(source.feature_matrix_from_equatorial(sol, ra, dec, vg), dtype=float)
    benchmark.req(observed.shape[0] == len(rows), "Sugar feature row mismatch")
    _native_eps, fourth_neighbor = source.transferred_epsilon(observed)
    eps = float(np.percentile(np.asarray(fourth_neighbor, dtype=float), float(percentile)))
    benchmark.req(math.isfinite(eps) and eps > 0.0, "invalid Sugar epsilon")

    merger = source.OverlapGraphMerger(len(rows))
    for iteration in range(int(clones)):
        seed = source.stable_seed(
            20170209,
            "orbittrace-symmetric-fair-v2",
            20132014,
            seed_tag,
            iteration,
        )
        features = source.clone_feature_matrix(
            sol, ra, dec, vg, ra_sd, dec_sd, vg_sd, seed=seed
        )
        merger.add_iteration(iteration, source.dbscan_clusters(features, eps))

    masters = merger.finalize()
    minimum_recurrence = max(1, int(round(int(clones) * 0.10)))
    labels, probabilities = source.hard_assignment(
        len(rows), masters, minimum_recurrence=minimum_recurrence
    )
    labels = np.asarray(labels, dtype=int)
    probabilities = np.asarray(probabilities, dtype=float)
    return benchmark.families_from_labels(
        labels,
        rows,
        "SUGAR2",
        probabilities,
        np.ones(len(rows), dtype=float),
    )


benchmark.sugar_candidate_output = sugar_candidate_output_exact
raise SystemExit(benchmark.main())
