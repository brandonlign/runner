# Coverage-normalized Mondrian four-clique: retrospective development protocol

Status: new formulation frozen after PR #36 was killed and before any January–June 2026 score is computed under this formulation.

## Separation from PR #36

PR #36 prospectively required at least 20 supported 10-degree strata in every panel. Its January–June 2026 panel had 15 supported strata and stopped before scoring, so that exact four-panel formulation remains killed. The closed PR, its workflow `30874109169`, and `mondrian_clique_development/RESULT.md` remain the authoritative record of that no-go.

This branch does not reinterpret PR #36 as a pass. It defines a separate development formulation whose feasibility requirement is allowed to depend on the predeclared calendar coverage of the panel:

- complete-year panels require at least 20 supported 10-degree strata;
- the fixed January–June panel requires at least 12 supported 10-degree strata;
- every panel requires at least 30 eligible established showers.

The H1 threshold was defined after the PR #36 feasibility result and therefore cannot be validated by the spent H1 panel. That panel is used only as retrospective development evidence. A pass across the retrospective matrix authorizes one separately frozen test on unused July 2026 data; only that future test can provide new confirmation evidence.

No method score, seed, bin width, bin boundary, calibration count, p-value formula, comparator, scientific endpoint, or scientific gate differs from the PR #36 scientific procedure. The exact implementation SHA-256 is `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`.

## Purpose

Test whether globally anchored 10-degree solar-longitude Mondrian calibration removes the local-background false-positive inflation seen in PR #32 while preserving the four-member sensitivity of the partition-invariant clique statistic.

## Retrospective panels

The fixed development panels are:

1. complete-year 2021 from the odd-year archive;
2. complete-year 2024 from the even-year archive;
3. complete-year 2025 from the odd-year archive;
4. fixed January–June 2026 from the spent PR #32 holdout.

Exact artifacts:

- odd archive workflow `30855193522`, artifact `real-shower-meta-data-audit`;
- even archive workflow `30863692214`, artifact `empirical-window-null-evenyear-data`;
- 2026 H1 workflow `30873092919`, artifact `partition-invariant-clique-2026h1-data`.

Exact selected-event SHA-256 values:

- odd archive: `63e1389e2666d10b05138044f428609266b367cabab2542295c154a510e40f01`;
- even archive: `518e12043ef838355d488c0fa675f1332961796168920c6c15e4b3db0583c812`;
- 2026 H1: `59e48ee6a0b653a2b4530f8a2221e2e93e6af3e6a9f11281c6f17fc428a85ddf`.

## GhostStream blindness

Remove every event with solar longitude from 20.0 degrees through 55.0 degrees before any stratum, calibration pool, negative window, positive window, score, fold, or endpoint is formed. No GhostStream radiant, speed, orbit, membership, event list, or score may be used.

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

- strata are `[0,10), [10,20), ..., [350,360)` degrees in solar longitude;
- only strata that can construct a 128-event empirical background window are included;
- each supported year-stratum receives 128 deterministic calibration windows and 64 independent negative windows from the same fixed sporadic corpus and generator;
- candidate p-values are `p = (1 + number of calibration scores >= score) / 129`;
- overlapping Monte Carlo windows are allowed, matching the previously validated same-corpus empirical mechanism.

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

## Frozen per-panel scientific gates

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

Any failed scientific gate in any panel kills this coverage-normalized development formulation. Do not change the feasibility thresholds, bin width, boundaries, calibration count, negative count, score, seeds, folds, shower subset, blind interval, thresholds, or scientific gates after results are observed.

A four-panel retrospective pass authorizes only a separately frozen July 2026 snapshot test. It does not authorize a GhostStream application, discovery claim, or catalog scan.
