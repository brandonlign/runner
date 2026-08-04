# Phase-adaptive nested conformal coherence: frozen July 2026 confirmation

Status: frozen before downloading or reading the July 2026 trajectory file.

## Scientific question

Can a partition-invariant four-event coherence score, normalized continuously against nearby solar-longitude background windows and then recalibrated by an independent outer conformal layer, detect weak real meteor showers while preserving false-alarm control under seasonal background drift?

This is a new candidate following the PR #34 no-go. It does not alter PR #34's score, seeds, thresholds, or verdict.

## Development and confirmation boundary

- Development and diagnosis data: 2019–2025 and January–June 2026.
- Untouched confirmation data: the official GMN July 2026 monthly trajectory summary only.
- August 2026 and all later data are excluded.
- No July event, label, score, count, or distribution may change this protocol.

## GhostStream blindness

Remove every event with solar longitude from 20.0° through 55.0° before any pool, block, score, calibration statistic, fold, or endpoint is formed. No GhostStream radiant, speed, orbit, membership, event list, or score is used.

## Frozen July data construction

Derive July 2026 from the exact PR #14 parser, verified by Git blob SHA `4a029051230f7c6e99b09e911f8a9e5228a58783`.

A shower is eligible when it has at least 12 quality events in July 2026. A strong shower has at least 50 quality events. Data gates:

- at least 20 eligible showers;
- at least 8 strong showers;
- at least 15 eligible MDC complex/parent units;
- at least 2 multi-shower complex units;
- at least 35,000 quality sporadic events before reservoir sampling;
- at least 95% selected-event completeness;
- at least 3 supported globally anchored 10° solar-longitude blocks after blindness.

Any failed data gate kills the confirmation. July may not be replaced or extended.

## Window generator

- 128 events per window;
- one observing year;
- a ±10° solar-longitude neighborhood around the selected center;
- negative windows contain only real local IAU `-1` meteors;
- calibration and audit windows are independent pseudorandom draws from the same fixed empirical July corpus;
- overlap between Monte Carlo windows is allowed.

## Fixed physical geometry

Use the exact PR #14 distance with scales:

- relative solar longitude / 2°;
- Sun-centered ecliptic longitude and latitude / 2°;
- geocentric speed / 2 km/s.

No orbital element, shower identity, absolute date, or absolute solar longitude enters the raw coherence score.

## Tri-supported four-star coherence score

For each 128-event window:

1. compute its complete pairwise physical-distance matrix;
2. treat each event as a center and add its three nearest neighbors;
3. measure the maximum pairwise distance within each resulting four-event star;
4. sort the 128 star diameters;
5. negate the mean of the three smallest diameters.

A single accidental quartet cannot dominate as strongly as under minimum diameter, while a real four-member cluster can create several mutually tight centered stars. The score is deterministic and partition-invariant.

## Phase-adaptive inner normalization

Use globally anchored 10° solar-longitude blocks. Within each supported block:

- draw 512 inner-reference windows;
- for a target window, select the 128 inner windows whose centers are nearest in circular solar longitude;
- linearly interpolate the target score within the selected scores' empirical mid-rank CDF;
- use the upper-tail coordinate `u = 1 - CDF` as a continuous locally normalized statistic.

The interpolation is only a normalization. It is not claimed to be a valid p-value by itself.

## Independent outer conformal calibration

Conditional on the fixed inner bank, draw 512 independent outer-calibration windows from the same block. Compute their local tail coordinates with the unchanged inner bank.

For a target coordinate `u`, define

`p = (1 + number of outer coordinates <= u) / 513`.

Outer and target windows are exchangeable within a block conditional on the inner bank, so this outer rank is the inferential p-value. This second layer restores finite-sample marginal validity even if the local interpolation is imperfect.

## Label-blind null audit

Run eight independent batches. Each batch uses fresh inner and outer banks plus 128 audit windows per supported block. Shower labels are discarded before scoring.

Frozen null gates:

1. at least 3 supported blocks;
2. mean batch FPR at alpha 0.05 <= 0.060;
3. mean batch FPR at alpha 0.01 <= 0.015;
4. one-sided 95% t upper bound for mean batch FPR <= 0.065 at alpha 0.05;
5. one-sided 95% t upper bound <= 0.020 at alpha 0.01;
6. no batch FPR exceeds 0.100 at alpha 0.05;
7. the largest block's FPR averaged across batches is <= 0.080 at alpha 0.05.

These batch-level gates evaluate persistent miscalibration without requiring every finite 512-window realization to land below an arbitrary 6% cutoff.

## Untouched real-shower power audit

Only after an all-pass null audit:

- construct positive windows containing `k in {4,6,8,12}` real members plus local real sporadics;
- include only showers for which all four member counts can be constructed under the frozen generator;
- use eight deterministic replicates per shower/member count;
- use fresh inner and outer banks and 256 independent negative windows per supported block;
- report five deterministic complete-complex folds;
- compare raw AUROC with fixed local density radius 2.5 and DBSCAN epsilon 2.5/min_samples 4.

Power gates:

1. at least 20 eligible power-panel showers and 400 weak positive windows;
2. negative FPR <= 0.060 at alpha 0.05 and <= 0.020 at alpha 0.01;
3. worst block FPR <= 0.120 at alpha 0.05;
4. weak-window AUROC >= 0.78;
5. candidate AUROC no more than 0.03 below the stronger fixed comparator;
6. at least four of five folds have AUROC >= 0.72 and no evaluable fold is below 0.67;
7. recall at alpha 0.05 is at least 0.15, 0.30, and 0.45 for k=4,6,8;
8. recall at alpha 0.01 is at least 0.05, 0.15, and 0.25 for k=4,6,8;
9. recall is nondecreasing through k=12 at both thresholds.

Any failed gate kills the candidate. No block width, neighbor count, interpolation rule, bank size, seed, score, threshold, comparator, month, or shower subset may change after July results are observed.

A pass authorizes only a separately frozen external weak-stream control and catalog-level family-wise error study. It does not authorize application to GhostStream.
