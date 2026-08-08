# OrbitTrace recurrent-core seed-envelope v5 — frozen development protocol

## Purpose

v4 established a useful boundary on target-excluded GMN 2022/2023. Deriving membership scale from each frozen component eliminated the catastrophic over-expansion of v1-v3 and preserved v8 recovery/precision, but a single ball centered on the component centroid was too conservative: global macro F1 improved by +0.0470, just below the frozen +0.05 gate, and annual gains remained small.

v5 changes only the *shape* of that same local envelope. It retains v4's exact non-tuned component radius, but centers support on the original component seed events so the membership envelope can follow the observed component geometry instead of being forced into one centroid-centered ball.

## Frozen base and blindness

- Base commit: promoted v8 `c9d6c44704013ba0c9430100e98a29a56b453304`.
- Exact target-excluded GMN 2022/2023 v8 components, recurrent families, pooled family-year centroids, scores, and multiplicity ranking are reproduced before membership refinement.
- Solar longitude 20°–55° remains excluded before label access.
- No OrbitTrace coordinate, member, identity, prior target family, target-region event, Stage A/B output, or reveal may enter this work.

## Sole v5 change

For every frozen v8 component in each year:

1. Keep its exact frozen component centroid and original seed-event membership.
2. Compute the exact v4 component radius: the maximum inherited-v8 distance of an original seed event from that frozen centroid. This radius is not changed from v4.
3. Use every original seed event of the component as a fixed support center.
4. A non-seed event in the same year is eligible for the recurrent family if its exact inherited-v8 distance to at least one original seed center is `<=` that component's fixed v4 radius.
5. If multiple families are eligible, assign exclusively to the family with the smallest seed-event distance; stable family ID breaks exact ties.
6. Original seed events remain members. Newly assigned events never become support and never alter centroids, component radii, components, scores, or ranking.

There is no global membership radius, radius multiplier, quantile, covariance fit, witness-count threshold, density threshold, recursive growth, or parameter grid. Cross-year recurrence remains supplied only by the already-frozen v8 family.

## Scientific rationale

v4 showed that the component-local radius is safe but a centroid-centered sphere misses stream structure beyond the sparse core. Re-centering the same fixed local radius on the already-observed seed events is the minimal shape-aware extension: it adds no scale parameter and does not let new events propagate the component.

## Evaluation

Reuse the exact scientific promotion gates from v1-v4 without relaxation:

- multiplicity recovery@100 >= 58;
- qualified matches >= 95;
- top-100 dominant precision >= 0.65;
- global macro F1 gain >= 0.05 over v8;
- all-shower annual mean-F1 gain >= 0.10 in both 2022 and 2023;
- 4–9 annual-member mean F1 may not regress by more than 0.02 in either year;
- at least one 10–24, 25–49, 50–99, or 100+ bin gains >=0.10 mean F1 in both years;
- every v5 integrity/blindness gate passes.

A failure is a permanent no-go for this exact seed-centered local-envelope rule. It does not authorize changing the component radius, multiplying it, changing its quantile, enabling recursive growth, or tuning a new threshold from the result.
