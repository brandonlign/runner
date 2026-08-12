# OrbitTrace GMN v31-principle shrinkage-Mahalanobis OOF diagnostic v1

## Scientific role

This is a **target-excluded GMN 2022/2023 successor diagnostic** to the binding `PASS_GMN_V31_PRINCIPLE_LOCAL_GEOMETRY_OOF` parent. It does not access SonotaCo, OrbitTrace target information, protected 20°–55° events, MAARSY, or DMS.

The successful parent uses a 23D intrinsic family representation, training-fold univariate z-standardization, and `k=1` Euclidean nearest-positive / nearest-nonpositive geometry. Univariate standardization equalizes marginal scales but does not account for correlated feature directions. If several intrinsic descriptors encode the same physical degree of freedom, ordinary Euclidean distance can implicitly count that direction multiple times.

This successor tests exactly one parameter-free covariance correction: **Ledoit–Wolf shrinkage Mahalanobis distance fit only on each training fold after the exact parent z-standardization**. Ledoit–Wolf is chosen before outcome because it provides a deterministic, analytically estimated shrinkage covariance without a tunable regularization parameter and is well-conditioned for a 23D representation with roughly 180 training families per fold.

No SonotaCo result is used to choose this metric.

## Immutable parent

The following remain exactly unchanged:
- 226 P19 hard-family candidates and memberships;
- immutable hard order;
- exact 23D intrinsic representation;
- target-excluded GMN 2022/2023 catalogue;
- parent recoverability reference definition;
- deterministic five-fold whole-shower groups;
- fold-training-only feature means and marginal standard deviations;
- `k=1` nearest positive and `k=1` nearest nonpositive reference rule;
- signed margin `d_nonpositive - d_positive`;
- diversity `lambda=0.8`, `scale=1.0`;
- hard-rank/stable-ID tie semantics;
- one equal rank-sum fusion with the immutable hard order.

Binding parent controls:
- OOF Euclidean margin SHA256: `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`
- recovered@100: `66`
- recovered@50: `41`
- top-100 dominant precision: `0.7229521515453452`
- MRR: `0.050244164168646674`
- qualified families: `95`

The same execution must reconstruct those parent controls exactly before the successor can be interpreted.

## Sole scientific change: training-fold shrinkage Mahalanobis metric

For each of the exact parent folds:

1. Compute the exact parent training-fold mean and population standard deviation for all 23 dimensions; replace only zero standard deviations by 1 exactly as in the parent.
2. Transform training and held-out features to the same parent z-space.
3. Fit `sklearn.covariance.LedoitWolf(assume_centered=False, store_precision=True)` on **all training-fold z-vectors without using recoverability labels**.
4. Require the returned precision matrix to be finite, symmetric to numerical tolerance, and positive definite.
5. For each held-out family, compute Mahalanobis distance under that one training-fold precision matrix to every positive and nonpositive training reference.
6. Set `d_pos` and `d_neg` to the respective `k=1` minima and define the sole successor score as `d_neg - d_pos`.

No diagonal-only, empirical covariance, OAS, manually regularized covariance, PCA, whitening rank cutoff, class-specific covariance, supervised metric learning, or shrinkage search is allowed.

The covariance fit is label-free and training-fold-only. Recoverability labels are used only to divide already-transformed training references into the same parent positive/nonpositive classes for nearest-reference lookup.

## Frozen post-score machinery

Use exactly the parent centroid geometry, diversity order (`lambda=0.8`, `scale=1.0`), tie semantics, and one equal rank-sum fusion with the immutable P19 hard order.

## Binding gate

The first technically valid result is binding.

PASS requires the sole fused shrinkage-Mahalanobis order simultaneously to:
- recover strictly more than `66` qualified families in the top 100;
- recover at least `41` in the top 50;
- top-100 dominant precision at least `0.7229521515453452`;
- MRR at least `0.050244164168646674`;
- preserve exactly `95` qualified families.

Failure of any gate permanently rejects this exact metric successor. No covariance estimator, regularization, metric interpolation, k, feature, scaling, diversity, fusion, threshold, or post-result rescue is authorized.

A PASS establishes only a target-excluded GMN mechanism improvement and may motivate a separately frozen cross-dataset successor.

## Firewall

- blind exclusion `[20.0,55.0]` remains mandatory;
- SonotaCo 2013/2014 access: false;
- target information access: false;
- target-region events accessed: false;
- MAARSY scientific access: false;
- DMS scientific access: false.
