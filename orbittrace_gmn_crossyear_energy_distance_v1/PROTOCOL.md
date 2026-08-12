# OrbitTrace GMN cross-year energy-distance representation v1

## Status

**PRE-OUTCOME FREEZE.** This protocol defines one target-excluded GMN 2022/2023 representation-level successor before implementation or first scientific evaluation.

## Motivation from permitted GMN evidence only

The candidate is motivated solely by target-excluded GMN development evidence:

1. The clean post-governance #1194 representative-share parent recovers `22/43/80/171` qualified shower labels at @25/@50/@100/@500 with top-100 dominant precision `0.8075287489258385`, MRR `0.02016666446026534`, and 256 qualified labels.
2. The separately frozen representative-share oracle diagnostic showed that the exact #1194 target and unchanged diversity operator reach `25/50/100/242` when the target is scored perfectly. Thus the current 80→100 gap is prediction/representation separability rather than candidate coverage or an intrinsic target/diversity ceiling.
3. The separately frozen member-scatter representation v1 added the complete per-year 4×4 residual second-moment tensor. It improved @25 and @50 but failed overall (`23/45/79/168`) and is closed. That experiment shows simple directional second-order morphology contains some signal but does not solve the gap.
4. The parent 34D representation contains annual centroid consistency and scalar radial member-cohesion summaries, but it does not directly measure whether the **full within-family member distribution has the same shape across 2022 and 2023 after annual centroid alignment**.
5. The historical cycle-consistent partial-transport Stage-0 is not this method: it matched individual events across multi-year local scenes using selected matching radii and connected components. This candidate performs no event matching, radius selection, optimal transport, component construction, or synthetic-scene training.

No SonotaCo 2013/2014 outcome, identity, rank, literature gap, missed family, or exposed transfer result is used to define or select this successor.

## Immutable parent

Use exactly the #1194 target-excluded GMN 2022/2023 union and learning/ranking machinery:

- hard families: 226;
- P19 families: 1,075;
- P20 families: 3,203;
- union: 4,504 unique families;
- eligible recurrent labels: 355;
- qualified labels: 256;
- exact #1194 source Git blob: `340f9d54b42ba2500652d7f0a74f22bbd3354f2e`;
- exact #839 34-dimensional parent feature matrix;
- exact #1194 representative-share target;
- exact deterministic whole-shower five-fold OOF assignment;
- exact grouped sample weights;
- exact `ExtraTreesRegressor(n_estimators=600, max_depth=4, min_samples_leaf=5, max_features=None, random_state=20260809)`;
- exact diversity operator `lambda=0.8`, `scale=1.0` and unchanged ties.

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

## Sole new representation feature

Append exactly **one** label-free scalar feature to the exact 34D parent matrix, yielding a 35D successor matrix.

For each family and each year separately, represent every existing member event by the same four-dimensional physically normalized residual vector about that family's frozen annual centroid:

1. circular solar-longitude residual `delta_sol / 10 deg`;
2. circular Sun-centered ecliptic-longitude residual `delta_sun_lon / 4 deg`;
3. ecliptic-latitude residual `delta_ecl_lat / 4 deg`;
4. logarithmic geocentric-speed residual `log(vg_event / vg_centroid) / log(1.10)`.

The scales are exactly the inherited physical scales already used by the frozen detector/#839 centroid geometry; they are not selected in this experiment.

Let `X` be the complete 2022 residual-vector set and `Y` the complete 2023 residual-vector set for the family. Define the single feature as the standard empirical multivariate **energy distance statistic** between the two empirical distributions:

`E(X,Y) = 2 mean_{x in X, y in Y} ||x-y||_2 - mean_{x,x' in X} ||x-x'||_2 - mean_{y,y' in Y} ||y-y'||_2`.

The within-year means include all ordered pairs, including diagonal self-pairs, so this is the deterministic V-statistic of the two empirical distributions. No square root, clipping, bias correction, sample-size normalization, bandwidth, radius, matching, optimal-transport solver, or learned parameter is used.

Every family must have at least one member event in both years; otherwise execution fails closed as a technical no-result rather than imputing the feature.

The energy-distance table must be computed from target-excluded event coordinates and family memberships before and independently of GMN shower truth/targets.

## Scientific question

This successor tests exactly one hypothesis: **cross-year distribution-shape consistency contains quality information that is lost by centroid distance, scalar radial cohesion, and per-year second moments**.

Unlike the failed second-moment augmentation, the energy statistic compares complete empirical distributions and can respond to distributional changes not reducible to a covariance tensor. Unlike partial transport, it does not establish event correspondences or select a distance radius.

## Binding evaluation

Run exactly the same strict whole-shower OOF evaluation twice in the same binding execution:

1. exact 34D #1194 parent control;
2. sole 35D parent + cross-year energy-distance successor.

The first technically valid execution is binding.

PASS requires **all**:

- recovered@100 **> 80**;
- recovered@50 **>= 43**;
- recovered@25 **>= 22**;
- recovered@500 **>= 171**;
- top-100 dominant precision **>= 0.8075287489258385**;
- MRR **>= 0.02016666446026534**;
- qualified matches **== 256**.

A PASS freezes exactly this one-feature representation with the unchanged #1194 learning/ranking machinery. It does not authorize additional distributional features or SonotaCo execution.

A FAIL permanently closes this exact cross-year centered-residual energy-distance augmentation. Do not rescue it with:

- coordinatewise energy distances;
- alternate norms or powered distances;
- square-root/normalized/bias-corrected variants;
- bandwidth-based MMD/kernel features;
- Wasserstein/optimal-transport variants chosen from this result;
- matching-radius features;
- within-year dispersion additions;
- member-scatter combinations or fusion;
- source-specific distribution features;
- feature subsets/interactions;
- estimator/hyperparameter changes;
- target or diversity changes;
- post-result feature or parameter searches.

Any later successor must be genuinely distinct and separately frozen before outcome.

## Required guards

Before scientific interpretation, execution must verify:

- exact #1194 source Git blob and parent metrics/order;
- exact #839 ranker source SHA-256 `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`;
- exact v8/P19/P20 input hashes;
- exact 4,504 family IDs and source counts;
- parent feature shape `(4504,34)`;
- energy feature shape `(4504,1)`;
- successor feature shape `(4504,35)`;
- all energy values finite;
- all feature construction occurs before family truth/target use;
- strict shower-group OOF isolation remains exact;
- family memberships/candidate identity remain unchanged.

## Protected-data firewall

Throughout execution:

- protected solar-longitude `[20.0,55.0]` remains excluded before labels, features, folds, scores and endpoints;
- `sonotaco_2013_2014_access = false`;
- `sonotaco_feature_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`.

This protocol authorizes only target-excluded GMN 2022/2023 development.