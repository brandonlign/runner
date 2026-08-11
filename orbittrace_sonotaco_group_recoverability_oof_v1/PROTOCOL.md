# OrbitTrace strict-group shower-recoverability SonotaCo OOF ranker v1

## Scientific role

This is one separately frozen **exposed SonotaCo development** successor motivated by the completed #999/#1002 diagnostics after #997 failed 2/4.

The fixed candidate/membership universe still has sufficient diagnostic headroom, but #999 showed that the HDBSCAN loss is already present in raw balanced-recovery score separability, and #1002 showed that at the HDBSCAN budgets the failure is **group recognition**, not selection of the wrong fragment inside a recognized shower group: every surfaced recoverable group already contained its target-positive family, while most recoverable shower groups were never surfaced at all.

This experiment therefore changes exactly one supervised quantity relative to #997: family labels are densified to the strict shower-group level. No feature, candidate, membership, fold, classifier capacity, weighting, diversity, fusion, or literature evaluator changes.

SonotaCo 2013/2014 remains exposed development only. No OrbitTrace target information, protected 20°–55° target-region data, MAARSY, or DMS is authorized.

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
- every family whose best recurrent label is the same shower shares strict group `SHOWER/<label>` across both routes;
- families with no recurrent best label use route-specific `NEG/<route>/<family_id>` groups;
- deterministic five-fold assignment is the existing v22/#839 hash rule;
- every fragment or near-miss of one known shower is therefore wholly absent from the training fold that predicts that shower.

## Base recoverability predicate

For each family with a recurrent best label, compute the same fixed #997 family-level balanced-recovery predicate:

`family_balanced_recovery = 1 iff F1_2013 > 0.5 AND F1_2014 > 0.5; otherwise 0`.

The `0.5` boundary is the already-frozen literature recovered-shower definition and is not selected here.

## Sole new target: strict shower-group recoverability

For each strict `SHOWER/<label>` group, define:

`group_recoverable = 1 iff ANY family in that strict shower group has family_balanced_recovery = 1`.

Then assign **every family in that same strict shower group** the target `group_recoverable`.

Every route-specific `NEG/<route>/<family_id>` remains target 0.

This is the sole scientific change from #997. It is designed to provide a denser supervised signal for the exact failure identified by #1002: recognizing a recoverable shower group at all.

The relabeling does not weaken the anti-leakage firewall. Because every family of a shower group is assigned to the same deterministic OOF fold, no fragment, near-miss, or other family from that shower appears in the four-fold training set used to score the held-out shower.

No alternate group-positive definition, annual threshold, fraction-of-positive-fragments threshold, soft group target, group size weighting, margin, route-specific group label, or target search is authorized.

## Sole classifier

Use exactly the #997 classifier:

- `ExtraTreesClassifier`;
- `n_estimators = 600`;
- `max_depth = 4`;
- `min_samples_leaf = 5`;
- `max_features = None`;
- `random_state = 20260809`;
- `n_jobs = -1` during OOF execution.

Training sample weights are exactly the pre-existing #839 inverse-whole-group weights on the unchanged strict groups. Because each group has fixed total weight under this rule, densifying labels does not give large fragmented shower groups greater total influence than small groups.

No class weight, resampling, focal loss, calibration, threshold, hyperparameter, feature, or model search is allowed.

For each held-out fold, score is the raw class-1 probability from a classifier fit only on the other four shower-group folds. The probability is a continuous ranking score only; no probability cutoff is selected.

## Sole successor order

For each route:

1. apply exact #839 geometric diversity to OOF positive-class probability with `lambda=0.8`, `scale=1.0`, and the exact frozen tie ranks;
2. take one parameter-free equal **rank-sum** with the exact frozen v19 order;
3. evaluate **only this fused successor order** as the promotion candidate.

The classifier-only and diversity-only orders may be recorded for provenance/diagnostics but are not additional promotion candidates. No fusion weight, alternate fusion, diversity value, source quota, family deletion, or budget-specific reranking is authorized.

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

A failure permanently rejects this exact shower-group-recoverability relabeling architecture. It does not authorize class weighting, resampling, probability calibration, target-definition changes, tree-capacity changes, alternate fusion/diversity, source quotas, or a post-result rescue on the same result.

## Full exposed-development model freeze

Only after a 4/4 grouped-OOF PASS may one full SonotaCo classifier be fit on all exposed-development examples with the same 71 features, strict group-recoverability target, exact group weights, and fixed ExtraTrees parameters. That full-fit model is deployable only; its in-sample scores are not promotion evidence. Any later protected cross-survey validation must be separately preregistered and must not access the OrbitTrace target region unless an already-frozen firewall explicitly authorizes it.

## Firewall

- SonotaCo 2013/2014 role: exposed development only.
- Pretruth payloads frozen before shower truth: required.
- Panel-specific model training: false; one shared stacked Sugar+HDBSCAN classifier.
- Strict whole-shower OOF: required.
- Feature search: false.
- Target/threshold search: false.
- Class-weight/resampling/calibration search: false.
- Model/hyperparameter search: false.
- Fusion/diversity search: false.
- Post-result second search: false.
- MAARSY scientific access: false.
- DMS scientific access: false.
- OrbitTrace target-information access: false.
- Protected 20°–55° target-region access: false.
