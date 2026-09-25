# OrbitTrace multiscale consensus contrast — v2 development

## Status and ancestry

This is a separately named successor to the failed adaptive local-likelihood v1. The v1 result remains frozen in `orbittrace_adaptive_likelihood_v1/FROZEN_RESULT.*` and is not edited or reinterpreted.

Existing OrbitTrace fixed4, Brown-family wavelet, dual-channel, Sugar, HDBSCAN, catalogue, and blind-recovery results remain untouched.

## Motivation fixed after v1

v1 was calibrated but almost non-responsive to injected stream membership. Its local shell frequently contained too little background support, so maximization over anchors and scales rewarded accidental compact groups.

v2 removes local Poisson background estimation entirely. It tests a different hypothesis: a real stream should produce matched-filter evidence that is simultaneously:

1. persistent across adjacent physical scales; and
2. repeated around multiple observed members.

## Frozen v2 statistic

For each 128-event episode:

1. Evaluate four fixed radiant/speed scale pairs: `2°/5%`, `3°/7.5%`, `4°/10%`, `6°/15%`.
2. At each scale compute the leave-one-out dimension-3 Mexican-hat coefficient at every observed-event location with radius-4 truncation.
3. Robustly normalize the 128 coefficients within that scale using median and `1.4826 * MAD`; fall back to ordinary standard deviation only if MAD is numerically degenerate.
4. For every anchor, form adjacent-scale persistence contrasts `(z_s + z_{s+1}) / sqrt(2)` for `(2,3)`, `(3,4)`, and `(4,6)` scale pairs.
5. The anchor evidence is the maximum adjacent-scale contrast.
6. The episode score is the arithmetic mean of the four largest anchor-evidence values.

The top-four aggregation is fixed because the target scientific regime begins at four-member streams. It is not selected from v2 results.

The existing frozen Mondrian benchmark supplies bin-wise empirical p-value calibration, so maximization over adjacent scale pairs and the top-four order statistic are included inside the calibrated statistic.

## Development corpus and blindness

The first v2 execution uses only the already exposed SonotaCo 2025 episode-development corpus. No OrbitTrace coordinate, member identity, activity interval, blind-recovery result, or target exception may enter source or scoring.

If v2 survives development, its exact source must be frozen before any reserved prospective corpus is opened.

## Development gates

A v2 primary-ranking pass requires:

- weak-stream AUROC strictly above the Brown-family wavelet;
- alpha=.05 k=4 recall at least fixed4;
- alpha=.05 k=6/8/12 recall no more than 0.03 below wavelet at each k;
- pooled alpha=.05 FPR <= 0.055;
- worst reporting-sector alpha=.05 FPR <= 0.08;
- exact upstream comparator reproduction and source-integrity gates.

If AUROC beats wavelet but the k=4 gate alone fails, v2 may be retained only as a candidate primary ranking for a separately evaluated fixed4 minimum-p rescue architecture; it is not itself a full pass.

A failure is frozen and cannot be silently overwritten. Material changes require a separately named v3.
