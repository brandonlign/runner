# OrbitTrace GMN member-cloud MST bottleneck topology v1

## Status

**PRE-OUTCOME FREEZE.** This protocol defines one target-excluded GMN 2022/2023 representation-level successor before implementation and before its first scientific evaluation.

## Scientific motivation

The exact #1194 representative-share parent on the immutable 4,504-family union recovers `22/43/80/171` qualified labels at @25/@50/@100/@500 with top-100 dominant precision `0.8075287489258385`, MRR `0.02016666446026534`, and 256 qualified labels.

The live lineage has already closed a wide set of nearby member-geometry representations:

- scalar radial member-cohesion summaries are already part of the 34D parent;
- 20D directional second moments/covariance shape failed, and that lane closes covariance/scatter normalizations, eigen summaries, marginal quantiles and higher moments;
- cross-year energy distance failed and closes energy/MMD/kernel/optimal-transport/member-scatter rescue variants;
- event-level nearest-competitor distance margin and categorical competitor-identity collision probability both failed their binding all-metric promotion gates;
- simple member-instance pooled regression reached a preregistered exact-event leakage blocker before metrics and cannot be rescued by weakening that purge;
- local-background density, cross-generator graph spacing, thinning stability, robust scaling, survey-relative transforms, survey weighting, and pairwise-ranking lanes are already closed.

One geometrically distinct information class remains untested in the repository: **connectivity topology of the within-family member cloud**. A point cloud can have nearly identical radial moments or covariance while differing strongly in whether it is connected through one long bridge between subclouds. Minimum-spanning-tree / single-linkage connectivity is a standard representation of zero-dimensional hierarchical topology and is conceptually distinct from fixed covariance moments or global two-sample distribution distances. The design is motivated by general hierarchical-clustering and persistent-connectivity literature (e.g. Carlsson & Mémoli, JMLR 2010; Rolle & Scoccola, JMLR 2024), not by any SonotaCo comparator outcome.

This experiment does **not** run HDBSCAN/DBSCAN, estimate core density, alter candidate generation, or tune a radius. It adds one fixed dimensionless connectivity statistic per year to the exact #1194 family representation.

No SonotaCo 2013/2014 result, literature-comparator miss, OrbitTrace target information, protected target-region event, MAARSY, or DMS information is used to define this successor.

## Immutable parent

Use exactly the #1194 target-excluded GMN 2022/2023 ranking line:

- hard families: 226;
- P19 families: 1,075;
- P20 families: 3,203;
- union: 4,504 unique candidate families;
- exact #1194 scientific source Git blob: `340f9d54b42ba2500652d7f0a74f22bbd3354f2e`;
- exact #839 34D parent feature matrix;
- exact representative-share target `y_share`;
- exact deterministic whole-shower five-fold OOF assignment;
- exact grouped family weights;
- exact `ExtraTreesRegressor(n_estimators=600, max_depth=4, min_samples_leaf=5, max_features=None, random_state=20260809)` from frozen `qmod.model()`;
- exact diversity operator `lambda=0.8`, `scale=1.0`, and exact tie semantics;
- unchanged family IDs, memberships, annual centroids, candidate universe, and evaluator.

Before successor interpretation, the parent must reproduce exactly:

- recovered@25 = 22;
- recovered@50 = 43;
- recovered@100 = 80;
- recovered@500 = 171;
- top-100 dominant precision = `0.8075287489258385`;
- MRR = `0.02016666446026534`;
- qualified matches = 256;
- parent order SHA-256 = `a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592`.

Any mismatch is a technical no-result.

## Sole new representation

Append exactly **two label-free features**, one for 2022 and one for 2023, to the exact 34D parent, giving a fixed 36D successor matrix.

### Four-dimensional member residual point cloud

For each family `F` and year `y`, sort that year's actual member event IDs lexicographically. For each member event `e`, compute its signed residual from `F`'s frozen annual centroid in exactly the inherited physical coordinates:

1. circular solar-longitude residual wrapped to `[-180,180)` and divided by 10 degrees;
2. circular Sun-centered ecliptic-longitude residual wrapped to `[-180,180)` and divided by 4 degrees;
3. ecliptic-latitude residual divided by 4 degrees;
4. logarithmic geocentric-speed residual `log(|vg_e|/|vg_c|) / log(1.10)`, with numerical floor `1e-12` applied separately to the event and centroid speed magnitudes.

Use ordinary Euclidean distance in this fixed 4D residual coordinate system.

These coordinates/scales are inherited and immutable; no feature rescaling, whitening, covariance transform, robust transform, or learned metric is permitted.

The entire topology feature table must be computed from target-excluded event observables, immutable memberships, and immutable annual centroids **before** shower truth/targets are used.

### Deterministic MST

