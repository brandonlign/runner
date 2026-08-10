# OrbitTrace strict-group balanced-recovery SonotaCo OOF ranker v1

## Scientific role

This is a separately named **exposed SonotaCo development** successor after the strict-group ranking chain v22–v29 failed to achieve all-panel literature superiority. SonotaCo 2013/2014 is already exposed development and is not pristine external validation.

The fixed candidate/membership universe has known diagnostic headroom, while the strongest prior strict-group learned rankers repeatedly miss rare high-quality held-out showers at the tiny HDBSCAN budgets. This experiment changes exactly one scientific quantity relative to the v22/v25 ranking framework: the supervised learning objective.

No OrbitTrace target information, protected 20°–55° target-region data, MAARSY, or DMS is authorized.

## Frozen pretruth inputs

Use exactly the valid v22 pretruth payloads independently regenerated for the two matched SonotaCo routes and verified before truth:

- exact 71-dimensional label-free feature interface;
- exact fixed v19-expanded family memberships;
- exact candidate universes and centroids;
- exact v19 order and tie ranks;
- exact Sugar-route and HDBSCAN-route label-free rows;
- exact v22 scientific identity hashes and round-to-12 feature fingerprints.

No feature, membership, candidate, centroid, route, or source definition changes.

## Frozen truth/group semantics

Only after both route payloads pass their complete pretruth identity guards may the immutable exposed SonotaCo truth/comparator package be loaded.

Use the exact v22–v25 recurrent-shower eligibility and best-label semantics:

- a recurrent shower is eligible only with at least 4 truth members in each year and at least 8 total;
- each family keeps the exact v22 combined-best recurrent label;
- every family whose best recurrent label is the same shower shares group `SHOWER/<label>` across both routes;
- families with no recurrent best label use route-specific `NEG/<route>/<family_id>` groups;
- deterministic five-fold assignment is the existing v22/#839 hash rule;
- every fragment or near-miss of one known shower is therefore wholly absent from the training fold that predicts that shower.

## Sole new target

For the unchanged best recurrent label, compute the existing annual membership F1 values `F1_2013` and `F1_2014` from the fixed family membership.

The single binary target is:

`balanced_recovery = 1 iff F1_2013 > 0.5 AND F1_2014 > 0.5; otherwise 0`.

The `0.5` boundary is **not selected here**. It is exactly the already-frozen literature evaluation definition of a recovered shower (`F1 > 0.5`), applied symmetrically to both years because the method must succeed in both annual panels.

No alternate F1 threshold, one-year target, soft target, target weighting, margin, ordinal target, or target grid is authorized.

## Sole classifier

Use one `ExtraTreesClassifier` with the exact #839 tree complexity already used by v25 pairwise ranking:

- `n_estimators = 600`;
- `max_depth = 4`;
- `min_samples_leaf = 5`;
- `max_features = None` (all 71 features);
- `random_state = 20260809`;
- `n_jobs = -1` during OOF execution.

Training sample weights are exactly the pre-existing #839 inverse-whole-group weights on the unchanged strict groups. No class weight, resampling, focal loss, calibration, threshold, hyperparameter, feature, or model search is allowed.

For each held-out fold, ranker score is the raw class-1 probability from a classifier fit only on the other four shower-group folds. Every training fold must contain both classes. The class probability is used only as a continuous ranking score; no probability cutoff is selected.

## Sole successor order

For each route:

1. apply exact #839 geometric diversity to the OOF positive-class probability with `lambda=0.8`, `scale=1.0`, and the exact frozen tie ranks;
2. take one parameter-free equal **rank-sum** with the exact frozen v19 order;
3. evaluate **only this fused successor order** as the promotion candidate.

The classifier-only order may be computed internally only to construct the frozen rank-sum and record provenance; it is not a second promotion candidate. No fusion weight, alternate fusion, diversity value, quota, deletion, or budget-specific reranking is authorized.

Exact v19 fixed-membership evaluation must reproduce in all four panels before the successor result is admissible.

## Literature gate

Evaluate the same fixed route orders under the exact existing equal-budget Hungarian semantics for:

- Sugar 2013;
- Sugar 2014;
- HDBSCAN 2013;
- HDBSCAN 2014.

A panel passes only if:

- candidate macro-F1 is **strictly greater** than the frozen comparator macro-F1; and
- candidate recovered-shower count (`Hungarian F1 > 0.5`) is **at least** the comparator count.

Scientific PASS requires **4/4 panel wins** for the single fused successor order.

A failure permanently rejects this exact balanced-recovery classifier architecture. It does not authorize threshold search, class weighting, probability calibration, tree-capacity changes, feature selection, fusion-weight tuning, source quotas, or a post-result rescue on the same result.

## Full exposed-development model freeze

Only after a 4/4 grouped-OOF PASS may one full SonotaCo classifier be fit on all exposed-development examples with the same 71 features, target, strict-group weights, and fixed ExtraTrees parameters. That full-fit model is a deployable artifact only; its in-sample scores are not promotion evidence. Any later protected cross-survey validation must be separately preregistered and must not use the OrbitTrace target region unless an already-frozen firewall explicitly authorizes it.

## Firewall

- SonotaCo 2013/2014 role: exposed development only.
- Pretruth payloads frozen before shower truth: required.
- Panel-specific model training: false; one shared stacked Sugar+HDBSCAN classifier.
- Feature search: false.
- Target/threshold search: false.
- Model/hyperparameter search: false.
- Fusion/diversity search: false.
- Post-result second search: false.
- MAARSY scientific access: false.
- DMS scientific access: false.
- OrbitTrace target-information access: false.
- Protected 20°–55° target-region access: false.
