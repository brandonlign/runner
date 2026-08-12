# OrbitTrace GMN balanced shrinkage Fisher OOF diagnostic v1

## Scientific role

This is a **target-excluded GMN 2022/2023 architectural successor diagnostic** using the same fixed family universe and 23D intrinsic representation as the binding successful v31-principle GMN parent, but a fundamentally different scoring mechanism.

The successful parent and the subsequently closed distributed-evidence mechanism are local-reference methods: they infer recoverability from either nearest references or a local kernel-weighted reference distribution. This successor tests a complementary hypothesis: **recoverable families may occupy a globally displaced direction in the intrinsic family space even when the local neighborhood is heterogeneous**.

The sole mechanism is a class-balanced, shrinkage-stabilized two-class Fisher direction fit within each exact OOF training fold. No SonotaCo result or protected target information is used to choose or tune it.

## Immutable scientific inputs

Unchanged:
- exact 226 P19 hard-family candidates and memberships;
- immutable P19 hard order;
- target-excluded GMN 2022/2023 catalogue;
- exact 23D intrinsic representation (10 structural, 7 cohesion, 6 centroid-neighbor dimensions);
- exact recoverability reference target;
- deterministic five-fold whole-shower grouping;
- fold-training-only mean and population-SD z-standardization, replacing only zero SD by 1;
- exact centroid geometry used by diversity;
- diversity `lambda=0.8`, `scale=1.0`;
- hard-rank/stable-ID tie semantics;
- exactly one equal rank-sum fusion with immutable hard order.

The same execution must reconstruct the successful parent k=1 Euclidean OOF margin and binding parent metrics before this successor is scientifically interpretable:
- parent OOF margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- recovered@100: `66`;
- recovered@50: `41`;
- top-100 dominant precision: `0.7229521515453452`;
- MRR: `0.050244164168646674`;
- qualified families: `95`.

## Balanced shrinkage Fisher mechanism

For each exact OOF fold, after the exact parent z-transform is fit on all training families:

1. Split only the training z-vectors into the exact parent positive and nonpositive recoverability reference classes.
2. Compute class means `mu_pos` and `mu_neg`.
3. Fit `sklearn.covariance.LedoitWolf(assume_centered=False, store_precision=False)` separately to the positive and nonpositive training z-vectors, yielding `Sigma_pos` and `Sigma_neg`.
4. Require both covariance matrices finite and symmetric to absolute tolerance `1e-12`, and require both Ledoit-Wolf shrinkage coefficients finite in `[0,1]`.
5. Form the **equal-class pooled covariance**

   `Sigma = 0.5 * (Sigma_pos + Sigma_neg)`.

   The exact `0.5/0.5` average prevents the larger class from dominating the within-class scatter merely through sample count.
6. Require `Sigma` finite, symmetric to absolute tolerance `1e-12`, and positive definite.
7. Compute the Fisher direction

   `w = solve(Sigma, mu_pos - mu_neg)`.

8. Define the equal-prior class midpoint

   `m = 0.5 * (mu_pos + mu_neg)`.

9. The sole raw held-out score is

   `f(x) = dot(x - m, w)`.

A positive score points toward the recoverable-class mean along the shrinkage-whitened between-class direction. Equal-class covariance weighting and the midpoint imply equal class priors; no empirical-prior intercept is added.

There is no logistic fit, SVM, tree, neural model, class-prior search, covariance estimator search, covariance mixing weight, diagonal covariance, class-specific quadratic discriminant, regularization parameter, dimensionality reduction, feature selection, threshold selection, or nonlinear transform.

## Frozen score-unit preservation

The fixed diversity machinery subtracts a proximity penalty directly from the score. To avoid changing the effective diversity weight merely because Fisher scores use different units, after all OOF scores are complete define:

- `A_parent = median(abs(parent_margin))`;
- `A_fisher = median(abs(f))`;
- require both finite and strictly positive;
- `unit_factor = A_parent / A_fisher`;
- sole diversity input `f_scaled = f * unit_factor`.

This is a positive scalar multiplication and cannot change the Fisher score sign or pre-diversity order. No alternate scale statistic or calibration is authorized.

## Frozen ranking and binding gate

Apply exactly the parent `diversity_order` to `f_scaled`, with `lambda=0.8`, `scale=1.0`, then exactly one equal rank-sum fusion with immutable hard order.

The first technically valid outcome is binding.

PASS requires the sole fused Fisher order simultaneously to:
- recover **strictly more than 66** qualified families in the top 100;
- recover at least `41` in the top 50;
- top-100 dominant precision at least `0.7229521515453452`;
- MRR at least `0.050244164168646674`;
- preserve exactly `95` qualified families.

Failure of any gate permanently rejects this exact balanced shrinkage Fisher architecture. No alternate prior, covariance weighting, covariance estimator, solver, regularization, feature subset, scaling, diversity, fusion, or post-result rescue is authorized.

A PASS establishes only a target-excluded GMN mechanism improvement and may motivate a separately frozen transfer/validation protocol. It does not authorize SonotaCo tuning.

## Firewall

- blind exclusion `[20.0,55.0]` mandatory;
- SonotaCo 2013/2014 access: false;
- target information access: false;
- target-region events accessed: false;
- MAARSY scientific access: false;
- DMS scientific access: false.
