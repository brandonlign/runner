# SonotaCo 2025 split-conformal multiview quartet fusion

Status: frozen before any fused score is computed.

## Scientific rationale

The original four-dimensional clique and the phase-gated three-dimensional clique recover different physically coherent four-member episodes. The original view favors compact activity timing; the three-dimensional view favors tight radiant-speed geometry across a wider activity interval. Attempts to collapse both hypotheses into one distance improved overall AUROC and stronger-stream recall but continued to lose sparse episodes from one side or the other.

## Single candidate

Preserve both previously frozen views unchanged:

1. the original PR #38 phase-weighted four-dimensional clique;
2. the PR #109 three-dimensional radiant-speed clique with a fixed 10° activity-phase span gate.

Within each 10° Mondrian bin:

- use 128 reference null episodes to compute conservative tail ranks for each view;
- define the fused nonconformity score as the negative of the smaller of the two reference-tail p-values;
- use a separate 128 null episodes to calibrate that fused scalar score;
- evaluate false positives on the unchanged 64 independent test-null episodes.

This is split-conformal multiview calibration. The second calibration layer accounts for selecting the more anomalous of the two views. No component threshold, weighted average, phase scale, union rule, or fusion family is tested.

## Unchanged components

The exact PR #69 parser, native labels, quality rules, blind interval, positive windows and seeds, 128-event episodes, globally anchored 10° bins, fixed comparators, complex-held-out folds, conservative rank p-values, alpha levels, and all scientific gates remain unchanged. The original detector is evaluated against the original 128 calibration seeds and must reproduce its frozen SonotaCo result exactly.

## Continuation gates

The fused candidate must pass every original SonotaCo transfer gate:

- pooled FPR <= 0.060 / 0.020 at alpha 0.05 / 0.01;
- worst 60° sector FPR <= 0.120;
- weak AUROC >= 0.75, within 0.03 of the strongest comparator, and no more than 0.01 below the original score;
- at least four folds with AUROC >= 0.70 and none below 0.65;
- recall at alpha 0.05 >= 0.15 / 0.30 / 0.45 for k=4/6/8;
- recall at alpha 0.01 >= 0.05 / 0.15 / 0.25 for k=4/6/8;
- monotonic recall through k=12 at both alpha levels.

Any failed gate kills this exact fusion. No result-dependent repair or alternative combination is authorized.

## Blindness

Every event at solar longitude 20°–55° inclusive is removed before labels, reservoirs, windows, component scores, calibration, folds, or endpoints. SonotaCo 2024 remains unopened. No GhostStream radiant, speed, orbit, membership, score, or local region is used.

A complete pass authorizes only a separately frozen robustness benchmark on already-spent GMN methodology data before any SonotaCo 2024 confirmation.

Frozen candidate source SHA-256: `8b54532198de52cd42729551ba4f2ee7af986486577492dd048002203d319750`.
