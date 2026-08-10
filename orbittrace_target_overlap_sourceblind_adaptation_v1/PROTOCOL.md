# OrbitTrace target-overlap source-blind adaptation v1

## Purpose

Test one unsupervised covariate-shift adaptation hypothesis after the truth-free GMN–SonotaCo diagnostic established substantial survey-domain separation in the same 21 generic source-blind family features.

The scientific question is whether the exact PR #977 source-blind purity architecture transfers more plausibly when GMN supervised training emphasizes families whose **label-free feature vectors resemble the target survey**, without using any SonotaCo shower truth or literature-comparator result.

This is a pretruth adaptation-development stage. SonotaCo contributes only canonical label-free family covariates and the survey-identity label `SonotaCo` versus `GMN`.

## Frozen inputs

Use exactly:

- target-excluded GMN 2022/2023 hard + P19 + P20 universe: 226 + 1,075 + 3,203 = 4,504 families;
- canonical label-free SonotaCo 2013/2014 seed-family universe: 25 hard + 84 P19 + 225 P20 = 334 families;
- PR #977's exact 21 generic source-blind features, in the same order and formulas;
- PR #839/#840 GMN family truth, strict whole-shower groups, diversity weights, HGB-31 purity architecture, and geometric diversity lambda `0.8`, scale `1.0`;
- PR #990's exact survey-domain classifier architecture and deterministic five-fold domain/source-stratified fold construction.

No SonotaCo shower truth, matched comparator rows, or literature-evaluation artifact may be downloaded in this stage.

## Exact domain-overlap rule

Construct the 21D GMN and SonotaCo feature matrices exactly as in the successful truth-free #990 diagnostic.

Fit the exact #990 domain classifier in five-fold OOF mode using only survey identity:

- `HistGradientBoostingClassifier`;
- learning rate `0.05`;
- `max_iter=250`;
- `max_leaf_nodes=31`;
- L2 regularization `1.0`;
- random state `20260809`;
- domain-balanced training weights within each fold;
- deterministic folds balanced within survey-domain × generator-source strata.

The OOF probability `p_target = P(SonotaCo | 21D features)` for each GMN family is its **target-overlap multiplier**. The multiplier is used directly and is therefore bounded in `[0,1]`; no odds transform, clipping threshold, temperature, exponent, calibration, or parameter is allowed.

For the exact #977 GMN purity model, replace only the training sample weight by:

`adapted_weight_i = exact_#840_weight_i * p_target_i * C`

where the deterministic normalization constant

`C = sum(exact_#840_weight) / sum(exact_#840_weight * p_target)`

preserves the total GMN training weight. No other model, feature, target, fold, diversity, ranking, or membership rule changes.

The source label hard/P19/P20 is used only to balance the **domain-classifier folds**, exactly as in #990. It is not a purity-model feature, quota, routing rule, or ranking input.

## Required controls

Before interpreting the adapted candidate:

1. reproduce the successful #990 truth-free domain OOF ROC AUC `0.88356922921475` from the same feature matrices and folds;
2. reproduce the exact raw #977 source-blind purity+diversity GMN metrics: r25/r50/r100/r500 = `24/47/82/165`, top-100 dominant precision `0.8558407874228419`, qualified matches `256`, MRR `0.021025165849542556`;
3. reproduce the unchanged hard-v8 baseline from the same GMN universe for the inherited viability gate.

## Pretruth GMN safety gate

Because this successor intentionally optimizes target-domain overlap rather than GMN source-domain fit, it is **not** required to improve on raw #977 in GMN OOF ranking.

It may freeze a deployable adapted model only if it passes the already-existing #971 viability gate, without introducing new thresholds:

- recovery@100 >= `75`;
- recovery@50 >= exact hard-v8 recovery@50;
- top-100 dominant precision >= exact hard-v8 top-100 precision minus `0.05`;
- qualified matches >= `230`.

A FAIL rejects this exact bounded overlap-weighting rule and does not authorize changing the probability transform, clipping, exponent, feature subset, source grouping, model, or gate.

## Full model freeze after PASS only

If the safety gate passes:

1. fit one full #990-architecture domain classifier on all 4,504 GMN + 334 label-free SonotaCo feature rows with domain-balanced weights;
2. compute full-model `P(SonotaCo | x)` on the 4,504 GMN training families;
3. apply the same bounded overlap rule and deterministic total-weight normalization;
4. fit exactly one full 21D HGB-31 purity model;
5. freeze both model files, exact feature names/order, training hashes, target hashes, weighting hashes, and exact diversity `0.8/1.0`.

Only that frozen purity model may later receive a separately named one-shot canonical SonotaCo literature application. This protocol itself performs no literature evaluation.

## Forbidden adaptations

No feature subset selection, KS-based feature deletion, alternate domain classifier, probability cutoff, odds/rate clipping, weight exponent, source quota, source routing, target threshold, calibration, diversity search, rank fusion, model-capacity search, parameter search, or post-result second search is authorized.

## Firewall

- GMN blind exclusion remains `[20.0, 55.0]` at source construction.
- SonotaCo label-free covariates used: true.
- SonotaCo shower truth accessed: false.
- Literature evaluation performed: false.
- Matched comparator rows used: false.
- MAARSY scientific access: false.
- DMS scientific access: false.
- OrbitTrace target-information access: false.
- Protected target-region events accessed: false.
