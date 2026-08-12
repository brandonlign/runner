# OrbitTrace GMN member-instance pooled regression v1

## Status

**PRE-OUTCOME FREEZE.** This protocol defines one target-excluded GMN 2022/2023 hierarchical/member-instance successor before implementation and before its first scientific evaluation.

## Scientific motivation

The exact #1194 representative-share parent on the 4,504-family union recovers `22/43/80/171` qualified labels at @25/@50/@100/@500, with top-100 dominant precision `0.8075287489258385`, MRR `0.02016666446026534`, and 256 qualified labels.

Several frozen results constrain what remains scientifically open:

- scalar second-order member covariance/shape features failed #1194 and closed alternate covariance/scatter estimators, but its binding conclusion explicitly leaves a genuinely learned/higher-order representation as a distinct future mechanism;
- cross-year energy distance failed and closes energy/MMD/kernel/OT/member-scatter summary variants;
- annual member-exclusivity margin and categorical nearest-competitor collision probability both failed promotion, so their margin/identity-summary rescue spaces are closed;
- local-background, graph-spacing, thinning-stability, robust-scaling, catalogue-relative, domain-weighting, and pairwise-ranking lanes are already closed;
- repository audit before this freeze found no prior target-excluded GMN event-level / multiple-instance family regressor.

The remaining hypothesis tested here is therefore not another handcrafted family statistic. A meteor family is naturally an unordered bag of member events. The exact 34D #1194 family representation compresses that bag into fixed summaries. A shallow model trained on individual member residuals while retaining the 34D family context can, in principle, learn non-linear higher-order distribution structure that a fixed mean/covariance/energy summary misses.

This follows the general multiple-instance / set-learning principle that a bag-level quantity can be learned from instance-level evidence with a permutation-invariant aggregate. To minimize researcher degrees of freedom, this experiment uses the already-frozen #1194 ExtraTrees model and plain arithmetic mean pooling. No neural network, attention mechanism, hidden width, embedding dimension, pooling search, or hyperparameter search is introduced.

No SonotaCo result, literature-comparator miss, OrbitTrace target information, or protected-region event is used to define this successor.

## Immutable parent

Use exactly the #1194 target-excluded GMN union and ranking machinery:

- hard families: 226;
- P19: 1,075;
- P20: 3,203;
- union: 4,504;
- exact #1194 scientific source Git blob `340f9d54b42ba2500652d7f0a74f22bbd3354f2e`;
- exact 34D #839 family feature matrix;
- exact #1194 representative-share target `y_share`;
- exact deterministic whole-shower five-fold assignment;
- exact #1194 grouped family weights;
- exact `ExtraTreesRegressor(n_estimators=600, max_depth=4, min_samples_leaf=5, max_features=None, random_state=20260809)` returned by the frozen `qmod.model()`;
- exact diversity operator `lambda=0.8`, `scale=1.0`, and tie semantics;
- unchanged 4,504 family IDs, memberships, annual centroids, and evaluator.

The exact #1194 parent must reproduce in the binding execution:

- recovered@25 = 22;
- recovered@50 = 43;
- recovered@100 = 80;
- recovered@500 = 171;
- top-100 dominant precision = `0.8075287489258385`;
- MRR = `0.02016666446026534`;
- qualified matches = 256;
- parent order SHA-256 = `a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592`.

Any mismatch is a technical no-result.

## Sole new hierarchical representation/training unit

Each candidate family is a bag. Each actual family-member occurrence becomes one model row.

### Pretruth member residuals

For each actual member event `e` of family `F`, use the annual centroid of `F` corresponding to `e`'s year and compute exactly four signed normalized residual coordinates:

1. circular solar-longitude residual `(sol_e - sol_F)` wrapped to `[-180,180)` and divided by 10 degrees;
2. circular Sun-centered ecliptic-longitude residual wrapped to `[-180,180)` and divided by 4 degrees;
3. ecliptic-latitude residual divided by 4 degrees;
4. logarithmic geocentric-speed residual `log(|vg_e|/|vg_F|) / log(1.10)`, with the inherited numerical floor `1e-12` applied separately to absolute event and centroid speeds.

These are the same physical coordinate scales already inherited by the project. They are not selected or tuned here.

The residual table must be constructed only from target-excluded scan observables, immutable family memberships, and immutable annual centroids before family truth/targets are used.

No nearest-alternative distance, competitor identity, margin, background point, orbital element, shower label, or uncertainty field enters the new instance representation.

### 38D instance row

After the exact parent 34D family matrix is reproduced, each member occurrence receives exactly:

`[the family's frozen 34D row, the member's four signed normalized residuals]`.

Thus the instance matrix has exactly 38 columns. No source/year indicator, event ID encoding, family ID encoding, interaction term, moment, quantile, norm, distance, or additional summary is appended.

