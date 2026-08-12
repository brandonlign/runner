# OrbitTrace GMN member-covariance shape OOF v1

Status: **FROZEN BEFORE IMPLEMENTATION OR SCIENTIFIC OUTCOME**.

## Scientific role

This is one target-excluded GMN 2022/2023 successor to the clean representative-share parent from PR #1194. It is motivated only by clean GMN development evidence.

The binding representative-share oracle diagnostic showed that the exact #1194 target and exact #1194 diversity rule can recover **100 distinct qualified shower labels in the first 100 ranks** when the target is known perfectly, whereas the deployable strict-OOF #1194 model recovers 80. Therefore the current bottleneck is prediction from the frozen 34D family representation, not candidate coverage, the representative-share target, or the fixed diversity operator.

The current 34D representation includes family counts, annual strengths, centroid drift, radial member-distance summaries, source indicators, P20 generation descriptors, and label-free family-neighborhood densities. It does not encode the joint second-order shape of the meteor events inside a family. The sole hypothesis here is that physically scaled within-family member-cloud covariance contains complementary, portable information about coherent shower morphology.

This is **not** the older v32 covariance-local-geometry mechanism. That exposed-development method estimated covariance across a fold-training 71D candidate-feature matrix to define Mahalanobis distances between candidate feature vectors. The present successor instead computes label-free second moments of the actual meteor events inside each already-generated GMN family and appends only invariant summaries to the clean #1194 representation.

## Immutable parent and inputs

Scientific parent source:

- commit: `a2d11f45cd6e5d6a3f80738a43e04962162abd23`;
- file: `orbittrace_gmn_representative_share_ranking_v1/run_development.py`;
- Git blob SHA-1: `340f9d54b42ba2500652d7f0a74f22bbd3354f2e`.

Immutable active URC source:

- source-export run: `31344632499`;
- artifact: `orbittrace-active-urc-ranker-source-export-v1`;
- source SHA-256: `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`.

Immutable candidate inputs:

- hard/v8 development run `31217916558`;
- P19 development run `31340446086`;
- P20 development run `31341591263`;
- exact candidate counts: hard `226`, P19 `1075`, P20 `3203`, union `4504`.

The runtime, parser, candidate memberships, family IDs, family centroids, labels, eligible-shower definition, strict shower grouping, and all 34 parent features are unchanged.

## Protected-data firewall

Before any label, feature, family, fold, score, or endpoint used here is formed, the existing protected solar-longitude exclusion **20.0° through 55.0° inclusive** remains in force through the inherited frozen GMN runtime.

This experiment must not access:

- OrbitTrace target information;
- target-region events;
- SonotaCo 2013/2014 data, features, labels, scores, or outcomes;
- MAARSY scientifically;
- DMS scientifically.

No SonotaCo result may select, alter, or interpret the candidate configuration.

## Sole scientific change: six label-free member-cloud shape features

For each existing family `f` and each year `y in {2022, 2023}`, use only that family's already-frozen member event IDs for year `y`, the corresponding events from the target-excluded GMN development scan, and the family's already-frozen annual centroid `c_y`.

Every family must have at least one member and a finite centroid in each year; otherwise execution fails closed before a candidate outcome.

For member event `e`, define the signed physically scaled offset from the frozen annual family centroid:

- `z0 = signed_circular_delta(e.sol, c_y.sol) / 10.0`;
- `z1 = signed_circular_delta(e.sun_lon, c_y.sun_lon) / 4.0`;
- `z2 = (e.ecl_lat - c_y.ecl_lat) / 4.0`;
- `z3 = log(max(abs(e.vg), 1e-6) / max(abs(c_y.vg), 1e-6)) / log(1.10)`.

where

`signed_circular_delta(a,b) = ((a - b + 180.0) mod 360.0) - 180.0`.

These are the same four physical axes and fixed scale constants already inherited by the GMN family geometry. No new physical scale is selected.

For year `y`, define the population fixed-centroid second-moment matrix

`C_y = (1 / n_y) * sum_e z_e z_e^T`.

