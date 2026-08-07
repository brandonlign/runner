# OrbitTrace high-resolution calibrated dual channel — v5 development protocol

## Preservation

v5 preserves every predecessor score and result. In particular:

- the continuous primary score is the frozen `orbittrace_multi_anchor_wavelet_energy_v3` ranking;
- the sparse channel is the frozen `orbittrace_fixed4` score;
- the Brown-family comparator and all literature comparators are unchanged;
- v1, v2, v3, v4, Sugar, HDBSCAN, catalogue, and blind-recovery records remain immutable.

v5 changes **calibration resolution and decision development only**. It does not change v3 geometry, top-anchor aggregation, fixed4 geometry, episode construction, positive injections, held-out negatives, or source-preserving null generation.

## Motivation fixed before execution

v3 transferred above the Brown-family wavelet on both exposed development years:

- SonotaCo 2025: `0.836860 > 0.828506`;
- SonotaCo 2023: `0.836263 > 0.831972`.

The v4 OR decision used 128 calibration null episodes per Mondrian bin, so each empirical p-value moved only in increments of `1/129 = 0.0077519...`. Its 2023 transfer missed the pooled-FPR cap by `0.000871` and the k=8 tolerance gate by `0.006585`, both smaller than one calibration step. The next experiment therefore tests whether finer empirical calibration can preserve the successful ranking while allocating the detection budget robustly.

## High-resolution calibration

For development only, the exact existing benchmark generators are rerun with:

- `CALIBRATION_NEGATIVES_PER_BIN = 512` instead of 128;
- all calibration seeds retain the same frozen seed namespace and simply extend the calibration index from `0..127` to `0..511`;
- held-out negative episodes remain unchanged;
- positive episodes remain unchanged;
- all method scores remain unchanged functions of an episode.

Empirical p-values therefore use the exact conservative rank rule with denominator **513**.

No 2024 data may be opened during this stage.

## Development corpora

The threshold architecture is developed jointly on the already exposed:

- SonotaCo 2025 benchmark; and
- SonotaCo 2023 benchmark.

Because the v4 2023 result has already been opened, SonotaCo 2023 is development evidence for v5 and cannot later be described as v5 validation.

## Candidate decision grid

The reporting rule remains an interpretable two-channel OR:

`(p_v3 <= r_v3/513) OR (p_fixed4 <= r_f4/513)`.

The finite preregistered grid is:

- `r_v3 in {1, ..., 26}`;
- `r_f4 in {1, ..., 26}`.

Thus neither individual channel is allowed a threshold above approximately nominal 0.05 (`26/513 = 0.050682...`). All 676 pairs must be preserved in the development artifact.

## Per-year feasibility gates

A pair is feasible only if **every** gate below passes separately on both 2025 and 2023:

- upstream benchmark integrity gates all pass;
- calibration count is exactly 512 per supported Mondrian bin;
- all v3 and fixed4 p-values lie on the exact denominator-513 grid;
- v3 weak-stream AUROC is at least Brown-family wavelet AUROC;
- combined pooled held-out-negative FPR <= 0.055;
- combined worst reporting-sector FPR <= 0.08;
- combined k=4 recall >= frozen fixed4 nominal-alpha=.05 k=4 recall from that same year;
- combined k=6 recall >= Brown nominal-alpha=.05 k=6 recall minus 0.03;
- combined k=8 recall >= Brown nominal-alpha=.05 k=8 recall minus 0.03;
- combined k=12 recall >= Brown nominal-alpha=.05 k=12 recall minus 0.03.

## Deterministic robust selector

If no pair is feasible, v5 fails and no threshold is promoted.

If one or more pairs are feasible, select deterministically by:

1. **largest minimum recall margin** across all eight year-specific recall constraints (k=4/6/8/12 for 2025 and 2023);
2. then **lowest maximum pooled FPR** across the two years;
3. then **largest v3 rank budget** `r_v3`, preserving the primary continuous channel when still tied;
4. then **smallest fixed4 rank budget** `r_f4`;
5. then lexicographic `(r_v3, r_f4)` as a final deterministic tie-break.

No selector rule may be changed after the 512-null results are opened.

## Promotion boundary

A passing v5 development result freezes:

- the 512-null calibration size;
- denominator 513;
- the selected integer threshold pair;
- the unchanged v3 and fixed4 scoring functions;
- the exact decision rule.

Only then may the architecture be run once on **SonotaCo 2024**, which remains the prospective corpus for this successor. No 2024 score, threshold, label performance, or method comparison may be inspected before the v5 development freeze is committed.

A 2024 failure must be preserved and may not trigger same-corpus retuning.