The event ID is retained only as a leakage-control key and never supplied to the learner.

## Strict OOF event-purging rule

Whole-shower family folds remain exactly the #1194 folds. Because the same observed event can occur in multiple overlapping candidate families, an additional deterministic leakage guard is required for instance-level training.

For each OOF fold:

1. test families are exactly families assigned to that #1194 fold;
2. collect the set of event IDs appearing in any test-family member row;
3. candidate training rows initially come from all non-test families;
4. remove every training row whose event ID is in the test-event set;
5. no test event ID may remain in training;
6. every training family must retain at least one row after purging, otherwise the execution is a technical no-result;
7. test-family predictions use all of their own member rows; test rows are not purged against one another.

There is no radius, similarity, or approximate purge. Identity equality is the only purge rule.

## Family-balanced instance weights

For a given fold, let family `F` have frozen parent family weight `w_F` and `m_F` retained training member rows after event-ID purging.

Every retained row from `F` receives weight exactly:

`w_F / m_F`.

Therefore the total training weight of every retained family is exactly its frozen #1194 family weight, regardless of membership size or purge count. No family is upweighted merely because it has more member events.

Each retained instance row receives the unchanged #1194 family target `y_share[F]`.

## Model and bag pooling

Fit the exact frozen `qmod.model()` on the retained 38D training instance rows and their repeated family targets with the family-balanced instance weights above.

Predict every member row of every held-out family.

The OOF family score is exactly the **unweighted arithmetic mean** of all predicted member-row scores belonging to that held-out family, across both years together.

No minimum, maximum, median, quantile, trimmed mean, year-balanced mean, attention weight, learned pooling, instance selection, threshold, top-k pooling, or family-size correction is permitted.

The resulting 4,504 OOF family scores then enter the exact unchanged #1194 diversity operator and evaluator.

## Binding scientific question

Does a shallow hierarchical model that directly sees the unordered collection of individual member residuals, while preserving the exact 34D family context, recover family-quality structure that fixed family summaries miss?

This is a change in statistical representation/training unit, not a new target, new learner family, or handcrafted member summary.

## Binding promotion gate

The first technically valid execution is binding.

PASS requires **all**:

- recovered@100 **> 80**;
- recovered@50 **>= 43**;
- recovered@25 **>= 22**;
- recovered@500 **>= 171**;
- top-100 dominant precision **>= 0.8075287489258385**;
- MRR **>= 0.02016666446026534**;
- qualified matches **== 256**.

A PASS freezes exactly this member-instance representation, purge rule, family-balanced instance weighting, arithmetic-mean pooling, and unchanged #1194 learner/ranker. It does not authorize SonotaCo execution; any transfer test must be separately frozen under the post-v60 governance rule.

A FAIL permanently rejects this exact member-instance pooled-regression v1.

## Closed rescue space

A FAIL does not authorize:

- neural/DeepSets/Set-Transformer/attention variants selected from this outcome;
- alternate tree depth/count/leaf size/max-features/model family;
- max/min/median/quantile/top-k/trimmed/year-balanced/learned pooling;
- adding member residual norms, powers, moments, covariance features, scatter/energy/kernel features, or orbital features;
- adding nearest-competitor distance, identity, margin, rank, graph, background, or density features;
- event pruning except the frozen cross-fold exact-ID leakage purge;
- instance weighting by year, residual magnitude, family size, quality, source, competitor, or model confidence;
- alternate family-weight redistribution after purging;
- feature subsets/interactions or dimensionality reduction;
- alternate target/folds/diversity/tie rule;
- parent-score blending or alternate parent ranker;
- post-result architecture/representation search.

Any later successor must be separately motivated and frozen before outcome.

## Required pre-interpretation guards

Execution must verify:

- exact source/input hashes and #1194 parent metrics/order;
- family feature shape `(4504,34)`;
- exact immutable family universe and IDs;
- every family member ID exists in the target-excluded scan lookup;
- member IDs are unique within each family;
- every member year is 2022 or 2023 and its annual family centroid exists;
- the pretruth residual matrix has 4 finite columns;
- total member-occurrence row count is exactly `74,497`, inherited from the already-frozen target-excluded membership payload provenance;
- the final instance matrix has shape `(74497,38)` and is finite;
- instance table construction does not use truth/target values;
- each OOF training/test family split remains exact #1194 whole-shower grouping;
- train/test event-ID intersection is empty after purge in every fold;
- every training family retains at least one instance after purge;
- per-family retained instance weights sum to the exact frozen parent family weight within numerical tolerance;
- every held-out family receives at least one predicted instance;
- family score aggregation is the exact arithmetic mean;
- no candidate identity or membership changes.

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