# OrbitTrace v63 GMN-balanced-Fisher SonotaCo transfer v1

## Scientific role

This is one separately frozen **SonotaCo 2013/2014 exposed-development transfer** motivated exclusively by the binding target-excluded GMN success `PASS_GMN_BALANCED_SHRINKAGE_FISHER_OOF`.

SonotaCo 2013/2014 remains exposed development only and is **not external validation**.

The binding GMN Fisher run (`31565972049`, job `94017720509`, artifact `9129508430`, artifact digest `sha256:d5338751651c4122dab4f91bc4e2b652b307c0f36d83d1f293fe68f5da8d15df`) improved the already-strong GMN local-geometry parent from 66 to 69 recovered families at top 100, retained 41 at top 50, raised top-100 dominant precision from 0.7229521515453452 to 0.7677499561973543, and raised MRR from 0.050244164168646674 to 0.05055989766869564. All preregistered GMN gates passed.

v63 transfers that **exact architectural principle** to the already-frozen SonotaCo intrinsic family representation. It does not tune Fisher parameters on SonotaCo and does not reuse the failed v62 local-geometry result to alter the mapped columns, class definition, covariance rule, diversity, fusion, memberships, or evaluation gate.

## Immutable SonotaCo candidate universe and representation

Use exactly the same v24/v22 SonotaCo pretruth payload and immutable memberships used by v31/v62:
- Sugar: 267 families;
- HDBSCAN: 229 families;
- exact v19 order unchanged;
- exact centroids unchanged;
- all source manifests and memberships must have `truth_accessed=false` before representation construction.

Construct the representation using **the exact frozen v62 pretruth constructor**, with no code or column change. Select exactly these zero-based columns from the immutable 71D v22 matrix:

`(1,2,3,4,5,6,7,8,9,10,14,15,16,17,18,19,20,28,29,30,31,32,33)`.

These are the exact 23 intrinsic dimensions used in the GMN Fisher PASS:
- 10 structural dimensions;
- 7 cohesion dimensions;
- 6 centroid-neighborhood dimensions.

The pretruth representation must reproduce the binding v62 seals exactly before SonotaCo truth is loaded:
- overall pretruth SHA256: `1988fcb89781a3ba94d19bd7b2e0c058c13b39c73ed020f7931c772952069e64`;
- Sugar 23D feature SHA256: `423c9aef746cd873270cf8950ce79d93620282d12161449ebc99863f748834c7`;
- HDBSCAN 23D feature SHA256: `e0a8162e2b4d73df68552d56f0f81305e28cda1fc539d9e88943e42fb3394663`.

No feature search, replacement, imputation, weighting, source indicator, relative-rank transform, graph feature, or post-result representation edit is allowed.

## Exact recoverability target transferred from GMN

After the 23D pretruth matrices are sealed, load the already-exposed SonotaCo 2013/2014 truth.

For each family, use the existing v22 `family_truth` definition over the combined two-year truth and the exact recurrent-shower eligibility rule. A family is positive exactly when:
- its best eligible recurrent label has precision `>= 0.5`; and
- overlap `>= 4`.

This is the same overall family recoverability definition used by the binding GMN Fisher mechanism. Annual F1 labels are **not** used for Fisher training and no annual-min Fisher variant is evaluated.

Strict whole-shower grouping remains mandatory across both routes: every fragment whose fixed best label is the same recurrent shower is assigned to the same deterministic five-fold OOF group. Nonpositive/no-label families use their fixed route/family negative group.

## Exact transferred Fisher architecture

Stack Sugar and HDBSCAN 23D families into one OOF training universe, preserving route offsets only for the final route-local ranking step.

For each deterministic OOF fold:

