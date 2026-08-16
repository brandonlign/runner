# OrbitTrace Persistable persistence-ladder candidate audit v1

Synthetic-only feasibility audit; no meteor data or target information may be accessed.

Pinned upstream: `LuisScoccola/persistable@7eb75b2e8d2fe5a18e49248aa7d1c97f829415be`.

## Candidate architecture

For each point cloud:

1. `Persistable(X, n_neighbors="auto", n_jobs=1)`, uniform measure, Euclidean metric.
2. Obtain exact package `_find_end()` and `compute_defaults()`.
3. Use the package-default **midpoint slice** (`X/Y_START_LINE`, `X/Y_END_LINE`). No vineyard and no gap selection.
4. Construct that one hierarchical clustering once with `lambda_linkage(start,end)`.
5. Let `B` be the number of strictly positive-persistence bars in its persistence diagram.
6. For every requested cluster count `g = 2..min(15,B)`, compute the package conservative persistence flattening using its exact `_compute_threshold(g)`; `keep_low_persistence_clusters=False`.
7. From every flattening retain non-noise memberships with at least 4 points and take the exact-membership union across all `g`. No ranking or preferred `g` exists.

The ladder is bounded by the package-default 15-vine display limit. Count 1 is excluded as the trivial single-root partition.

## Synthetic panel

Reuse exactly the four nested 6,144→768 four-dimensional synthetic replicates frozen in `orbittrace_persistable_auto_selector_audit_v1` (same centers, weights, variances, uniform background, PCG64 seeds `202608160..163`). Truth is secondary only.

## Symmetric coherence

Restrict dense candidates to the sparse universe, dropping restricted memberships below 4. Compute:

- sparse→dense mean best Jaccard;
- restricted-dense→sparse mean best Jaccard;
- symmetric score = arithmetic mean of those two directional means.

Extra unmatched candidates therefore reduce the score rather than automatically helping.

## Frozen gates

PASS only if every replicate:

1. dense and sparse candidate sets are nonempty;
2. both sets contain at most 119 candidates (`sum(2..15)` hard architectural ceiling before deduplication);
3. symmetric cross-scale mean-best-Jaccard >= `0.60`;
4. each directional mean-best-Jaccard >= `0.50`;
5. no invalid slice/persistence value, insufficient-neighbor warning, exception, manual choice, alternate flattening, or fallback occurs.

A PASS authorizes one separately frozen zero-label target-excluded GMN diagnostic against recurrent-EOM. A FAIL closes this exact default-midpoint persistence-ladder architecture and all changes to its slice, ladder range, support, neighbor policy, flattening, synthetic panel/seeds, coherence metric, and gates.