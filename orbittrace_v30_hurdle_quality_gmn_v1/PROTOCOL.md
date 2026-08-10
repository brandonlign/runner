# OrbitTrace v30 hurdle-quality GMN development v1

## Motivation

The exposed v29 canonical SonotaCo failure and the non-deployable #976 oracle diagnose a **ranking-transfer failure, not a candidate/membership ceiling**. v29's purity-only score over-promoted many P20 families that were genuinely shower-pure but incomplete: purity solves false-positive contamination but does not estimate recall/completeness.

This successor is developed **only on the already-target-excluded GMN 2022/2023 development corpus**. No SonotaCo truth or oracle-selected family/rank/source information enters training, model selection, features, weights, or thresholds.

The architecture is a standard hurdle decomposition of the same frozen family-quality target:

`expected family quality = P(positive seed) * E(F1 | positive seed)`.

The first factor is the exact #840 purity model. The second factor uses the exact #839 regression architecture, but is trained only on positive families so it learns variation in F1/completeness among genuinely shower-like seeds instead of spending most capacity separating zeros from nonzeros.

## Frozen universe and features

Use exact #839/#840 target-excluded GMN inputs:

- 226 hard v8 families;
- 1,075 P19 families;
- 3,203 P20 families;
- 4,504 total;
- exact 20°–55° firewall.

### Purity head

Exact #840 selected head:

- exact 28 #840 features;
- target = exact #839 positive predicate (dominant precision >= 0.5 and overlap >= 4);
- strict whole-shower groups including nonqualified near-misses;
- exact #840 diversity weights;
- `HistGradientBoostingClassifier`, learning rate .05, 250 iterations, 31 leaves, L2=1, seed 20260809.

No #840 Jaccard suppression/family deletion is used.

### Conditional-quality head

- exact #839 34 features;
- target = exact family F1;
- training examples = **only families satisfying the same positive predicate** used by the purity head;
- exact #839 `ExtraTreesRegressor` architecture: 600 trees, depth 4, leaf 5, all features, seed 20260809;
- strict whole-shower deterministic folds using the same best-label grouping; no held-out group may occur in conditional training;
- exact #839 grouped weights, restricted to positive training examples.

The conditional model predicts for every held-out family, but is fitted only to positive training families.

## Single successor score

For every family under OOF prediction:

`hurdle_score = purity_probability * conditional_F1_prediction`.

No exponent, mixing weight, calibration, threshold, clipping search, rank fusion, source quota, or alternative combiner is tested.

Pass this single score through exact #839 geometric diversity at the already-selected lambda `0.8`, scale `1.0`, exact tie semantics, with complete backfill and no family deletion.

## Mandatory controls

The same run must reproduce:

1. exact #839 quality+diversity metrics: r25/r50/r100/r500 = 22/40/75/159, top100 precision `0.7645689180574315`, qualified=256;
2. exact #971 purity+diversity metrics: r25/r50/r100/r500 = 24/47/81/166, top100 precision `0.8534939929790234`, MRR `0.02094738537699626`, qualified=256.

Failure of either control invalidates the run.

## Promotion rule

Compute exact #839 monotone catalogue metrics for the hurdle order.

The hurdle successor passes GMN development only if:

1. it satisfies the original #839 viability gates; and
2. its preregistered comparison key
   `(recovery@100, recovery@50, recovery@25, top100 dominant precision, MRR)`
   is **strictly greater than the reproduced v29 purity+diversity key**.

A tie or tradeoff that is lexicographically worse is a FAIL. No second model or post-result search is authorized.

## Full model freeze

Only on PASS, fit the exact two full GMN heads and freeze:

- purity HGB-31;
- conditional-quality ExtraTrees trained only on positive GMN families;
- deployment score = product;
- diversity = exact 0.8/1.0 complete-backfill rule.

No in-sample full-fit score is used for selection.

## Boundary

This is target-excluded GMN development only. No SonotaCo 2013/2014, Sugar/HDBSCAN matched rows, #976 oracle identities/ranks, MAARSY, DMS, OrbitTrace target information, or target-region event is accessed. A PASS would authorize only a separately frozen canonical SonotaCo exposed-development application.