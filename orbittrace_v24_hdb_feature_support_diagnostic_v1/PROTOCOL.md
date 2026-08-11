# OrbitTrace v24 HDB 71D training-support geometry diagnostic v1

## Scientific role

Post-result diagnostic only. No successor method, score, order, feature subset, threshold, or parameter is selected here.

The exact v24 annual-regression lineage remains the strongest trustworthy exposed-SonotaCo baseline on HDBSCAN. Later objective variants (binary conjunction, annual binary, four-state, group-dense, pairwise, and equal-rank fusions) failed to beat HDBSCAN. PR #1018 further showed that the frozen radius-1.0 graph is high-purity structural evidence but is neither necessary nor sufficient for v24 top-budget recovery. The unresolved question is therefore whether v24's missed high-quality HDB families are poorly supported in the frozen 71D representation itself, or whether close high-quality training analogs exist but the learned ranker fails to use them.

## Frozen diagnostic geometry

Use the exact immutable PR #950 v22 71D feature matrices, memberships, family identities, and truth definitions. Reproduce the exact v24 strict whole-shower five-fold OOF regression/final HDB order first; if the exact HDB 2013/2014 v24 metrics do not reproduce, the diagnostic is invalid.

For each deterministic OOF fold:

1. compute the arithmetic mean and population standard deviation (`ddof=0`) of each of the 71 features using **training-fold examples only**, pooling the same Sugar+HDBSCAN training examples used by v24;
2. replace only exactly-zero standard deviations with `1.0`; no variance floor, clipping, robust transform, feature weighting, or feature selection is allowed;
3. z-score both training examples and held-out examples with those training-fold statistics;
4. use ordinary Euclidean distance in all 71 standardized dimensions.

For each year separately, define an annual-positive training family exactly as `annual F1 > 0.5` for the unchanged v22 fixed best label. The 0.5 threshold is the pre-existing literature recovery criterion, not selected here. Annual-nonpositive training families are all remaining training families.

For every annual-positive HDB held-out family, record:

- nearest annual-positive training distance;
- nearest annual-nonpositive training distance;
- support margin = `nearest_negative_distance - nearest_positive_distance`;
- whether it is closer to a positive than to a negative training example;
- identity, route, and strict shower group of both nearest references.

Because the exact whole-shower fold holds all same-shower Sugar/HDB fragments out together, the nearest positive reference must come from a different strict shower group; this is asserted explicitly.

## Group-level comparison

For each HDB annual-recoverable strict shower group, choose exactly one diagnostic representative: the annual-positive family from that group with the earliest rank in the exact reproduced v24 final HDB order (ties by stable family ID). Mark the group `surfaced` iff that representative rank is within the already-frozen HDB comparator budget (11 in 2013, 9 in 2014).

Compare surfaced and missed group representatives using only predeclared summaries:

- group count;
- median and 90th percentile nearest-positive distance;
- median nearest-negative distance;
- median support margin;
- count and fraction closer to positive than negative support;
- median reproduced v24 representative rank.

All annual-positive family rows and all recoverable-group representative rows are retained in the artifact. No distance cutoff, significance threshold, clustering, feature attribution, nearest-k choice, alternate metric, or post-result subgroup selection is permitted.

## Interpretation boundary

This diagnostic may support only a broad mechanistic conclusion:

- substantially weaker positive-neighbor support among missed groups would support a **representation/training-support limitation** hypothesis;
- comparable positive-neighbor support for surfaced and missed groups would support a **model discrimination/ranking limitation despite available representation support** hypothesis;
- mixed results remain mixed and do not authorize a successor automatically.

No successor is selected or evaluated by this PR. Any later method change must be separately frozen after this diagnostic.

SonotaCo 2013/2014 remains exposed development-only. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar-longitude 20°–55° content remain inaccessible.