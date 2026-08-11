# OrbitTrace v24 joint annual recovery-state classifier v1

## Scientific role

Separately named exposed-SonotaCo development successor after three distinct strict whole-shower objectives failed: continuous annual-F1 regression (#950), balanced two-year recovery classification (#997), and two independent annual family-level recovery classifiers (#1013). The remaining objective-level hypothesis is that the binary classifiers discard useful structure by treating a family that is recoverable in exactly one year as equivalent to a family recoverable in neither year.

## Sole scientific change

For every family, keep the exact PR #950 annual F1 values for the unchanged v22 fixed best label and convert them at the already-frozen literature recovery threshold 0.5 into one four-state target:

- state 0: neither year recoverable (`F1_2013<=0.5`, `F1_2014<=0.5`);
- state 1: 2014 only;
- state 2: 2013 only;
- state 3: both years recoverable.

The 0.5 threshold is inherited from the literature evaluator and is not searched.

Fit one `ExtraTreesClassifier` using the exact PR #951 capacity: 600 trees, depth 4, min leaf 5, all 71 features, seed 20260809, `class_weight='balanced'` recomputed from the classes present in each OOF training fold, plus exact #839 inverse-group sample weights. All fragments/near-misses tied to one known shower remain in the same deterministic whole-shower five-fold split across both Sugar and HDBSCAN routes.

The sole held-out quality score is the classifier probability of **state 3 (both-year recoverable)**. Partial-recovery class probabilities are not combined, weighted, or separately ranked. State-3 probability receives exact #839 diversity (`lambda=0.8`, `scale=1.0`) and one parameter-free equal rank-sum with exact frozen v19. Only that final order is a promotion candidate.

## Frozen quantities

- exact immutable PR #950 v22 71D pretruth features, centroids, fixed memberships, candidate universes, and v19 orders;
- exact v22 best-label/group semantics and exact PR #950 annual F1 definitions;
- exact literature recovery threshold 0.5;
- exact strict whole-shower five-fold grouping across both matched routes;
- exact PR #951 classifier capacity and fold-local balanced class weighting;
- exact #839 inverse-group weights;
- exact #839 diversity 0.8/1.0;
- exact v19 order and one equal rank-sum fusion;
- exact equal-budget one-to-one annual literature evaluator.

No class merging, state weight, probability combination, threshold, model capacity, class-weight formula, calibration, resampling, feature, diversity, fusion, source quota, or comparator-specific search is authorized. Exactly one classifier score/order is evaluated.

## Binding gate

The first technically valid execution is binding. PASS requires the sole final order to beat the literature comparator in all four Sugar/HDBSCAN 2013/2014 panels: macro-F1 strictly higher and recovered `F1>0.5` count at least equal in every panel. Otherwise this exact four-state classifier is a permanent no-go.

Only a 4/4 OOF PASS may freeze a full exposed-SonotaCo classifier. In-sample full-fit scores are never promotion evidence.

SonotaCo 2013/2014 remains exposed development-only. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar-longitude 20°–55° content remain inaccessible.