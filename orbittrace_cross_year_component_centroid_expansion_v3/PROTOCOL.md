# OrbitTrace cross-year component-centroid expansion v3 — frozen development protocol

## Purpose

v1 and v2 established a consistent mechanism on target-excluded GMN 2022/2023: expanding frozen v8 families can greatly improve membership F1, especially for large showers, but event-level support badly over-expands. v2 showed why: accepted events had a median 62/100 source seed-event witnesses (2022/2023), so event-count multiplicity was mostly redundant evidence from dense same-year components.

v3 makes one source-level repair only: collapse each already-existing v8 source-year component to its frozen component centroid before cross-year membership assignment.

## Frozen base

- Base commit: promoted v8 `c9d6c44704013ba0c9430100e98a29a56b453304`.
- Exact v8 target-excluded GMN 2022/2023 family universe, pooled family-year centroids, scores, and multiplicity ranking are reproduced before expansion.
- Solar longitude 20°–55° remains removed before label access.
- No OrbitTrace coordinate, member, identity, prior target family, target-region event, Stage A/B output, or reveal may enter this work.

## Sole v3 change

For each target year independently:

1. For each frozen v8 family, take only its original components from the *other* year.
2. Replace each source component by the exact centroid already stored on that component. No centroid is refit.
3. A non-seed target-year event is eligible for that family only if its exact inherited v8 distance to at least one of those source-component centroids is `<= 1.5`.
4. If multiple families are eligible, assign the event exclusively to the family with the smallest component-centroid distance; stable family ID breaks exact ties.
5. Original v8 seed events are retained.
6. Newly assigned events never become support. There is no recursive growth.

The radius 1.5 is the existing v8 family-link radius. It is not retuned. There is no event-witness count, component-count threshold, radius grid, density threshold, weighting rule, pruning rule, or alternative support statistic.

## Why this successor is allowed

v2 did not justify increasing the event-witness count: it showed that event witnesses are highly redundant within a component. Collapsing each component to one frozen centroid directly removes that redundancy while preserving the pre-existing v8 structural units. This is not a search over alternatives.

## Evaluation and gates

Use the exact v1/v2 promotion gates without relaxation:

- multiplicity recovery@100 >= 58;
- qualified matches >= 95;
- top-100 dominant precision >= 0.65;
- global macro F1 gain >= 0.05 over v8;
- all-shower annual mean-F1 gain >= 0.10 in both 2022 and 2023;
- 4–9 annual-member mean F1 may not regress by more than 0.02 in either year;
- at least one of the 10–24, 25–49, 50–99, or 100+ bins must gain >=0.10 mean F1 in both years;
- every integrity/blindness gate must pass.

Pass only if all gates pass. A failure is a permanent no-go for component-centroid membership expansion and does not authorize changing the 1.5 radius or testing alternative component aggregation rules.
