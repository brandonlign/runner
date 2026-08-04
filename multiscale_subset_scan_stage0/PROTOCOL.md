# Partition-invariant multiscale subset scan: frozen development protocol

Status: frozen before any candidate score, established-shower power endpoint, or continuation decision is computed.

## Scientific question

Can a single calibrated adaptive scan over coherent 4-, 6-, and 8-event subsets recover the exactly-four-member sensitivity lost by reference/query partitioning without sacrificing the strong k=6/k=8 performance and calibration of local conformal coherence?

This is a distinct candidate. PR #31 remains killed under its frozen exactly-four-member recall gates. PR #32 remains killed because its single four-clique score produced a fresh-2026 pooled false-positive rate of 0.06836 at nominal 0.05. PR #33 remains killed because a nested minimum-p union of LCC and quartet cover was over-conservative and lost power. None of those frozen results may be relabelled or retuned.

## Development and confirmation boundary

- Development years: GMN 2019, 2021, 2023, and 2025 from the exact PR #14 selected-event artifact.
- Retired confirmation years: 2020, 2022, and 2024. No event, label, score, or endpoint from those years may be read.
- Retired fresh panel: January–June 2026. Its PR #32 result motivated the calibration diagnosis, but no 2026 event, label, score, or endpoint may be read by this development run.
- If and only if every frozen development gate passes, the next authorized step is a separately frozen data-only feasibility gate for complete 2018 GMN files, followed by one untouched 2018 confirmation run.
- A development pass does not authorize a GhostStream application, catalogue scan, threshold change, or claim.

## GhostStream blindness

Before any reservoir, window, calibration sample, score, fold, or endpoint is formed, remove every event with solar longitude from 20.0 degrees through 55.0 degrees inclusive. No GhostStream radiant, speed, orbit, membership, event list, detection score, or local region enters design or evaluation.

## Frozen input and episode construction

- Exact runner workflow artifact: `real-shower-meta-data-audit` from run `30855193522`.
- Selected-event SHA-256: `63e1389e2666d10b05138044f428609266b367cabab2542295c154a510e40f01`.
- Audit SHA-256: `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`.
- Exact baseline payload SHA-256: `2cb82a8c12913a6176ddd7c6333b57a4d672334934c0d2ca4b572e878590cfa2`.
- Exact decoded baseline-source SHA-256: `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`.
- Preserve the PR #14 parser, quality filters, five complex-disjoint folds, MDC complex/parent grouping, and ESV exclusion.
- Every window contains 128 events from one year and a plus-or-minus 10 degree solar-longitude neighborhood.
- Positive windows contain `k in {4, 6, 8, 12}` real members from one eligible established shower-year plus local real IAU `-1` meteors.
- Use two deterministic positive replicates for every eligible shower-year-member-count combination.
- Negative and calibration windows contain only local real IAU `-1` meteors.

## Fixed physical geometry

Use the unchanged PR #14 feature space and scaling:

- relative solar longitude divided by 2 degrees;
- Sun-centered ecliptic radiant longitude divided by 2 degrees;
- Sun-centered ecliptic radiant latitude divided by 2 degrees;
- geocentric speed divided by 2 km/s.

No orbital element, shower identity, absolute date, absolute solar longitude, or catalogue parameter enters the candidate statistic.

## Partition-invariant multiscale subset statistic

For each 128-event window and each subset size `m in {4, 6, 8}`:

1. Compute the complete physical-distance matrix.
2. For every event, form an anchored candidate subset containing that event and its `m-1` nearest other events.
3. Compute the complete-link diameter, the maximum pairwise distance within that candidate subset.
4. Take the minimum diameter across all 128 anchors.
5. Negate the minimum diameter so larger values indicate stronger coherent-subset evidence.

This requires only three nearest-neighbor searches and at most 128 small complete-link evaluations per scale. It is partition-invariant, deterministic, and feasible for a 128-event window.

