# Mondrian four-clique: unused July 2026 confirmation protocol

Status: frozen before `traj_summary_monthly_202607.txt` is downloaded or any July shower label, candidate score, comparator score, p-value, or power endpoint is read.

## Scientific question

Does the coverage-normalized 10-degree Mondrian four-clique methodology that passed the four-panel retrospective matrix in PR #38 retain calibrated false-alarm control and weak established-shower power on a previously unused July 2026 GMN snapshot?

This is a one-shot independent confirmation. Any failed feasibility or scientific gate kills the exact formulation. No July-derived threshold, bin boundary, shower subset, seed, endpoint, or score change is permitted.

## Confirmation target

- GMN monthly trajectory file: `traj_summary_monthly_202607.txt`;
- the official index listed the snapshot as 43 MB dated July 20, 2026 before this protocol was frozen;
- the workflow will download the file once, record source metadata and cryptographic hashes, and preserve the selected event artifact;
- the file is treated as a July snapshot, not assumed to contain the complete calendar month.

July 2026 has not appeared in any prior GhostStream methodology score, calibration audit, power benchmark, threshold selection, or model comparison.

## GhostStream blindness

Remove every event with solar longitude from 20.0 degrees through 55.0 degrees before any stratum, calibration pool, negative window, positive window, score, fold, or endpoint is formed. No GhostStream radiant, speed, orbit, membership, event list, or score may be used.

## Frozen data extraction

Use the exact PR #14 row parser and quality filters, and the exact current IAU MDC complex/parent mapping.

- year: 2026;
- month: July only;
- labeled reservoir: at most 500 quality events per shower;
- sporadic reservoir: at most 20,000 quality IAU `-1` events;
- eligible shower: at least 20 quality events, matching the frozen EpisodeFactory threshold;
- strong shower: at least 100 quality events;
- 10-degree bins are globally anchored at integer multiples of 10 degrees;
- a bin is supported only if at least one real center in that bin can form a 128-event empirical-background window within plus or minus 10 degrees.

Exact data-extraction source SHA-256: `1349da2d94b6f300ec7982bee7f5c17df5318c425da8a7d1f15d8befa1f551ec`.

### Frozen data gates

Every gate must pass before the power workflow is authorized:

1. at least 30 eligible showers;
2. at least 8 strong showers;
3. at least 25 eligible MDC complex/parent units;
4. at least 2 multi-shower complex units;
5. at least 30,000 raw quality sporadics;
6. at least 15,000 retained sporadics outside the blind interval;
7. at least 2 supported 10-degree bins;
8. retained feature completeness at least 0.95.

The data gate may inspect counts, completeness, complex membership, source hashes, and local-window feasibility only. It may not compute the clique score, comparator scores, p-values, AUROC, recall, or any power endpoint.

## Frozen windows and geometry

- 128 events per window;
- one year and one July snapshot per window;
- plus or minus 10 degrees in solar longitude around the center event;
- positive windows contain `k in {4, 6, 8, 12}` real members from one established shower and real local IAU `-1` meteors;
- four deterministic positive replicates per eligible shower and member count;
- weak-power endpoints use `k in {4, 6, 8}`;
- exact PR #14 physical distance and scales:
  - relative solar longitude / 2 degrees;
  - Sun-centered ecliptic longitude and latitude / 2 degrees;
  - geocentric speed / 2 km/s.

Positive centers are restricted to data-gate-supported 10-degree bins so every evaluated positive window has a prospectively valid local empirical calibration stratum. This restriction is frozen before July data is read and does not use a method score.

## Frozen partition-invariant score

For each window:

1. compute the complete 128-by-128 physical-distance matrix;
2. for each meteor, identify its three nearest other meteors;
3. form the four-event subset containing that meteor and those neighbors;
4. compute the complete-link diameter of the subset;
5. take the minimum diameter over all anchors;
6. negate it so larger values indicate stronger coherence.

No radius, cluster threshold, random partition, orbit element, shower identity, or absolute solar longitude enters the candidate score.

## Frozen Mondrian calibration

- strata are `[0,10), [10,20), ..., [350,360)` degrees in solar longitude;
- only prospectively supported July strata are evaluated;
- each supported stratum receives 128 deterministic calibration windows and 64 independent negative windows from the same retained empirical sporadic corpus and generator;
- candidate p-values are `p = (1 + number of calibration scores >= score) / 129`;
- overlapping Monte Carlo windows are allowed, matching the same-corpus empirical mechanism validated in PRs #29 and #38.

Exact seed prefixes:

- support: `mondrian-july-confirmation-support`;
- calibration: `mondrian-july-confirmation-calibration`;
- independent negatives: `mondrian-july-confirmation-negative`;
- positive windows: `mondrian-july-confirmation-positive`;
- split comparator: `mondrian-july-confirmation-split`.

No seed may be replaced after results are observed.

## Frozen comparators and folds

Compute on the exact same positive and independent-negative windows:

- the killed eight-split reference/query statistic;
- radius-2.5 local density;
- epsilon-2.5, minimum-samples-4 DBSCAN largest cluster;
- five deterministic event-count-balanced folds of complete MDC complex/parent units.

No comparator parameter or fold assignment may be reselected.

Exact power implementation SHA-256: `7a551f0fc7ce4b40642e83449f4ce37d5b0cd9a7abf900c46a1250e159e96fb0`.

## Frozen confirmation gates

Every gate must pass:

1. pooled candidate FPR at alpha 0.05 is at most 0.060;
2. pooled candidate FPR at alpha 0.01 is at most 0.020;
3. worst 60-degree reporting-sector FPR at alpha 0.05 is at most 0.120;
4. weak-window AUROC is at least 0.75;
5. candidate AUROC is no more than 0.03 below the strongest fixed comparator;
6. at least four of five folds have candidate AUROC at least 0.70;
7. no fold has candidate AUROC below 0.65;
8. candidate recall at alpha 0.05 is at least 0.15, 0.30, and 0.45 for `k = 4, 6, 8`;
9. candidate recall at alpha 0.01 is at least 0.05, 0.15, and 0.25 for `k = 4, 6, 8`;
10. recall is nondecreasing from `k = 4` to 6 to 8 to 12 at both thresholds.

## Kill and continuation rules

Any failed data or confirmation gate kills this exact formulation. Do not change the file snapshot, eligibility thresholds, supported-bin requirement, bin width, boundaries, calibration count, negative count, score, seeds, folds, shower subset, blind interval, thresholds, comparators, or endpoints after results are observed.

A pass would establish independent method-level evidence that the partition-invariant clique plus 10-degree Mondrian empirical calibration generalizes beyond all development panels. It would authorize only separately frozen external-survey and catalog-level multiplicity studies. It would not by itself authorize a GhostStream discovery claim or application.