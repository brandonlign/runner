# Mondrian four-clique: unused July 2026 confirmation protocol

Status: frozen before `traj_summary_monthly_202607.txt` is downloaded or any July shower label, candidate score, comparator score, p-value, or power endpoint is read.

## Source-payload repair record

The first source-audit attempt failed before any July network request because the committed gzip/base64 July payload ended before its gzip end-of-stream marker. No July file was downloaded and no July count, label, score, or endpoint was observed. The incomplete payloads were replaced with complete, locally syntax-checked implementations while the untouched-data boundary remained intact. No scientific threshold, bin, score, seed, comparator, endpoint, or gate changed.

- frozen July data implementation SHA-256: `a9bd2f3ff033c7e4f524e214b28096c14e7a5cdddf56a043c20069a2b3d6d94e`;
- frozen July power implementation SHA-256: `8559424a4453ce4938654de37be7c164f3ca100ddd6c7d943c38df33cf3c2044`.

## Scientific question

Does the coverage-normalized 10-degree Mondrian four-clique methodology that passed the four-panel retrospective matrix in PR #38 retain calibrated false-alarm control and weak established-shower power on a previously unused July 2026 GMN snapshot?

This is a one-shot independent confirmation. Any failed feasibility or scientific gate kills the exact formulation. No July-derived threshold, bin boundary, shower subset, seed, endpoint, or score change is permitted.

## Confirmation target and blindness

- GMN monthly trajectory file: `traj_summary_monthly_202607.txt`;
- the file is treated as the available July snapshot, not assumed to contain the complete calendar month;
- the workflow records its URL, byte count, cryptographic hash, and extraction provenance;
- July 2026 has not appeared in any prior methodology score, calibration audit, power benchmark, threshold selection, or model comparison;
- remove every event with solar longitude from 20.0° through 55.0° before every retained reservoir used for support, calibration window, negative window, positive window, score, fold, and endpoint;
- no GhostStream radiant, speed, orbit, membership, event list, or score is used.

## Frozen data extraction

Use the exact PR #14 row parser, quality filters, current IAU MDC complex/parent mapping, and deterministic reservoir helper.

- year/month: 2026/07 only;
- labeled reservoir: at most 500 quality events per shower;
- sporadic reservoir: at most 20,000 quality IAU `-1` events;
- eligible shower: at least 20 quality events;
- strong shower: at least 100 quality events;
- 10-degree bins are globally anchored at integer multiples of 10°;
- a bin is supported only if at least one retained real sporadic center in that bin can form a 128-event empirical-background window within ±10°.

Every data gate must pass:

1. at least 30 eligible showers;
2. at least 8 strong showers;
3. at least 25 eligible MDC complex/parent units;
4. at least 2 multi-shower complex units;
5. at least 30,000 raw quality sporadics;
6. at least 15,000 retained sporadics outside the blind interval;
7. at least 2 supported 10-degree bins;
8. retained feature completeness at least 0.95.

The data stage may inspect only source provenance, counts, completeness, complex membership, and local-window feasibility. It may not compute the clique score, comparator scores, p-values, AUROC, recall, or any power endpoint.

## Frozen windows and geometry

- 128 events per window;
- one July snapshot and one year per window;
- ±10° solar-longitude neighborhood around the center;
- positive windows contain `k in {4,6,8,12}` real members from one established shower plus local real IAU `-1` meteors;
- four deterministic positive replicates per eligible shower and member count;
- positive centers are restricted to data-gate-supported 10-degree bins;
- weak endpoints use `k in {4,6,8}`;
- unchanged PR #14 physical coordinates and scales: relative solar longitude / 2°, Sun-centered ecliptic radiant longitude / 2°, Sun-centered ecliptic radiant latitude / 2°, and geocentric speed / 2 km/s.

## Frozen candidate score

For each window, compute the complete 128×128 physical-distance matrix. For every meteor, form the four-event subset consisting of that meteor and its three nearest other meteors, compute the subset's complete-link diameter, take the minimum diameter over all anchors, and negate it. No radius, cluster threshold, random partition, orbit element, shower identity, or absolute solar longitude enters the candidate score.

## Frozen Mondrian calibration

- strata: `[0,10), [10,20), …, [350,360)` degrees;
- evaluate only prospectively supported July strata;
- 128 deterministic calibration windows and 64 independent negative windows per supported stratum from the same retained empirical sporadic corpus;
- candidate p-value: `(1 + number of calibration scores >= test score) / 129`;
- overlapping Monte Carlo windows are allowed, matching the validated same-corpus empirical mechanism.

Frozen seed prefixes:

- support: `mondrian-july-confirmation-support`;
- calibration: `mondrian-july-confirmation-calibration`;
- independent negatives: `mondrian-july-confirmation-negative`;
- positive windows: `mondrian-july-confirmation-positive`;
- split comparator: `mondrian-july-confirmation-split`.

No seed may be replaced after results are observed.

## Frozen comparators and folds

On the exact same positive and independent-negative windows compute:

- the killed eight-split reference/query statistic;
- radius-2.5 local density;
- epsilon-2.5, minimum-samples-4 DBSCAN largest cluster;
- five deterministic event-count-balanced folds of complete MDC complex/parent units.

No comparator parameter or fold assignment may be reselected.

## Frozen confirmation gates

Every gate must pass:

1. pooled candidate FPR at alpha 0.05 ≤ 0.060;
2. pooled candidate FPR at alpha 0.01 ≤ 0.020;
3. worst 60-degree reporting-sector FPR at alpha 0.05 ≤ 0.120;
4. weak-window AUROC ≥ 0.75;
5. candidate AUROC no more than 0.03 below the strongest fixed comparator;
6. at least four of five fold AUROCs ≥ 0.70;
7. no fold AUROC < 0.65;
8. candidate recall at alpha 0.05 ≥ 0.15, 0.30, and 0.45 for `k=4,6,8`;
9. candidate recall at alpha 0.01 ≥ 0.05, 0.15, and 0.25 for `k=4,6,8`;
10. recall nondecreasing from `k=4` to 6 to 8 to 12 at both thresholds.

## Kill and continuation rules

Any failed data or confirmation gate kills this exact formulation. Do not change the file snapshot, eligibility threshold, supported-bin rule, bin width, boundaries, calibration count, negative count, score, seeds, folds, shower subset, blind interval, thresholds, comparators, or endpoints after results are observed.

A pass establishes independent method-level evidence that partition-invariant quartet coherence plus 10-degree Mondrian empirical calibration generalizes beyond all retrospective panels. It authorizes only separately frozen external-survey and catalog-level multiplicity studies; it does not by itself authorize a GhostStream application or discovery claim.
