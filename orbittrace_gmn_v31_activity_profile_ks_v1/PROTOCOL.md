# OrbitTrace GMN v31 cross-year activity-profile KS v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 representation successor to exact v31. It is frozen before implementation and before any candidate outcome.

The current GMN-only v31 diagnostics establish that the dominant top-100 failure is genuine representation overlap rather than fusion, calibration, or a one-reference boundary error:

- 21/29 exact fused-v31 top-100 misses are outside the same budget in both frozen parent constituents;
- all 21 have no positive family representative with raw v31 margin > 0;
- 17/21 have at least two nonpositive references ahead of even their best nearest positive representative;
- the wrong-side squared-distance gap is multi-coordinate: every one of those 21 has at least six negative-favoring coordinates, with median nine.

Second-order member-cloud covariance/anisotropy and simple MST topology are already closed. The present successor therefore introduces a genuinely different physical observable: **cross-year recurrence of the within-family meteor activity-phase distribution**.

Meteor-shower activity is physically defined as occurrence rate versus solar longitude, and multi-year/multi-instrument studies use the activity profile's duration and shape to characterize streams. The frozen hypothesis is that a real recurrent shower family should reproduce not only a centroid and radial cohesion but also the empirical distribution of member occurrence phase from 2022 to 2023, whereas an accidental family can match coarse geometry without reproducing the full activity-phase CDF.

The sole scientific change is one new scalar feature: the two-sample Kolmogorov-Smirnov distance between each family's 2022 and 2023 member solar-longitude offsets from its own frozen annual centroid. No histogram, binning, bandwidth, moment, width, FWHM, skewness, p-value, or activity-feature search is used.

## Independent methodological basis fixed before outcome

The two-sample KS statistic is

`D_KS(F22,F23) = sup_x |F22(x)-F23(x)|`

for the two empirical CDFs. It is deterministic, parameter-free, invariant to a common positive scale, and sensitive to any one-dimensional distribution-shape difference rather than only mean/variance.

The use here is strictly as a label-free family representation feature. No KS p-value is used, because the sample-size-dependent p-value would confound shape difference with family member count already represented elsewhere.

The activity-profile motivation is fixed from primary meteor literature before outcome: activity profiles are measured as functions of solar longitude and their duration/shape are physical stream observables; multi-instrument analyses compare annual profile shape and duration across years. No literature result is used to choose a threshold or weight.

## Authoritative inputs and exact v31 reconstruction

This successor must use the exact target-excluded GMN runtime and exact frozen hard-family memberships already audited by the member-cloud development lineage.

Immutable candidate source:

- exact P19 prelabel hard-family payload used by the #1194 lineage;
- hard-family count = **226**;
- exact hard order identical to the offline-v31 package.

The exact v31 23D representation must be reconstructed from the raw frozen runtime before the activity feature is evaluated:

1. ten exact intrinsic structural features;
2. seven exact URC-v2 cohesion features;
3. six exact hard-family centroid-neighborhood features computed on the 226-family hard centroid matrix only.

Explicitly exclude source indicators, P20 metadata, hard-rank percentile, and any new feature other than the sole KS observable.

The reconstructed 226x23 matrix must be numerically identical to the authoritative offline-v31 package under the exact pinned runtime and must hash to:

`fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`.

The reconstructed exact 226x8 centroid matrix must hash to:

`a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`.

The exact parent raw strict-OOF Euclidean margin must hash to:

