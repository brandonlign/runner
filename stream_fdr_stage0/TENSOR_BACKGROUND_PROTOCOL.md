# Robust background-decomposition Stage-0 protocol

## Purpose

Test whether recurring weak meteor streams can be separated from the real sporadic background by decomposing a year-by-phase-space count matrix into:

- a low-rank component representing recurring survey/background structure; and
- a column-group-sparse positive residual representing localized phase-space cells that recur across years.

This is a runner-only surrogate. GhostStream is excluded from all design, tuning, and continuation decisions.

## Why this direction is different

Previous failed candidates assumed a locally smooth null, trained on synthetic stream morphologies, imposed hard cross-network agreement, or searched a fixed physical tube. This candidate instead learns the dominant real background modes directly from the observed annual count maps and asks whether a recurring localized residual remains after those modes are removed.

Generic robust PCA and low-rank-plus-sparse tensor decomposition are established methods. Methodological novelty would require a later meteor-specific structured Poisson formulation with physical neighborhood and recurrence constraints. This Stage 0 tests only whether the underlying separation premise has enough empirical value to justify that work.

## Data

Use the public GMN shower-removed asteroidal subset released with Shober (2026).

- years: 2019–2025;
- target scene: a 20-degree solar-longitude window;
- exactly 60 real background events sampled per year;
- M2026-A1 solar longitudes excluded from null and injection design;
- coordinates: Sun-centered geocentric ecliptic longitude, geocentric ecliptic latitude, and geocentric speed.

## Fixed phase-space grid

- longitude: 12 periodic bins over `[-180, 180)`;
- latitude: 8 bins over `[-90, 90]`;
- speed: 8 bins over `[5, 75] km/s`, with physically valid values clipped to the edge bins;
- total cells: 768.

The count matrix has 7 annual rows and 768 phase-space columns. Counts receive the Anscombe transform before decomposition.

## Primary decomposition

Solve the column-sparse robust decomposition

`Z = L + S`

by an augmented-Lagrangian proximal algorithm minimizing

`||L||_* + lambda ||S||_{2,1}`

with fixed `lambda = 1/sqrt(7)`.

- `L` is the learned low-rank annual background;
- `S` is the column-group-sparse residual;
- only positive residuals contribute to candidate evidence.

No rank, sparsity, or decomposition threshold is selected from the test scenes.

## Candidate score

For every phase-space cell:

1. aggregate positive sparse residual over its fixed `3 x 3 x 3` neighborhood, wrapping longitude;
2. sum the annual neighborhood residuals after removing the largest single-year contribution;
3. require positive neighborhood residual in at least three of seven years.

The scene score is the maximum over cells. This complete maximization is calibrated on independent real null scenes.

## Baselines

Every baseline uses the same grid, neighborhood, recurrence requirement, candidate maximization, and separate null-calibrated threshold:

1. pooled raw neighborhood count;
2. recurrent raw count after removing the largest annual contribution;
3. annual-median residual count;
4. rank-2 truncated-SVD positive residual without robust sparse separation.

## Independent benchmark

- 128 calibration-null scenes;
- 128 independent test-null scenes;
- 96 paired injection scenes per condition;
- separate fixed seeds;
- thresholds target 5% scene-level false positives and are never tuned on injections or M2026-A1.

## Injection conditions

1. recurring sparse: 2 compact events per year;
2. recurring moderate: 3 compact events per year;
3. intermittent: 3 compact events in five randomly selected years;
4. late onset: zero in 2019–2020, then 3 compact events per year;
5. diffuse recurring: 3 wider events per year;
6. drifting recurring: 3 events per year with a fixed annual phase-space drift;
7. strong recurring: 5 compact events per year;
8. one-year artifact: 12 compact events in one random year;
9. broad recurring ridge: a non-stream background mismatch spread across many neighboring cells and all years.

The physical center is not supplied to any detector.

## External control

After all thresholds are frozen, scan the untouched M2026-A1 window using 60 events per year. The accepted primary maximum must localize near the published trajectory. The control is not used for tuning.

## Frozen continuation gates

A meteor-specific structured Poisson tensor model is permitted only if every gate passes:

1. primary test-null false-positive rate <= 0.10 and Wilson upper 95% bound <= 0.15;
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

## Kill interpretation

If low-rank separation absorbs recurring streams, sparse residuals track structured sporadic sources, or the method fails the untouched real control, the direction is killed. One principled redesign is allowed only if the failure isolates a specific representation defect, such as fixed voxels splitting a physical trajectory. Hyperparameter tuning or changing the score after observing results is prohibited.

A pass would justify a larger benchmark and a physically structured Poisson formulation. It would not yet authorize GhostStream application or a first-ever claim.
