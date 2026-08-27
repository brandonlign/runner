# OrbitTrace multi-anchor wavelet energy — v3 development

## Status and preservation

v1 and v2 remain frozen failures. No fixed4, Brown-family wavelet, dual-channel, Sugar, HDBSCAN, catalogue, blind-recovery, or prior negative-result source is modified.

## Motivation fixed after v2

v2 showed that repeated support around multiple anchors contains useful sparse-stream information: its k=4 recall exceeded the Brown-family wavelet. But v2 replaced raw matched-filter amplitude with robust within-episode normalization and consequently lost most moderate/strong-stream sensitivity.

v3 therefore preserves the exact successful Brown-family 4° / 10%-speed matched-filter geometry and raw coefficient scale. It changes only the episode aggregation.

## Frozen v3 statistic

1. Compute the exact leave-one-out Brown-family dimension-3 Mexican-hat coefficient at every observed-event location using:
   - angular probe `4°`;
   - fractional speed probe `10%` of the test-event speed;
   - radius-4 truncation;
   - no self contribution.
2. Retain the four largest positive coefficients. If fewer than four coefficients are positive, zero-pad to four.
3. Define the episode score as their Euclidean energy:

   `E4 = sqrt(c1^2 + c2^2 + c3^2 + c4^2)`.

This contains the Brown maximum continuously: if only one anchor carries positive evidence, `E4` reduces to that positive peak. Multiple coherent anchors increase the score without a fitted blending weight or within-episode rescaling.

`TOP_ANCHORS=4` is fixed from the scientific minimum sparse-stream regime and is not selected from v3 results.

The external frozen Mondrian benchmark calibrates the complete statistic bin-wise, including the order-statistic aggregation.

## Development corpus and blindness

The first v3 execution uses only the already exposed SonotaCo 2025 episode-development corpus. No OrbitTrace coordinate, member identity, activity interval, blind-recovery output, or target-specific exception enters the method.

## Development gates

Primary pass requires:

- weak-stream AUROC strictly above the Brown-family wavelet;
- alpha=.05 k=4 recall at least fixed4;
- alpha=.05 k=6/8/12 recall no more than 0.03 below wavelet;
- pooled alpha=.05 FPR <= 0.055;
- worst reporting-sector alpha=.05 FPR <= 0.08;
- exact upstream comparator reproduction and source-integrity gates.

If the primary ranking passes except only the k=4 fixed4 gate, it may proceed to a separately frozen inherited fixed4 minimum-p rescue evaluation. Otherwise a failed v3 is frozen and material changes require v4.
