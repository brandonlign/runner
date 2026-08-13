# OrbitTrace GMN v31 radial-coherence KS v1 — frozen protocol

## Status

**PRE-OUTCOME SCIENTIFIC FREEZE.** This document fixes one target-excluded GMN 2022/2023 successor to the exact v31 hard-family local-geometry method before implementation is executed and before any candidate performance outcome is available.

Parent: exact v31 GMN offline-development package / 226 immutable hard families. Parent fused controls are fixed at:

- recovered@25 = `23`
- recovered@50 = `41`
- recovered@100 = `66`
- top-100 dominant precision = `0.7229521515453452`
- MRR = `0.050244164168646674`
- qualified matches = `95`

The protected solar-longitude interval `[20°,55°]` remains inaccessible. SonotaCo 2013/2014 is not accessed by this experiment. OrbitTrace target information/events, MAARSY, and DMS are not accessed.

## Scientific motivation

Exact v31 already contains substantial recurrence/coherence information. Its immutable 23D representation includes event-count, anchor/quartet/component structure, best detector score, annual support-strength min/max/balance, member-year balance, cross-year centroid distance, pooled member-to-centroid distance summaries, and label-free centroid-neighborhood features. Therefore this successor does **not** add another support-balance, event-count, centroid-shift, nearest-neighbor, or summary-spread feature.

The remaining representation question is narrower: a physically recurrent stream should reproduce not only its centroid and a few upper-tail spread summaries, but the **shape of its member concentration around the radiant/speed centroid** across independent years. Two families can have the same median/q90/max radial spread while having materially different radial concentration profiles. That distributional recurrence is not represented by the exact v31 23D coordinates.

This is distinct from the closed activity-profile KS lane. Activity-profile KS compared annual distributions along the activity coordinate (`sol`). The present successor excludes the activity coordinate entirely and uses only the three-dimensional radiant/speed residual state. It is also distinct from covariance-shape successors: no covariance matrix, principal axis, eigenvalue, orientation, anisotropy, or Mahalanobis quantity is computed. The proposed statistic is a scalar, rotation-insensitive empirical radial-profile recurrence measure.

## Sole scientific change

Append exactly one 24th feature to the exact v31 23D feature matrix.

For each immutable hard family `f` and each year `y in {2022, 2023}`:

1. Use the exact frozen family membership and exact frozen annual centroid `c_y`.
2. For every member event `e` from year `y`, compute one radiant/speed radial distance

   `r(e,c_y) = sqrt(d_lon^2 + d_lat^2 + d_v^2)`

   where:

   - `d_lon = circular_delta(e['sun_lon'], c_y['sun_lon']) / 4.0`
   - `d_lat = abs(e['ecl_lat'] - c_y['ecl_lat']) / 4.0`
   - `d_v = abs(log(|e['vg']| / |c_y['vg']|)) / log(1.10)`

   with both speeds floored only by the established numerical floor `1e-6` before the ratio.
3. The activity coordinate `sol` is **not** used in this new distance.
4. Require at least one exact frozen member in each year; otherwise fail closed before scoring.
5. Let `R_2022` and `R_2023` be the two empirical radial-distance samples.
6. Compute the ordinary two-sample Kolmogorov-Smirnov distance

   `D_KS = sup_r |F_2022(r) - F_2023(r)|`.

7. Append exactly `D_KS` as the 24th coordinate. No p-value is used.

The statistic has no bandwidth, histogram, bin count, radius threshold, k, covariance estimator, learned parameter, or fitted scale.

## Exact inherited v31 architecture

Everything except the single appended feature is immutable:

- exact 226 hard-family universe and memberships;
- exact v31 23D matrix, byte-for-byte reconstructed and checked against the frozen offline package;
- exact five deterministic strict-whole-shower folds;
- exact frozen binary qualified/nonqualified development reference used by the v31 GMN principle test;
- fold-training mean / population-standard-deviation z-scaling, zero standard deviation -> `1.0`;
- ordinary Euclidean distance in the resulting 24D standardized space;
- k = `1` nearest positive and nearest nonpositive reference;
- margin = `d_nonpositive - d_positive`;
- exact diversity order with lambda `0.8`, scale `1.0`, and immutable hard-order tie semantics;
- exact equal 1-based rank-sum fusion with the immutable P19 hard order;
- exact evaluator and eligibility semantics.

The experiment must first reproduce the exact 23D parent matrix, centroid matrix, parent OOF margin hash, hard baseline metrics, and parent fused metrics before the 24D candidate is accepted as technically valid.

## Binding promotion gate

The first technically valid candidate outcome is binding.

PASS requires **all** of:

1. recovered@100 > `66`;
2. recovered@25 >= `23`;
3. recovered@50 >= `41`;
4. top-100 dominant precision >= `0.7229521515453452`;
5. MRR >= `0.050244164168646674`;
6. qualified matches exactly `95`;
7. every provenance and protected-data/firewall assertion passes.

A PASS may authorize a separately frozen SonotaCo exposed-development compatibility benchmark. It does not itself establish literature superiority or external validation.

A FAIL terminates this successor without SonotaCo access.

## No-rescue closure

After the first technically valid result, do **not** rescue this mechanism by changing or adding:

- Cramer-von Mises, Anderson-Darling, Wasserstein, energy, MMD, or another distribution statistic;
- KS p-values, sample-size weighting, weighted KS, one-sided KS, signed KS, or annual direction rules;
- histogram/bin/kernel/bandwidth/radius representations;
- activity-coordinate (`sol`) inclusion or any activity/radiant combined-axis variant;
- per-axis KS statistics, axis subsets, axis weights, alternate physical scales, log/exp/power transforms of `D_KS`, or clipping;
- radial quantile/moment/skew/kurtosis companions;
- covariance/eigenvalue/anisotropy/Mahalanobis variants;
- alternate centering, pooled-year centering, robust centering, member trimming, outlier removal, or membership changes;
- k, metric, fold, scaling, reference-definition, diversity, fusion, threshold, budget, rank-window, source, feature-subset, or weight changes;
- blending this feature with the failed activity-profile KS feature or another failed successor;
- post-result identity-specific corrections or second searches.

Any future method after a binding FAIL must change mechanism class and be independently motivated and frozen.

## Firewall and claim boundary

The workflow must assert:

- `blind_exclusion == [20.0,55.0]`;
- `sonotaco_2013_2014_access == false`;
- `target_information_access == false`;
- `target_region_events_accessed == false`;
- `maarsy_scientific_access == false`;
- `dms_scientific_access == false`.

Scientific role: `TARGET_EXCLUDED_GMN_2022_2023_V31_SUCCESSOR_DEVELOPMENT_ONLY`.

No SonotaCo result, target identity, protected-region event, MAARSY result, DMS result, post-result diagnostic identity, HDB oracle identity, or three-way-consensus identity may enter this feature or its ranking rule.
