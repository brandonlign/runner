# Recurrent-EOM latent-hierarchy residual diagnostic v1

## Purpose

This is a mechanism diagnostic only, not a successor detector or ranker. It follows the frozen recurrent-EOM residual decomposition (#1290), which classified 58/135 pooled panel misses as `CANDIDATE_GENERATION_FAILURE` because no selected recurrent-EOM candidate achieved F1 > 0.5 for those panel showers.

The diagnostic asks whether those apparent candidate-generation failures are truly absent from the exact pooled HDBSCAN hierarchy, or whether a recoverable branch exists in the condensed hierarchy but is not selected by recurrent-EOM EOM extraction.

## Immutable inputs and method

Use the exact SonotaCo label-free rows and recurrent-EOM parent identities from the binding benchmark:

- rows run `31354363306` with exact hashes already frozen in recurrent-EOM;
- parent recurrent-EOM pretruth SHA-256 `c6afbc0c3443b6c34e3f90b0f63453a0a35bfae3f3c84ffe8a479f8f50cffeef`;
- exact GEO6 + HDBSCAN `min_cluster_size=10`, `min_samples=10`, Euclidean metric;
- recurrent-EOM source blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`.

For each route (`sugar`, `hdbscan`), fit exactly one pooled 2013+2014 HDBSCAN hierarchy and verify that exact recurrent-EOM selected family memberships reproduce the immutable parent pretruth before accepting any hierarchy diagnostic.

## Latent hierarchy catalogue

Before shower truth or residual classifications are available, enumerate every condensed-tree **cluster node** whose recursive point-descendant membership contains at least 10 events. For each node persist only:

- node ID;
- complete sorted event-ID membership at node birth (all recursive point descendants);
- member count;
- ordinary HDBSCAN stability when available;
- recurrent annual-normalized stability when available;
- whether the node is selected by recurrent-EOM.

The complete latent-node catalogues for both routes must be persisted and hash-frozen before truth access.

No alternate tree cut, membership trimming, lambda threshold, persistence threshold, support change, candidate ranking, or post-truth node definition is permitted.

## Truth-stage diagnostic

After the complete latent hierarchy is frozen, restore:

1. the same immutable exposed SonotaCo truth used by recurrent-EOM's binding benchmark;
2. residual-analysis result SHA-256 `19a50655a5612e6ef00e40e0eba7c1793f5bfe298c68c082baf8b35af4856078` from run `31994209058`.

For each panel record whose frozen category is exactly `CANDIDATE_GENERATION_FAILURE`, evaluate every frozen latent node on that panel's truth universe using the same family-vs-shower F1 definition as the existing evaluator. Record the maximum latent-node F1 and its node ID/member count.

Classify each such miss as:

- `LATENT_TREE_EXTRACTION_FAILURE` iff max latent-node F1 > 0.5;
- `HIERARCHY_REPRESENTATION_FAILURE` otherwise.

No threshold other than the already-established recovered-shower criterion `F1 > 0.5` is introduced.

## Predeclared interpretation

Across the pooled panel-level 58 candidate-generation failures:

- if >= 50% are `LATENT_TREE_EXTRACTION_FAILURE`, the next method work should target extraction/pruning of the existing hierarchy rather than a new clustering geometry;
- if < 50%, the next method work should target hierarchy/candidate construction rather than EOM extraction.

This threshold is diagnostic guidance only; it does not promote a method.

## Firewall

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`. Protected `[20°,55°]`, OrbitTrace target information/events, AMOS, MAARSY and DMS remain inaccessible. No pristine endpoint is accessed.