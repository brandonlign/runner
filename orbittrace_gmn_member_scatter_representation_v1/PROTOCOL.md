# OrbitTrace GMN member-scatter representation v1

## Status

**PRE-OUTCOME FREEZE.** This protocol defines one target-excluded GMN 2022/2023 representation-level successor before implementation or first scientific evaluation.

## Motivation from permitted GMN evidence only

The candidate is motivated only by target-excluded GMN development evidence:

1. PR #1194 is the clean post-governance representative-share parent on the fixed 4,504-family union. It recovers `22/43/80/171` qualified shower labels at @25/@50/@100/@500 with top-100 dominant precision `0.8075287489258385`, MRR `0.02016666446026534`, and 256 qualified labels.
2. The separately frozen representative-share oracle diagnostic v1 showed that the **exact frozen #1194 target and exact unchanged diversity operator reach the known 100@100 ceiling when the target is scored perfectly**: `25/50/100/242`, precision `0.897219089102914`, MRR `0.023595698250011923`. Therefore the present 80→100 gap is prediction/separability, not candidate coverage or an intrinsic target/diversity ceiling.
3. The exact #1194/#839 34-dimensional representation already contains structural counts/scores, cross-year centroid location/consistency, seven scalar member-cohesion summaries, source indicators, P20 summaries, and six centroid-neighborhood density descriptors. Its member-level geometry is compressed primarily to scalar radial distances (median, q90, maximum and year-q90 maximum). It does **not** retain the directional second-order scatter of member residuals within each year.
4. The prior real-shower Deep Sets Stage-0 and InvariantStreamNet experiments are not predecessors of this candidate: they were local 128-event/48-event window detectors for stream presence/member segmentation, not ranking representations for the already-generated GMN family union. Both are preserved failures and are not being rescued. This candidate introduces no synthetic stream training, episode construction, attention, segmentation, neural architecture, or window detector.

No SonotaCo 2013/2014 result, identity, literature gap, rank, missed family, or exposed transfer outcome is used to define this successor.

## Immutable parent

Use exactly the PR #1194 family universe, truth semantics, folds, target, weights, estimator and diversity machinery:

- years: 2022 and 2023 only;
- protected solar-longitude interval `[20.0,55.0]` excluded before labels, features, folds and scores;
- hard families: 226;
- P19 soft families: 1,075;
- P20 soft families: 3,203;
- union: 4,504 unique families;
- eligible recurrent labels: 355;
- qualified labels: 256;
- exact #1194 source Git blob: `340f9d54b42ba2500652d7f0a74f22bbd3354f2e`;
- exact #839 34-dimensional parent feature matrix construction;
- exact representative-share target `y_share = q_i / sum_G q` within every recoverable shower group, zero otherwise;
- exact deterministic whole-shower OOF folds;
- exact #839 grouped sample weights;
- exact `ExtraTreesRegressor(n_estimators=600, max_depth=4, min_samples_leaf=5, max_features=None, random_state=20260809)`;
- exact diversity operator `lambda=0.8`, `scale=1.0` and exact tie semantics.

The exact parent must reproduce before the successor is interpreted:

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

Append exactly **20 label-free member-scatter features** to the exact 34 parent features, giving a fixed 54-dimensional matrix.

For each family and each year separately, use the family's existing event members and the exact existing event lookup. For an event `e` and that family's frozen year centroid `c`, define the four-dimensional physical residual vector:

1. circular solar-longitude residual `delta_sol / 10 deg`;
2. circular Sun-centered ecliptic-longitude residual `delta_sun_lon / 4 deg`;
3. ecliptic-latitude residual `delta_ecl_lat / 4 deg`;
4. logarithmic geocentric-speed residual `log(vg_e / vg_c) / log(1.10)`.

These scales are not newly tuned; they are the exact physical scales already inherited by the frozen detector/#839 centroid distance.

For each year, compute the **uncentered second moment about the frozen family centroid**

`S_y = mean_e (r_e r_e^T)`

across that year's member events. Because residuals are defined about the already-frozen family centroid, no label-dependent or learned centering is permitted.

Flatten the ten unique upper-triangular elements of `S_y` in this exact order:

- `(0,0)`
- `(0,1)`
- `(0,2)`
- `(0,3)`
- `(1,1)`
- `(1,2)`
- `(1,3)`
- `(2,2)`
- `(2,3)`
- `(3,3)`

Append the ten 2022 entries followed by the ten 2023 entries.

No eigenvalue transform, determinant, trace, Frobenius norm, cross-year difference, quantile, skewness, kurtosis, clipping, robust covariance estimator, shrinkage, PCA, rotation, feature selection, interaction, source-specific feature, or alternative physical scale is evaluated in this lane.

The second moment uses denominator `n`, not `n-1`, so the definition is deterministic for every nonempty year-member set and does not require a sample-covariance correction. Every family must have at least one member in each year; otherwise execution fails closed as a technical no-result rather than inventing an imputation rule.

## Scientific interpretation

The new representation tests one specific hypothesis: **directional member morphology contains predictive information about family quality that is lost by the parent representation's scalar radial cohesion summaries**.

Examples of information now represented without label use include anisotropy and coordinate coupling: a coherent family elongated mainly along solar-longitude/radiant drift can differ from a diffuse accidental family even when their median or q90 radial distance is similar.

This is not an estimator rescue: estimator class, depth, leaf size, tree count, target, weights, folds and diversity are unchanged. The only scientific change is the 20-dimensional label-free member-scatter representation.

## Binding evaluation

Run exactly the same five whole-shower OOF folds twice in the same binding execution:

1. exact 34D #1194 parent control;
2. sole 54D member-scatter successor.

The first technically valid execution is binding.

PASS requires **all**:

- recovered@100 **> 80**;
- recovered@50 **>= 43**;
- recovered@25 **>= 22**;
- recovered@500 **>= 171**;
- top-100 dominant precision **>= 0.8075287489258385**;
- MRR **>= 0.02016666446026534**;
- qualified matches **== 256**.

A PASS freezes exactly this 54D representation with the already-frozen #1194 learning/ranking machinery. It does not authorize feature pruning, representation expansion, estimator search, or SonotaCo execution.

A FAIL permanently closes this exact physical residual second-moment augmentation. Do not rescue it with:

- alternate covariance/scatter normalization;
- robust/shrunk covariance;
- eigenvalues/eigenvectors;
- trace/determinant/anisotropy ratios;
- different residual scales;
- marginal quantiles or higher moments;
- source-specific scatter features;
- representation subsets;
- estimator/hyperparameter changes;
- target changes or blends;
- diversity changes;
- score fusion with the parent;
- post-result feature selection.

A later representation successor must be genuinely distinct and separately frozen before outcome.

## Required provenance and leakage guards

Before interpretation, execution must verify:

- exact #1194 scientific source Git blob;
- exact #839 quality source SHA-256 `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`;
- exact P19/P20/v8 input hashes;
- exact 4,504 family IDs and source counts;
- exact 34D parent feature shape;
- exact appended feature shape `(4504,20)` and successor shape `(4504,54)`;
- all scatter values finite;
- every scatter feature is computed before and independently of GMN shower truth/targets;
- same shower group is wholly contained in one OOF fold;
- exact #1194 parent metrics and order reproduce;
- no family membership or candidate identity is changed.

## Protected-data firewall

Throughout execution:

- protected solar longitude `[20.0,55.0]` remains excluded before labels, features, folds, scores and endpoints;
- `sonotaco_2013_2014_access = false`;
- `sonotaco_feature_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`.

This protocol authorizes only target-excluded GMN 2022/2023 development.