# OrbitTrace GMN source-blind quality-diversity v1

## Purpose

Test one GMN-only domain-robustness hypothesis suggested independently by PR #977's target-excluded result: whether the successful #839 family-quality regressor remains viable or improves when the entire seven-feature generator/source-specific block is removed.

This experiment does not access SonotaCo, MAARSY, DMS, OrbitTrace target information, or protected 20°–55° target-region events.

## Frozen universe

Use exactly the #839 target-excluded GMN 2022/2023 union:

- 226 hard families;
- 1,075 P19 families;
- 3,203 P20 families;
- union 4,504.

Use exact #839 family truth, positive predicate, same-shower grouping, inverse-group weights, ExtraTrees regression complexity, and geometric diversity lambda `0.8`, scale `1.0`, complete backfill, no family deletion.

## Required control

Before the candidate is interpretable, exact #839 quality+diversity must reproduce:

- r25/r50/r100/r500 = 22/40/75/159;
- top100 dominant precision = `0.7645689180574315`;
- qualified matches = 256;
- MRR = `0.019037817654898162`.

## Single candidate

Exact #839 uses 34 features in this order:

1. 14 pre-existing generic structural features;
2. 7 pre-existing generic membership-cohesion features;
3. 7 generator/source-specific features: hard/P19/P20 one-hot plus four P20-native fields;
4. 6 pre-existing label-free neighbor-density features.

The sole source-blind candidate removes item 3 as one indivisible seven-feature block. It therefore uses exactly **27 features**: the first 21 generic structural/cohesion features plus the exact six #839 neighbor-density features.

Everything else is unchanged:

- target = exact #839 family F1 when the exact positive predicate passes, otherwise zero;
- exact deterministic same-shower five-fold OOF grouping;
- exact inverse-group sample weights;
- `ExtraTreesRegressor`, 600 trees, max depth 4, min leaf 5, all features, seed 20260809;
- exact #839 diversity lambda 0.8 / scale 1.0;
- complete 4,504-family backfill.

No alternate feature subset, neighbor definition, model, target, fold, weight, diversity setting, fusion, calibration, source quota, or parameter search is authorized.

## GMN gate

The 27D source-blind candidate passes only if:

- recovery@100 >= 75;
- recovery@50 >= the exact hard-v8 baseline recovery@50;
- top100 dominant precision >= hard-v8 top100 precision - 0.05;
- qualified matches >= 230; and
- comparison key `(r100, r50, r25, top100 precision, MRR)` is lexicographically strictly greater than exact #839.

Only a PASS may freeze the full 27D GMN ExtraTrees model for a later separately named no-retuning exposed-SonotaCo application. A FAIL permanently rejects this exact source-block ablation and does not authorize partial restoration or feature search.

## Firewall

`blind_exclusion = [20.0, 55.0]` remains enforced. SonotaCo 2013/2014 access = false. MAARSY scientific access = false. DMS scientific access = false. OrbitTrace target information access = false. Target-region events accessed = false.
