# OrbitTrace v32 strict-OOF Ledoit-Wolf local-geometry ranker v1

## Scientific role
Separately frozen exposed-SonotaCo development successor after the clean v31 no-go and diagnostic #1028. v31 showed that parameter-free local geometry is competitive, reaching full HDBSCAN-2014 recovery (9/9) while missing its macro-F1 by only ~0.0049, but ordinary Euclidean distance after per-feature standardization still lost both HDBSCAN panels. Independently, #1028 showed that the dominant raw-#839 and relative-noncategorical feature blocks jointly carry most nearest-positive distance and are structurally correlated; no small removable feature block explains the gap.

This experiment changes exactly one structural assumption from v31: diagonal standardized Euclidean geometry -> a single covariance-aware Mahalanobis geometry estimated by parameter-free Ledoit-Wolf shrinkage on each fold's training covariates. It does not reopen k, feature, target, threshold, annual-combiner, diversity, or fusion choices.

## Sole ranking rule
Use the immutable #950 v22 71D features, fixed memberships/candidate universes, and exact deterministic strict-whole-shower five-fold OOF assignment across stacked Sugar+HDBSCAN exposed-development families.

For each OOF fold:
1. compute fold-training arithmetic mean and population standard deviation (`ddof=0`) for all 71 features; replace exactly-zero standard deviations by 1.0;
2. standardize training and held-out examples using only those fold-training statistics;
3. fit exactly `sklearn.covariance.LedoitWolf(assume_centered=True, store_precision=True)` to the standardized fold-training covariates only, with no labels entering covariance estimation;
4. require the fitted precision matrix to be finite, symmetric, and positive definite, then use its unique symmetric positive-definite square-root to map standardized vectors into a whitened Euclidean space whose ordinary distance equals the Ledoit-Wolf Mahalanobis distance;
5. for each year separately, define annual positive training examples by the existing frozen event `F1_y > 0.5` for the exact fixed v22 best recurrent label; all remaining fold-training examples are annual nonpositive;
6. for each held-out family compute distance to the single nearest annual-positive and single nearest annual-nonpositive training examples in that covariance-aware space;
7. annual margin is `d_nonpositive - d_positive` (larger = more recoverable-like);
8. combine annual margins with exact frozen v24/v31 conservative rule `min(margin_2013, margin_2014)`.

There is no k search (`k=1` only), shrinkage selection, covariance estimator search, feature subset/weight, distance threshold, calibration, class weighting, resampling, route-specific geometry, or source quota. Ledoit-Wolf's shrinkage coefficient is estimated analytically by its fixed algorithm and is not a tuned hyperparameter.

## Frozen post-score machinery
For each route independently apply exact #839 diversity (`lambda=0.8`, `scale=1.0`) to the combined margin, then exactly one parameter-free equal rank-sum with the immutable v19 order. Only that fused order is a promotion candidate. No local-only promotion, rank product, sequential fusion, alternate diversity, or fusion weight is evaluated.

## Binding gate
The first technically valid execution is binding. PASS requires the sole fused order to beat the corresponding literature comparator in all four Sugar/HDBSCAN 2013/2014 panels: macro-F1 strictly higher and recovered F1>0.5 count at least equal in every panel. Otherwise this exact v32 covariance-aware geometry is permanently rejected; no alternate covariance estimator, shrinkage, regularization, metric, k, scaling, feature subset, annual combiner, diversity, or fusion rescue is authorized.

A full exposed-SonotaCo reference package may freeze only after a 4/4 OOF PASS. SonotaCo 2013/2014 remains exposed development-only, not pristine external validation. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar longitude 20-55 degrees remain inaccessible.
