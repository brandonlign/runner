# Registered-scale contrast recurrence: frozen no-score source audit

Status: frozen before any candidate score, null catalogue, injection, threshold, FWER, recovery endpoint, or continuation decision is computed.

## Motivation from preserved results

The exact hard third-year recurrence statistic already showed excellent persistent-stream power, but broad spatial structure shared across observing years can create repeated false peaks. PR #105 tested smooth-consensus subtraction and failed because shared-structure FWER remained 0.2333 and the hard recurrence comparator retained higher persistent power.

This candidate does not subtract an estimated background field and introduces no new spatial scale. It tests whether evidence is spatially localized by comparing only adjacent widths in the already registered template bank.

## Frozen candidate

Start from exact consensus-lowpass framework source SHA-256 `9f630c8eca2ffb1a5bdbc0598b744dffccb6026d2476467b99c6caa3d410a9fa`, which already contains both null families, the five-of-fifteen recurrence condition, the twelve-of-fifteen persistent shared-background condition, the one-year artifact control, and all inherited comparators.

For each year and each of the four unchanged registered template widths:

1. compute the unchanged one-sided Poisson tail evidence map;
2. retain every existing comparator map unchanged;
3. for each of the three adjacent registered width pairs, compute the positive evidence drop `max(E_narrow - E_broad, 0)`;
4. take the unchanged third-strongest annual contrast at each grid cell;
5. maximize across the three registered adjacent-scale pairs.

The fixed pairs are generated only as `zip(WIDTHS[:-1], WIDTHS[1:])`. No width, interpolation, coefficient, smoothing scale, annulus, or selected pair is introduced.

A spatially narrow recurrent stream should lose tail evidence when pooled to the next coarser registered support. Broad shared structure should remain significant across adjacent supports and therefore have a smaller evidence drop.

## Fixed conditions and comparators

Retain exactly:

- ideal independent-year null;
- shared-structure null;
- five-of-fifteen recurrent injection;
- twelve-of-fifteen recurrent injection on shared-structure background;
- one-year artifact injection;
- strengths 4, 6, 8, and 12 per active year;
- pooled, pooled-confirmed, hard recurrence, soft recurrence, complete-median majority conditioning, and consensus-lowpass comparators;
- unchanged histogram grid, templates, recurrence order, locations, jitter, evidence, calibration, and complete-search evaluation.

## Allowed source-audit operations

- reconstruct exact parent source SHA-256 `9f630c8eca2ffb1a5bdbc0598b744dffccb6026d2476467b99c6caa3d410a9fa` from pinned commit `e6fa3cbcf3dacc3287592874e12fda21f3a8d245`;
- decode the pre-frozen candidate payload;
- require candidate SHA-256 `601807767c7969d7e2ef07ae9d9ea9af8d2904fabc96af4135b1f4cf9315eb12`;
- compile and statically inspect the candidate;
- verify the exact registered pair construction, positive evidence drop, third-year recurrence, retained conditions, comparators, nulls, and gates;
- record source bytes, lines, functions, calls, transformation manifest, and exact source.

## Forbidden operations

This branch may not install scientific dependencies, download the observed subset, import or execute the candidate, generate a histogram, sample either null family, inject a stream, compute a score, threshold, FWER, recovery value, or comparator endpoint.

A successful audit authorizes only one separately frozen reduced kill screen with a new seed and prospectively fixed trial counts and gates. It does not authorize a full benchmark, real-shower testing, confirmation, catalogue scanning, or GhostStream application.