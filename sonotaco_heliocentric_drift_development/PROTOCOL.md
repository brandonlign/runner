# SonotaCo 2025 heliocentric-velocity drift-aligned quartet development

Status: frozen before any candidate score, p-value, AUROC, recall, false-positive endpoint, or fold result is computed.

## Scientific question

The strongest prior SonotaCo revisions improved overall discrimination but remained at or just below the four-member alpha-0.05 gate. PR #114 verified that the existing phase-gated score compares raw geocentric radiant and speed coordinates. Those observables drift across a shower activity interval partly because Earth's orbital velocity changes with solar longitude.

Does a fixed physical transformation from geocentric radiant/speed to heliocentric Cartesian velocity make sparse stream members more coherent without fitting a trajectory to each quartet?

## Why this is distinct from the killed affine candidate

The candidate fits no quartet slope, intercept, tube, orbit, or free trajectory. Every event is transformed independently using one fixed circular-Earth-orbit velocity vector. The quartet search then uses ordinary complete-link diameter. Thus the method cannot absorb accidental background structure through per-quartet affine flexibility.

## Frozen transformation and score

For event solar longitude `lambda_s`, ecliptic radiant direction `r_hat`, and geocentric speed `Vg`:

1. geocentric meteoroid velocity is `-Vg * r_hat`;
2. Earth's heliocentric velocity has fixed magnitude **29.78 km/s** and ecliptic longitude `lambda_s - 90°`;
3. heliocentric meteoroid velocity is their vector sum;
4. pairwise distance is the Euclidean heliocentric-velocity difference divided by **2 km/s**;
5. for each anchor, enumerate all quartets formed from its six nearest neighbors;
6. retain only quartets spanning at most **10°** in solar longitude;
7. score the episode by the negative minimum complete-link diameter.

The source includes a synthetic frame/sign self-test that constructs one fixed heliocentric velocity observed at three solar longitudes and requires exact recovery within numerical precision.

## Inherited components

The following remain unchanged from the exact audited sources:

- SonotaCo 2025 archive, parser, native-prefix label mapping, quality rules, and aggregate boundary;
- removal of solar longitude 20°–55° inclusive before labels, reservoirs, windows, scores, folds, and endpoints;
- 128-event windows from ±10° neighborhoods;
- 32 supported 10° Mondrian bins;
- 128 calibration negatives and 64 independent test negatives per bin;
- four positive replicates for k in {4,6,8,12};
- positive, calibration, and negative seeds;
- conservative rank p-values at alpha 0.05 and 0.01;
- five complex/parent folds;
- exact original PR #38 score and fixed split, density, and DBSCAN comparators.

## Frozen continuation gates

The exact original result must reproduce:

- pooled FPR 0.041015625 / 0.0068359375;
- k=4 recall 0.13970588235294118 / 0.03676470588235294.

The candidate must satisfy all of:

- pooled FPR <=0.060 / 0.020 at alpha 0.05 / 0.01;
- worst 60° reporting-sector FPR <=0.120 at alpha 0.05;
- weak-window AUROC >=0.75, within 0.03 of the strongest fixed comparator, and no more than 0.01 below the original;
- candidate AUROC exceeds density and DBSCAN;
- at least four of five fold AUROCs >=0.70, no fold below 0.65, and every fold finite/nonempty;
- recall at alpha 0.05 >=0.15, 0.30, and 0.45 for k=4,6,8;
- recall at alpha 0.01 >=0.05, 0.15, and 0.25 for k=4,6,8;
- recall nondecreasing through k=4,6,8,12 at both alpha levels;
- parser, support, and eligible-shower gates all pass.

No Earth speed, phase span, velocity scale, neighbor pool, calibration count, seed, threshold, comparator, fold, event filter, or gate may change after the result.

A complete pass authorizes only a separately preregistered one-shot SonotaCo 2024 confirmation of the exact frozen candidate. It does not authorize a catalogue scan or GhostStream application. SonotaCo 2024 remains untouched in this run.

Frozen candidate source SHA-256: `9a3873758b87aff129603fa6e375fa55c5eb4d22b2cf7231d0ffad359c2eae4e`.
