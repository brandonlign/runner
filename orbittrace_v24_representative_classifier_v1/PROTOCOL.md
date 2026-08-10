# OrbitTrace v24 — representative classifier under strict whole-shower OOF

## Motivation

v23 made the ranking target catalogue-slot aware by assigning one deterministic positive
representative per eligible shower, while holding every sibling fragment in the same
unseen-shower fold. That change improved the hardest HDBSCAN-2014 panel from the v19
rank-sum baseline of 5 recovered showers to 7, but the fixed #839 F1-regression objective
still failed the two HDBSCAN panels.

The v23 target is sparse: 29 Sugar-route and 27 HDBSCAN-route representative positives
among 496 total candidate families. v24 therefore changes **only the supervised loss** from
continuous F1 regression to binary representative classification.

Proposal generation, fixed memberships, truth definition, representative selection,
71 label-free features, global same-shower folds, diversity, v19 fusion, comparator budgets
and the literature evaluator are unchanged.

## Frozen pretruth representation

Before truth, regenerate and SHA-256 freeze the exact v22/v23 pretruth payload on each
matched route:

- exact v19-expanded fixed memberships;
- exact 71-dimensional label-free feature matrix;
- exact centroid geometry;
- exact v19 rank-sum order.

No truth enters this stage.

## Representative labels

After both route payloads freeze, load the immutable exposed SonotaCo truth and reproduce
exactly the v23 eligibility/matching rule:

- known shower eligible only if it has >=4 truth events in 2013, >=4 in 2014, and >=8 total;
- family best match uses fixed combined-two-year memberships;
- candidate-positive family requires best-shower precision >=0.5 and overlap >=4;
- within each route and eligible shower, exactly one deterministic representative is chosen
  by highest F1, then precision, then overlap, then lexicographically smallest family ID.

The chosen representative receives binary class `1`; every sibling fragment, near-miss and
truth-negative family receives class `0`.

This rule is identical to v23 except that representative F1 magnitude is not used as a
regression target.

## Anti-leakage grouping

Grouping is unchanged from v22/v23:

- every family whose best truth label is shower X across both matched routes receives group
  `SHOWER/X`, including the representative, zero-target siblings and near-misses;
- families without a best shower label receive stable unique negative groups.

Five deterministic folds use exact #839 SHA-256 group hashing. Therefore every OOF
probability for shower X is produced by a classifier trained on no family whose best truth
label is X in either route.

## Frozen classifier

Use exactly one classifier architecture; there is no model grid:

- `ExtraTreesClassifier`;
- 600 trees;
- maximum depth 4;
- minimum leaf size 5;
- all 71 features at each split (`max_features=None`);
- random state 20260809;
- `class_weight='balanced'`, recomputed separately inside every OOF training fold;
- exact #839 inverse-group sample weights supplied to `fit`;
- `n_jobs=1` for deterministic execution.

No probability calibration, thresholding or class-weight search is allowed. Ranking uses the
raw OOF probability of class 1.

## Frozen ranking variants

Exactly two successor orders are evaluated:

1. `representative_classifier_oof`: class-1 OOF probability followed by exact #839
   diversity lambda 0.8 / scale 1.0;
2. `representative_classifier_oof_v19_rank_sum`: parameter-free equal rank-sum fusion of
   variant 1 with exact frozen v19 rank-sum.

Exact v19 rank-sum with the same fixed memberships is the identity control.

There is no feature search, model search, class-weight search, probability threshold,
diversity grid, fusion weight, top-K tuning or post-result second search.

## Development verdict and freeze boundary

Evaluation uses exact frozen #854-compatible equal-budget one-to-one maximum-total-F1
assignment.

A v24 OOF PASS requires, in all four comparator/year panels:

- candidate macro-F1 strictly greater than the frozen literature comparator; and
- recovered F1>0.5 count greater than or equal to the comparator.

Only an OOF PASS permits fitting the identical classifier once on all exposed SonotaCo
development families and fingerprinting it for a later candidate-specific protected
cross-survey validation. No full-fit in-sample SonotaCo score may be used as promotion
evidence.

## Firewall and claim boundary

SonotaCo 2013/2014 remains exposed development only. No MAARSY, DMS, OrbitTrace target
information, target-region event, or solar-longitude 20°–55° target content is authorized.
A v24 SonotaCo OOF pass would be development superiority under strict unseen-shower folds,
not external validation.
