# OrbitTrace GMN diagonal shrinkage Fisher OOF diagnostic v1

## Scientific role

This is a **target-excluded GMN 2022/2023 architectural successor** to the binding `PASS_GMN_BALANCED_SHRINKAGE_FISHER_OOF` method. It is frozen before outcome and uses no SonotaCo 2013/2014 result, OrbitTrace target information, protected 20°–55° event, MAARSY, or DMS information to choose its mechanism.

The Fisher parent uses separate positive/nonpositive Ledoit–Wolf covariance estimates and then an equal-class pooled full covariance. In every binding GMN fold, the positive covariance is heavily shrunk (`~0.61–0.73`) while the nonpositive covariance is moderately shrunk (`~0.21–0.23`). The failed QDA successor showed that retaining class-specific full covariance geometry is worse than Fisher, while equal-block and group-balanced successors also failed. This leaves one clean structural question: **are the off-diagonal covariance terms themselves useful, or are the stable marginal variances carrying most of the Fisher signal?**

This successor tests exactly one simplification: retain the diagonal of each already-fixed Ledoit–Wolf covariance, discard every off-diagonal entry, then perform the same equal-class Fisher construction. No covariance interpolation or alternate diagonal estimator is evaluated.

## Authoritative parent and fixture

Binding parent: `PASS_GMN_BALANCED_SHRINKAGE_FISHER_OOF`.

Use only the exact `PASS_GMN_DEVELOPMENT_FIXTURE_V1` artifact. Fail closed unless it reproduces:
- candidate count `226`;
- feature dimension `23`;
- feature SHA256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- immutable hard-order SHA256 `2dcaaffaefca68e877fea82ff46a68bbd4c7960dedfdd00a114311d41605b65e`;
- exact k=1 parent margin SHA256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- exact scaled Fisher score SHA256 `9957292fbe41efa407b9bc5b1f4160cdc0899632135a10b56d2f91f04d54c46e`;
- Fisher recovered@100 `69`;
- Fisher recovered@50 `41`;
- Fisher top-100 dominant precision `0.7677499561973543`;
- Fisher MRR `0.05055989766869564`;
- qualified families `95`.

The fixture is an engineering cache of already-authorized target-excluded GMN development information. Candidate generation and memberships remain immutable.

Before candidate interpretation, reproduce the binding Fisher parent ranking and all five parent metrics exactly from the fixture's frozen Fisher score.

## Exact OOF preprocessing and target

Use the fixture's exact 226×23 feature matrix, recoverability vector, whole-shower groups/folds, centroid matrix, memberships, truths, eligible-label universe, IDs, and hard order.

For each exact five-fold OOF split:
1. fit arithmetic mean and population standard deviation (`ddof=0`) on **all individual training families** in all 23 dimensions;
2. replace only exactly-zero standard deviations with `1.0`;
3. z-transform all training and held-out families;
4. split the training z-vectors by the exact parent recoverability class.

No feature, target, fold, group, or scaling change is permitted.

## Sole scientific change: diagonalized Ledoit–Wolf Fisher geometry

Within each fold:
1. compute positive and nonpositive class means `mu_pos`, `mu_neg`;
2. fit exactly `LedoitWolf(assume_centered=False, store_precision=False)` separately to positive and nonpositive training z-vectors, producing full covariances `Sigma_pos`, `Sigma_neg`;
3. require both full covariance estimates finite, symmetric to absolute tolerance `1e-12`, with shrinkage coefficients finite in `[0,1]`;
4. define the sole diagonalized covariances:

   `D_pos = diag(diag(Sigma_pos))`

   `D_neg = diag(diag(Sigma_neg))`;

5. require every retained diagonal variance finite and strictly positive;
6. form the exact equal-class diagonal pool

   `D = 0.5 * D_pos + 0.5 * D_neg`;

7. require every pooled diagonal entry finite and strictly positive;
8. compute the Fisher direction exactly as

   `w = solve(D, mu_pos - mu_neg)`;

9. use the exact equal-prior midpoint

   `m = 0.5 * (mu_pos + mu_neg)`;

10. the sole raw held-out score is

   `d(x) = dot(x - m, w)`.

There is no raw empirical diagonal-variance model, variance floor, covariance interpolation, full/diagonal blend, shrinkage search, alternate covariance estimator, class-prior adjustment, feature subset, dimensionality reduction, QDA term, block term, group balancing, nonlinear transform, or threshold.

## Frozen score-unit preservation

The parent diversity routine subtracts a fixed proximity penalty directly from score units. Therefore restore the raw diagonal-Fisher score to the typical absolute scale of the exact binding Fisher parent score:

- `A_parent = median(abs(fisher_parent_scaled))`;
- `A_diag = median(abs(d))`;
- require both finite and strictly positive;
- `unit_factor = A_parent / A_diag`;
- sole successor diversity input `d_scaled = d * unit_factor`.

This is one positive scalar multiplication only and cannot change the pre-diversity score sign or ordering. No alternate scale statistic or calibration is allowed.

## Frozen ranking and binding gate

Apply exactly the Fisher parent:
- centroid geometry;
- diversity `lambda=0.8`, `scale=1.0`;
- hard-rank/stable-ID tie semantics;
- exactly one equal rank-sum fusion with immutable P19 hard order.

The first technically valid outcome is binding.

PASS requires the sole fused diagonal-Fisher order simultaneously to:
- recover **strictly more than 69** qualified families in the top 100;
- recover at least `41` in the top 50;
- top-100 dominant precision at least `0.7677499561973543`;
- MRR at least `0.05055989766869564`;
- preserve exactly `95` qualified families.

Failure of any gate permanently rejects this exact diagonal-covariance architecture. No full/diagonal interpolation, alternate diagonal variance estimator, covariance weighting, parent/diagonal blend, feature change, score calibration, diversity/fusion change, threshold, or post-result rescue is authorized.

A PASS is target-excluded GMN development only. It does not automatically authorize another SonotaCo transfer.

## Firewall

- blind exclusion `[20.0,55.0]` remains mandatory;
- SonotaCo 2013/2014 access: false;
- target information access: false;
- target-region events accessed: false;
- MAARSY scientific access: false;
- DMS scientific access: false.
