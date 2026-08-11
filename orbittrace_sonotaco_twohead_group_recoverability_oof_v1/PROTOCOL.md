# OrbitTrace two-head annual shower-recoverability SonotaCo OOF ranker v1

## Scientific role

This is one separately frozen **exposed SonotaCo development** successor after #1004's strict shower-group recoverability model produced a genuine near-miss but still failed 2/4.

#1004 showed that densifying supervision to the shower-group level materially improved HDBSCAN performance, especially 2014, but its single target still encoded a two-year conjunction (`F1_2013>0.5 AND F1_2014>0.5`) while the frozen literature benchmark is evaluated independently in 2013 and 2014. Earlier v24 established a preregistered two-annual-head pattern using the conservative `min(head_2013, head_2014)` combination.

This successor therefore changes exactly one quantity relative to #1004: replace the single conjunctive group target with two **annual** strict-group recoverability targets and combine their OOF probabilities using the already-existing v24 `min` rule. Everything else remains fixed.

SonotaCo 2013/2014 is exposed development only. No OrbitTrace target information, protected 20°–55° target-region data, MAARSY, or DMS is authorized.

## Frozen pretruth inputs

Use exactly the valid v22 pretruth payloads for Sugar and HDBSCAN routes:

- exact 71-dimensional label-free features;
- exact fixed v19-expanded memberships;
- exact candidate universes and centroids;
- exact v19 order and tie ranks;
- exact route-specific label-free rows;
- exact v22 identity hashes and rounded-12 feature fingerprints.

No feature, candidate, membership, centroid, source, or route change is allowed.

## Frozen strict-group firewall

Only after both pretruth payloads reproduce may the immutable exposed SonotaCo truth/comparator package be loaded.

Use exact v22–v25 recurrent-shower eligibility, best-label semantics, and strict groups:

- eligible recurrent shower: >=4 truth members in each year and >=8 total;
- exact combined-best recurrent label per family;
- all families with the same best recurrent label share `SHOWER/<label>` across both routes;
- no-label families use route-specific `NEG/<route>/<family_id>`;
- deterministic five-fold assignment is the existing v22/#839 hash rule;
- every fragment/near-miss of one shower is therefore wholly absent from the four-fold training set that scores that shower.

## Sole new targets

For each family with a recurrent best label, compute its unchanged annual membership F1 values.

For each year `y` in `{2013,2014}`, define the family annual predicate:

`family_recovered_y = 1 iff F1_y > 0.5; otherwise 0`.

The `0.5` threshold is the already-frozen literature recovered-shower definition and is not selected here.

For each strict `SHOWER/<label>` group and each year separately, define:

`group_recoverable_y = 1 iff ANY stacked Sugar/HDBSCAN family in that strict shower group has family_recovered_y = 1`.

Then every family in that strict shower group receives the corresponding annual target `group_recoverable_y`. Every `NEG/...` family receives 0 for both heads.

No alternate annual threshold, route-specific group target, fraction-of-fragments rule, soft label, joint target, target weighting, margin, or target search is authorized.

## Two frozen classifiers

Train two independent annual heads, one for 2013 and one for 2014. Each uses exactly the #997/#1004 classifier:

- `ExtraTreesClassifier`;
- `n_estimators=600`;
- `max_depth=4`;
- `min_samples_leaf=5`;
- `max_features=None`;
- `random_state=20260809`;
- `n_jobs=-1` during OOF execution.

Both heads use exactly the #839 inverse-strict-group training weights. No class weighting, resampling, calibration, thresholding, hyperparameter search, feature search, or model search.

For each OOF fold, both heads are fit only on the other four strict shower-group folds. Each training fold must contain both classes for both annual heads.

## Frozen head combination and order

For every held-out family, compute raw annual positive-class probabilities `p2013` and `p2014` and combine them using the already-existing v24 conservative two-head rule:

`score = min(p2013, p2014)`.

This `min` rule is fixed before execution and is not compared against average, product, maximum, rank sum, or any other head combination.

For each route:

1. apply exact #839 geometric diversity to the combined OOF score with `lambda=0.8`, `scale=1.0`, and exact tie ranks;
2. take one parameter-free equal rank-sum with exact frozen v19 order;
3. evaluate only that fused order as the promotion candidate.

No fusion-weight, diversity, quota, deletion, or budget-specific reranking search is allowed.

Exact v19 fixed-membership evaluation must reproduce in all four panels before the successor result is admissible.

## Literature gate

Evaluate under the exact existing equal-budget Hungarian semantics on:

- Sugar 2013;
- Sugar 2014;
- HDBSCAN 2013;
- HDBSCAN 2014.

A panel passes only if candidate macro-F1 is strictly greater than the frozen comparator and recovered-shower count (`Hungarian F1>0.5`) is at least the comparator count.

Scientific PASS requires 4/4 panel wins.

A failure permanently rejects this exact two-head annual group-recoverability architecture. It does not authorize class weighting, annual-head weighting, alternate head combination, target changes, calibration, tree-capacity changes, alternate diversity/fusion, source quotas, or post-result rescue.

## Full exposed-development model freeze

Only after a 4/4 grouped-OOF PASS may two full annual classifiers be fit on all exposed-development examples with the same features, annual group targets, exact weights, and fixed classifier parameters. Full-fit models are deployable artifacts only; in-sample results are not promotion evidence.

## Firewall

- SonotaCo role: exposed development only.
- Pretruth identity before truth: required.
- Strict whole-shower OOF: required.
- Shared stacked models across routes: required.
- Feature search: false.
- Target/threshold search: false.
- Annual-head combination search: false.
- Class-weight/resampling/calibration search: false.
- Model/hyperparameter search: false.
- Fusion/diversity search: false.
- Post-result second search: false.
- MAARSY scientific access: false.
- DMS scientific access: false.
- OrbitTrace target-information access: false.
- Protected 20°–55° target-region access: false.
