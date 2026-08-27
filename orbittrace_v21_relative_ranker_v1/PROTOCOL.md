# OrbitTrace v21 — catalogue-relative quality ranking

## Scientific motivation

v17–v20 establish that the broad hard/P19/P20 proposal universe contains enough genuine
families to beat the exposed SonotaCo literature panels, while the remaining failure is
very-top ranking. v18 exhausted the old diversity grid, v19 simple rank fusion remained
short on HDBSCAN, and v20 direct geometric first-pass diversification also failed.

The existing #839 quality model was trained on GMN using 34 structural/cohesion/source/
neighbor features in their absolute GMN scale. v21 tests one survey-transfer hypothesis:
retain the exact feature definitions and exact model complexity, but represent noncategorical
features by their empirical percentile within the current two-year candidate catalogue.

No SonotaCo truth is used to fit this model.

## Frozen training corpus and target

Training uses only the original target-excluded GMN 2022/2023 development universe:

- exact 226 hard + 1,075 P19 + 3,203 P20 families;
- exact #839 family-quality target and strict whole-shower grouping;
- exact #839 ExtraTrees regressor: 600 trees, depth 4, leaf 5, all features,
  random state 20260809;
- exact #839 diversity operating point lambda 0.8, scale 1.0.

The 34 feature definitions are unchanged. Source one-hot columns 21–23 and the binary
`is_soft` column 0 remain categorical values. Every other feature column is replaced by
average-tie empirical percentile `(rank-1)/(N-1)` computed within that catalogue.

The transform is fit-free: it has no stored SonotaCo or GMN scale parameter.

## GMN development guard

Before any SonotaCo row is restored, five-fold strict-group OOF prediction must satisfy:

- recovery@100 >= 70;
- recovery@50 >= 38;
- top100 dominant precision >= 0.70;
- qualified known showers >= 230.

Failure stops v21 before SonotaCo application.

If the guard passes, the exact model is fit once on all target-excluded GMN development
families and fingerprinted before any SonotaCo input.

## Fixed SonotaCo successor variants

On each already-exposed label-free SonotaCo matched row route, v21 regenerates the exact
v17 proposal universe and fixed membership layer. It evaluates exactly two predeclared
orders:

1. `relative_quality`: the GMN-trained catalogue-relative model followed by the fixed
   #839 diversity lambda 0.8 / scale 1.0.
2. `relative_v19_rank_sum`: parameter-free equal-weight rank-sum fusion of
   `relative_quality` with exact v19 rank-sum.

`v19_control` must reproduce exact v19 rank-sum families and all four v19 metrics.

All six SonotaCo candidate outputs freeze before exposed truth is loaded. There is no
SonotaCo model fit, feature selection, hyperparameter search, percentile-column search,
fusion-weight search, or post-result second search.

## Evaluation and firewall

Evaluation uses exact #854-compatible equal-budget one-to-one F1 assignment and the same
four-panel robust selection rule as v19/v20.

SonotaCo 2013/2014 is exposed development only. No MAARSY, DMS, OrbitTrace target
information, target-region event, or 20°–55° target content is authorized. Even a v21
SonotaCo pass remains development evidence and must later face a candidate-specific
protected external-validation protocol.
