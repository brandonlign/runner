# Partition-invariant four-clique with 10° Mondrian calibration: fresh 2018 confirmation

Status: frozen before any 2018 GMN file is downloaded, counted, scored, or inspected.

## Scientific question

Does the unchanged partition-invariant four-event complete-link statistic, calibrated within globally anchored 10° solar-phase strata, preserve false-alarm control and weak-shower power on one completely untouched full observing year?

This is a fresh confirmation, not a rescue of any prior frozen result.

- PR #32 remains killed because coarse 60° calibration produced pooled 2026 H1 FPR 0.06836 against a frozen 0.060 limit.
- PR #36 remains killed because its exact four-panel protocol required at least 20 supported 10° strata in every panel, while partial-year 2026 H1 had only 15.
- PR #35 remains killed because adaptive 4/6/8 multiscale combination reduced power and failed worst-sector calibration.

The present formulation is different only in its prospectively declared target population: a **complete year**. Its score, 10° boundaries, calibration counts, comparators, folds, thresholds, and power gates are inherited unchanged from the successful complete-year PR #36 panels.

## Development and confirmation boundary

- Development and spent evidence: 2019–2026 results already recorded in PRs #31–#36.
- Fresh confirmation year: **2018 only**.
- Before this protocol was committed, no 2018 GMN event, file checksum, count, shower label, supported-bin count, candidate score, comparator score, or power endpoint was inspected for this project.
- The first job is data-only. It may inspect availability, counts, completeness, MDC grouping, and fixed-window feasibility, but it may not compute any candidate or comparator score.
- The score job runs only if every frozen data gate passes.
- Any failed data or power gate kills this exact formulation. No source file, threshold, bin, seed, shower subset, or gate may be changed after any 2018 result is observed.

A complete pass authorizes only a separately frozen cross-survey control and catalogue-level multiplicity study. It does not authorize a GhostStream application or discovery claim.

## GhostStream blindness

Before any calibration reservoir, negative window, positive window, score, fold, or endpoint is formed, remove every event with solar longitude from 20.0° through 55.0° inclusive.

No GhostStream radiant, speed, orbit, membership, event list, local region, or detection score may be used. The data-only audit may download the complete 2018 monthly summaries, but the blind interval is removed before fixed-window feasibility is assessed and before all later scoring.

## Frozen 2018 data extraction

Derive the one-year audit at runtime from the exact PR #14 source:

- source path: `real_shower_meta_stage0/audit_real_shower_data.py`;
- required Git blob SHA: `4a029051230f7c6e99b09e911f8a9e5228a58783`;
- year: `(2018,)`;
- months: January through December;
- exact PR #14 row parser, physical fields, quality filters, MDC complex/parent mapping, deterministic reservoirs, and source provenance;
- labeled reservoir: at most 500 quality events per shower-year;
- sporadic reservoir: at most 5,000 quality IAU `-1` events per month.

For the one-year audit only:

- an eligible shower requires at least 200 quality events, representation in 2018, and at least 20 events in 2018;
- a strong shower requires at least 300 quality events in 2018.

These thresholds are frozen before download and are used only to establish that a meaningful real-shower confirmation panel exists.

## Frozen data gates

Every gate must pass before any score source is decoded:

1. at least 30 eligible showers;
2. at least 8 strong showers;
3. at least 20 eligible MDC complex/parent units;
4. at least 2 multi-shower complex/parent units;
5. at least 50,000 raw quality IAU `-1` meteors;
6. selected-event feature completeness at least 0.95;
7. after removing solar longitude 20.0°–55.0°, at least 30 globally anchored 10° phase bins contain at least one sporadic center whose ±10° same-year neighborhood contains at least 128 retained sporadics;
8. the selected artifact contains only year 2018 and all twelve source months have nonzero downloaded files.

Failure ends the workflow before scoring and gives `KILL_2018_DATA_GATE`.

## Frozen search windows

If and only if the data gate passes, use the exact PR #36 implementation with:

- 128 events per window;
- one year per window;
- a ±10° solar-longitude neighborhood around the selected center event;
- positive windows containing `k in {4,6,8,12}` real members from one eligible established shower and real local IAU `-1` meteors;
- four deterministic positive replicates per eligible shower and member count;
- weak-power endpoints using k=4/6/8;
- negative and calibration windows containing only retained real local IAU `-1` meteors.

## Fixed physical geometry

Use the exact PR #14 feature space and scaling:

- relative solar longitude / 2°;
- Sun-centered ecliptic radiant longitude / 2°;
- Sun-centered ecliptic radiant latitude / 2°;
- geocentric speed / 2 km/s.

No orbital element, shower identity, absolute date, absolute solar longitude, or catalogue parameter enters the candidate score.

## Fixed partition-invariant four-clique score

Use the exact frozen PR #36 source, SHA-256 `e3dc3dfcbfbfdc15bead220464213ee271f7411cbf550bbecf0536153b85344e`:

1. compute the complete 128×128 physical-distance matrix;
2. for each event, select its three nearest other events;
3. form the four-event subset containing the anchor and those three neighbors;
4. compute its complete-link diameter, the largest of its six pairwise distances;
5. take the minimum diameter over all 128 anchors;
6. negate it so larger scores indicate stronger four-event coherence.

No radius, split, model weight, or tunable cluster threshold enters the score.

## Frozen 10° Mondrian calibration

Use globally anchored phase strata:

`[0°,10°), [10°,20°), ..., [350°,360°)`.

For every supported 2018 stratum outside the blind interval:

- draw 128 deterministic calibration windows from the fixed same-corpus empirical sporadic generator;
- draw 64 independent deterministic negative windows from the same generator;
- compute `p = (1 + number of calibration scores >= score) / 129`.

A stratum is supported only if the frozen generator can form a complete 128-event window. Unsupported strata are not merged, shifted, widened, or replaced.

Exact seed prefixes remain those frozen in PR #36:

- support: `mondrian-development-support`;
- calibration: `mondrian-development-calibration`;
- independent negatives: `mondrian-development-negative`;
- positive windows: `mondrian-development-positive`;
- split comparator: `mondrian-development-split`.

No seed may be replaced after execution.

## Fixed comparators and folds

Compute on the exact same windows:

- the killed eight-split PR #31 statistic;
- radius-2.5 local density;
- epsilon-2.5, minimum-samples-4 DBSCAN largest-cluster score;
- five deterministic event-count-balanced folds of complete MDC complex/parent units.

No comparator parameter or fold assignment may be reselected.

## Frozen confirmation gates

Every gate must pass:

1. pooled candidate FPR at alpha 0.05 ≤0.060;
2. pooled candidate FPR at alpha 0.01 ≤0.020;
3. worst 60° reporting-sector FPR at alpha 0.05 ≤0.120;
4. weak-window AUROC ≥0.75;
5. candidate AUROC no more than 0.03 below the strongest fixed comparator;
6. at least four of five folds have candidate AUROC ≥0.70 and no fold is below 0.65;
7. candidate recall at alpha 0.05 is at least 0.15, 0.30, and 0.45 for k=4,6,8;
8. candidate recall at alpha 0.01 is at least 0.05, 0.15, and 0.25 for k=4,6,8;
9. candidate recall is nondecreasing from k=4 to 6 to 8 to 12 at both thresholds.

These are the exact per-panel gates from PR #36. A failure gives `KILL_MONDRIAN_CLIQUE_2018_CONFIRMATION`. A pass gives `PASS_MONDRIAN_CLIQUE_2018_CONFIRMATION` and authorizes only the next separately frozen external-control stage.
