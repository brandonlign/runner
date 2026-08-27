# Event-centered robust-background confirmation

## Authorized redesign

The fixed-voxel Stage 0 controlled false positives and rejected a broad recurring ridge, but it suppressed even strong compact streams and localized poorly. The only authorized redesign replaces fixed voxels with annual local-density fields evaluated at observed event centers. The background-decomposition objective, recurrence score, data, and decision standard remain conceptually unchanged.

If this confirmation fails, the robust low-rank/background direction is closed for GhostStream.

## Representation

For each 20-degree GMN solar-longitude scene:

- sample 60 real events from each year 2019–2025;
- pool every observed event as a possible candidate center;
- use the same standardized Sun-centered radiant/speed geometry as prior GhostStream work;
- evaluate radii `{0.8, 1.0, 1.2}`;
- for every candidate, year, and radius, count events inside the radius and inside an outer radius `2.5r`;
- estimate the local expected inner count from the outer shell;
- convert observed versus expected counts into a signed square-root Poisson deviance.

This produces a seven-year by candidate-center local-density field for each radius without quantizing candidate locations.

## Primary method

For each radius, decompose the signed-deviance field as

`Z = L + S`

using the same column-group-sparse robust objective and fixed `lambda = 1/sqrt(7)` as v1.

For each candidate:

1. retain positive sparse residuals;
2. sum annual residuals after removing the largest single-year contribution;
3. require positive residual support in at least three years.

The primary scene score is the maximum over all observed candidate centers and all three radii. Independent real null scenes calibrate the complete center-and-radius search.

## Baselines

Every baseline receives the same candidate centers, radii, recurrence rule, and separate null threshold:

1. pooled positive Poisson deviance;
2. recurrent positive Poisson deviance after removing the largest year;
3. recurrent raw inner count after removing the largest year;
4. rank-2 SVD positive-residual recurrence.

## Benchmark

- 128 calibration-null scenes;
- 128 independent test-null scenes;
- 96 paired injection scenes per condition;
- M2026-A1 excluded from all design and null scenes;
- thresholds target 5% scene-level false positives.

## Conditions

Use exactly the v1 signal families:

- recurring sparse: 2 compact events per year;
- recurring moderate: 3 compact events per year;
- intermittent: 3 events in five of seven years;
- late onset: 3 per year from 2021 onward;
- diffuse recurring: 3 wider events per year;
- drifting recurring: 3 per year with fixed annual drift;
- strong recurring: 5 compact events per year;
- one-year artifact: 12 compact events in one year;
- broad recurring ridge: 8 broad events per year.

## External control

After all thresholds are frozen, evaluate the untouched M2026-A1 window with 60 events per year. Candidate locations are observed meteor coordinates, so localization is evaluated directly in the standardized physical metric.

## Frozen continuation gates

A structured Poisson tensor/dictionary model is permitted only if every gate passes:

1. primary test-null FPR <= 0.10 and Wilson upper 95% bound <= 0.15;
2. recurring-sparse recovery exceeds the strongest baseline by >= 0.10 with paired-bootstrap lower 95% bound > 0;
3. recurring-moderate recovery >= 0.70;
4. intermittent recovery >= 0.40;
5. late-onset recovery >= 0.40;
6. diffuse recovery >= 0.35;
7. drifting recovery >= 0.40;
8. strong recovery >= 0.90;
9. one-year-artifact acceptance <= 0.10;
10. broad-ridge acceptance <= 0.15;
11. M2026-A1 is accepted and localizes within two standardized units of the published reference;
12. primary recovery is not more than 0.10 below the strongest baseline in any recurring-stream condition.

No second representation redesign, lambda tuning, radius-grid tuning, or threshold tuning is authorized.