1. Fit the arithmetic mean and population standard deviation (`ddof=0`) on **all training families only** for all 23 dimensions; replace exactly-zero standard deviations by 1.0.
2. Transform train and held-out families to that training z-space.
3. Split training references by the exact overall positive/nonpositive recoverability target.
4. Compute `mu_pos` and `mu_neg`.
5. Fit `sklearn.covariance.LedoitWolf(assume_centered=False, store_precision=False)` separately to positive and nonpositive training z-vectors, producing `Sigma_pos` and `Sigma_neg`.
6. Form the exact equal-class covariance

   `Sigma = 0.5 * (Sigma_pos + Sigma_neg)`.

7. Require finite, symmetric, positive-definite covariance and finite Ledoit-Wolf shrinkage coefficients in `[0,1]`.
8. Compute the exact Fisher direction

   `w = solve(Sigma, mu_pos - mu_neg)`.

9. Compute the equal-prior midpoint

   `m = 0.5 * (mu_pos + mu_neg)`.

10. Sole raw Fisher score for held-out family `x`:

    `f(x) = dot(x - m, w)`.

There is no class-prior search, covariance-weight search, covariance-estimator search, regularization search, diagonal approximation, QDA, logistic model, tree, SVM, neural model, feature subset, dimensionality reduction, threshold, or nonlinear transform.

## Exact score-unit transfer for frozen diversity

The GMN Fisher PASS preserved the existing diversity weight by scaling Fisher scores to the typical absolute scale of the corresponding **overall 23D k=1 OOF nearest-positive/nonpositive margin**. v63 transfers that units rule exactly.

In the same SonotaCo folds, compute an auxiliary overall reference margin using the same overall recoverability classes:

`r(x) = d_nonpositive - d_positive`

where each distance is ordinary Euclidean distance in the exact 23D fold-training z-space to the nearest training reference of that class (`k=1`).

This auxiliary reference margin is **not a promotion candidate and is never evaluated against literature**. It exists only to preserve score units for the unchanged diversity routine.

After all OOF scores are complete:
- `A_ref = median(abs(r))` over the complete stacked 496-family OOF universe;
- `A_fisher = median(abs(f))` over the same universe;
- require both finite and strictly positive;
- `unit_factor = A_ref / A_fisher`;
- sole ranking score `f_scaled = f * unit_factor`.

No route-specific scaling, alternate quantile/statistic, interpolation, clipping, calibration, or post-result scale adjustment is allowed.

## Frozen route-local ranking and parent controls

For each route separately:
1. take its slice of `f_scaled`;
2. apply the exact #839 geometric diversity with `lambda=0.8`, `scale=1.0` and immutable tie ranks;
3. exactly one equal rank-sum fusion with the immutable v19 route order;
4. evaluate that fused order as the sole v63 promotion candidate.

The exact exported v31 parent orders must reproduce these frozen SonotaCo parent controls before v63 interpretation:
- Sugar 2013: `0.2719801488280529 / 16`;
- Sugar 2014: `0.31529041952487225 / 17`;
- HDBSCAN 2013: `0.14888037368183737 / 9`;
- HDBSCAN 2014: `0.15198123772301594 / 9`.

## Binding literature gate

The first technically valid v63 outcome is binding.

PASS requires the sole fused Fisher order to beat the corresponding frozen literature comparator in **all four** Sugar/HDBSCAN × 2013/2014 panels:
- macro-F1 strictly greater than literature; and
- recovered `F1 > 0.5` count at least equal to literature.

Otherwise v63 is permanently rejected. No route-specific rule, Fisher/local-geometry blend, annual Fisher, alternate covariance, prior, scaling, diversity, fusion, threshold, source quota, feature change, or membership rescue is authorized.

v31 remains the strongest demonstrated SonotaCo method unless v63 passes this frozen 4/4 gate.

## Firewall

- SonotaCo 2013/2014 role: `EXPOSED_DEVELOPMENT_ONLY`.
- OrbitTrace protected target solar-longitude interval 20°–55° remains inaccessible.
- OrbitTrace target information and target-region events remain inaccessible.
- MAARSY and DMS remain scientifically inaccessible.
- Candidate memberships are immutable.
- No protected or held-out catalogue is authorized by this protocol.
