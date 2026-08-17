# OrbitTrace v25 — two-head catalogue-rank consensus

## Motivation

Authoritative v24 run `31419316002` improved HDBSCAN 2013 to the same recovered-shower count as the literature comparator but still failed macro-F1, and HDBSCAN 2014 remained 7 versus 9 recovered. Artifact-only diagnostic run `31419852987` then reproduced v24 exactly and established `RANK_PLACEMENT_HEADROOM_REMAINS`: the same fixed candidate universe/memberships have diagnostic equal-budget oracle fronts that exceed HDBSCAN in both years, including 2014 macro-F1 0.1664677465 with 9 recovered versus HDBSCAN 0.1568959558 with 9.

The v24 two-head architecture therefore has useful annual quality signal, but its sole combiner `min(predicted_F1_2013,predicted_F1_2014)` assumes the two regression heads are numerically calibrated on the same score scale. The next minimal hypothesis is to preserve both heads exactly and combine only their **within-catalogue ranks**, which is invariant to monotone rescaling of either head.

## Frozen scientific change

v25 changes no candidate generation, family membership, feature, target, training row, group, fold, model, sample weight, geometry, diversity constant, or literature evaluator.

Inputs are the exact frozen v24 route payloads from artifact `9074742322` and exact #839 ranker source SHA-256 `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`.

The two OOF heads are retrained exactly as v24 under the same deterministic strict whole-shower five folds:

- head 2013 target: `F1_2013` for the unchanged v22 best label, zero for unchanged v22-nonpositive families;
- head 2014 target: `F1_2014` under the same rule.

Before any v25 result is accepted, the raw v24 combiner and exact downstream ordering are replayed and must reproduce all four authoritative v24 panel metrics exactly.

### Sole v25 quality score

For each matched-route catalogue separately, convert the two held-out prediction vectors to deterministic descending empirical rank percentiles:

- highest prediction = percentile `1.0`;
- lowest prediction = percentile `0.0`;
- ties are broken only by the already-frozen v22 `tie_rank`, then stable family ID.

The sole v25 base quality score is:

`Q25 = min(percentile_2013, percentile_2014)`.

This is equivalent to requiring a family to rank well under both annual heads and is invariant to monotone calibration differences between heads. There is no year weight, score transform grid, quantile threshold, or alternate rank combiner.

The exact #839 diversity ordering is then applied unchanged to `Q25` with `lambda=0.8`, `scale=1.0` and the exact frozen centroid matrix/tie semantics.

The **sole deployable v25 final order** is the parameter-free equal rank-sum of that diversified v25 quality order and the exact frozen v19 rank-sum order, using the already-frozen v19 fusion helper. The pure v25 quality order is diagnostic only and cannot be selected instead.

## Evaluation

The exact already-exposed SonotaCo truth/comparator artifact is used only after all method/source identities are verified. The exact #854 equal-budget one-to-one maximum-total-F1 semantics are unchanged.

v25 passes only if its single final order wins all four frozen matched panels. A pairwise win requires:

- candidate macro-F1 > literature macro-F1; and
- candidate recovered-F1>0.5 count >= literature.

No selector chooses among v25 alternatives because there is only one deployable successor.

Only an all-four-panel OOF PASS may authorize fitting/fingerprinting the same two exact full exposed-SonotaCo heads for a later separately preregistered protected cross-survey validation. Full-fit in-sample SonotaCo performance is never promotion evidence.

## Prohibitions

- no change to annual targets or model hyperparameters;
- no alternate percentile/rank definition;
- no year weighting;
- no rank-product/median/mean/max-grid comparison;
- no diversity/fusion search;
- no candidate or membership change;
- no comparator-budget-specific ranking logic;
- no post-result v25 rescue;
- no MAARSY, DMS, OrbitTrace target information, target-region event, or 20°–55° target-content access.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.