For each family-year point cloud with `n` members, construct a deterministic Euclidean minimum spanning tree by Prim's algorithm:

- vertex order is the lexicographically sorted event-ID order;
- start from vertex index 0;
- at each step select the unvisited vertex with smallest current connection distance;
- exact distance ties are resolved by the smallest vertex index;
- when updating a vertex's current best connection, replace it only on a strictly smaller distance, so existing equal-distance parents remain fixed.

This deterministic rule is an implementation/provenance guard; the scientific statistic depends only on MST edge lengths.

### Annual bottleneck-share statistic

If `n = 1`, define the annual statistic `B_y = 0.0` because there is no finite H0 merge/death edge.

If `n >= 2`, let the MST edge lengths be `l_1,...,l_(n-1)` and define:

`B_y = max_i(l_i) / sum_i(l_i)`

when `sum_i(l_i) > 0`.

If all MST edge lengths are exactly zero, define `B_y = 0.0`.

Thus `B_y` lies in `[0,1]`. It measures the fraction of total tree connectivity carried by the single largest bridge. A cloud containing two internally coherent subclouds connected by one long bridge can have a larger `B_y` than a similarly scaled cloud whose connectivity is distributed more uniformly.

Append exactly `[B_2022, B_2023]` in that order.

No total MST length, mean/median/q90 edge, second-largest edge, edge-count transform, entropy, coefficient of variation, normalized-by-n statistic, persistence diagram vectorization, cycle/higher-dimensional homology, thresholded component count, or cross-year min/mean/max/difference is computed or evaluated in this lane.

## Scientific question

Does **within-family connectivity topology**, specifically single-bridge dominance in the member cloud, carry family-quality information that is absent from the 34D structural/radial representation and from failed covariance/distribution summaries?

This is deliberately a representation-only test. Candidate generation, target, learner, folds, family weights, diversity and evaluation remain unchanged.

## Binding evaluation and promotion gate

The first technically valid execution is binding.

In the same execution run:

1. exact 34D #1194 parent OOF control;
2. sole 36D parent + two annual MST bottleneck-share features.

PASS requires **all**:

- recovered@100 **> 80**;
- recovered@50 **>= 43**;
- recovered@25 **>= 22**;
- recovered@500 **>= 171**;
- top-100 dominant precision **>= 0.8075287489258385**;
- MRR **>= 0.02016666446026534**;
- qualified matches **== 256**.

A PASS freezes exactly this 36D representation with the unchanged #1194 model/ranking machinery. It does not authorize SonotaCo execution; any transfer benchmark must be separately frozen under the current post-v60 governance rule.

A FAIL permanently closes this exact MST-bottleneck topology augmentation.

## Closed rescue space

A FAIL does not authorize:

- total/mean/median/quantile/standard-deviation/CV MST-edge features;
- second-largest edge, largest-to-second ratio, edge entropy, Gini, or alternate bottleneck normalization;
- normalization by `n`, `sqrt(n)`, dimension-based powers, radial scale, covariance scale, or family diameter;
- single-linkage cut counts at chosen thresholds;
- threshold/radius/k-neighbor searches;
- persistence-image/landscape/vectorization chosen from the result;
- H1/H2 cycles or higher-dimensional persistent homology chosen from the result;
- alternate linkage, mutual-reachability/core-distance/HDBSCAN-derived trees;
- source/year/subset-specific topology rules;
- feature subsets/interactions or combining this feature with failed margin/collision/scatter/energy/graph/background features;
- target/model/hyperparameter/fold/weight/diversity changes;
- parent-score blending or alternate parent rankers;
- post-result topology-statistic search.

Any later topology successor would require genuinely independent motivation and a separately frozen protocol rather than a variant selected from this outcome.

## Required provenance / leakage guards

Before interpretation, execution must verify:

- exact #1194 scientific source Git blob;
- exact #839 source/input hashes;
- exact 4,504 family IDs and source counts;
- parent feature matrix shape `(4504,34)`;
- topology feature matrix shape `(4504,2)`;
- successor feature matrix shape `(4504,36)`;
- every family member ID exists in the target-excluded scan;
- every family has at least one member in each year;
- all annual centroids/residual coordinates/pairwise distances/MST edge lengths/features are finite;
- deterministic event-ID sorting and Prim tie rules are exact;
- feature table construction occurs before family truth/target use;
- whole-shower OOF groups/folds remain exact;
- parent metrics/order reproduce exactly;
- no family membership/candidate identity changes.

## Protected-data firewall

Throughout execution:

- protected solar longitude `[20.0,55.0]` remains excluded before memberships/features/folds/scores/endpoints;
- `sonotaco_2013_2014_access = false`;
- `sonotaco_feature_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`.

This protocol authorizes only target-excluded GMN 2022/2023 development.