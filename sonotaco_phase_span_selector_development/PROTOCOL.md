# SonotaCo 2025 phase-span-conditioned quartet selector

Status: frozen before any selector score is computed.

## Motivation

The original phase-weighted clique and the phase-gated 3D clique recover complementary k=4 episodes. In the preserved SonotaCo 2025 anatomy, original-only detections have much narrower selected phase spans than phase3-only detections, while unconstrained radiant drift overfits accidental background quartets and is killed.

The remaining justified test is therefore a conditional selector, not another score geometry or multiple-testing fusion: trust the original view only when the phase3-selected quartet is phase-narrow, and otherwise use the phase-separated view.

## Exact inherited data and controls

Preserve the exact PR #69 parser, mapping, labels, quality filters, 20°–55° inclusive blind removal before all labels and endpoints, 128-event episodes, ±10° neighborhoods, globally anchored 10° Mondrian bins, positive windows, seeds, folds, alpha levels, fixed comparators, and test negatives.

The original detector keeps its exact 128 calibration episodes per bin. The phase3 component uses 512 independent reference episodes per bin and must reproduce the frozen PR #112 component metrics.

## Preregistered selector family

Exactly three thresholds are allowed: 2.5°, 5.0°, and 7.5°, the equally spaced interior quarters of the existing 10° phase gate.

For each episode:

1. compute the exact original score and exact phase3 score;
2. record the phase span of the phase3-selected quartet;
3. if that span is at or below the threshold, choose the original component reference-tail p-value;
4. otherwise choose the phase3 component reference-tail p-value;
5. negate that chosen component p-value to form one scalar selector score;
6. calibrate that scalar on 512 separate selector-calibration episodes per bin.

This independent final calibration controls the data-dependent view choice. No minimum-p fusion, phase weight, soft blend, threshold outside the frozen family, or post-result repair is allowed.

## Complex-held-out selection

For each held-out complex fold, choose among the three thresholds using only positive windows from the other four folds. Use the frozen lexicographic order:

1. k=4 recall at alpha 0.05;
2. k=4 recall at alpha 0.01;
3. k=6 recall at alpha 0.05;
4. k=8 recall at alpha 0.05;
5. mean k=4 negative log10 p-value;
6. prefer the smaller threshold.

Apply the selected threshold to held-out positives. Assign test negatives to deterministic pseudo-folds and apply that fold’s threshold.

## Frozen pass gates

The cross-fitted candidate must satisfy all parser, support, calibration, control-reproduction, and selection-integrity gates plus:

- pooled FPR <= 0.060 / 0.020 at alpha 0.05 / 0.01;
- worst 60° sector FPR <= 0.120 at alpha 0.05;
- weak AUROC >= 0.75, within 0.03 of the strongest comparator, and no more than 0.01 below phase3;
- at least four folds with AUROC >= 0.70 and none below 0.65;
- recall at alpha 0.05 >= 0.15 / 0.30 / 0.45 for k=4/6/8;
- recall at alpha 0.01 >= 0.05 / 0.15 / 0.25 for k=4/6/8;
- k=6 and k=8 recall no more than 0.05 below phase3 at either alpha;
- monotonic recall through k=12 at both alpha levels.

Any failed gate kills this exact selector. SonotaCo 2024 and GhostStream remain untouched.

Frozen candidate source SHA-256: `aab855db949bd520aa142a51a140c6e181918be0428bdee082b427fd1240a569`.
