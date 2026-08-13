# OrbitTrace GMN v31 centroid-width ratio v1 — frozen protocol

## Status

**PRE-OUTCOME SCIENTIFIC FREEZE.** This defines exactly one target-excluded GMN 2022/2023 offline successor to the exact v31 hard-family local-geometry method before any candidate score/rank/performance result is calculated.

Authoritative offline package: `orbittrace-gmn-v31-offline-development-package-v1`, artifact `9167087908`. Exact parent feature matrix SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`; parent margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

Parent fused controls:
- recovered@25 = `23`
- recovered@50 = `41`
- recovered@100 = `66`
- top-100 dominant precision = `0.7229521515453452`
- MRR = `0.050244164168646674`
- qualified matches = `95`

No raw catalogue, SonotaCo, OrbitTrace target, protected 20°–55° region, MAARSY, or DMS access is required or authorized.

## Scientific motivation

Exact v31 already contains both (a) cross-year centroid displacement and (b) member-cloud radial width, but it treats them as independent standardized coordinates. The physically relevant stability question is scale-relative: the same absolute annual centroid displacement is much less concerning for a broad stream than for a very narrow stream.

This successor therefore adds one dimensionless persistence quantity: annual centroid displacement normalized by the family’s own conservative annual radial width. It is not a new metric search, activity-profile statistic, covariance model, drift fit, feature subset, or supervised transformation.

## Sole scientific change

Append exactly one 24th coordinate to the immutable v31 23D matrix:

`centroid_width_ratio = centroid_crossyear_distance / year_q90_distance_max`

Using exact v31 feature indexing this is:

`X[:, 9] / X[:, 16]`.

The source schema is fixed:
- v31 coordinate 9 = `centroid_crossyear_distance`;
- v31 coordinate 16 = `year_q90_distance_max`, the maximum of the annual member-to-centroid q90 distances.

A pre-outcome, label-free feasibility audit established only that all 226 denominators are finite and strictly positive; therefore no epsilon, clipping, fallback, missing-value rule, or filtering is needed. That feasibility check did not inspect development labels or candidate outcomes.

No existing coordinate is removed. The candidate matrix is exactly `column_stack([X23, centroid_width_ratio])`.

## Exact inherited v31 evaluator

Everything else remains exact v31:
- immutable 226 hard families;
- exact offline strict-group folds and binary development labels;
- five strict whole-shower OOF folds;
- fold-training mean / population-standard-deviation scaling, zero std -> `1.0`;
- ordinary Euclidean distance;
- k=1 nearest positive and nearest nonpositive;
- margin `d_nonpositive - d_positive`;
- exact diversity lambda `0.8`, scale `1.0`, immutable hard-order ties;
- exact equal 1-based rank-sum fusion with immutable P19 hard order;
- exact monotone GMN evaluator and eligible-label universe.

The offline evaluator must reproduce the exact parent feature SHA, parent margin SHA, hard-order control, and fused v31 control before the new coordinate can produce a technically valid outcome.

## Binding PASS gate

The first technically valid outcome is binding. PASS requires all:
1. recovered@100 > `66`;
2. recovered@25 >= `23`;
3. recovered@50 >= `41`;
4. top-100 dominant precision >= `0.7229521515453452`;
5. MRR >= `0.050244164168646674`;
6. qualified matches exactly `95`;
7. all offline-package and firewall provenance checks pass.

A FAIL terminates this ratio mechanism without SonotaCo access.

## No-rescue closure

After the binding outcome do not retry:
- inverse, logarithm, square root, square, sigmoid, clipping, winsorization, ranking, percentile, or other transform of the ratio;
- alternate denominator using pooled median/q90/max, annual minimum q90, event counts, support strengths, centroid-neighbor distance, covariance scale, or any fitted scale;
- alternate numerator, signed displacement, per-axis displacement, activity-coordinate displacement, or drift slope;
- additive/difference/product/harmonic/geometric combination of the same two coordinates;
- thresholds, bins, top-k/rank-window rules, source conditioning, feature selection, weighting, metric/k/scaling/diversity/fusion changes;
- blending with activity KS, radial-coherence KS, or another failed/unfinished successor;
- any post-result identity-specific correction or second search.

Any later successor must change mechanism class and be independently motivated/frozen.

## Firewall

Scientific role: `TARGET_EXCLUDED_GMN_2022_2023_V31_OFFLINE_SUCCESSOR_DEVELOPMENT_ONLY`.

Required assertions:
- raw event rows accessed = false;
- SonotaCo 2013/2014 accessed = false;
- protected target-region events accessed = false;
- OrbitTrace target information accessed = false;
- MAARSY scientific access = false;
- DMS scientific access = false.
