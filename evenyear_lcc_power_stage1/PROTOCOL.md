# Empirical-window local conformal coherence: untouched even-year power protocol

Status: frozen before any established-shower result from 2020, 2022, or 2024 is computed.

## Scientific question

After the same-corpus empirical-window null passed every frozen calibration gate on untouched even years, does the unchanged cross-fitted coherence statistic retain useful power for weak real meteor showers in those same previously unseen years?

This stage tests power only. It does not scan a catalog, inspect GhostStream, change the score, or authorize a discovery claim.

## Development and confirmation boundary

- Development years: 2019, 2021, 2023, and 2025.
- Untouched confirmation years: 2020, 2022, and 2024.
- The score, distance, window size, cross-fit construction, calibration mechanism, sectors, comparator parameters, endpoints, and gates were fixed before reading any established-shower power result from the confirmation years.
- The Stage-0 null audit used no shower labels. This Stage-1 may now read the frozen labels only to construct positive windows and report power.

## GhostStream blindness

Remove every event with solar longitude from 20.0 degrees through 55.0 degrees before any pool, window, score, calibration distribution, fold, or endpoint is formed. No GhostStream radiant, speed, orbit, membership, event list, or detection score may be used.

## Frozen data

Use the exact even-year artifact produced by runner workflow `30863692214`:

- years 2020, 2022, and 2024;
- 36 official GMN monthly trajectory summaries;
- exact PR #14 parser and quality filters;
- exact IAU MDC complex/parent mapping;
- 142 eligible established showers, 124 eligible complex units, and 178,742 saved sporadic events before the blind interval;
- every Stage-0 data gate passed.

## Search windows

- 128 events per window;
- one year per window;
- a plus-or-minus 10 degree solar-longitude neighborhood;
- positive windows contain `k in {4, 6, 8, 12}` real members from one eligible shower-year and real local IAU `-1` meteors;
- four deterministic positive replicates for every eligible shower-year-member-count combination;
- weak-power endpoints use `k in {4, 6, 8}`;
- negative windows contain only real local IAU `-1` meteors.

## Fixed physical distance

Use the exact PR #14 geometry with fixed scales:

- relative solar longitude / 2 degrees;
- Sun-centered ecliptic longitude and latitude / 2 degrees;
- geocentric speed / 2 km/s.

No orbital elements, shower identity, absolute date, or absolute solar longitude enter the candidate score.

## Frozen cross-fitted coherence score

For each 128-event window:

1. Compute the complete fixed physical-distance matrix.
2. For each of eight deterministic salts, split the window into exactly 64 reference and 64 query events.
3. For each query event, compute its distance to the second-nearest reference event.
4. Average the two smallest query distances and negate the result.
5. Use the median of the eight split scores.

## Frozen same-corpus local calibration

For each supported year and 60-degree solar-longitude sector:

- draw 512 calibration negative windows from the fixed empirical sporadic corpus;
- draw 256 independent audit negative windows from the same corpus and generator;
- convert every candidate score to `p = (1 + number of calibration scores >= score) / 513`;
- overlap among Monte Carlo windows is allowed, as in the passed Stage-0 mechanism.

The power-stage seeds are fixed and distinct from all Stage-0 audit batches. No seed may be replaced after results are observed.

## Frozen comparators and folds

- fixed radius-2.5 local-density score;
- fixed epsilon-2.5, minimum-samples-4 DBSCAN largest-cluster score;
- five deterministic event-count-balanced folds of complete MDC complex/parent units;
- no complex may occur in more than one fold;
- folds are reporting units only and do not train or tune the candidate.

## Frozen endpoints

Primary:

- mean weak-window AUROC across all confirmation positives and negative windows;
- recall at local `p <= 0.05` and `p <= 0.01` for `k = 4, 6, 8`;
- pooled and worst-sector false-positive rates on independent negative windows.

Secondary:

- per-fold weak AUROC;
- power monotonicity through `k = 12`;
- candidate AUROC relative to fixed local-density and DBSCAN comparators.

## Frozen continuation gates

Every gate must pass:

1. pooled negative false-positive rate at alpha 0.05 is at most 0.060;
2. pooled negative false-positive rate at alpha 0.01 is at most 0.020;
3. worst supported year-sector false-positive rate at alpha 0.05 is at most 0.120;
4. mean weak-window AUROC is at least 0.75;
5. candidate weak AUROC is no more than 0.03 below the stronger fixed density/DBSCAN comparator;
6. at least four of five folds have candidate weak AUROC at least 0.70, and no fold is below 0.65;
7. recall at alpha 0.05 is at least 0.15, 0.30, and 0.45 for `k = 4, 6, 8`;
8. recall at alpha 0.01 is at least 0.05, 0.15, and 0.25 for `k = 4, 6, 8`;
9. recall is nondecreasing from `k = 4` to 6 to 8 to 12 at both thresholds.

## Kill and continuation rules

Any failed gate kills this confirmation formulation. Do not change the neighbor count, top-event count, split count, scales, sector width, calibration size, seeds, comparator parameters, folds, shower subset, blind interval, thresholds, or gates after seeing results.

A pass authorizes only a separately frozen external weak-stream control and catalog-level family-wise error study. It does not authorize a GhostStream application.