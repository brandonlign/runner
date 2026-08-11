# OrbitTrace GMN representative-share ranking v1

## Scientific role

This is a **target-excluded GMN 2022/2023 development experiment only**, created after the binding SonotaCo development closure memo #1190. It does not use SonotaCo 2013/2014 outcomes, comparator identities, budgets, ranks, or any other exposed SonotaCo information to define or select the method.

The experiment addresses a pre-existing GMN-only limitation documented by #838/#839: the exact hard+P19+P20 union contains 4,504 candidate families and 256 eligible known showers with at least one qualified candidate, but the #839 strict-group quality/diversity ranking recovers only 75 showers at rank 100 while mean qualified fragments per recovered shower are about 7.88. The fixed-universe oracle ceiling reaches 100/100. The scientific question is therefore whether the supervised target should allocate one unit of recoverability credit **within each known-shower group**, rather than rewarding every good fragment independently.

Protected OrbitTrace solar longitude 20°–55° remains excluded before candidate generation, labels, folds, features, targets, scoring, and evaluation. No OrbitTrace target information, target-region events, SonotaCo 2013/2014, MAARSY, or DMS may be accessed.

## Immutable development universe and parent

The candidate universe and all input artifacts are exactly the already-frozen target-excluded GMN 2022/2023 union used by #839:

- 226 hard families;
- 1,075 P19-soft families;
- 3,203 P20-soft families;
- 4,504 total families.

The implementation must reproduce the exact #839 quality/diversity control before evaluating the new target:

- recovered@25 = 22;
- recovered@50 = 40;
- recovered@100 = 75;
- recovered@500 = 159;
- qualified matches = 256;
- top-100 dominant precision = `0.7645689180574315`;
- MRR = `0.019037817654898162`.

Everything remains exact #839 unless explicitly changed below:

- exact 34D #839 family feature representation;
- exact target-excluded GMN 2022/2023 catalogue and eligible-label construction;
- exact strict whole-shower deterministic five-fold grouping, including nonqualified near-miss fragments of the same known shower in the same fold;
- exact #839 grouped sample weights;
- exact #839 ExtraTrees quality-regression model and hyperparameters;
- exact #839 centroid diversity ranking with lambda `0.8`, scale `1.0`, complete backfill, no family deletion;
- exact candidate memberships and tie ordering;
- exact monotone GMN metrics.

## Sole scientific change: representative-share target

Let `q_i` be the exact #839 absolute family-quality target for candidate i:

- `q_i = family F1` when the frozen #839 truth rule marks the family positive;
- `q_i = 0` otherwise.

Let `g_i` be the exact #839 strict group:

- `SHOWER/<best_label>` when a best known shower label exists;
- `NEG/<family_id>` otherwise.

For each strict shower group G, define

`Q_G = sum(q_j for j in G)`.

The new target is

`r_i = q_i / Q_G` when `g_i` is a SHOWER group and `Q_G > 0`,

and

`r_i = 0` otherwise.

Thus every recoverable known-shower group contributes exactly one unit of target mass across all of its fragments, apportioned in direct proportion to the same fixed #839 family quality. A unique strong representative receives most of the group's target mass; multiple near-duplicate strong fragments must share it. No hard winner, rank transform, exponent, temperature, threshold, additive constant, clipping, group-size coefficient, or alternative normalization is allowed.

The model, features, folds, grouped weights, diversity rule, candidate universe, and evaluator are unchanged.

## Frozen GMN-only selection gate

The exact #839 control must reproduce first. Then exactly one representative-share OOF order is evaluated on the same target-excluded GMN development universe.

Use the pre-existing comparison key already used in later GMN ranking labs:

`(recovered_at_100, recovered_at_50, recovered_at_25, top100_dominant_precision, MRR)`

with ordinary lexicographic comparison.

The candidate is viable only if all inherited viability conditions hold:

- recovered@100 >= 75;
- recovered@50 >= the exact hard-v8 recovered@50 control;
- top-100 dominant precision >= exact hard-v8 precision minus 0.05;
- qualified matches >= 230.

The experiment PASS requires both:

1. viability; and
2. the representative-share comparison key is strictly greater than the exact #839 comparison key.

No SonotaCo result can enter this decision. If the GMN gate fails, the method is rejected and must not be benchmarked on SonotaCo.

## Full-model freeze after GMN PASS only

Only if the GMN gate passes, fit one full model on all 4,504 target-excluded GMN families using the exact 34D features, exact #839 grouped weights, and the frozen representative-share target. Freeze the model bytes, feature matrix hash, target hash, weights hash, feature names, and deployment diversity rule before any later external application.

A later SonotaCo application, if separately authorized, must use this exact frozen model and rule without retraining or selection among alternatives.

## No rescue

If this GMN experiment fails, permanently close the exact representative-share target. Do not retry on the basis of its result with:

- winner-only or top-fragment classification;
- within-group rank/percentile targets;
- softmax/temperature/exponent transforms;
- group-size penalties;
- max-normalized rather than sum-normalized quality;
- alternative grouped weights;
- different features/model/hyperparameters;
- different diversity lambda or scale;
- top-k/budget-specific rules;
- SonotaCo-informed modifications.

Any successor must be independently motivated from non-SonotaCo development evidence and separately frozen.

## Firewall

Every output must assert:

- `sonotaco_2013_2014_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- `blind_exclusion = [20.0, 55.0]`.
