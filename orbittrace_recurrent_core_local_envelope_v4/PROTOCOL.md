# OrbitTrace recurrent-core local-envelope v4 — frozen development protocol

## Purpose

v1-v3 established that frozen v8 recurrent families contain useful high-purity cores, but cross-year membership expansion with a global 1.5 distance scale over-expands badly. v3 removed event-witness multiplicity and still assigned 162,646 new events, showing that v8's 1.5 cross-year family-link radius is not an event-membership radius.

v4 separates the two tasks:

- v8 recurrence remains the detector and ranking mechanism;
- within-year frozen component geometry defines membership refinement.

## Frozen base and blindness

- Base commit: promoted v8 `c9d6c44704013ba0c9430100e98a29a56b453304`.
- Exact target-excluded GMN 2022/2023 v8 components, recurrent families, pooled family-year centroids, scores, and multiplicity ranking are reproduced before expansion.
- Solar longitude 20°–55° remains excluded before label access.
- No OrbitTrace coordinate, member, identity, prior target family, target-region event, Stage A/B output, or reveal may enter this work.

## Sole v4 change

For every frozen v8 component in each year:

1. Keep its exact frozen component centroid.
2. Using only that component's original frozen seed events, compute each seed event's exact inherited v8 distance to the centroid.
3. Define the component membership radius as the **maximum** of those seed-to-centroid distances. This is the smallest ball centered on the already-frozen centroid that contains the entire original component.
4. A non-seed event in the same year is eligible for the recurrent family if it lies inside at least one of that family's same-year component envelopes.
5. If multiple families are eligible, assign exclusively to the nearest component centroid; stable family ID breaks exact ties.
6. Original seed events are retained. Newly assigned events never alter centroids, radii, components, scores, or ranking and never become support.

There is no global membership radius, multiplier, quantile, witness threshold, density threshold, covariance fit, recursive growth, or parameter grid. The inherited v8 radius 1.5 remains unchanged for family construction only and is not used for membership.

## Scientific rationale

The membership envelope is derived directly from each frozen component's own observed support rather than from a cross-year linking tolerance. The max-radius rule has no tunable hyperparameter and exactly preserves the full seed component by construction. Cross-year recurrence remains required because only already-recurrent v8 families are eligible for refinement.

## Evaluation

Reuse the exact scientific promotion gates from v1-v3 without relaxation:

- multiplicity recovery@100 >= 58;
- qualified matches >= 95;
- top-100 dominant precision >= 0.65;
- global macro F1 gain >= 0.05 over v8;
- all-shower annual mean-F1 gain >= 0.10 in both years;
- 4-9 annual-member mean F1 may not regress by more than 0.02 in either year;
- at least one 10-24, 25-49, 50-99, or 100+ bin gains >=0.10 mean F1 in both years;
- every v4 integrity/blindness gate passes.

A failure is a permanent no-go for this exact local-envelope rule. It does not authorize multiplying the envelope radius, changing max to a searched quantile, or tuning any scale from the result.