No Bessel correction, robust covariance estimator, shrinkage, ridge, trimming, outlier rejection, or learned metric is permitted.

Let:

- `t_y = trace(C_y)`;
- `lambda_y = sort_desc(clip(eigvalsh(C_y), 0, +inf))`;
- `s_y = sum(lambda_y)`;
- with fixed numerical constant `eps = 1e-12`, `p_y = lambda_y / s_y` when `s_y > eps`, otherwise the four-vector of zeros;
- `H_y = -sum_{j:p_yj>0} p_yj * log(p_yj) / log(4)` when `s_y > eps`, otherwise `0`.

Append exactly these six features, in this order, to the existing 34 parent features:

1. `member_shape_log_mean_scatter = log1p((t_2022 + t_2023) / 2)`;
2. `member_shape_mean_major_fraction = (p_2022[0] + p_2023[0]) / 2`;
3. `member_shape_mean_spectral_entropy = (H_2022 + H_2023) / 2`;
4. `member_shape_scatter_balance = (min(t_2022,t_2023) + eps) / (max(t_2022,t_2023) + eps)`;
5. `member_shape_covariance_alignment = sum(C_2022 * C_2023) / (||C_2022||_F * ||C_2023||_F)` when the denominator is greater than `eps`, otherwise `0`;
6. `member_shape_log_drift_to_scatter = log1p(d_centroid / sqrt((t_2022 + t_2023)/2 + eps))`, where `d_centroid` is the exact inherited #1194 `centroid_crossyear_distance` in the same fixed four-dimensional physical geometry.

Numerical roundoff may be clipped only as follows:

- eigenvalues below zero after symmetric eigendecomposition are set to zero;
- covariance alignment is clipped to `[0,1]` after computation.

No other clipping or transform is allowed.

The candidate feature matrix therefore has exactly **40 columns**: the unchanged 34D #1194 representation followed by this fixed six-feature block.

## Everything else frozen from #1194

The following are identical to #1194:

- representative-share target construction;
- strict `SHOWER/<label>` whole-shower five-fold OOF assignment;
- all fragments of one positive shower remain in one fold;
- grouped training weights;
- `ExtraTreesRegressor` with `n_estimators=600`, `max_depth=4`, `min_samples_leaf=5`, `max_features=None`, `random_state=20260809`;
- no estimator or hyperparameter search;
- exact label-free diversity rule with `lambda=0.8`, `scale=1.0`;
- candidate universe and memberships;
- all evaluation definitions.

The 34D parent must be recomputed in the same execution and reproduce exactly before the 40D candidate is accepted as a scientific result.

Required exact parent controls:

- recovered@25 = `22`;
- recovered@50 = `43`;
- recovered@100 = `80`;
- recovered@500 = `171`;
- top-100 dominant precision = `0.8075287489258385`;
- MRR = `0.02016666446026534`;
- qualified matches = `256`;
- parent OOF order SHA-256 = `a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592`.

Any mismatch is technical no-result and fails closed.

## Binding scientific gate

The first technically valid 40D strict-OOF execution is binding.

PASS requires **all** of the following simultaneously:

- recovered@100 **> 80**;
- recovered@25 **>= 22**;
- recovered@50 **>= 43**;
- recovered@500 **>= 171**;
- top-100 dominant precision **>= 0.8075287489258385**;
- MRR **>= 0.02016666446026534**;
- qualified matches **== 256**.

A PASS permits a separately frozen full-GMN fit of this exact representation/model and later governance-compliant transfer work. It does not authorize SonotaCo-guided tuning or protected-target application.

If any gate fails, this exact member-covariance-shape augmentation is a permanent no-go. Do not rescue it by changing the physical scales, centering rule, covariance estimator, `ddof`, epsilon, eigenvalue treatment, feature subset, feature transforms, orientation/alignment formula, per-source variants, estimator, ExtraTrees hyperparameters, target, group weights, folds, diversity parameters, or by blending with the parent.

A failure does not by itself close genuinely different higher-order or learned family representations, but those would require a new independently motivated and separately frozen protocol.
