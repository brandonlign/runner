# SonotaCo 2025 high-resolution split-conformal multiview fusion

Status: frozen before any high-resolution fused score is computed.

## Why this is a distinct justified test

The exact 128+128 split-conformal fusion in PR #111 had strong discrimination and conservative false positives, but its component tail ranks had minimum resolution 1/129. Many strong injected episodes tied at that floor before the second calibration layer, especially at alpha 0.01. This candidate tests calibration resolution only; it does not alter either physical view, their fusion rule, any threshold, or any scientific gate.

## Single candidate

Preserve unchanged:

1. the original PR #38 phase-weighted four-dimensional clique;
2. the PR #109 three-dimensional radiant-speed clique with the fixed 10° activity-phase span gate;
3. the fused score equal to the negative minimum of the two reference-tail p-values.

Within each 10° Mondrian bin use four disjoint deterministic null streams:

- 128 original-calibration episodes with the exact PR #69 seeds, solely to reproduce the original detector;
- 512 reference episodes to rank the two component scores for fusion;
- 512 separate fusion-calibration episodes to calibrate the fused scalar;
- the unchanged 64 test episodes to measure false positives.

The larger reference and fusion-calibration samples improve empirical tail resolution from 1/129 to 1/513 while retaining conservative rank p-values and independent test negatives. No scale, weight, component threshold, fusion family, or result-dependent choice is permitted.

## Unchanged components and gates

Use the exact PR #69 parser, native labels, quality rules, blind interval, positive windows and seeds, 128-event episodes, globally anchored 10° bins, fixed comparators, complex-held-out folds, alpha levels, and all original scientific gates. The original detector must reproduce its frozen FPR and k=4 recall exactly using its separate 128-null calibration.

The fused candidate must still pass:

- pooled FPR <= 0.060 / 0.020 at alpha 0.05 / 0.01;
- worst 60° sector FPR <= 0.120;
- weak AUROC >= 0.75, within 0.03 of the strongest comparator, and no more than 0.01 below the original;
- at least four folds with AUROC >= 0.70 and none below 0.65;
- recall at alpha 0.05 >= 0.15 / 0.30 / 0.45 for k=4/6/8;
- recall at alpha 0.01 >= 0.05 / 0.15 / 0.25 for k=4/6/8;
- monotonic recall through k=12 at both levels.

Any failed gate kills this exact high-resolution fusion. No further calibration-size increase or fusion repair is authorized from this result.

## Blindness

Every event at solar longitude 20°–55° inclusive is removed before labels, reservoirs, windows, component scores, calibration, folds, or endpoints. SonotaCo 2024 remains unopened. No GhostStream radiant, speed, orbit, membership, score, or local region is used.

A complete pass authorizes only a separately frozen robustness benchmark on already-spent GMN methodology data before any SonotaCo 2024 confirmation.

Frozen candidate source SHA-256: `7ab556184e0965ce066d24a75f2067b9256465d1899c805afa0061f717d34382`.
