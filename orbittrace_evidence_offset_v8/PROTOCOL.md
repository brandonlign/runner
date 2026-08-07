# OrbitTrace calibrated evidence-offset family — v8 development

## Preservation

The component methods are frozen:

- primary: `orbittrace_multi_anchor_wavelet_energy_v3`;
- sparse: `orbittrace_fixed4`.

v8 does not alter either component, the Brown-family geometry, episode construction, Mondrian calibration universe, or any predecessor result. v1–v7 remain preserved.

## Motivation

v7 with inherited offset `+0.25` passed every 2023 gate and every 2025 gate except fixed4-level k=4 recall by exactly one positive episode, while achieving strong AUROC and low FPR. The exposed 2025+2023 panel is therefore used for one explicit final development sweep over the relative log-evidence offset between the same two frozen channels.

No result from this sweep is prospective evidence. A winner must be frozen before SonotaCo 2016 scientific access.

## Frozen candidate family

For each target episode in a Mondrian bin, convert the frozen v3 and fixed4 scores to empirical upper-tail p-values `p_v3` and `p_fixed4` against that bin's calibration negatives.

For offset `m`, define:

`T_m = max(-log(p_v3), -log(p_fixed4) - m)`.

The preregistered offsets are exactly:

- `m = -0.75`;
- `m = -0.50`;
- `m = -0.25`;
- `m = 0.00`;
- `m = +0.25` (the frozen v7 reference);
- `m = +0.50`.

Negative `m` gives the known sparse specialist fixed4 more log-evidence priority; positive `m` requires fixed4 to exceed the v3 evidence by a larger margin.

Each candidate is independently calibrated against paired leave-one-out null `T_m` values from the same calibration episodes. The final reporting p-value is therefore empirical and includes channel dependence and the max operation.

There is no continuous margin search, no interpolation, no fitted weight, no year-specific parameter, and no target-specific rule.

## Development panel

Both SonotaCo 2025 and SonotaCo 2023 are fully exposed development corpora. Every candidate is scored unchanged on both.

No OrbitTrace target coordinate, member identity, target activity interval, blind-recovery output, or target-specific exception may enter v8.

## Feasibility gates — each year independently

A candidate is feasible only if **all** of these pass in both 2025 and 2023:

- weak-stream AUROC strictly exceeds Brown-family wavelet;
- alpha=.05 k=4 recall is at least fixed4 alpha=.05 recall;
- alpha=.05 k=6/8/12 recall is no more than 0.03 below Brown-family wavelet at each k;
- pooled alpha=.05 FPR <= 0.055;
- worst reporting-sector alpha=.05 FPR <= 0.08;
- frozen v3 AUROC is reproduced;
- every upstream source/parser/comparator integrity gate passes.

## Frozen selector

If no candidate is feasible in both years, v8 fails and SonotaCo 2016 remains unopened.

If one or more candidates are feasible, select deterministically by:

1. largest minimum annual AUROC margin over Brown;
2. largest mean annual AUROC margin over Brown;
3. largest minimum annual k=4 recall margin over fixed4;
4. largest minimum annual recall margin across k=4/6/8/12 relative to its gate;
5. smallest absolute offset `|m|`;
6. fixed offset order `-0.75, -0.50, -0.25, 0.00, +0.25, +0.50`.

The complete six-candidate, two-year table is preserved regardless of outcome.

## Prospective boundary

If v8 passes, the exact selected offset, source hashes, component definitions, empirical calibration, reporting alpha=.05, and gates are frozen before any 2016 scientific scoring.

SonotaCo **2016** remains the preregistered preferred prospective year. The next stage must first be a transport/schema/eligibility audit that computes no detector score, AUROC, recall, or FPR, followed by a source-only prospective-runner audit. Only then may one one-shot 2016 scientific run occur. No 2016 result may alter v8.
