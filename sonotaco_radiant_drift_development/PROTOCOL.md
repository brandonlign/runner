# SonotaCo 2025 phase-ordered radiant-drift quartet development

Status: frozen before any radiant-drift score is computed.

## Motivation

PR #108 showed that nearest-neighbor search was not the k=4 bottleneck and that solar-longitude separation dominated the true-quartet diameter in 105/136 windows. PRs #109-#112 then separated phase from radiant-speed coherence and produced strong, calibrated gains, but the best result remained one k=4 alpha-0.05 recovery short of the frozen gate.

The preserved PR #112 anatomy shows that the remaining misses often have broad phase spans and elevated raw radiant-speed diameter. A physically coherent meteor shower need not occupy a phase-independent ball: its radiant can drift approximately linearly during the activity interval. This experiment therefore tests a phase-ordered local manifold, not another phase threshold, calibration-size change, or fusion repair.

## Exact inherited data and controls

Preserve the exact PR #69 SonotaCo 2025 parser, GMN-MDC mapping, native labels, quality filters, 20°-55° inclusive blind removal before all labels and endpoints, 128-event episodes, ±10° neighborhoods, globally anchored 10° Mondrian bins, positive windows, seeds, complex-held-out folds, alpha levels, fixed comparators, and test negatives.

The exact original four-dimensional clique remains a control with its original 128 calibration episodes per supported bin. The exact PR #109 phase-gated 3D score remains a control and is calibrated on the exact 512 PR #112 reference episodes per supported bin. Both controls must reproduce their frozen metrics exactly.

## Preregistered candidate family

Use the exact PR #109 10° activity-span gate, six-neighbor pool, and enumeration of every anchor plus three neighbors. For each valid quartet, form all six pair differences in the inherited standardized geometry:

- wrapped ecliptic radiant longitude multiplied by cosine mean latitude and divided by 2;
- ecliptic radiant latitude divided by 2;
- geocentric speed divided by 2.

Fit one common linear phase slope by least squares across all six pair differences, then score the quartet by the maximum residual pair distance. The episode score is the negative minimum residual diameter.

Exactly two candidates are allowed:

1. `radiant_drift`: detrend longitude and latitude; leave speed unchanged.
2. `radiant_speed_drift`: detrend longitude, latitude, and speed.

No slope bound, phase-span sweep, neighbor-pool change, nonlinear trajectory, robust-regression variant, fusion rule, or post-result repair is allowed.

## Calibration and complex-held-out selection

Calibrate both candidates independently with conservative rank p-values using the exact 512 PR #112 reference episodes per supported bin. Keep the unchanged 64 exact test negatives per bin for final false-positive measurement.

For each held-out complex fold, select between the two candidates using only positive windows from the other four folds. Use this frozen lexicographic order:

1. k=4 recall at alpha 0.05;
2. k=4 recall at alpha 0.01;
3. k=6 recall at alpha 0.05;
4. k=8 recall at alpha 0.05;
5. mean k=4 negative log10 p-value;
6. prefer the simpler radiant-only candidate.

Apply each fold's selected candidate to its held-out positives. Assign each final test negative to one deterministic pseudo-fold using a stable hash of its bin and index, then apply that fold's selected candidate. Use negative calibrated p-value as the common cross-fitted AUROC score.

## Frozen pass gates

All parser, mapping, support, calibration, control-reproduction, and selection-integrity gates must pass. The cross-fitted candidate must satisfy:

- pooled FPR <= 0.060 / 0.020 at alpha 0.05 / 0.01;
- worst 60° reporting-sector FPR <= 0.120 at alpha 0.05;
- weak AUROC >= 0.75, within 0.03 of the strongest fixed comparator, and no more than 0.01 below the phase-gated 3D control;
- at least four folds with AUROC >= 0.70 and none below 0.65;
- recall at alpha 0.05 >= 0.15 / 0.30 / 0.45 for k=4/6/8;
- recall at alpha 0.01 >= 0.05 / 0.15 / 0.25 for k=4/6/8;
- k=6 and k=8 recall no more than 0.05 below the phase-gated 3D control at either alpha;
- monotonic recall through k=12 at both alpha levels.

Any failed gate kills this exact family and selection rule. Negative results must be preserved. No threshold, slope model, candidate family, selection order, seed, calibration size, or gate may be changed after observing the result.

## Diagnostics and blindness

Preserve selected-quartet membership, phase span, raw 3D diameter, residual diameter, fitted standardized slopes, and corresponding true-quartet anatomy for k=4 positives.

SonotaCo 2024 must not be requested or opened. No GhostStream radiant, orbit, member, score, solar-longitude region, or local neighborhood is used.

A complete pass freezes one final development formulation and authorizes only a separately preregistered robustness benchmark on already-spent methodology data before any one-shot SonotaCo 2024 confirmation protocol.

Frozen candidate source SHA-256: `f72f7bd9478414c32edffc68209e8e8dd4de8b36bfef884be17c93cbe5b3b0af`.
