# OrbitTrace jointly calibrated Tippett reporting layer — v5

## Preservation

The continuous primary ranking remains the frozen `orbittrace_multi_anchor_wavelet_energy_v3`. v5 does not change its geometry, coefficients, top-four L2 aggregation, or any v3 result.

The sparse component remains the frozen `orbittrace_fixed4` score. v5 changes neither component score.

v1–v4, Brown-family wavelet, prior dual-channel, Sugar, HDBSCAN, catalogue, and blind-recovery records remain untouched.

## Motivation fixed after v4 transfer

The v3 ranking exceeded Brown-family wavelet AUROC without retuning on both SonotaCo 2025 and 2023. The v4 manually allocated component thresholds did not fully transfer, indicating that a fixed split of the false-positive budget between correlated channels is brittle.

v5 therefore uses one standard, symmetric joint statistic and empirically calibrates its dependence within every Mondrian bin.

## Frozen v5 reporting statistic

Components:

- `orbittrace_multi_anchor_wavelet_energy_v3`;
- `orbittrace_fixed4`.

For each component and each Mondrian bin:

1. convert a target component score to the existing conservative empirical survival p-value;
2. for every calibration-negative episode, compute the corresponding leave-one-out component survival p-value;
3. combine the two component p-values with the Tippett statistic
   `T = -log(min(p_v3, p_fixed4))`;
4. compute the calibration-null Tippett statistic for every calibration episode using its paired leave-one-out component p-values;
5. convert the target Tippett statistic to a second empirical survival p-value against those paired calibration-null Tippett statistics.

Reporting detection is `p_joint <= 0.05`.

No component weight, threshold grid, alternative combiner, or post-result parameter exists in v5.

The continuous ranking used for AUROC remains v3 alone. The joint p-value is a reporting/significance layer, not a replacement ranking.

## Development panel

Both SonotaCo 2025 and SonotaCo 2023 are now fully exposed development/transfer corpora. v5 is required to pass unchanged on both. Neither year is prospective evidence for v5.

No OrbitTrace target coordinate, member identity, activity interval, blind-recovery output, or target-specific exception may enter v5.

## Frozen development gates — each year independently

For both 2025 and 2023:

- v3 weak-stream AUROC strictly exceeds Brown-family wavelet;
- joint-p alpha=.05 k=4 recall is at least fixed4 alpha=.05 recall;
- joint-p k=6/8/12 recall is no more than 0.03 below Brown-family wavelet alpha=.05 recall;
- pooled joint-p alpha=.05 FPR <= 0.055;
- worst reporting-sector joint-p alpha=.05 FPR <= 0.08;
- every upstream source/parser/comparator reproduction gate passes.

v5 development passes only if every gate passes in both years. A failure is frozen and cannot be retuned on either year.

## Next-stage boundary

A two-year development pass authorizes only a source-frozen prospective test on a predesignated year/corpus not used to select v5. No prospective result may change the combiner, the component methods, or the alpha=.05 reporting threshold.
