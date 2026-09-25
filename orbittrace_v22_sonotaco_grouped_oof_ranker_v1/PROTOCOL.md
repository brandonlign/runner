# OrbitTrace v22 — strict-group SonotaCo domain ranking

## Why this successor exists

v17–v21 establish two facts on the now-exposed SonotaCo 2013/2014 development benchmark:

1. the hard/P19/P20 proposal universe contains enough good families to beat both literature
   comparators at their exact budgets (truth-aware oracle diagnosis);
2. GMN-trained ranking transfer, diversity-grid tuning, simple rank fusion, event-overlap
   suppression, and geometry-only first-pass diversification still fail the HDBSCAN panels.

Therefore v22 changes only the **ranking calibration domain**. SonotaCo is already exposed
and may be used as development data. v22 does not claim that a full-fit SonotaCo score is
validation.

## Fixed candidate and membership universe

Before any SonotaCo truth is loaded, v22 independently regenerates the exact v17 proposal
universe on both already-exposed matched row routes and freezes:

- hard families with v15 adaptive density ranking input;
- P19/P20 pair-portable proposals;
- exact #839/#853 raw 34-feature matrix and centroid geometry;
- exact #843 consensus graph at radius 1.0 and source-quality weight 2.0;
- exact v19 rank-sum order;
- exact v19 fixed joint-conformal top-100 membership expansion.

The **v19-expanded family memberships are then held fixed** for all v22 ranking development.
This makes v22 a ranking-only experiment and removes the circularity in which a new ranker
would otherwise change its own membership target.

## Frozen v22 feature vector

One feature representation is used; there is no feature-set search.

For every family, concatenate:

1. exact #839 raw 34 features;
2. empirical-percentile versions of the 30 noncategorical #839 columns, using average-tie
   `(rank-1)/(N-1)` within that route catalogue;
3. normalized rank percentiles for exact #839 quality order, exact #843 consensus order,
   and exact v19 rank-sum order;
4. four exact #843 graph descriptors at radius 1.0: `log1p(degree)`,
   `log1p(cross_source_degree)`, number of distinct neighboring generator sources minus one,
   and source-order percentile.

Total dimension: **71**. No column selection, interaction search, threshold search, or
normalization search is allowed.

## Truth target and anti-leakage grouping

After both route feature/membership payloads are hash-frozen, the immutable exposed
SonotaCo truth is loaded.

For each route, use the exact #839 recurrent-family truth definition:

- a known shower is eligible only if it has >=4 truth events in 2013, >=4 in 2014, and
  >=8 combined;
- family target is its best combined two-year F1 against eligible showers;
- target is zero unless best-shower precision >=0.5 and overlap >=4.

Training examples from the Sugar and HDBSCAN row routes are stacked into **one model**.
There is no comparator-specific model.

Grouping is stricter than route-level splitting:

- every family whose best truth label is the same known shower receives group
  `SHOWER/<label>` across **both routes**;
- all fragments and near-misses of that shower therefore enter the same fold;
- truth-negative families receive stable unique negative groups.

Five deterministic folds use the exact #839 group-hash rule. Each family's OOF prediction
comes from a model that saw **no family from that shower in either route**.

## Frozen model and ranking variants

Model complexity is the exact #839 ExtraTrees regressor:

- 600 trees;
- max depth 4;
- min samples leaf 5;
- all features;
- random state 20260809;
- exact #839 inverse-group sample weighting.

Exactly two OOF ranking variants are evaluated:

1. `sonotaco_oof_quality`: grouped-OOF prediction followed by exact #839 diversity
   lambda 0.8 / scale 1.0;
2. `sonotaco_oof_v19_rank_sum`: parameter-free equal rank-sum fusion of the first order
   with exact frozen v19 rank-sum.

Exact v19 rank-sum remains the control. There is no model grid, diversity grid, fusion
weight, top-K tuning, comparator-budget feature, or post-result second search.

## Development verdict

All three rankings use the same fixed v19-expanded memberships. Evaluation uses exact
#854-compatible equal-budget one-to-one maximum-total-F1 assignment.

A v22 OOF development PASS requires the selected OOF variant to:

- beat literature macro-F1 on all four comparator/year panels; and
- tie or beat literature recovered-F1>0.5 count on all four panels.

The selected variant is determined by the same robust lexicographic all-panel key used in
v19–v21, with `sonotaco_oof_quality` preferred only as the final exact tie-break.

Only if the OOF verdict passes may the exact same 71-feature/model architecture be fit once
on all exposed SonotaCo development families and frozen as a candidate for a later protected
cross-survey validation. The full-fit SonotaCo model is never scored in-sample for promotion.

## Firewall and claim boundary

SonotaCo 2013/2014 is exposed development only. v22 OOF can establish development
superiority under strict unseen-shower folds; it is not external validation.

No MAARSY, DMS, OrbitTrace target information, target-region event, or solar-longitude
20°–55° target content may be accessed. A v22 OOF pass still requires a separately frozen,
candidate-specific protected-validation protocol before any protected scientific values are
opened.
