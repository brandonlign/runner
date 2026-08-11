# OrbitTrace v24 two-head + representative-classifier fusion v1

## Scientific role

Separately named exposed-SonotaCo development successor reconciling the two complementary strict whole-shower OOF v24 branches already preserved in PR #950 and PR #951. This is not a retune of either failed branch.

PR #950's two annual F1 regression heads were stronger on HDBSCAN 2013 (10/10 recovered, macro-F1 0.14257102406283795), while PR #951's representative classifier was slightly stronger in HDBSCAN 2014 macro-F1 (0.13072925356649356 versus 0.12833942693327394), with both branches beating Sugar 2013/2014. PR #951 explicitly froze the scientific boundary that a later successor may reconcile these complementary held-out signals.

## Sole successor order

Recompute the exact two historical strict-group OOF learned signals on the exact same immutable v22 71D route payloads:

1. **Two-head annual-quality signal** — exact PR #950 logic: exact v22 best-label/group assignment; annual `F1_2013` and `F1_2014` targets for unchanged v22-positive families; two exact #839 ExtraTrees regressors; held-out score `min(pred_2013,pred_2014)`; exact #839 diversity `lambda=0.8`, `scale=1.0`.
2. **Representative-classifier signal** — exact PR #951 logic: one deterministic best positive representative per eligible shower per route; exact strict same-shower global folds; one fixed ExtraTreesClassifier (600 trees, depth 4, min leaf 5, all features, seed 20260809, `class_weight='balanced'` within each fold); raw held-out class-1 probability; exact #839 diversity `lambda=0.8`, `scale=1.0`.
3. **Frozen v19 signal** — exact pre-existing v19 rank-sum order from the immutable v22 pretruth manifest.

The sole successor order is one **equal three-way rank sum** over those three complete catalogue orders. Each family receives the sum of its 1-based positions in: (a) the diversity-processed two-head order, (b) the diversity-processed representative-classifier order, and (c) exact v19. Lower summed rank is better. Exact v22 `tie_rank`, then stable family ID, break exact summed-rank ties.

This formulation counts v19 exactly once. The already-v19-fused historical v24 winner orders are controls only and are not re-fused, so v19 cannot receive implicit double weight.

## Binding reproduction guards

Before the new fusion result is accepted, the recomputation must reproduce the exact historical v24 winner metrics:

PR #950 `twohead_worst_prediction_v19_rank_sum`:
- Sugar 2013: 0.27806630131631344 / 16
- Sugar 2014: 0.32869544907104964 / 17
- HDBSCAN 2013: 0.14257102406283795 / 10
- HDBSCAN 2014: 0.12833942693327394 / 7

PR #951 `representative_classifier_oof_v19_rank_sum`:
- Sugar 2013: 0.27806630131631344 / 16
- Sugar 2014: 0.31911211573771636 / 17
- HDBSCAN 2013: 0.13911011444031582 / 9
- HDBSCAN 2014: 0.13072925356649356 / 7

If either control fails exact metric reproduction (within 1e-12 for macro-F1, exact recovered count), the execution is a technical no-result and the successor is not evaluated as scientific evidence.

## Frozen quantities

- exact v22 71-dimensional pretruth features, centroids, candidate universes, and fixed v19-expanded memberships;
- exact shared Sugar+HDBSCAN strict whole-shower deterministic five-fold assignment;
- exact #839 model complexity and inverse-group weights for the annual regression heads;
- exact PR #951 representative target and classifier capacity/class-balancing rule;
- exact #839 diversity `lambda=0.8`, `scale=1.0` applied independently to each learned signal before fusion;
- exact v19 complete order;
- exact #854-compatible equal-budget one-to-one annual literature evaluator.

No fusion weight, rank product, sequential fusion, min/max vote, annual combiner, representative threshold, classifier/regressor capacity, class weight, calibration, feature, diversity, source quota, or comparator-budget-specific search is authorized. There is exactly one successor candidate.

## Binding gate

The first technically valid execution is binding. PASS requires the sole three-way order to beat the corresponding literature comparator on all four Sugar/HDBSCAN 2013/2014 panels: macro-F1 strictly higher and recovered `F1>0.5` count at least equal in every panel. Otherwise this exact complementary-signal fusion is a permanent no-go.

Only a 4/4 OOF PASS may freeze full exposed-SonotaCo component models for later separately governed protected validation. In-sample full-fit scores are never promotion evidence.

SonotaCo 2013/2014 remains exposed development-only. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar-longitude 20°–55° content remain inaccessible.