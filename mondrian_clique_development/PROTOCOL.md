# Mondrian partition-invariant clique: retrospective pressure-test protocol

Status: scientific method frozen before any 10-degree Mondrian score was computed. A panel-coverage feasibility rule was corrected after the initial 2026 H1 job stopped before scoring; no score, p-value, power endpoint, or comparator result existed for that panel when the correction was made.

## Purpose

PR #32 showed that the partition-invariant four-clique score solved the exactly-four-member power problem but failed one fresh false-positive gate because a 60-degree calibration sector mixed a rapidly changing background. Both the clique and the killed split comparator were elevated in the same 2026 sector.

This stage tests a new calibration formulation: fixed 10-degree solar-longitude Mondrian strata. It does not rescue or rerun PR #32, and it does not inspect GhostStream.

## Why 10 degrees

The search neighborhood is fixed at plus or minus 10 degrees in solar longitude. A 10-degree calibration stratum limits center-location heterogeneity to no more than half the total search-window width while retaining enough empirical windows for rank p-values at alpha 0.01. The strata are globally anchored at integer multiples of 10 degrees; no boundary is selected from a shower or result.

A spent-data width screen on January–June 2026 showed that fixed 2.5, 5, 10, and 15 degree strata all removed the coarse-sector false-positive inflation. Ten degrees is frozen as the least granular tested width that preserved four-member power while directly matching the physical search scale. The width will not be reselected after the retrospective matrix runs.

## Retrospective panels

The exact panels are fixed:

1. 2021 from the odd-year archive;
2. 2024 from the untouched-even-year archive, now spent by PR #31;
3. 2025 from the odd-year archive;
4. January–June 2026 from the spent PR #32 holdout.

These panels span different network densities and activity seasons. They are retrospective development evidence only. A pass authorizes one separately frozen test on the unused July 2026 snapshot.

Exact source artifacts:

- odd archive workflow `30855193522`, artifact `real-shower-meta-data-audit`;
- even archive workflow `30863692214`, artifact `empirical-window-null-evenyear-data`;
- 2026 H1 workflow `30873092919`, artifact `partition-invariant-clique-2026h1-data`.

Exact selected-event SHA-256 values:

- odd archive: `63e1389e2666d10b05138044f428609266b367cabab2542295c154a510e40f01`;
- even archive: `518e12043ef838355d488c0fa675f1332961796168920c6c15e4b3db0583c812`;
- 2026 H1: `59e48ee6a0b653a2b4530f8a2221e2e93e6af3e6a9f11281c6f17fc428a85ddf`.

The corrected exact retrospective implementation SHA-256 is `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`.

## Pre-score feasibility correction

Initial workflow `30874109169` applied a minimum of 20 supported 10-degree bins to every panel. The three full-year panels completed and passed all scientific gates. The fixed January–June panel stopped before calibration or candidate scoring with exactly 15 supported bins because a full-year coverage requirement had been applied to a half-year corpus.

The correction is limited to panel coverage:

- full-year 2021, 2024, and 2025 require at least 20 supported 10-degree bins;
- fixed January–June 2026 requires at least 12 supported 10-degree bins;
- every panel still requires at least 30 eligible established showers.

Twelve is fixed before H1 scoring and represents 80% of the 15 bins that its fixed calendar span can support after the blind interval. The observed count is 15, so the corrected rule is not set at the observed boundary. No method score, seed, bin width, bin boundary, calibration count, p-value formula, comparator, scientific endpoint, or scientific gate changed.

## GhostStream blindness

Remove every event with solar longitude from 20.0 degrees through 55.0 degrees before any center stratum, calibration pool, negative window, positive window, score, fold, or endpoint is formed. No GhostStream radiant, speed, orbit, membership, event list, or score may be used.

## Frozen windows and geometry

- 128 events per window;
- one year per window;
- plus or minus 10 degrees in solar longitude around the center event;
- positive windows contain `k in {4, 6, 8, 12}` real members from one established shower and real local IAU `-1` meteors;
- four deterministic positive replicates per eligible shower and member count;
- weak-power endpoints use `k in {4, 6, 8}`;
- exact PR #14 physical distance and scales:
  - relative solar longitude / 2 degrees;
  - Sun-centered ecliptic longitude and latitude / 2 degrees;
  - geocentric speed / 2 km/s.

## Frozen partition-invariant score

For each window:

1. compute the complete physical-distance matrix;
2. for each meteor, identify its three nearest other meteors;
3. form the four-event subset containing the meteor and those neighbors;
4. compute the complete-link diameter of that subset;
5. take the minimum diameter over all anchors;
6. negate it so larger values indicate stronger coherence.

No radius, cluster threshold, random split, orbit element, shower identity, or absolute solar longitude enters the score.

## Frozen Mondrian calibration

- Strata are `[0,10), [10,20), ..., [350,360)` degrees in solar longitude.
- Only strata that can construct a 128-event empirical background window are included.
- For every supported year-stratum, draw 128 deterministic calibration windows and 64 independent negative windows from the same fixed sporadic corpus and generator.
- Convert the candidate score to `p = (1 + number of calibration scores >= score) / 129`.
- Overlap among Monte Carlo windows is allowed, matching the previously validated same-corpus empirical mechanism.
- Full-year panels require at least 20 supported strata; the fixed January–June 2026 panel requires at least 12.
- Every panel requires at least 30 eligible showers.

Exact seed prefixes:

- support: `mondrian-development-support`;
- calibration: `mondrian-development-calibration`;
- independent negatives: `mondrian-development-negative`;
- positive windows: `mondrian-development-positive`;
- split comparator: `mondrian-development-split`.

## Frozen comparators and folds

Compute on the same positive and independent-negative windows:

- the killed eight-split reference/query statistic;
- radius-2.5 local density;
- epsilon-2.5, minimum-samples-4 DBSCAN largest cluster;
- five deterministic event-count-balanced MDC complex/parent folds.

Comparators are evaluated by raw AUROC and cannot change the candidate p-value.

## Frozen per-panel gates

Every gate must pass independently in 2021, 2024, 2025, and 2026 H1:

1. pooled candidate FPR at alpha 0.05 is at most 0.060;
2. pooled candidate FPR at alpha 0.01 is at most 0.020;
3. worst 60-degree reporting-sector FPR at alpha 0.05 is at most 0.120;
4. weak-window AUROC is at least 0.75;
5. candidate AUROC is no more than 0.03 below the strongest fixed comparator;
6. at least four of five folds have candidate AUROC at least 0.70, and no fold is below 0.65;
7. candidate recall at alpha 0.05 is at least 0.15, 0.30, and 0.45 for `k = 4, 6, 8`;
8. candidate recall at alpha 0.01 is at least 0.05, 0.15, and 0.25 for `k = 4, 6, 8`;
9. recall is nondecreasing from `k = 4` to 6 to 8 to 12 at both thresholds.

## Kill and continuation rules

Any failed scientific gate in any panel kills this exact 10-degree formulation. Do not change the bin width, boundaries, calibration count, negative count, score, seeds, folds, shower subset, blind interval, thresholds, or scientific gates after results are observed.

A four-panel pass authorizes only a separately frozen July 2026 snapshot gate. It does not authorize a GhostStream application, discovery claim, or catalog scan.