## Full transductive conformal calibration of the scale search

For each year-by-60-degree solar-longitude sector:

- draw 256 deterministic calibration windows from one fixed same-corpus empirical sporadic generator;
- draw 64 independent audit-negative windows from the same generator;
- calibrate each audit or positive window separately against the unchanged 256 calibration windows;
- append the test window to the calibration matrix, giving 257 exchangeable rows;
- for every row and every subset scale, compute its upper-tail rank p-value within all 257 rows;
- define that row's adaptive statistic as the maximum across scales of negative log rank p-value;
- define the final candidate p-value as the upper-tail rank of the test row's adaptive statistic among all 257 rows.

The full augmented-sample construction treats the adaptive scale maximum as one permutation-symmetric statistic. It does not use a minimum component p-value as though it were already calibrated, and it does not split the empirical corpus into nested inner and outer samples.

Window overlap is permitted because the inferential unit is a deterministic Monte Carlo draw from the fixed empirical-window generator, matching the successful same-corpus mechanism established previously.

Frozen seed prefixes:

- support probe: `multiscale-support`;
- calibration windows: `multiscale-calibration-window`;
- audit-negative windows: `multiscale-audit-window`;
- positive windows: `multiscale-positive-window`;
- LCC diagnostic splits: `multiscale-lcc-split`.

No seed may be replaced after results are observed.

## Fixed comparators

Compute on the exact same windows:

- unchanged eight-split local conformal coherence from PR #31;
- marginal single-scale subset scans at sizes 4, 6, and 8;
- radius-2.5 local density;
- DBSCAN with epsilon 2.5 and minimum samples 4;
- five unchanged complex-disjoint folds.

No comparator parameter, scale, fold, or shower subset may be reselected.

## Frozen endpoints and continuation gates

Every gate must pass:

1. pooled candidate FPR at `p <= 0.05` is at most 0.060;
2. pooled candidate FPR at `p <= 0.01` is at most 0.020;
3. worst year-sector candidate FPR at `p <= 0.05` is at most 0.120;
4. candidate weak-window AUROC for `k in {4,6,8}` is at least 0.80;
5. candidate AUROC is no more than 0.005 below the strongest of LCC, density, and DBSCAN;
6. candidate AUROC is no more than 0.005 below the strongest marginal single-scale scan;
7. at least four of five candidate fold AUROCs are at least 0.75;
8. no candidate fold AUROC is below 0.70;
9. candidate k=4 recall at 0.05 is at least 0.15;
10. candidate k=4 recall at 0.05 exceeds contemporaneous LCC by at least 0.02;
11. candidate k=4 recall at 0.01 is at least 0.05;
12. candidate k=4 recall at 0.01 exceeds contemporaneous LCC by at least 0.01;
13. candidate k=6 recall at 0.05 is no more than 0.02 below LCC;
14. candidate k=8 recall at 0.05 is no more than 0.02 below LCC;
15. candidate k=6 recall at 0.01 is no more than 0.02 below LCC;
16. candidate k=8 recall at 0.01 is no more than 0.02 below LCC;
17. candidate recall is nondecreasing from k=4 to 6 to 8 to 12 at 0.05;
18. the same monotonicity holds at 0.01;
19. at least 2% of all k=4 positives are detected by the candidate at 0.05 while missed by LCC.

## Kill and continuation rules

Any failed gate kills this exact formulation. Do not alter subset sizes, anchoring, complete-link diameter, feature scales, transductive calibration, sample counts, sectors, seeds, thresholds, folds, comparator parameters, member counts, or blind interval after seeing the result.

A complete pass authorizes only the separately frozen 2018 confirmation data gate. A failure is preserved as a negative-method result and cannot be rescued by reweighting scales or changing the p-value construction.

The exact frozen candidate source SHA-256 is `660f436e173ff01fbd3af6e5cf88df6e1caa2dbfbc63f499875327ecd597dcce`.
