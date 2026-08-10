# OrbitTrace v24 — two-head annual-quality strict-group OOF ranking

## Motivation

v22 (combined two-year F1 target) and v23 (worst-year scalar F1 target) both failed the two catalogue-HDBSCAN panels while continuing to beat Sugar. v23's worst-year target is extremely concentrated near zero (HDBSCAN-route median ~0.014), and its pure OOF ranking was worse than the v19 fusion. The exposed candidate oracle still shows that the fixed family universe contains enough strong families to beat HDBSCAN.

The next admissible question is therefore not another scalar-target transformation. v24 asks whether the same label-free family features can learn **annual membership quality separately** before the two-year constraint is imposed.

## Frozen inputs and unchanged architecture

v24 preserves exactly:
- the v22/v23 71-dimensional label-free pretruth feature vector;
- the exact fixed v19-expanded family memberships and candidate universes;
- the shared Sugar+HDBSCAN exposed-development training pool;
- the exact #839 ExtraTrees regression architecture and inverse-group weighting;
- deterministic five-fold whole-shower grouping across both routes;
- exact #839 diversity lambda `0.8`, scale `1.0`;
- exact v19 rank-sum order as identity control and optional parameter-free fusion partner;
- exact #854-compatible equal-budget one-to-one maximum-total-F1 evaluation.

Before truth, regenerated memberships and centroids must remain byte-identical to the first valid v22 payload; the feature array must pass the same frozen round-to-12-decimal semantic fingerprint used by the repaired valid v23 run. No feature, model, fold, diversity, membership, fusion weight, radius, threshold, candidate, or comparator-budget search is allowed.

## Sole scientific change from v23

For each frozen family, determine `best_label` exactly as in v22/v23 from the combined two-year recurrent-shower comparison. This preserves the same strict-group identity and does not permit a different label per annual head.

Using the fixed membership and that fixed `best_label`, compute two targets:
- `y_2013 = F1_2013`
- `y_2014 = F1_2014`

Two independent copies of the exact frozen #839 ExtraTrees regressor are fitted in each OOF fold, one per annual target, using identical training rows, group weights, and fold membership. All fragments and near-misses of a known shower remain absent from both annual-head training sets for their held-out fold.

The deployable OOF family score is fixed **before evaluation** as:

`score = min(predicted_F1_2013, predicted_F1_2014)`

This is not a target grid. No mean, product, geometric mean, harmonic mean, learned combiner, calibration, clipping threshold, or year weighting is evaluated in v24.

## Frozen variants and gate

Exactly two successor orders are evaluated:
1. `two_head_min_oof_quality`: exact #839 diversity order applied to the fixed minimum of the two annual OOF predictions.
2. `two_head_min_oof_v19_rank_sum`: parameter-free equal-weight rank-sum between that OOF order and exact v19 rank-sum.

The exact v19 order remains an identity control and must reproduce all four v19 fixed-membership metrics.

PASS requires a single frozen successor to win **all four** comparator/year panels: candidate macro-F1 strictly above the corresponding literature comparator and recovered F1>0.5 count at least equal to the comparator in every panel. The same robust four-panel lexicographic selector used by v22/v23 chooses between the two frozen successors.

Only an OOF all-panel PASS may fit and fingerprint two identical full-development annual heads. Full-fit in-sample scores are ineligible as promotion evidence. A v24 OOF failure is a permanent no-go for this two-head architecture and does not authorize a prediction-combiner search.

## Firewall

SonotaCo 2013/2014 remains exposed development-only. No MAARSY, DMS, OrbitTrace target information, target-region event, or protected 20°–55° content is authorized. Any protected cross-survey validation requires a separate candidate-specific pretruth protocol after an OOF PASS.
