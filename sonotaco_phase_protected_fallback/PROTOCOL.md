# SonotaCo phase3-primary narrow-span protected fallback

Status: frozen after the valid PR #132 selector failure and before any protected-fallback score is computed.

## Failure anatomy motivating this distinct candidate

PR #132 showed that phase-span conditioning can rescue sparse k=4 episodes at alpha 0.05: the 2.5° selector reached 22/136 recoveries, above both frozen controls. However, the selector replaced phase3 evidence and then recalibrated the replacement statistic. This destroyed tail power even when no view switch occurred.

The preserved records establish that every k=6 and k=8 episode selected phase3, yet independent final calibration alone removed 8/20 and 11/14 phase3 detections at alpha 0.05/0.01 for k=6 and k=8 respectively. At k=4, the selector gained four narrow-span original-only detections at alpha 0.05 but lost phase3 detections through final calibration. The next justified formulation must therefore retain phase3 as the primary statistic and permit original evidence only as a narrow-span augmentation.

## Single fixed formulation

Use the exact 2.5° threshold selected in all five held-out folds of PR #132. No threshold family or new selection is allowed.

For every episode:

1. compute the exact original and phase3 scores;
2. compute their conservative reference-tail p-values using the exact PR #112 512-reference stream;
3. if the phase3-selected quartet span is greater than 2.5°, use the phase3 reference-tail p-value;
4. if the span is at most 2.5°, use the minimum of the phase3 and original reference-tail p-values;
5. negate that value to form one phase3-primary protected-fallback scalar;
6. calibrate the scalar on the exact separate 512 selector-calibration episodes per bin used in PR #132.

Thus the raw candidate can never weaken phase3 evidence. Original evidence is eligible only in the narrow stratum, and it is active only when stronger than phase3. Independent final calibration preserves false-positive control for the conditional augmentation.

## Exact inherited controls and boundaries

Preserve unchanged:

- the exact PR #69 parser, native labels, quality filters, 128-event windows, ±10° neighborhoods, globally anchored 10° Mondrian bins, positive windows, folds, seeds, alpha levels, fixed comparators, and test negatives;
- removal of solar longitude 20°–55° inclusive before labels, reservoirs, windows, scores, folds, or endpoints;
- the original detector with its exact 128 calibration episodes per bin;
- the exact PR #112 phase3 component and 512 reference episodes per bin;
- the exact separate 512 selector-calibration episodes per bin;
- all original control-reproduction, FPR, AUROC, fold, k=4/k=6/k=8, no-material-drop, and monotonicity gates from PR #132.

No phase threshold, component score, p-value rule, calibration size, seed, fold, endpoint, or gate may be tuned after the result.

## Source-audit decision

The source-only audit must verify exact parent source SHA-256 `1fc071aeb742b70cadbf19be9bac719e79d57ca7a74ab0ce1cb960a827df4f2a`, exact candidate source SHA-256 `3cfd613a0beefaab1bff975dec296d7db8bed3cc9fc2cd9f176a7678d7c86085`, compilation, the fixed 2.5° threshold, phase3-primary minimum rule, exact 128/512/512 streams, unchanged controls and gates, and the absence of SonotaCo 2024 or GhostStream values.

A pass authorizes only one separately frozen SonotaCo 2025 development run. SonotaCo 2024 remains quarantined and must not be requested or opened.
