# Contrastive quartet persistence: frozen development protocol

Status: frozen before any candidate score, established-shower power endpoint, or continuation decision is computed.

## Scientific question

Can a four-event coherent core be distinguished from an accidental sporadic quartet by measuring its compactness relative to the immediate local background geometry, while preserving the partition-invariant weak-stream sensitivity demonstrated by the raw four-event scan?

This is a new candidate, not a retuning of a killed formulation. PR #32 remains killed because the raw partition-invariant four-clique statistic failed the untouched January–June 2026 pooled false-positive gate. PR #33 remains killed because the nested LCC/quartet union lost power. PR #35 remains killed because combining 4-, 6-, and 8-event subset scales reduced AUROC and failed conditional calibration. PR #36 remains killed under its frozen four-panel feasibility rule even though fixed 10-degree calibration passed three complete years.

The present candidate changes the scientific statistic itself: it tests whether the best four-event core is compact **relative to its own surrounding event scale**, rather than relying on absolute quartet compactness or adding more subset sizes.

## Development and confirmation boundary

- Development years: GMN 2019, 2021, 2023, and 2025 from the exact PR #14 selected-event artifact.
- Retired years: 2020, 2022, and 2024. No event, label, score, or endpoint from those years may be read.
- Retired partial-year panel: January–June 2026. No event, label, score, or endpoint from that panel may be read.
- Fresh reserve: complete GMN 2018 files. They may be accessed only if every frozen development gate passes, first through a separately frozen data-only feasibility gate and then through one untouched confirmation run.
- A development pass does not authorize a GhostStream application, catalogue scan, threshold change, or discovery claim.

## GhostStream blindness

Before any reservoir, window, calibration sample, score, fold, or endpoint is formed, remove every event with solar longitude from 20.0 degrees through 55.0 degrees inclusive. No GhostStream radiant, speed, orbit, membership, event list, detection score, or local solar-longitude region enters design or evaluation.

## Frozen input and episode construction

- Exact runner workflow artifact: `real-shower-meta-data-audit` from run `30855193522`.
- Selected-event SHA-256: `63e1389e2666d10b05138044f428609266b367cabab2542295c154a510e40f01`.
- Audit SHA-256: `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`.
- Exact baseline payload SHA-256: `2cb82a8c12913a6176ddd7c6333b57a4d672334934c0d2ca4b572e878590cfa2`.
- Exact decoded baseline-source SHA-256: `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`.
- Preserve the PR #14 parser, quality filters, five complex-disjoint folds, MDC complex/parent grouping, and ESV exclusion.
- Every window contains 128 events from one year and a plus-or-minus 10-degree solar-longitude neighborhood.
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

## Contrastive quartet persistence statistic

For each 128-event window:

1. Compute the complete physical-distance matrix.
2. For each event as an anchor, select the anchor and its three nearest other events.
3. Compute the complete-link diameter of that four-event core: the maximum pairwise distance among its four events.
4. Compute the anchor's 13th-nearest-neighbor distance in the full window.
5. Define the anchor contrast as

   `log(13th-neighbor radius / four-event complete-link diameter)`.

6. Define the window score as the maximum anchor contrast across all 128 anchors.

The 13th-neighbor rank is fixed because positive episodes contain at most 12 injected stream members; under ideal ordering it is the first rank guaranteed to extend beyond the complete injected stream. The statistic therefore asks whether a four-event core is unusually compact relative to the surrounding non-core geometry. It is deterministic, partition-invariant, dimensionless, and uses no learned parameter.

No alternative context rank, core size, distance aggregation, ratio transform, anchor rule, or scale combination may be tested after results are observed.

## Calibration

For each year-by-60-degree solar-longitude sector:

- draw 256 deterministic calibration windows from one fixed same-corpus empirical sporadic generator;
- draw 64 independent audit-negative windows from the same generator;
- compute the candidate score on every calibration and test window;
- assign a conservative upper-tail rank p-value `(1 + exceedances) / 257`.

The same calibration windows also calibrate the frozen raw quartet and LCC diagnostics. Window overlap is permitted because the inferential unit is a deterministic Monte Carlo draw from the fixed empirical-window generator, matching the previously validated same-corpus mechanism.

Frozen seed prefixes:

- support probe: `contrastive-quartet-support`;
- calibration windows: `contrastive-quartet-calibration-window`;
- audit-negative windows: `contrastive-quartet-audit-window`;
- positive windows: `contrastive-quartet-positive-window`;
- LCC diagnostic splits: `contrastive-quartet-lcc-split`.

No seed may be replaced after results are observed.

## Fixed comparators

Compute on the exact same windows:

- unchanged eight-split local conformal coherence from PR #31;
- raw partition-invariant four-event compactness from PR #32/#35;
- radius-2.5 local density;
- DBSCAN with epsilon 2.5 and minimum samples 4;
- five unchanged complex-disjoint folds.

No comparator parameter, fold, shower subset, or endpoint may be reselected.

## Frozen endpoints and continuation gates

Every gate must pass:

1. pooled candidate FPR at `p <= 0.05` is at most 0.060;
2. pooled candidate FPR at `p <= 0.01` is at most 0.020;
3. worst year-sector candidate FPR at `p <= 0.05` is at most 0.120;
4. candidate weak-window AUROC for `k in {4,6,8}` is at least 0.80;
5. candidate AUROC is no more than 0.01 below the raw quartet comparator;
6. candidate AUROC is no more than 0.01 below the strongest of LCC, density, and DBSCAN;
7. at least four of five candidate fold AUROCs are at least 0.75;
8. no candidate fold AUROC is below 0.70;
9. candidate k=4 recall at 0.05 is at least 0.15;
10. candidate k=4 recall at 0.05 exceeds contemporaneous LCC by at least 0.01;
11. candidate k=4 recall at 0.01 is at least 0.05;
12. candidate k=4 recall at 0.01 exceeds contemporaneous LCC by at least 0.005;
13. candidate k=6 recall at 0.05 is no more than 0.03 below LCC;
14. candidate k=8 recall at 0.05 is no more than 0.03 below LCC;
15. candidate k=6 recall at 0.01 is no more than 0.03 below LCC;
16. candidate k=8 recall at 0.01 is no more than 0.03 below LCC;
17. candidate recall is nondecreasing from k=4 to 6 to 8 to 12 at 0.05;
18. the same monotonicity holds at 0.01;
19. at least 2% of all k=4 positives are detected by the candidate at 0.05 while missed by LCC.

## Kill and continuation rules

Any failed gate kills this exact formulation. Do not alter the context rank, core size, complete-link diameter, feature scales, calibration groups, sample counts, seeds, thresholds, folds, comparator parameters, member counts, or blind interval after seeing the result.

A complete pass authorizes only the separately frozen 2018 data gate. A failure must be preserved as a negative-method result and cannot be rescued by changing the ratio, rank, neighborhood, or calibration.

The exact candidate source SHA-256 will be recorded in this file and the workflow before execution.