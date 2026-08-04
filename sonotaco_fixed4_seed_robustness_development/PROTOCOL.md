# SonotaCo 2025 fixed-4° calibration-seed robustness benchmark

Status: frozen after the source-only pass in PR #138 and before any robustness score is computed.

## Fixed model

Use only the exact fixed 4° activity-phase scale from PR #113. No scale selection, scan, fusion, selector, geometry revision, or threshold change is permitted.

Preserve the exact PR #69 / PR #113 SonotaCo 2025 parser, GMN-MDC mapping, native labels, quality filters, removal of solar longitude 20°–55° inclusive before labels or endpoints, 128-event windows, ±10° neighborhoods, globally anchored 10° calibration bins, positive episode seeds, complex folds, comparators, alpha levels, and scientific gates.

## Null panels

Evaluate four fully specified panels:

1. `original`: the exact PR #113 calibration and test streams, solely to reproduce the frozen fixed-4° result.
2. `robust_a`: a new deterministic 128-calibration / 64-test stream per supported bin.
3. `robust_b`: a second independent deterministic 128-calibration / 64-test stream per supported bin.
4. `robust_c`: a third independent deterministic 128-calibration / 64-test stream per supported bin.

All four panels score the identical positive episodes. No panel may be selected, dropped, reseeded, or rerun after inspection.

## Pass rule

The original fixed-4° result must reproduce exactly. Each fresh panel must satisfy the inherited FPR and AUROC constraints. At least two of three fresh panels must pass the complete original recall standard. The median across the three fresh panels must satisfy:

- k=4 recall >= 0.15 / 0.05 at alpha 0.05 / 0.01;
- k=6 recall >= 0.30 / 0.15;
- k=8 recall >= 0.45 / 0.25;
- k=6 and k=8 recall no more than 0.05 below the original panel at either alpha;
- monotonic recall through k=12.

Any failed gate kills calibration-seed robustness of the fixed 4° formulation. No seed, sample count, scale, threshold, endpoint, or gate may be changed from the result.

SonotaCo 2024 and GhostStream remain untouched. A complete pass establishes a robust SonotaCo 2025 fixed-model development conclusion but does not itself authorize opening SonotaCo 2024.

Frozen source SHA-256: `8424f5c1d0a88fc6e2c275437e5d9587eaa1ba71143ab4b4cc87205dcf9b20f0`.
