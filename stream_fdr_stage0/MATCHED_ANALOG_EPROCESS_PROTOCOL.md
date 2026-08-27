# Matched-analogue sequential evidence protocol

## Why this redesign is permitted

The first predictive e-process used a geometric inner-to-outer volume ratio as the held-out-year null. It failed decisively on real backgrounds: primary null acceptance was 0.336 at the nominal 0.10 threshold. The protocol authorized one principled redesign using prespecified matched analogue controls.

No radius, mixture weight, E-value threshold, or favorable solar-longitude region is tuned from the failed results.

## Core redesign

Candidate discovery remains fully adaptive but uses only revealed target years. For each next unseen year, the candidate center, radius, and training-estimated excess rate are frozen.

The unseen-year target statistic is compared with the identical statistic at prespecified solar-longitude analogue windows in the same observing year:

- target window width: 20 degrees;
- target and every analogue sample: 60 events;
- analogue offsets: `40, 60, ..., 320` degrees from the target center;
- adjacent `±20` degree windows are excluded to avoid overlap with the target activity interval;
- at least 10 of the 15 analogue windows must have 60 events in that year.

Each analogue uses the same Sun-centered candidate radiant, speed, scale, and training-estimated alternative. Only solar longitude changes.

## Year-level evidence

Let `T0` be the target statistic and `T1,...,Tm` be the available analogue statistics. The conservative rank p-value is

`p = (1 + number of Ti >= T0) / (m + 1)`.

It is converted to an e-value with the fixed p-to-e calibrator

`E_year = 0.5 / sqrt(p)`.

Under target/analogue exchangeability this has expectation at most one. The sequential product is therefore valid under optional continuation, while the real-background null benchmark directly tests whether the required exchangeability is adequate in practice.

## Candidate search

The target data use 2019–2025 GMN years, 60 sampled events per year, and the same frozen variables and scales as v1:

- Sun-centered geocentric ecliptic longitude;
- geocentric ecliptic latitude;
- geocentric speed;
- radii `{0.8, 1.0, 1.2}`;
- support in at least two revealed years.

Candidate-search scores remain descriptive and never serve as evidence.

## Primary and comparisons

Primary:

- arithmetic mean of eight prespecified adaptive year-order e-processes.

Nonadaptive valid baselines:

- fixed candidate after the first two chronological years;
- fixed split: discover on 2019–2021, then multiply analogue-calibrated evidence over 2022–2025.

Ablations:

- chronological adaptive e-process;
- naive same-data candidate selection and scoring.

The chronological adaptive procedure is an ablation of the proposed adaptive method, not an independent conventional baseline. The main power comparison is against the strongest nonadaptive valid baseline. The primary may not trail the chronological ablation by more than 0.10 in any recurring-signal condition.

## Independent benchmark

- 128 new real-background null scenes;
- 96 paired injection scenes per condition;
- new seeds not used by v1;
- target solar longitudes exclude the M2026-A1 region;
- theoretical threshold remains fixed at `E >= 10`; no empirical threshold calibration.

## Injection conditions

The v1 weak injection saturated at 1.000 recovery for both adaptive methods, so it could not measure a power difference. The redesign retains that condition and adds a sparser condition rather than deleting favorable or unfavorable results.

1. recurring moderate: 3 events in every year;
2. recurring sparse: 2 events in every year;
3. intermittent sparse: 3 events in five of seven years;
4. late onset sparse: zero in 2019–2020, then 3 per year;
5. diffuse recurring: 3 per year with wider dispersion;
6. strong recurring: 5 per year;
7. one-year artifact: 12 events in one randomly selected year.

Only target windows receive injected events. Analogue windows remain untouched.

## External control

After all rules are frozen, the untouched M2026-A1 target window is tested against the same fifteen analogue offsets, using 60 events per year. It is not used in null assessment or method tuning.

## Frozen continuation gates

A known-stream benchmark is permitted only if every gate passes:

1. primary null acceptance <= 0.10 and Wilson upper 95% bound <= 0.15;
2. no individual prespecified order has null acceptance > 0.15;
3. recurring-sparse primary recovery exceeds the strongest nonadaptive valid baseline by >= 0.10, with paired-bootstrap lower 95% bound > 0;
4. recurring-moderate recovery >= 0.75;
5. intermittent-sparse recovery >= 0.40;
6. late-onset-sparse recovery >= 0.40;
7. diffuse-recurring recovery >= 0.35;
8. strong-recurring recovery >= 0.85;
9. one-year-artifact acceptance <= 0.10;
10. primary recovery is not more than 0.10 below chronological adaptive recovery in either recurring condition;
11. M2026-A1 has `E >= 10` and localizes near the published reference.

## Kill interpretation

If null acceptance remains inflated, target and analogue windows are not exchangeable enough and the sequential-evidence direction is killed for this project. No second analogue redesign, offset tuning, p-to-e calibrator tuning, or empirical threshold tuning is authorized.

A pass would justify only a larger known-stream and parent-stream-disjoint benchmark. It would not yet authorize GhostStream application or a first-ever claim.
