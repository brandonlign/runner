# SonotaCo 2025 cross-predictive radiant-drift quartet development

Status: frozen before any candidate score, p-value, recall, AUROC, or false-positive endpoint is computed.

## Scientific motivation

PR #118 showed that unconstrained in-quartet phase detrending compresses background quartets much more strongly than true shower quartets. The fitted quartet and the validated quartet were identical: each slope was estimated from all six pair differences among the same four events. All-four-member selection consequently fell from 53/136 for the phase-gated 3D control to 34/136 for radiant-only drift and 27/136 for radiant-plus-speed drift.

The single authorized revision is cross-prediction. A quartet may fit a radiant trajectory on three events, but it must predict the held-out fourth event. No event may contribute to the fit used to score its own residual.

## Exact fixed score

Preserve the PR #118 candidate quartet reservoir exactly:

- compute the phase-gated 3D radiant-speed distance;
- for every anchor, enumerate triplets from its six nearest radiant-speed neighbors;
- retain only quartets spanning at most 10° in relative solar longitude.

For each retained quartet:

1. express radiant longitude in a permutation-invariant local circular coordinate;
2. for each of the four possible held-out events, fit separate affine longitude and latitude trends against relative solar longitude using only the other three events;
3. predict the held-out longitude and latitude;
4. scale the held-out radiant residual by the inherited 2° longitude and 2° latitude scales;
5. do not fit or detrend geocentric speed; use the maximum raw speed difference between the held-out event and the three training events on the inherited 2 km/s scale;
6. combine the two radiant residual components and raw speed component by Euclidean norm;
7. define the quartet diameter as the worst of the four held-out errors;
8. define the episode score as the negative minimum diameter over all retained quartets.

If the three training phases have numerical variance at or below 1e-12 deg², the corresponding radiant slope is exactly zero and the prediction is the training mean. There is no slope cap, regularization, interpolation, alternate phase span, speed trend, candidate family, or held-out selection.

## Exact inherited components

Preserve unchanged:

- the exact PR #69 SonotaCo parser and native-prefix mapping;
- removal of solar longitude 20°–55° inclusive before labels, reservoirs, windows, scores, folds, or endpoints;
- SonotaCo 2025 as the development survey;
- 128-event windows and ±10° activity neighborhoods;
- globally anchored 10° Mondrian bins;
- exact positive, calibration, negative, support, and comparator seeds;
- 128 original-control calibration windows per supported bin;
- 512 candidate and phase-gated-control calibration windows per supported bin, as in PR #118;
- 64 independent test-negative windows per supported bin;
- four positive replicates at k in {4,6,8,12};
- exact original and phase-gated 3D controls;
- split, density, and DBSCAN comparators;
- five complex/parent folds, alpha 0.05 and 0.01, and reporting sectors.

There is one fixed candidate and no full-data or held-out model selection.

## Frozen continuation gates

The exact original and phase-gated controls must reproduce PR #118. The candidate must satisfy all of the following:

- pooled FPR ≤0.060 / 0.020 at alpha 0.05 / 0.01;
- worst 60° reporting-sector FPR at alpha 0.05 ≤0.120;
- weak AUROC ≥0.75, no more than 0.01 below the phase-gated control, and within 0.03 of the strongest fixed comparator;
- at least four fold AUROCs ≥0.70 and none below 0.65;
- k=4 recall ≥0.15 at alpha 0.05;
- k=4 recall at alpha 0.01 at least equals the phase-gated control's frozen 0.066176 value;
- k=6 recall ≥0.30 / 0.15 and k=8 recall ≥0.45 / 0.25 at alpha 0.05 / 0.01;
- k=6 and k=8 recall at either alpha no more than 0.05 below the phase-gated control;
- monotonic recall through k=12 at both alpha levels.

All-four-member selection, held-out residual distributions, phase spans, and phase-gated-only versus candidate-only k=4 detections are diagnostic anatomy, not post-result tuning variables.

Any failed gate kills this exact candidate. No threshold, calibration-size, phase-span, neighbor-pool, slope, score-combination, or candidate-family repair is authorized after seeing the result.

A complete pass authorizes only a separately frozen full SonotaCo-2025 revised-development benchmark. It does not authorize SonotaCo 2024, a catalogue scan, or GhostStream application.

## Blindness

SonotaCo 2024 remains unopened. No GhostStream radiant, speed, orbit, members, score, solar-longitude region, or local information is used.

Frozen candidate source SHA-256: `3c4e019586e300a236d6f181eb82d72a521e1fe0be6b269ebd1faee23b117e5a`.
