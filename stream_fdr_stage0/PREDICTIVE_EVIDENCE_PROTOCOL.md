# Sequential predictive evidence Stage-0 protocol

## Purpose

Test whether blind meteor-stream discovery can retain adaptive candidate search while producing valid out-of-sample evidence, instead of selecting a cluster and assessing significance on the same meteors.

GhostStream is excluded from all design, threshold, and continuation decisions.

## Methodological candidate

Treat observing years as sequentially independent experiments.

For each fixed year ordering:

1. use only the accumulated earlier years to search freely over candidate centers and scales;
2. freeze the selected center, scale, and alternative rate;
3. evaluate the next unseen year with a likelihood-ratio e-value;
4. multiply the year-level e-values into an e-process;
5. update the candidate using the newly revealed year and continue.

The final primary evidence is the arithmetic mean of e-processes from eight prespecified year orderings. An average of valid e-values remains an e-value. Evidence threshold `E >= 10` therefore targets a type-I error bound of 0.10 without calibrating the threshold on favorable scenes.

This does not make the discovery algorithm itself novel. The candidate contribution is an adaptive, recurring-stream discovery procedure whose evidence remains valid because every increment is predictive rather than retrospective.

## Data

Use only the public GMN shower-removed asteroidal subset released with Shober (2026).

- usable years: 2019–2025;
- 2018 is excluded before testing because it contains only 17 valid events in the released subset;
- each scene is a 20-degree solar-longitude window;
- sample 90 real background meteors per year so survey growth does not make later years dominate;
- M2026-A1 solar longitudes are excluded from all null and injection design.

Each event uses:

- Sun-centered geocentric ecliptic longitude;
- geocentric ecliptic latitude;
- geocentric speed.

## Local predictive model

For a candidate center and inner radius `r`, let the outer radius be `2.5r`.

In the next unseen year:

- `K` is the number of events in the inner ball;
- `N` is the number in the outer ball, including the inner ball;
- under a locally smooth three-dimensional background, `K | N ~ Binomial(N, p0)` with `p0 = (1/2.5)^3`;
- `p1` is estimated only from earlier years with beta smoothing and is frozen before the new year is opened.

The raw likelihood ratio is mixed equally with the null:

`E_year = 0.5 + 0.5 * LR(p1 versus p0)`.

This mixture remains an e-value while preventing one inactive year from automatically erasing all earlier evidence. The sequential product remains valid under optional continuation if the local conditional null is adequate.

## Candidate search

Earlier years may be searched arbitrarily over:

- candidate centers drawn from observed earlier-year events;
- radii `{0.8, 1.0, 1.2}` in the frozen standardized metric;
- cumulative inner-versus-outer binomial excess;
- a recurrence requirement of support in at least two earlier years.

The candidate search score is not itself treated as significance.

## Prespecified orderings

Eight orderings of 2019–2025 are fixed in source before execution:

- chronological;
- reverse chronological;
- three cyclic rotations;
- three pseudorandom permutations generated from a fixed seed.

Each ordering uses two warm-up years followed by five predictive tests. The arithmetic mean of the eight final e-values is the primary statistic.

## Baselines

Valid baselines:

1. chronological adaptive e-process;
2. fixed-candidate chronological e-process: discover after two years, never update, test the remaining five;
3. one fixed split: discover on the first three years and test the final four jointly.

Diagnostic only:

4. naive same-data likelihood ratio after discovering and scoring on all seven years. This is expected to illustrate post-selection inflation but is not eligible as a valid baseline.

All procedures use the same candidate geometry and fixed threshold `E >= 10`.

## Independent Stage-0 scenes

- 128 real-background null scenes;
- 96 paired injection scenes per condition;
- separate fixed random seeds for each condition;
- no empirical threshold tuning.

## Injection conditions

1. recurring weak: 3 injected events in every year;
2. intermittent: 4 injected events in five of seven years;
3. late onset: zero in 2019–2020, then 4 per year in 2021–2025;
4. diffuse recurring: 4 per year with wider intrinsic dispersion;
5. strong recurring: 6 per year;
6. one-year artifact: 15 events in one randomly selected year only.

The physical center is shared across active years but is not supplied to the detector.

## External positive control

After all design and thresholds are frozen, scan the untouched M2026-A1 activity region. The final all-years localization must lie near the published trajectory. This control is not used for tuning.

## Statistical reporting

- empirical null acceptance with Wilson 95% interval;
- paired recovery decisions for every method;
- paired bootstrap 95% interval for primary recovery gain over the best valid baseline;
- per-order e-values and order sensitivity;
- candidate localization error;
- one-year-artifact acceptance;
- raw naive same-data null inflation as a diagnostic.

## Frozen continuation gates

A larger known-stream benchmark is permitted only if all gates pass:

1. primary null acceptance <= 0.10 and Wilson upper 95% bound <= 0.15;
2. recurring-weak recovery exceeds the strongest valid baseline by >= 0.10, with paired-bootstrap lower 95% bound > 0;
3. intermittent recovery >= 0.50;
4. late-onset recovery >= 0.50;
5. diffuse-recurring recovery >= 0.40;
6. strong-recurring recovery >= 0.85;
7. one-year-artifact acceptance <= 0.10;
8. untouched M2026-A1 control has `E >= 10` and localizes near the published trajectory;
9. no individual prespecified ordering has null acceptance > 0.15.

## Kill conditions and claim boundary

If real null scenes violate the nominal e-value bound, the local smooth-background conditional model is invalid and this implementation is killed. It may receive one principled redesign using preselected matched analogue controls; bandwidth or radius tuning after observing the failures is prohibited.

A pass would support only this provisional claim:

> Sequential predictive evidence can support adaptive recurring meteor-stream searches while controlling false discoveries more honestly than same-data significance and retaining more power than one fixed data split.

It would not yet justify applying the method to GhostStream, claiming a new stream, or claiming a first-ever method without a completed literature audit and larger known-stream benchmark.
