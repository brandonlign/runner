# OrbitTrace v23 — one-representative-per-shower ranking target

## Motivation

The first valid v22 strict whole-shower OOF result still loses both catalogue-HDBSCAN
panels even though the already-exposed oracle diagnosis shows the fixed v19 family universe
has sufficient headroom. v22's own target diagnostics reveal a direct objective mismatch:

- Sugar route: 207 positive candidate families for only 45 eligible recurrent showers;
- HDBSCAN route: 192 positive candidate families for only 43 eligible recurrent showers.

The v22/#839-style target rewards every sufficiently precise fragment of a shower. Under
9/11-candidate HDBSCAN budgets, ranking several fragments of the same shower wastes the
scarce catalogue slots.

v23 changes **only the supervised ranking target**. Proposal generation, memberships,
features, model complexity, folds, diversity, fusion, comparator budgets and evaluator are
unchanged from v22.

## Frozen pretruth representation

For each matched SonotaCo row route, v23 regenerates and freezes the exact v22 pretruth
payload before truth:

- exact v19-expanded fixed memberships;
- exact 71-dimensional v22 label-free feature matrix;
- exact centroid geometry and v19 rank-sum order.

No truth enters this stage.

## Truth eligibility and family truth

After both route payloads freeze, use the identical v22 truth definition:

- known shower eligible only if it has >=4 truth events in 2013, >=4 in 2014, and >=8 total;
- every family receives its best combined-two-year shower match using fixed memberships;
- a family is candidate-positive only if best-shower precision >=0.5 and overlap >=4.

These calculations are identical to v22.

## Representative target

Within **each route independently**, for every eligible known shower that has at least one
candidate-positive family, exactly one representative family keeps a nonzero regression
target.

Representative selection is deterministic and frozen:

1. highest combined-two-year F1;
2. then highest precision;
3. then greatest truth overlap;
4. then lexicographically smallest stable family ID.

The representative target equals that family's F1. Every sibling fragment whose best truth
label is the same shower receives target zero. All truth-negative/near-miss families also
receive zero.

This is not a top-K or comparator-budget target; the same rule is used for Sugar and
HDBSCAN route catalogues.

## Anti-leakage grouping

Grouping is unchanged from v22 and remains stricter than the target:

- every family whose best truth label is the same known shower receives group
  `SHOWER/<label>` across **both routes**, including siblings whose representative target is
  zero and near-misses;
- negatives without a best shower label receive stable unique negative groups.

Five deterministic folds use exact #839 SHA-256 group hashing. Thus an OOF prediction for
a representative or sibling of shower X is produced by a model that saw no family whose
best truth label is X in either route.

## Frozen model and variants

Use exact v22 model complexity and weighting:

- ExtraTreesRegressor, 600 trees, depth 4, min leaf 5, all features, random state 20260809;
- exact #839 inverse-group sample weighting.

Exactly two OOF ranking variants:

1. `representative_oof_quality`: OOF representative-target prediction + exact #839
   diversity lambda 0.8 / scale 1.0;
2. `representative_oof_v19_rank_sum`: parameter-free equal rank-sum fusion of variant 1
   with exact v19 rank-sum.

Exact v19 fixed-membership order remains the identity control.

There is no model grid, target threshold search, representative-count search, feature
search, diversity grid, fusion weight, top-K tuning or post-result second search.

## Verdict and promotion boundary

Evaluation is the exact frozen #854-compatible equal-budget one-to-one F1 assignment.
A v23 OOF PASS requires macro-F1 superiority and recovered-F1>0.5 tie/superiority on all
four comparator/year panels.

Only an OOF PASS permits fitting the identical representative-target architecture once on
all exposed SonotaCo development families and fingerprinting it for a later protected
cross-survey validation. No in-sample full-fit score can be used for promotion.

SonotaCo 2013/2014 remains exposed development only. No MAARSY, DMS, OrbitTrace target
information, target-region event, or solar-longitude 20°–55° content is authorized.
