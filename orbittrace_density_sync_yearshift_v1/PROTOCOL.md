# OrbitTrace density-sync year-shift v1 — frozen protocol

## Purpose

Test one new, parameter-free cross-year generalization mechanism on top of the exact density-synchronous recurrent-EOM v1 GMN champion. This is frozen before implementation and before any scientific outcome.

The mechanism is independent of the failed wavelet-recurrence result. Its motivation is cross-year exchangeability: for a genuinely recurring physical stream, the calendar-year label should explain essentially none of the family geometry after the existing sun-centered GEO6 representation. A pooled density cluster whose geometry shifts materially between 2022 and 2023 is less survey-stable even if it has density support in both years.

This is not a density, kNN, mutual-nearest, phase-warp, uncertainty, or reciprocal-transfer rescue. It introduces no neighborhood k, radius, learned model, threshold, fitted coefficient, or external-data feature.

## Exact parent

Density-synchronous recurrent-EOM HDBSCAN v1, PR #1263, binding head `182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`.

Binding GMN run `31852836840`, artifact `9238142199`.

- prelabel SHA-256: `efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993`
- result SHA-256: `ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711`
- exact successor candidate count: `2,094`

Parent metrics:

2022: @50 `45`, @100 `89`, precision `0.7873334042799703`, MRR `0.022505373166085363`, fragmentation `1.0`.

2023: @50 `46`, @100 `90`, precision `0.7898245986099988`, MRR `0.02203028490649908`, fragmentation `1.0`.

Parent total recovered@100: `179`.

## Frozen statistic

For each exact parent candidate C, use only its exact event IDs and the exact inherited GEO6 coordinates:

`[cos(sol), sin(sol), sin(lon)cos(lat), cos(lon)cos(lat), sin(lat), vg/72]`.

Let the candidate contain n events, with annual groups 2022 and 2023.

Compute pooled centroid `mu`, annual centroids `mu_22` and `mu_23`, total sum of squared GEO6 distances

`T = sum_i ||x_i - mu||^2`,

and between-year sum of squares

`B = n_22 ||mu_22-mu||^2 + n_23 ||mu_23-mu||^2`.

Define raw year-label explained geometry

`R2_year = B/T` when `T>0`, else `0`.

Correct the two-group finite-sample chance effect with the standard one-predictor adjusted-R2 form

`R2_adj = 1 - (1-R2_year)*(n-1)/(n-2)`.

Clamp only the chance-side negative tail:

`year_shift = max(0, R2_adj)`.

If either year has zero members, define `year_shift=1` (complete annual segregation).

Define the parameter-free retained-overlap factor

`overlap = 1 - year_shift`,

and the successor score

`S_yearshift(C) = S_sync(C) * overlap`,

where `S_sync` is the exact frozen density-synchronous stability already attached to the parent candidate.

Candidates are ranked descending by:

1. `S_yearshift`;
2. parent synchronous stability;
3. ordinary stability;
4. member count;
5. stable family ID.

No other normalization, transform, clipping, exponent, blend weight, threshold, family-size rule, or tie rule is allowed.

## Firewall

Development corpus is only target-excluded GMN 2022+2023 using the exact frozen parser/runtime already used by #1263. Inclusive solar-longitude interval `[20.0,55.0]` remains removed before geometry or truth handling.

Before hidden known-shower truth is opened, the complete 2,094-candidate successor order and all year-shift statistics must be persisted and hash-frozen.

The following remain inaccessible during GMN development:

- OrbitTrace target information/events;
- SonotaCo 2013/2014;
- AMOS;
- MAARSY;
- DMS.

The first technically valid scientific outcome is binding.

## Strong GMN gate

PASS requires all of:

1. mechanism active;
2. exact candidate count remains `2,094`;
3. exact candidate membership universe remains identical to #1263;
4. in each year separately, no regression versus #1263 on recovered@50, recovered@100, top-100 dominant precision, MRR, or median top-500 fragmentation;
5. total recovered@100 across 2022+2023 improves by at least `+2`, from `179` to at least `181`.

A one-family gain is deliberately insufficient.

## Pre-frozen SonotaCo contingency

Only if the first technically valid GMN result passes may this exact unchanged successor be tested on the already-exposed SonotaCo 2013/2014 development-validation benchmark. SonotaCo is not pristine external validation.

SonotaCo promotion requires no macro-F1 or recovered-count regression on any of the four established Sugar/HDBSCAN panels, strict macro-F1 improvement on at least two panels, and continued superiority over the corresponding frozen literature comparator on all four panels.

Even a SonotaCo PASS does not establish external generalization. A separately frozen robustness diagnostic is required before any final-method claim, and untouched AMOS remains unavailable for development/tuning.

## Permanent no-rescue rule

After the first technically valid GMN outcome, do not change the adjusted-R2 formula, clamp, GEO6 representation, parent score, multiplicative form, group definition, family-size handling, tie order, HDBSCAN settings, gate, metric, or candidate membership. Failure permanently closes this exact version.
