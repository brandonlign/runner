# Final SonotaCo 2013/2014 truth-free comparator execution — v1

## Role

This layer converts a frozen pairwise shared SonotaCo manifest into the **primary pre-truth catalogue output** for the exact frozen Sugar and catalogue-HDBSCAN comparators. It performs no archive download, known-shower mapping, scientific evaluation, target lookup, or result-based filtering.

It is frozen before any SonotaCo 2013/2014 scientific value is opened.

## Exact source identity

Execution must load the already-audited decoded source modules and attach their verified byte hashes as `__source_sha256__` before this adapter may call them:

- Sugar core SHA-256 `5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb`;
- catalogue-HDBSCAN source SHA-256 `a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2`.

The adapter fails closed on source-identity drift.

## Sugar

The adapter calls the exact frozen Sugar functions/classes rather than reproducing their internals:

- `feature_matrix_from_equatorial`;
- `transferred_epsilon`;
- `clone_feature_matrix`;
- `dbscan_clusters`;
- `OverlapGraphMerger`;
- `hard_assignment`.

Frozen constants are checked at runtime: min samples 5, epsilon percentile 23, 1000 clone iterations, 0.5 overlap, minimum recurrence 100, strong recurrence 500, seed root 20170209.

The input rows must already satisfy the exact final #820 Sugar pairwise rule, which is also rechecked at execution: multi-camera/base validity, **strict convergence angle `qc > 15°`**, finite nonnegative RA/Dec/Vg uncertainty, and **`vg_sd <= 0.10*vg + 1.0 km/s`**. Zero uncertainty is a valid zero-width Gaussian; negative uncertainty is rejected.

The remaining deterministic seed identities are fixed pre-data as:

- corpus namespace: `sonotaco-final-label-free-sugar-v1`;
- comparator-pair identifier: `ORBITTRACE_VS_SUGAR`.

Each clone seed is the exact frozen-core call:

`stable_seed(20170209, "sonotaco-final-label-free-sugar-v1", year, "ORBITTRACE_VS_SUGAR", iteration)`

Both strings are frozen before final-year scientific access and may not change afterward.

The primary Sugar catalogue is the exact recurrence>=100 `hard_assignment` output. Families contain exactly the event IDs assigned to each nonnegative native label. Probabilities are recorded diagnostically but do not alter membership.

## Catalogue HDBSCAN

The adapter calls the exact frozen runner's `feature_matrix` and `run_hdbscan` functions after rows have already passed the exact pairwise physical-quality predicate in the shared normalizer.

It verifies min cluster size 100 and HDBSCAN version 0.8.44. All non-noise native labels become primary catalogue families with their exact assigned event IDs.

## Truth firewall

The adapter rejects input records containing truth-bearing keys such as shower/label/reference/background designations. Only years 2013 and 2014 are accepted, one year at a time, with unique stable event IDs.

Output family IDs are deterministic hashes of the frozen member-ID sets. Native comparator labels remain recorded. This naming operation does not merge, split, rank, suppress, or otherwise change comparator membership.

No known-shower truth may open until these outputs and their source/input hashes are frozen by the final execution workflow.