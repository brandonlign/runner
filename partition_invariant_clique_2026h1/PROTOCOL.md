# Partition-invariant four-clique scan: frozen 2026 H1 protocol

Status: frozen before any method score or established-shower power result is computed from 2026 data.

## Scientific question

Can a partition-invariant four-point coherence statistic preserve the calibrated false-alarm control of the empirical-window framework while recovering the exactly-four-member power lost by the reference/query split statistic?

This is a new method, not a rescue of PR #31. The PR #31 score, thresholds, seeds, and result remain unchanged and killed.

## Development and confirmation boundary

- Development data: GMN 2019, 2021, 2023, and 2025.
- Fresh confirmation data: complete monthly GMN files from January through June 2026.
- The 2026 files have not appeared in any prior GhostStream methodology score, power benchmark, threshold selection, or model comparison.
- No 2026 shower label may be used until this protocol and the data-extraction source are committed.
- The 2026 data gate may inspect counts, completeness, complex membership, and local-window feasibility only. It may not compute the candidate score or any power endpoint.
- The exact frozen power source SHA-256 is `22b9ddeab4b628a8991d255c740ba709ffe7977c209fd21a2ad9083c2c726e2f`.

## Fresh data gate result before scoring

Runner workflow `30873092919` passed all eight frozen data gates without computing any candidate or comparator score.

- artifact: `8878551241`;
- artifact digest: `sha256:a0d49849f30db3af4c51d13d5e7e6e8bc6dbdd70c41d1aed189f57aec75572f4`;
- selected events SHA-256: `59e48ee6a0b653a2b4530f8a2221e2e93e6af3e6a9f11281c6f17fc428a85ddf`;
- audit SHA-256: `45a367043ff91f4b44be4934d56d5b923ac4aea555ddf41fdd7cebfa7bc5d28e`;
- 119 eligible showers and 26 strong showers;
- 114 eligible complex/parent units and 5 multi-shower units;
- 274,308 raw quality sporadics;
- 23,726 retained sporadics outside the blind interval;
- supported sectors: 0, 1, 4, and 5;
- selected feature completeness: 1.0.

These feasibility results do not alter the already frozen score, gates, seeds, or endpoints.

## GhostStream blindness

Remove every event with solar longitude from 20.0 degrees through 55.0 degrees before any calibration pool, negative window, positive window, score, fold, or endpoint is formed. No GhostStream radiant, speed, orbit, membership, event list, or detection score may be used.

## Frozen 2026 H1 data extraction

- year: 2026;
- months: January through June inclusive;
- exact PR #14 row parser and quality filters;
- exact current IAU MDC complex/parent grouping;
- at most 500 quality events retained per eligible shower;
- at most 5,000 quality IAU `-1` events retained per month;
- an eligible shower has at least 60 quality events in the six-month panel;
- a strong shower has at least 300 quality events.

The exact extraction source SHA-256 is `93f400bc92eda40a42f0cc5684a374972c3c083320844bdb7c5004a6539cd26d`.

### Frozen data gates

Every gate must pass before a power source is allowed to run:

1. at least 20 eligible showers;
2. at least 8 strong showers;
3. at least 15 eligible MDC complex/parent units;
4. at least 2 multi-shower complex units;
5. at least 100,000 raw quality sporadics;
6. at least 20,000 retained sporadics outside the blind interval;
7. at least four 60-degree solar-longitude sectors can form a 128-event local window outside the blind interval;
8. retained feature completeness is at least 0.95.

Any failed data gate kills the 2026 confirmation before scoring.

## Frozen search windows

- 128 events per window;
- one year per window;
- a plus-or-minus 10 degree solar-longitude neighborhood;
- positive windows contain `k in {4, 6, 8, 12}` real members from one eligible shower and real local IAU `-1` meteors;
- four deterministic positive replicates per eligible shower and member count;
- weak-power endpoints use `k in {4, 6, 8}`;
- negative windows contain only real local IAU `-1` meteors.

## Fixed physical distance

Use the exact PR #14 geometry and scales:

- relative solar longitude / 2 degrees;
- Sun-centered ecliptic longitude and latitude / 2 degrees;
- geocentric speed / 2 km/s.

No orbital elements, shower identity, absolute date, or absolute solar longitude enter the candidate score.

## Partition-invariant four-clique score

For each 128-event window:

1. compute the complete 128-by-128 physical-distance matrix;
2. for each meteor, identify its three nearest other meteors;
3. form the four-event subset containing that meteor and those three neighbors;
4. compute the subset diameter, the maximum of its six pairwise distances;
5. take the minimum diameter across all 128 candidate subsets;
6. negate that minimum so larger scores indicate stronger four-point coherence.

The score contains no random partition, split count, tunable radius, or cluster threshold. A truly compact four-member subset is represented by the same quartet from at least one of its members, while chains and single dense centers are penalized by the complete-link diameter.

## Frozen same-corpus local calibration

For every supported 60-degree sector in 2026:

- draw 512 deterministic calibration windows from the fixed retained empirical sporadic corpus;
- draw 256 deterministic independent negative windows from the same corpus and generator;
- convert a score to `p = (1 + number of calibration scores >= score) / 513`;
- overlapping Monte Carlo windows are allowed, matching the Stage-0 mechanism that passed on four development years and three untouched even years.

Exact seed prefixes:

- support probes: `clique-2026h1-support`;
- calibration windows: `clique-2026h1-calibration`;
- independent negative windows: `clique-2026h1-negative`;
- positive windows: `clique-2026h1-positive`;
- frozen split-comparator partitions: `clique-2026h1-split`.

No seed may be replaced after results are observed.

## Frozen comparators and folds

Compute on the exact same windows:

- radius-2.5 local density;
- epsilon-2.5, minimum-samples-4 DBSCAN largest cluster;
- the killed PR #31 reference/query coherence statistic as a diagnostic comparator only, with eight 64/64 splits, second-nearest reference distance, top-two mean, and median aggregation;
- five deterministic event-count-balanced folds of complete MDC complex/parent units.

No comparator parameter or fold assignment may be reselected.

## Frozen endpoints and continuation gates

Every gate must pass:

1. pooled negative FPR at alpha 0.05 is at most 0.060;
2. pooled negative FPR at alpha 0.01 is at most 0.020;
3. worst supported sector FPR at alpha 0.05 is at most 0.120;
4. mean weak-window AUROC is at least 0.75;
5. candidate weak AUROC is no more than 0.03 below the strongest fixed comparator;
6. at least four of five folds have candidate weak AUROC at least 0.70, and no fold is below 0.65;
7. candidate recall at alpha 0.05 is at least 0.15, 0.30, and 0.45 for `k = 4, 6, 8`;
8. candidate recall at alpha 0.01 is at least 0.05, 0.15, and 0.25 for `k = 4, 6, 8`;
9. candidate recall is nondecreasing from `k = 4` to 6 to 8 to 12 at both thresholds;
10. candidate k=4 recall is no lower than the split comparator at both thresholds;
11. candidate k=4 recall exceeds the split comparator by at least 0.01 at one or both thresholds.

## Kill and continuation rules

Any failed gate kills this exact formulation. Do not change the nearest-neighbor count, subset size, diameter definition, feature scales, sector width, calibration count, seeds, comparator parameters, folds, shower subset, blind interval, thresholds, or endpoints after seeing 2026 results.

A pass authorizes a separately frozen cross-survey weak-stream and catalog-level multiplicity study. It does not authorize a GhostStream claim or application.
