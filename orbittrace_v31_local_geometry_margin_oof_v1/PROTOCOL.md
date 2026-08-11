# OrbitTrace v31 strict-OOF local-geometry margin ranker v1

## Scientific role
Separately frozen exposed-SonotaCo development successor after diagnostics #1020/#1021. This is not a rescue of v24 and does not alter the fixed candidate universe, memberships, 71D representation, folds, diversity, or literature evaluator.

The motivating frozen diagnostics show two facts: (1) missed HDB recoverable groups have lower training support in aggregate, and (2) several near-cutoff misses are nevertheless locally closer in the exact 71D geometry to annual-recoverable training examples than to nonrecoverable examples. The tree/loss family has already been exhausted. This experiment therefore changes only the supervised mapping from the fixed 71D representation to ranking score: replace learned tree prediction with one parameter-free nearest-reference geometry margin.

## Sole ranking rule
Use the immutable #950 v22 71D features and exact deterministic strict-whole-shower five-fold OOF assignment across the stacked Sugar+HDBSCAN exposed-development family universe.

For each OOF fold and each year separately:
1. compute arithmetic mean and population standard deviation (`ddof=0`) for every one of the 71 features on fold-training examples only; replace exactly-zero standard deviations by 1.0;
2. standardize training and held-out examples with those fold-training statistics;
3. define annual positive training examples by the already-frozen literature event `F1_y > 0.5` for the exact fixed v22 best recurrent label; all remaining training examples are annual nonpositive;
4. for each held-out family compute ordinary Euclidean distance to the single nearest annual-positive training example and single nearest annual-nonpositive training example;
5. annual margin is `d_nonpositive - d_positive`, so larger is more recoverable-like;
6. combine the two annual margins with the already-frozen conservative v24 rule `min(margin_2013, margin_2014)`.

There is no k search (`k=1` only), metric search, feature subset, distance weighting, temperature, margin threshold, calibration, class weight, resampling, tree/model fit, route-specific rule, or source quota.

## Frozen post-score machinery
For each route independently, apply exact #839 geometric diversity (`lambda=0.8`, `scale=1.0`) to the combined margin and then one parameter-free equal rank-sum with the immutable v19 order. Only that fused order is a promotion candidate. No classifier-only/local-margin-only promotion candidate, rank product, sequential fusion, alternate diversity, or fusion weight is evaluated.

## Binding gate
The first technically valid execution is binding. PASS requires the sole fused order to beat the corresponding literature comparator in all four Sugar/HDBSCAN 2013/2014 panels: macro-F1 strictly higher and recovered F1>0.5 count at least equal in every panel. Otherwise this exact local-geometry architecture is permanently rejected; no k, metric, scaling, target threshold, annual combiner, diversity, or fusion rescue is authorized.

A full exposed-SonotaCo reference package may freeze only after a 4/4 OOF PASS and is not pristine external validation. SonotaCo 2013/2014 remains exposed development-only. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar longitude 20-55 degrees remain inaccessible.
