# SonotaCo 2025 phase-span selector valid rerun

Status: frozen before any selector score is computed.

## Authorization

PR #125 completed but is scientifically invalid because its phase3 reference calibration stream used the wrong seed prefix. PR #129 proved that the repaired candidate differs from the exact PR #124 source by one literal substitution only:

- invalid: `mondrian-span-selector-reference`
- repaired: `mondrian-multiview-hires-reference`

The repaired source SHA-256 is `1fc071aeb742b70cadbf19be9bac719e79d57ca7a74ab0ce1cb960a827df4f2a`.

This run changes nothing else from the frozen PR #125 protocol.

## Exact inherited formulation

Preserve the exact PR #69 parser, mapping, labels, quality filters, removal of solar longitude 20°–55° inclusive before all labels, reservoirs, windows, scores, folds, and endpoints, 128-event episodes, ±10° neighborhoods, globally anchored 10° Mondrian bins, positive windows, seeds, folds, alpha levels, fixed comparators, and test negatives.

The original detector keeps its exact 128 calibration episodes per bin. The phase3 component uses 512 independent reference episodes per bin with the exact PR #112 reference stream. The final selector uses 512 separate selector-calibration episodes per bin.

Exactly three thresholds remain allowed: 2.5°, 5.0°, and 7.5°.

For each episode:

1. compute the exact original score and exact phase3 score;
2. record the phase span of the phase3-selected quartet;
3. if that span is at or below the threshold, choose the original component reference-tail p-value;
4. otherwise choose the phase3 component reference-tail p-value;
5. negate that chosen component p-value to form one scalar selector score;
6. calibrate that scalar on the independent selector-calibration stream.

For each held-out complex fold, choose the threshold using only positive windows from the other four folds under the frozen lexicographic order: k=4 recall at alpha 0.05, k=4 recall at alpha 0.01, k=6 recall at alpha 0.05, k=8 recall at alpha 0.05, mean k=4 negative log10 p-value, then the smaller threshold. Test negatives receive deterministic pseudo-fold assignments.

## Frozen pass gates

All parser, support, calibration, exact original-control reproduction, exact phase3-control reproduction, and selection-integrity gates must pass, plus:

- pooled FPR <= 0.060 / 0.020 at alpha 0.05 / 0.01;
- worst 60° sector FPR <= 0.120 at alpha 0.05;
- weak AUROC >= 0.75, within 0.03 of the strongest comparator, and no more than 0.01 below phase3;
- at least four folds with AUROC >= 0.70 and none below 0.65;
- recall at alpha 0.05 >= 0.15 / 0.30 / 0.45 for k=4/6/8;
- recall at alpha 0.01 >= 0.05 / 0.15 / 0.25 for k=4/6/8;
- k=6 and k=8 recall no more than 0.05 below phase3 at either alpha;
- monotonic recall through k=12 at both alpha levels.

Any failed gate kills this exact selector. No threshold, seed, calibration size, component score, selection rule, or gate may be repaired after the result.

A complete pass authorizes only a separately frozen full SonotaCo 2025 revised-development benchmark. It does not authorize SonotaCo 2024, a catalogue scan, or GhostStream application.

SonotaCo 2024 and GhostStream remain untouched.
