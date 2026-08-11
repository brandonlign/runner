# OrbitTrace v24 annual recovery classifier v1

## Scientific role

Separately named exposed-SonotaCo development successor after the v24 annual-F1 regressors localized the remaining problem to rare high-quality ordering under unseen-shower generalization. The post-result v24 diagnosis showed several genuinely excellent held-out families were shrunk toward the bulk by squared-error regression. This successor changes the supervised loss/objective, not the candidate universe, memberships, representation, folds, or literature gate.

## Sole scientific change

Keep the exact PR #950 annual F1 targets for the unchanged v22 fixed best label, but threshold each annual target at the already-frozen literature recovery criterion:

- `y_2013 = 1` iff exact `F1_2013 > 0.5`, else 0;
- `y_2014 = 1` iff exact `F1_2014 > 0.5`, else 0.

The 0.5 threshold is the existing benchmark recovered-shower definition and is not selected from this experiment.

Fit exactly two annual `ExtraTreesClassifier` heads using the already-frozen PR #951 classifier architecture: 600 trees, depth 4, min leaf 5, all 71 features, seed 20260809, `class_weight='balanced'` recomputed inside each training fold, plus exact #839 inverse-group sample weights. Strict deterministic whole-shower five-fold OOF grouping remains global across both Sugar and HDBSCAN routes, so no family from a held-out shower is present in either annual head's training fold.

Held-out quality is exactly the already-frozen v24 conservative combiner `min(P(recoverable_2013), P(recoverable_2014))`. That single score receives exact #839 diversity (`lambda=0.8`, `scale=1.0`) and then one parameter-free equal rank-sum with exact frozen v19. Only that final fused order is a promotion candidate.

## Frozen quantities

- exact immutable v22 71D pretruth features, centroids, candidate universes, and v19-expanded fixed memberships from the valid PR #950 artifact;
- exact v22 best-label and positive/group semantics;
- exact deterministic global same-shower five-fold OOF firewall;
- exact PR #951 classifier capacity and fold-local balanced class weighting;
- exact #839 inverse-group sample weights;
- exact annual probability combiner `min(p2013,p2014)`;
- exact #839 diversity `lambda=0.8`, `scale=1.0`;
- exact frozen v19 order and one equal rank-sum fusion;
- exact #854-compatible equal-budget one-to-one annual literature evaluator.

No threshold, class-weight formula, probability calibration, resampling, annual combiner, model capacity, feature, diversity, fusion weight, rank product, source quota, or comparator-specific search is authorized. There is exactly one successor order.

## Binding gate

The first technically valid execution is binding. PASS requires the single final order to beat the corresponding literature comparator in all four Sugar/HDBSCAN 2013/2014 panels: macro-F1 strictly higher and recovered `F1>0.5` count at least equal in every panel. Otherwise this exact annual-recovery classifier architecture is a permanent no-go.

Only a 4/4 OOF PASS may freeze full exposed-SonotaCo annual classifier heads. In-sample full-fit scores may never determine promotion.

SonotaCo 2013/2014 remains exposed development-only. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar-longitude 20°–55° content remain inaccessible.