`f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

Any mismatch is a technical no-result and the activity feature must not be interpreted.

## Protected-data firewall

Before any feature, fold, truth, or score used here is formed, the inherited GMN parser must exclude protected solar longitude **20.0° through 55.0° inclusive**.

This experiment must not access:

- OrbitTrace target information;
- protected target-region events;
- SonotaCo 2013/2014 data, labels, features, scores, or outcomes;
- MAARSY scientifically;
- DMS scientifically.

No SonotaCo information may select or modify this successor.

## Sole new observable: annual activity-profile KS distance

For each exact hard family `f` and year `y in {2022,2023}`:

1. use only the family's exact frozen member event IDs belonging to year `y`;
2. use the corresponding events from the target-excluded GMN scan;
3. use the family's exact frozen annual centroid `c_y`;
4. require at least one member in each year and a finite annual centroid, otherwise fail closed before a candidate result;
5. for each member event `e`, define the signed circular activity-phase offset in degrees:

   `u(e,y) = ((e.sol - c_y.sol + 180) mod 360) - 180`.

Here `sol` is the same event solar-longitude field and annual-centroid solar-longitude field already used in the frozen member-cloud lineage. No physical scale is needed because KS is invariant to common positive scaling.

Let `U22(f)` and `U23(f)` be the two empirical samples. Compute exactly the ordinary two-sided two-sample KS statistic

`activity_profile_ks = sup_x |F_U22(x)-F_U23(x)|`.

Implementation must compute the statistic directly from the two empirical CDFs or use a pinned deterministic SciPy `ks_2samp(..., alternative='two-sided', method='exact'/'auto')` only if exact equality to the direct implementation is self-tested. The **statistic only** is retained; p-value is discarded and must not enter any feature or diagnostic.

Require every KS value finite and within `[0,1]`.

Append exactly this one feature as column 24 after the unchanged v31 23D matrix.

No activity-profile feature other than this KS distance is computed for candidate evaluation.

## Exact v31 OOF local geometry with one added coordinate

Keep the exact v31 five strict whole-shower folds and truth semantics.

For each fold independently:

- fit arithmetic mean and population standard deviation (`ddof=0`) on fold-training rows for all 24 columns;
- replace exactly-zero standard deviations by 1.0;
- standardize training and held-out rows using fold-training statistics;
- compute ordinary Euclidean distance to the single nearest positive training reference and single nearest nonpositive training reference;
- define candidate raw margin `d_nonpositive - d_positive`.

There is no k search, metric learning, covariance metric, feature weighting, scaling variant, activity-feature weighting, calibration, class weighting, resampling, probability model, or threshold.

In the same execution, recompute the exact 23D parent margin and require the frozen parent margin hash before accepting the 24D candidate.

## Frozen post-score machinery

The sole promotion candidate uses exactly the parent machinery:

1. inherited geometric diversity `lambda=0.8`, `scale=1.0`, using the exact 226x8 centroid matrix;
2. equal 1-based rank-sum fusion between the diversified 24D local order and immutable hard order;
3. exact monotone evaluator over the frozen 355 eligible labels.

The 24D diversified local-only order is diagnostic only. No alternate diversity, hard/local fusion weight, RRF, rank product, sequential rule, source quota, or budget-specific fusion is allowed.

## Required exact parent controls

Before interpreting the successor, exact v31 must reproduce:

- recovered@25 = **23**;
- recovered@50 = **41**;
- recovered@100 = **66**;
- top-100 dominant precision = **0.7229521515453452**;
- MRR = **0.050244164168646674**;
- qualified matches = **95**.

Hard-order control must reproduce:

- @25 = **21**;
- @50 = **38**;
- @100 = **59**;
- top-100 dominant precision = **0.6884631112636006**;
- MRR = **0.046734076055452344**;
- qualified matches = **95**.

## Binding GMN promotion gate

The first technically valid 24D result is binding. PASS requires every condition:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 dominant precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified matches **= 95**;
7. exact 23D/centroid/parent-margin/fold/evaluator/firewall reproduction passes.

Failure of any gate permanently rejects this exact activity-profile-KS successor.

## Fixed diagnostics only

Record without creating alternate candidates:

- min/median/max KS over all 226 families;
- min/median/max KS among positive/nonpositive families separately;
- per-family KS value and annual member counts;
- candidate 24D raw margin hash and fused order hash;
- exact parent/candidate metrics.

No subgroup-selected rank or feature is evaluated.

## Explicit no-search / no-rescue rules

There is exactly one activity feature and no search over:

- KS axis other than `sol`;
- raw-vs-centered activity phase;
- annual-centroid centering rule;
- histogram bins;
- KDE bandwidth;
- Wasserstein/energy/MMD activity distances;
- Cramér-von Mises, Anderson-Darling, Kuiper, Earth-mover, Jensen-Shannon, or other distribution distance;
- KS p-value;
- activity width/FWHM/IQR/MAD;
- skewness/kurtosis/multimodality;
- activity peak count;
- feature transforms, clipping, exponents, thresholds, weights, interactions, or blocks;
- k, metric, reference editing, diversity, or fusion variants.

If this first valid result fails, no alternate activity-profile statistic may be chosen from the outcome as a rescue. A genuinely different observable would require independent motivation and a separately frozen protocol.

## SonotaCo boundary

Only a GMN PASS may authorize a separately frozen one-shot SonotaCo comparison using the already-established exact v31 feature correspondence plus a **pre-outcome auditable SonotaCo implementation of this same activity-profile KS observable**. If that exact observable cannot be reconstructed comparably on SonotaCo without post-result mapping choices, transfer must stop rather than improvise.

SonotaCo remains EXPOSED DEVELOPMENT ONLY, never external validation.