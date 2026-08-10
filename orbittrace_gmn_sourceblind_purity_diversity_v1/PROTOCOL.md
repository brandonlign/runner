# OrbitTrace GMN source-blind purity-diversity v1

## Purpose

Test one narrowly defined cross-survey robustness hypothesis on the original target-excluded GMN 2022/2023 development universe: whether the strong #971/#972 purity+diversity signal remains scientifically viable when the purity model is denied generator/source identity and P20-native source-specific fields.

This experiment is GMN-only. It does not access or evaluate SonotaCo, MAARSY, DMS, OrbitTrace target information, or protected 20°–55° target-region events.

## Motivation boundary

PR #973 established that the exact 28-feature GMN purity model does not transfer to the canonical SonotaCo catalogue, while PR #975 established that fixed candidate/membership headroom remains. Those exposed results justify testing domain robustness, but they do **not** authorize a SonotaCo source quota, source weight, oracle imitation rule, or feature search.

Therefore exactly one new model is allowed here: remove the complete seven-feature source-specific suffix that #840 added to its pre-existing generic structural/cohesion representation. No individual source feature may be selected or restored based on results.

## Frozen universe and controls

Use exactly the #839/#840 target-excluded GMN universe:

- 226 hard families;
- 1,075 P19 families;
- 3,203 P20 families;
- total 4,504.

Use exact #839 family truth and positive predicate, exact strict whole-shower grouping, exact #840 diversity weights, exact #840 HGB-31 model, and exact #839 geometric diversity lambda `0.8`, scale `1.0`, with complete backfill and no family deletion.

Two immutable controls must reproduce before the candidate is interpretable:

1. exact #839 quality+diversity metrics: r25/r50/r100/r500 = 22/40/75/159, top100 precision `0.7645689180574315`, qualified 256;
2. exact #971 28-feature purity+diversity diagnostic: r25/r50/r100/r500 = 24/47/81/166, top100 precision `0.8534939929790234`, qualified 256, MRR `0.02094738537699626`.

## Single source-blind candidate

The #840 28-feature vector is frozen as:

- 14 pre-existing generic structural features;
- 7 pre-existing generic membership-cohesion features;
- 7 #840 source-specific features: hard/P19/P20 one-hot plus four P20-native fields.

The sole candidate uses exactly the first **21 generic features** and removes the entire seven-feature source-specific suffix as one indivisible block.

Everything else remains exact #840/#971:

- target = exact #839 positive predicate;
- deterministic strict same-shower five-fold OOF grouping, including near-misses;
- exact #840 diversity weights;
- `HistGradientBoostingClassifier`, learning rate 0.05, 250 iterations, 31 leaves, L2=1.0, random state 20260809;
- raw class-1 probability;
- exact #839 geometric diversity lambda 0.8 / scale 1.0;
- complete 4,504-family backfill.

No alternate feature subset, model, capacity, class weight, threshold, calibration, diversity value, rank fusion, source quota, or parameter search is allowed.

## GMN gate

The source-blind candidate passes only if:

- recovery@100 >= 75;
- recovery@50 >= the exact hard-v8 baseline recovery@50;
- top100 dominant precision >= hard-v8 top100 precision - 0.05;
- qualified matches >= 230; and
- its exact #839 comparison key `(r100, r50, r25, top100 precision, MRR)` is lexicographically strictly greater than exact #839 quality+diversity.

This gate is fixed before execution. The source-blind model is **not required to beat the 28-feature purity control**, because the scientific question is whether removing explicit generator/source information preserves a GMN-viable improvement over #839.

Only a PASS may freeze the full 21-feature GMN HGB-31 model for a later separately named no-retuning exposed-SonotaCo application. A FAIL permanently rejects this exact source-blind ablation; no partial restoration of source features is authorized from this result.

## Firewall

- `blind_exclusion = [20.0, 55.0]` remains enforced at source construction;
- SonotaCo 2013/2014 access = false;
- MAARSY scientific access = false;
- DMS scientific access = false;
- OrbitTrace target information access = false;
- target-region events accessed = false.
