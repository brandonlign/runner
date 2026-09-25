# OrbitTrace v24 contingency — two-head worst-predicted-year ranking

## Dormant status

This protocol is frozen while v23 run `31418890891` is still in progress and before any v23 scientific result is known.

v24 is **dormant unless v23 returns a scientific FAIL**. A v23 PASS permanently disables this contingency. A technical v23 no-result does not authorize v24; v23 must first be repaired and scientifically adjudicated without changing its frozen science.

## Purpose

v22 showed that combined-two-year family-quality training can prioritize cross-year-imbalanced representatives. v23 tests the single-target remedy `min(F1_2013,F1_2014)`. If that single-target formulation fails, the only preregistered next ranking hypothesis is to model each year's membership quality separately and require both predictions to be strong.

## Frozen architecture

v24 preserves exactly the v22/v23:

- pretruth family universe;
- fixed v19 rank-sum top-100 joint-conformal memberships;
- 71 label-free features;
- unchanged v22 best-label/group assignment;
- strict whole-shower deterministic five-fold grouping across Sugar/HDBSCAN routes;
- exact #839 ExtraTrees model class/hyperparameters and inverse-group weighting;
- diversity lambda `0.8`, scale `1.0`;
- exact v19 parameter-free rank-sum fusion;
- exact #854 equal-budget one-to-one literature evaluation;
- all pretruth/truth/firewall ordering.

For each family, the unchanged v22 best label is first fixed. Families nonpositive under v22's unchanged precision/overlap qualification have both regression targets set to zero. Positive families receive two targets against that same label:

- `T2013 = F1_2013`
- `T2014 = F1_2014`

Two independent copies of the exact #839 model are trained on the same training rows and the same strict grouped folds, one per target. For each held-out family the sole v24 quality score is:

`min(predicted_F1_2013, predicted_F1_2014)`.

No averaging, product, learned combiner, calibration, target weight, year weight, or alternate score is allowed.

Exactly two deployable OOF orders are permitted:

1. `twohead_worst_prediction_quality`: exact #839 diversity ordering of the sole worst-predicted-year score.
2. `twohead_worst_prediction_v19_rank_sum`: parameter-free equal rank-sum of order 1 with exact v19 rank-sum, using the already-frozen v19 fusion helper.

Exact v19 remains a mandatory identity control.

## Decision gate

Selection uses the unchanged v22/v23 robust four-panel lexicographic key. A pairwise win requires candidate macro-F1 > frozen literature macro-F1 and candidate recovered-F1>0.5 count >= literature. v24 passes only if one frozen successor wins all four matched panels.

Only an OOF all-panel PASS may authorize one full two-head SonotaCo model freeze for later separately preregistered protected cross-survey validation. Full-fit in-sample SonotaCo performance is ineligible evidence.

## Prohibitions

- no execution before a scientific v23 FAIL;
- no target/model/feature/diversity/fusion search;
- no alternate combination of the two predictions;
- no candidate or membership change;
- no comparator-budget-specific ranking rule;
- no post-result v24 rescue;
- no MAARSY, DMS, OrbitTrace target information, target-region event, or 20°–55° target-content access.

SonotaCo remains exposed development only.
