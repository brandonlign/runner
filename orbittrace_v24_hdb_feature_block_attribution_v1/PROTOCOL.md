# OrbitTrace v24 HDB 71D feature-block attribution diagnostic v1

## Scientific role

Post-result diagnostic only. PR #1021 established that exact-v24 missed annual-recoverable HDB shower groups have weaker nearest-positive support in the full frozen 71D representation, especially in 2014. This diagnostic asks only which already-defined feature blocks contribute to that full-space support gap. It does not select a successor, feature subset, score, rank, metric, threshold, or parameter.

## Immutable inputs and replay

Use the exact immutable PR #950 v22 71D pretruth feature matrices, memberships, family identities, and truth definitions. Reproduce the exact v24 strict whole-shower five-fold OOF final HDB order and exact HDB 2013/2014 metrics before interpreting any diagnostic statistic.

The 71 features are partitioned exactly by their frozen construction order, with no regrouping:

- `raw_839`: columns 0:34 (34 dimensions);
- `relative_noncat_839`: columns 34:64 (30 dimensions);
- `rank_percentiles`: columns 64:67 (3 dimensions);
- `consensus_graph`: columns 67:71 (4 dimensions).

## Frozen attribution geometry

For each deterministic OOF fold, use the exact same training-fold arithmetic mean and population standard deviation (`ddof=0`) across all 71 dimensions as PR #1021; replace only exactly-zero standard deviations with 1.0. Use ordinary Euclidean distance in the complete standardized 71D space.

For each year separately, annual-positive means exact annual F1 > 0.5 for the unchanged v22 fixed best label. For every annual-positive held-out HDB family, identify exactly the same full-71D nearest annual-positive training reference as PR #1021. Same-shower references remain forbidden by the strict whole-shower fold.

For that single fixed nearest-positive reference only, decompose squared standardized distance into the four frozen feature blocks. For each block record:

- squared-distance contribution (sum of squared standardized differences in the block);
- contribution fraction of the complete 71D squared distance;
- RMS standardized difference, `sqrt(block_squared_distance / block_dimension)`.

No nearest reference is recomputed within a block. This is attribution of the already-defined full-space nearest-positive geometry, not a four-way feature-subset or metric comparison.

## Group-level comparison

Use the exact PR #1021 annual-recoverable group representative rule: the annual-positive HDB family from each strict shower group with the earliest exact-v24 final rank, stable family ID tie-break. A group is `surfaced` iff its representative rank is within the frozen HDB comparator budget (11 in 2013, 9 in 2014).

For surfaced and missed group representatives separately, report for each block only:

- median squared-distance contribution;
- median contribution fraction;
- median RMS standardized difference;
- 90th percentile RMS standardized difference.

Retain all per-family and group-representative attribution rows in the artifact.

## Interpretation boundary

This diagnostic may support only a mechanistic statement about where the already-observed 71D support gap resides. A larger missed-versus-surfaced RMS contribution in a block suggests that block contributes to the representation mismatch; comparable contributions imply the gap is distributed or lies elsewhere. No numeric cutoff defines "large", no block is promoted or removed here, and no feature-set successor is authorized automatically.

Any later representation change must be separately named and frozen after this result. No feature deletion, block weighting, block-only model, transformed distance, new rank, or literature evaluation occurs in this PR.

SonotaCo 2013/2014 remains exposed development-only. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar-longitude 20°–55° content remain inaccessible.
