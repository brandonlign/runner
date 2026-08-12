# OrbitTrace GMN rank-Gaussian Fisher OOF diagnostic v1

## Scientific role

This is a **target-excluded GMN 2022/2023 architectural successor** to the binding `PASS_GMN_BALANCED_SHRINKAGE_FISHER_OOF` method. It is frozen before outcome and uses no SonotaCo 2013/2014 result, OrbitTrace target information, protected 20°–55° event, MAARSY, or DMS information to choose its mechanism.

The Fisher parent assumes that fold-training arithmetic z-standardization makes the 23 intrinsic dimensions suitable for a covariance-based linear discriminant. The exact authorized fixture shows strong marginal-shape heterogeneity without using recoverability truth: count-like dimensions span `4→343` and `5→660` and have substantial extreme-tail mass, while several fixed neighbor-derived dimensions are constant zero in this family universe. Such skew/heavy tails can give a small number of families high covariance leverage even after ordinary z-scoring.

This successor tests exactly one monotone robustification: **fit a training-fold empirical CDF independently for each feature, map that CDF to standard-normal quantiles, then apply the exact balanced shrinkage Fisher architecture**. The transform preserves within-feature order while reducing sensitivity to raw marginal tail magnitude. No transform family, clipping, winsorization, feature selection, or tuning is evaluated.

## Authoritative parent and fixture

Binding parent: `PASS_GMN_BALANCED_SHRINKAGE_FISHER_OOF`.

Use only the exact `PASS_GMN_DEVELOPMENT_FIXTURE_V1` artifact and fail closed unless it reproduces:
- candidate count `226`;
- feature dimension `23`;
- feature SHA256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- immutable hard-order SHA256 `2dcaaffaefca68e877fea82ff46a68bbd4c7960dedfdd00a114311d41605b65e`;
- k=1 parent margin SHA256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- scaled Fisher parent SHA256 `9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e`;
- Fisher recovered@100 `69`;
- Fisher recovered@50 `41`;
- Fisher top-100 dominant precision `0.7677499561973543`;
- Fisher MRR `0.05055989766869564`;
- qualified families `95`.

The fixture is engineering-only; candidate generation and memberships remain immutable. Before candidate interpretation, reproduce the exact Fisher parent ranking and all five metrics from the fixture's frozen Fisher score.

## Exact OOF empirical normal-score transform

Use the fixture's exact features, recoverability target, deterministic five whole-shower folds, centroids, memberships, truths, eligible-label universe, IDs, and hard order.

For each fold and each of the 23 features independently, let the **raw training values only** be `t_1,...,t_n`.

For any scalar value `x`, define:
- `L(x) = number of training values strictly less than x`;
- `E(x) = number of training values exactly equal to x`;
- empirical plotting position

  `p(x) = [L(x) + 0.5*E(x) + 0.5] / (n + 1)`.

The sole transformed value is

`r(x) = Phi^{-1}(p(x))`,

where `Phi^{-1}` is the standard-normal inverse CDF.

Properties of this fixed rule:
- it uses no labels;
- it uses training-fold values only;
- `0 < p(x) < 1` for every finite training or held-out value, so no clipping or epsilon is required;
- exact ties receive one shared midpoint score;
- a training-constant feature maps identically to zero (`p=0.5`) for training and equal held-out values.

Apply this transform to every training and held-out family using only that fold's training empirical distribution.

### Exact post-rank standardization

To preserve the Fisher parent's scale semantics after the monotone transform, fit the arithmetic mean and population standard deviation (`ddof=0`) of the transformed **training** rows for each feature. Replace only exactly-zero transformed standard deviations by `1.0`, then z-standardize transformed training and held-out rows with those training statistics.

There is no alternate plotting-position formula, quantile clipping, interpolation between order statistics, smoothing, Box–Cox/Yeo-Johnson transform, robust-z transform, feature-specific rule, or transform search.

## Exact balanced shrinkage Fisher after transformation

Using the transformed/z-standardized training rows and the exact parent recoverability classes:
1. compute `mu_pos` and `mu_neg`;
2. fit `LedoitWolf(assume_centered=False, store_precision=False)` separately to positive and nonpositive training rows;
3. require finite symmetric class covariances and shrinkage coefficients in `[0,1]`;
4. form `Sigma = 0.5*Sigma_pos + 0.5*Sigma_neg`;
5. require positive-definite pooled covariance;
6. compute `w = solve(Sigma, mu_pos - mu_neg)`;
7. midpoint `m = 0.5*(mu_pos + mu_neg)`;
8. sole raw held-out score `rF(x) = dot(x-m,w)`.

There is no class-prior adjustment, covariance estimator search, covariance weighting, regularization search, QDA term, feature subset, dimensionality reduction, group balancing, block balancing, nonlinear classifier, threshold, or parent/candidate blend.

## Frozen score-unit preservation

Because the unchanged diversity routine subtracts a fixed proximity penalty directly from score units, restore the raw rank-Gaussian Fisher score to the typical absolute scale of the binding Fisher parent score:
- `A_parent = median(abs(fisher_parent_scaled))`;
- `A_rank = median(abs(rF))`;
- require both finite and strictly positive;
- `unit_factor = A_parent / A_rank`;
- sole successor diversity input `rF_scaled = rF * unit_factor`.

This positive scalar cannot change pre-diversity sign or ordering. No alternate scale statistic or calibration is authorized.

## Frozen ranking and binding gate

Apply exactly the parent centroid geometry, diversity (`lambda=0.8`, `scale=1.0`), tie semantics, and exactly one equal rank-sum fusion with immutable P19 hard order.

The first technically valid outcome is binding.

PASS requires the sole fused rank-Gaussian Fisher order simultaneously to:
- recover **strictly more than 69** qualified families in top 100;
- recover at least `41` in top 50;
- top-100 dominant precision at least `0.7677499561973543`;
- MRR at least `0.05055989766869564`;
- preserve exactly `95` qualified families.

Failure of any gate permanently rejects this exact rank-Gaussian architecture. No plotting-position variant, clipping, transform blend, raw/rank Fisher blend, covariance change, feature change, calibration, diversity/fusion change, threshold, or post-result rescue is authorized.

A PASS is target-excluded GMN development only and does not automatically authorize a SonotaCo transfer.

## Firewall

- blind exclusion `[20.0,55.0]` mandatory;
- SonotaCo 2013/2014 access: false;
- target information access: false;
- target-region events accessed: false;
- MAARSY scientific access: false;
- DMS scientific access: false.
