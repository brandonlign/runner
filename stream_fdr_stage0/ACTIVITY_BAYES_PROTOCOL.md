# Activity-marginalized Bayes scan Stage-0 protocol

## Purpose

Test a new formulation for weak recurring meteor-stream discovery that permits intermittent, late-onset, and unequal annual activity without treating a one-year spike as a recurring stream.

GhostStream is excluded from all design, tuning, and continuation decisions.

## Candidate method

For each observed candidate center, annual local counts are measured at standardized radii `{0.8, 1.0, 1.2}`:

- `K_y`: events inside the inner radius in year `y`;
- `N_y`: events inside the outer radius `2.5r`, including the inner events.

Under a locally smooth null, `K_y | N_y` has inner probability

`p0 = (1/2.5)^3`.

For an active stream year, the inner probability is assigned an equal discrete prior over

`p = {0.12, 0.20, 0.35, 0.55}`.

The resulting active-year Bayes factor is the mean of the four binomial likelihood ratios.

## Activity-pattern marginalization

A real candidate may be active in any subset of at least three of the seven years. The method integrates rather than maximizes over all such patterns.

- active-year count `m` is uniform over `{3,4,5,6,7}`;
- conditional on `m`, every subset of `m` years has equal prior probability;
- the candidate Bayes factor is the prior-weighted sum over all 99 permitted activity subsets.

This explicitly charges a complexity cost for choosing favorable active years while allowing intermittent and late-onset signals. The complete maximum over candidate centers and radii is calibrated on independent real null scenes.

## Data and representation

- public GMN shower-removed asteroidal subset;
- years 2019–2025;
- 20-degree solar-longitude scenes;
- 60 real events sampled per year;
- Sun-centered geocentric ecliptic longitude, ecliptic latitude, and geocentric speed;
- every observed meteor is a possible candidate center;
- M2026-A1 excluded from design and null scenes.

## Baselines

Every baseline uses the same candidate centers, radii, and separate null-calibrated threshold:

1. pooled positive Poisson deviance;
2. recurrent positive Poisson deviance after removing the largest year;
3. sum of the three strongest annual positive deviances;
4. recurrent raw inner count after removing the largest year.

## Independent benchmark

- 128 calibration-null scenes;
- 128 independent test-null scenes;
- 96 paired injection scenes per condition;
- thresholds target 5% scene-level false positives;
- no prior probability, activity pattern, radius, or threshold is tuned after execution.

## Conditions

- recurring sparse: 2 compact events per year;
- recurring moderate: 3 compact events per year;
- intermittent: 3 compact events in five of seven years;
- late onset: 3 per year from 2021 onward;
- diffuse recurring: 3 wider events per year;
- drifting recurring: 3 per year with fixed annual drift;
- strong recurring: 5 compact events per year;
- one-year artifact: 12 compact events in one year;
- broad recurring ridge: 8 broad events per year.

## External control

After thresholds are frozen, evaluate the untouched M2026-A1 window using 60 events per year. The accepted primary maximum must localize within two standardized units of the published trajectory.

## Frozen continuation gates

A full hierarchical point-process benchmark is permitted only if every gate passes:

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
11. M2026-A1 is accepted and localizes near the published reference;
12. primary recovery is not more than 0.10 below the strongest baseline in any recurring-stream condition.

## Claim boundary and kill rule

Generic Bayes factors, activity priors, and Poisson/binomial count models are established statistics. A later methodological claim would require demonstrating that the activity-pattern marginalization and meteor-specific candidate search materially outperform strong stream-detection baselines on held-out known weak streams.

If this frozen Stage 0 fails, no prior tuning, active-year threshold tuning, or M2026-driven redesign is authorized. The activity-marginalized Bayes direction is killed for GhostStream.
