# OrbitTrace cross-year anisotropic envelope v5 — frozen development protocol

## Purpose

Target-excluded membership-expansion v1–v4 isolate a scalar-width tradeoff:

- broad isotropic radius-1.5 expansion materially improves annual F1 but admits too much background;
- the exact parameter-free observed component radius in v4 restores recovery/precision but is too conservative to achieve the frozen annual-F1 gain gates.

The remaining hypothesis is **shape rather than scalar radius**. Meteor-stream support in the frozen solar-longitude/radiant/speed geometry can be elongated. Every v1–v4 membership rule used isotropic balls.

v5 tests exactly one parameter-free anisotropic post-detection membership envelope. It does not change candidate generation, recurrence, family topology, v8 pooled centroids, scores, or ranking.

## Frozen source representation

For an original source component and its already-frozen centroid `c`, convert each original component member event `e` into the exact four residual coordinates whose Euclidean norm equals the frozen v6/v8 centroid distance:

1. `wrap180(sol_e - sol_c) / 4`;
2. `wrap180(sun_lon_e - sun_lon_c) * cos((lat_e + lat_c)/2) / 2`;
3. `(lat_e - lat_c) / 2`;
4. `(vg_e - vg_c) / 2`.

Angles in the cosine are converted to radians exactly as in the frozen metric. The component centroid is not refit.

## Frozen anisotropic envelope

For every source component independently:

1. Form the residual matrix from **all and only** its unique original component member events.
2. Fit `sklearn.covariance.LedoitWolf(assume_centered=True)` to those residuals. This analytically estimates shrinkage from the source component itself and introduces no hand-tuned covariance regularization parameter.
3. Using the fitted precision matrix, compute each original source member's squared Mahalanobis distance.
4. Freeze the component's anisotropic support threshold as the **maximum** of those training squared Mahalanobis distances. There is no percentile, multiplier, offset, or quantile.
5. A target-year non-seed event may be supported by this component only if both:
   - its raw exact frozen-metric distance to the component centroid is `<= 1.5`; and
   - its squared Mahalanobis distance under the source component's frozen shrinkage covariance is `<=` that component's frozen maximum training squared Mahalanobis distance.

The raw 1.5 condition is the unchanged v8 predecessor tolerance, so the anisotropic envelope can never extend beyond the broad v3 membership ball.

## Cross-year assignment

For each target year independently:

- only original frozen components from the other year may support membership;
- a family is eligible if any of its other-year components admits the event under the exact rule above;
- within a family, use the smallest **raw exact frozen-metric centroid distance** among admitting components as the assignment distance;
- if multiple families are eligible, assign exclusively to the family with the smallest assignment distance; stable family ID breaks exact ties;
- original v8 seed events are retained;
- newly assigned events never become support;
- no recursive growth occurs.

## Frozen base and blindness

- Base commit: promoted v8 `c9d6c44704013ba0c9430100e98a29a56b453304`.
- GMN development years: 2022 and 2023 only.
- Solar longitude 20°–55° remains removed by the already-audited parser before label access.
- The exact v8 226-family universe, pooled family-year centroids, multiplicity values, and ranking must reproduce before expansion.
- No OrbitTrace coordinate, member, identity, target family, target-region event, Stage A/B output, reveal result, or literature-benchmark result may enter envelope construction.

## Prior covariance no-go boundary

The repository's earlier `KILL_OR_REDESIGN_COVARIANCE_FLOW_ALIGNMENT` result concerned a 100-year dynamical covariance-orientation classifier in orbital tangent space. v5 does not integrate dynamics, classify covariance flow, use orbital elements, or reuse that objective. It is a static cross-fitted post-detection membership envelope in the already-frozen v8 observational geometry.

## No-search rule

There is no search over covariance estimator, shrinkage parameter, residual representation, center, Mahalanobis threshold, threshold multiplier, quantile, percentile, raw-distance cap, component-count threshold, witness count, density rule, tie-break distance, recursive growth, reranking, score fusion, or evaluation endpoint.

If this exact Ledoit–Wolf/max-training-support formulation fails, it is a permanent no-go and does not authorize trying OAS, empirical covariance, robust covariance, PCA rank choices, covariance floors, alternate thresholds, or a relaxed 1.5 cap on this exposed panel.

## Promotion gates

Reuse the exact v1/v2/v3/v4 gates without relaxation. All must pass:

- multiplicity recovery@100 >= 58;
- qualified matches >= 95;
- top-100 dominant precision >= 0.65;
- global macro F1 gain >= 0.05 over v8;
- all-shower annual mean-F1 gain >= 0.10 in both 2022 and 2023;
- 4–9 annual-member mean F1 may not regress by more than 0.02 in either year;
- at least one of 10–24, 25–49, 50–99, or 100+ annual-member bins must gain >=0.10 mean F1 in both years;
- every inherited and v5-specific integrity/blindness gate must pass.

A pass promotes only this membership-expansion architecture for later fresh validation. It does not modify promoted v8 or authorize OrbitTrace target access.
