# Ten-degree Mondrian calibration for partition-invariant clique coherence

Status: frozen development benchmark before the full 2019/2021/2023/2025 score and power run.

## Scientific question

Can fixed, physically local solar-phase strata repair the residual false-positive inflation of the partition-invariant four-event clique score without sacrificing the strong weak-shower power demonstrated on fresh 2026 H1 data?

This is a calibration replacement, not a reinterpretation of PR #32. PR #32 remains killed because its 60°-sector pooled false-positive rate was 0.06836 against a frozen maximum of 0.06000.

## Development and confirmation boundary

- Full development benchmark: GMN 2019, 2021, 2023, and 2025 from the exact PR #14 artifact.
- Spent diagnostic years: 2020, 2022, 2024, and January–June 2026. These years motivated the calibration diagnosis and may not validate this replacement.
- Reserved fresh confirmation year: 2018. No 2018 event, label, score, count, or feasibility result may be read unless every gate in this development benchmark passes.
- A pass authorizes only a separately frozen 2018 data gate and confirmation benchmark. It does not authorize a catalog scan or GhostStream application.

## Failure diagnosis motivating the new calibration

The fresh PR #32 detector passed every discrimination and power gate:

- weak AUROC 0.82674;
- k=4 recall 0.23485 at alpha 0.05 and 0.10354 at alpha 0.01;
- all complex folds between 0.78798 and 0.86601.

Its sole failure was pooled alpha-0.05 FPR 0.06836 under coarse 60° calibration. False positives were concentrated within narrow solar-longitude subregions, especially 280°–289° and 55°–59°, and the killed split comparator was elevated in the same background region. The detector therefore remains fixed; only the conditional calibration unit changes.

Before this full run, reduced spent-data screens established that center-local calibration controlled every historical year-sector and that fixed 10° bins reduced the spent 2026 diagnostic FPR to 0.04010 at alpha 0.05 and 0.00781 at alpha 0.01, with worst-bin FPR 0.10156. Those diagnostics are development evidence only.

## GhostStream blindness

Remove every event with solar longitude from 20.0° through 55.0° before any calibration pool, negative window, positive window, score, fold, or endpoint is formed. No GhostStream radiant, speed, orbit, membership, event list, or detection score may be used.

## Frozen source data

- exact runner workflow `30855193522` artifact `real-shower-meta-data-audit`;
- selected-event SHA-256 `63e1389e2666d10b05138044f428609266b367cabab2542295c154a510e40f01`;
- audit SHA-256 `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`;
- exact PR #14 parser, quality filters, ESV exclusion, MDC complex/parent grouping, and five complex-disjoint folds;
- expected years exactly 2019, 2021, 2023, and 2025.

## Frozen search windows

- 128 events per window;
- one year per window;
- a ±10° solar-longitude neighborhood;
- positive windows contain `k in {4,6,8,12}` real members from one eligible established shower-year and real local IAU `-1` meteors;
- two deterministic positive replicates per eligible shower-year-member-count combination;
- negative windows contain only real local IAU `-1` meteors.

## Fixed physical geometry

Use the exact PR #14 distance and scales:

- relative solar longitude / 2°;
- Sun-centered ecliptic longitude / 2°;
- Sun-centered ecliptic latitude / 2°;
- geocentric speed / 2 km/s.

No orbital elements, shower identity, absolute date, or absolute solar longitude enter the detector score.

## Fixed partition-invariant clique score

The detector is unchanged from PR #32:

1. compute the complete 128×128 physical-distance matrix;
2. for each event, select its three nearest other events;
3. form the four-event subset containing the anchor and those three neighbors;
4. compute the complete-link diameter, the largest of the six pairwise distances;
5. take the minimum diameter across all 128 anchor-defined subsets;
6. negate the result so larger scores indicate stronger four-event coherence.

No radius, split, learned weight, or post-result parameter enters the score.

## New fixed Mondrian calibration

Assign each window to the fixed solar-phase category

`floor((center solar longitude mod 360°) / 10°)`.

The 10° width is fixed because it equals the half-width of the ±10° search neighborhood. Categories are determined solely from the window center and never from a score or shower label.

For every supported year-by-10° category:

- draw 128 deterministic calibration windows from the fixed empirical sporadic corpus;
- draw 128 independent deterministic audit-negative windows from the same corpus and generator;
- compute the conservative rank p-value

`p = (1 + number of calibration scores >= candidate score) / 129`.

A category is supported only if the frozen empirical generator can form a complete 128-event window. At least 100 categories must be supported across the four years. No unsupported category may be merged after results are observed.

Overlapping Monte Carlo windows are allowed. Within a fixed year-phase category, calibration and audit windows are exchangeable draws from the same empirical generator.

## Fixed comparators

On the exact same windows, compute raw AUROC for:

- the killed eight-split PR #31 statistic;
- radius-2.5 local density;
- epsilon-2.5, minimum-samples-4 DBSCAN largest cluster.

Comparators are diagnostic only; no parameter is reselected.

## Exact seed prefixes

- support: `mondrian10-support`;
- calibration: `mondrian10-calibration`;
- independent negatives: `mondrian10-negative`;
- positives: `mondrian10-positive`;
- split comparator: `mondrian10-split`.

No seed may be replaced after execution.

## Frozen continuation gates

Every gate must pass:

1. at least 100 supported year-phase categories;
2. pooled candidate FPR at alpha 0.05 ≤0.060;
3. pooled candidate FPR at alpha 0.01 ≤0.020;
4. worst supported category FPR at alpha 0.05 ≤0.120;
5. candidate weak-window AUROC ≥0.79;
6. candidate AUROC no more than 0.03 below the strongest fixed comparator;
7. at least four of five complex folds have candidate AUROC ≥0.75;
8. no complex fold has candidate AUROC below 0.70;
9. recall at alpha 0.05 is at least 0.15, 0.30, and 0.45 for k=4,6,8;
10. recall at alpha 0.01 is at least 0.05, 0.15, and 0.25 for k=4,6,8;
11. recall is nondecreasing from k=4 to 6 to 8 to 12 at both thresholds.

## Kill rule

Any failed gate gives `KILL_MONDRIAN10_CALIBRATION`. Do not alter the 10° categories, category support rule, calibration or audit counts, score, seeds, thresholds, folds, member counts, blind interval, or gates after observing the result.

A pass gives only `PROCEED_TO_2018_FRESH_DATA_GATE`.
