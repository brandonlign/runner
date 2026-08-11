# OrbitTrace v32 exact-v24 leaf-support OOF ranker v1

## Scientific role

Separately frozen exposed-SonotaCo development successor after v31 (#1027) failed its binding 4/4 gate and after diagnostics #1020/#1024 localized a distinct failure mode in the exact v24 forests. #1020 showed that recoverable held-out families often enter leaves containing high-quality training analogs; #1024 showed that those analogs can carry too little training mass, so the regression leaf mean is strongly diluted. Several important missed families have positive-leaf support above 0.9 despite low v24 regression predictions.

This successor tests one anti-dilution hypothesis only. It does not tune v24 or v31 and does not use #1024's positive-weight fraction as a score.

## Sole scientific change

Reproduce the exact PR #950 strict whole-shower OOF annual regression forests using the immutable v22 71D features, exact annual F1 targets, exact #839 inverse-group weights, and exact #839 ExtraTrees regression architecture.

For each annual head and held-out family, replace the regression prediction with exactly:

`positive_leaf_support_fraction = (# trees whose held-out leaf contains at least one fold-training family with exact annual F1 > 0.5) / 600`.

The 0.5 threshold is the pre-existing literature recovery criterion. A leaf counts as supported if at least one positive training family is present; positive training weight fraction, leaf mean target, number of positive groups, leaf size, and support intensity are not used in the score.

The two annual support fractions combine with the already-frozen conservative rule:

`score = min(support_2013, support_2014)`.

That one score receives exact #839 diversity (`lambda=0.8`, `scale=1.0`) and then one parameter-free equal rank-sum with exact frozen v19. Only the final fused order is a promotion candidate.

## Binding controls

Before the v32 order is accepted, the same fitted OOF forests must reproduce the exact historical PR #950 v24 winner metrics:

- Sugar 2013: 0.27806630131631344 / 16
- Sugar 2014: 0.32869544907104964 / 17
- HDBSCAN 2013: 0.14257102406283795 / 10
- HDBSCAN 2014: 0.12833942693327394 / 7

Any failure of those controls makes the run a technical no-result.

## Frozen quantities

- exact immutable PR #950 v22 71D pretruth features, centroids, candidate universes, fixed memberships, and v19 orders;
- exact v22 best-label/group semantics and exact PR #950 annual F1 targets;
- exact deterministic global same-shower five-fold OOF assignment across Sugar+HDBSCAN;
- exact #839 inverse-group weights and ExtraTrees regression architecture;
- exactly 600 trees and the literal support-presence definition above;
- exact annual threshold 0.5 and exact `min` annual combiner;
- exact #839 diversity 0.8/1.0;
- exact frozen v19 complete order and one equal rank-sum;
- exact equal-budget one-to-one annual literature evaluator.

No positive-weight-fraction score, regression/support mixture, geometry margin, support threshold, required number of positive examples/groups, tree subset, target threshold, model capacity, feature, annual combiner, diversity, fusion weight, source quota, or comparator-specific search is authorized. There is exactly one successor candidate.

## Binding gate

The first technically valid execution is binding. PASS requires the single final order to beat the corresponding literature comparator in all four Sugar/HDBSCAN 2013/2014 panels: macro-F1 strictly higher and recovered `F1>0.5` count at least equal in every panel. Otherwise this exact leaf-support-presence architecture is a permanent no-go.

Only a 4/4 OOF PASS may freeze full exposed-SonotaCo annual forests plus their per-tree positive-leaf sets. In-sample full-fit scores are never promotion evidence.

SonotaCo 2013/2014 remains exposed development-only. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar-longitude 20°–55° content remain inaccessible.