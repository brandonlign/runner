# Consensus-lowpass recurrence: frozen reduced kill screen

Status: frozen before any candidate score, null threshold, FWER, recovery value, or continuation decision is computed.

## Exact candidate

This screen executes exact source SHA-256 `9f630c8eca2ffb1a5bdbc0598b744dffccb6026d2476467b99c6caa3d410a9fa`, audited without scoring in PR #102 and pinned at commit `e6fa3cbcf3dacc3287592874e12fda21f3a8d245`.

The candidate subtracts only the fixed low-pass projection of the pointwise annual-median evidence map, then takes the unchanged third-strongest adjusted annual evidence and maximizes over the unchanged four template widths.

Fixed additions relative to the passed majority-conditioned source:

- persistent activity: exactly 12 of 15 years;
- persistent injections use the unchanged shared-structure null background;
- fixed smoothing sigma `(1.6, 1.6, 1.0, 0.9)`, inherited from the original annual null fit.

No smoothing width, quantile, active-year count, coefficient, recurrence order, template, grid, null family, injection rule, comparator, or threshold is selected in this screen.

## Frozen reduced design

- independent seed: `20260807`;
- 30 calibration catalogs per null family;
- 30 fresh ideal-null catalogs;
- 30 fresh shared-structure-null catalogs;
- 30 injection trials per strength for each condition;
- original minority recurrence: 5 active years;
- persistent shared-background recurrence: 12 active years;
- one-year artifact: 1 active year;
- strengths: unchanged 4, 6, 8, and 12 meteors per active year;
- recurrence requirement: unchanged third-strongest year;
- catalog alpha: `0.10`;
- threshold construction: unchanged worst-family maximum of separately calibrated ideal-null and shared-structure complete-search thresholds.

This is a reduced kill screen. It cannot validate the method.

## Fixed comparators

- pooled virtual year;
- pooled plus annual confirmation;
- original hard third-year recurrence;
- worst-family soft recurrence;
- complete-median majority conditioning.

## Frozen continuation gates

Every gate encoded in the exact candidate source must pass:

1. ideal-null FWER at most `0.20`;
2. shared-structure-null FWER at most `0.20`;
3. original five-year weak recovery no more than `0.05` below the strongest comparator;
4. weak one-year-artifact detection at most `0.20`;
5. weak persistent shared-background recovery at least `0.05` above the strongest comparator;
6. weak persistent recurrence-margin gain at least `0.05` above the strongest comparator;
7. strong persistent shared-background recovery no more than `0.05` below the strongest comparator.

Any failed gate kills this exact formulation. Do not change the low-pass scale, annual consensus, active-year counts, null model, distortion, grid, template widths, seed, trial counts, alpha, threshold construction, comparator, or gate after the result.

A complete pass authorizes only one separately frozen, independently seeded full Stage-0 with stricter FWER gates. It does not authorize real-shower testing, confirmation, catalogue scanning, or GhostStream application.