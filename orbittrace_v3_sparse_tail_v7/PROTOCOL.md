# OrbitTrace v3-primary sparse-tail augmentation — v7

## Preservation

The primary evidence source is the frozen OrbitTrace v3 multi-anchor wavelet-energy score. The complementary sparse evidence source is the frozen fixed4 score. Neither component is altered.

All prior OrbitTrace methods/results remain preserved: v1-v6, Brown-family wavelet, the earlier Brown-primary sparse-tail experiment, the promoted Brown+fixed4 dual channel, Sugar, HDBSCAN, catalogue work, and blind-recovery records.

## Why this successor is justified

Across unchanged SonotaCo 2025 and 2023, v3 is the first OrbitTrace-owned continuous ranking to exceed the Brown-family wavelet AUROC in both years. Pure re-pooling of the same anchor coefficients cannot recover fixed4's full four-member advantage: the complete preregistered v6 family already fails that gate on 2025.

The missing information therefore comes from fixed4 rather than another transformation of Brown coefficients.

A sparse-tail architecture was independently developed earlier for Brown+fixed4 and selected the exact margin `0.25` from a preregistered grid before v3 existed (PR #188). v7 inherits that already frozen margin rather than selecting any new value from v3 results.

## Frozen v7 statistic

For each Mondrian bin, use paired calibration-negative scores from:

- `orbittrace_multi_anchor_wavelet_energy_v3`;
- `orbittrace_fixed4`.

Convert each component score to an empirical upper-tail p-value. Then compute

`T = max(-log(p_v3), -log(p_fixed4) - 0.25)`.

For every calibration episode, compute leave-one-out component p-values and its paired null `T`. The final target p-value is the empirical upper-tail p-value of the target `T` against those paired null `T` values.

Thus dependence, the max operation, and the inherited sparse-tail margin are all included in the final empirical calibration.

Continuous ranking for the method is `T`; reporting detection is final calibrated `p_v7 <= 0.05`.

There is:

- no margin grid;
- no learned weight;
- no year-specific parameter;
- no target-specific condition;
- no threshold selection after results.

The exact margin is **0.25**, inherited from the earlier independently frozen sparse-tail development and not selected using v3.

## Development panel

SonotaCo 2025 and SonotaCo 2023 are the exposed v7 development panel. The exact same v7 implementation must independently satisfy all gates in both years.

No OrbitTrace target coordinate, member identity, activity interval, blind-recovery result, or target-specific exception may enter v7.

## Frozen gates — each year independently

In both 2025 and 2023:

- v7 weak-stream AUROC strictly exceeds Brown-family wavelet;
- v7 alpha=.05 k=4 recall is at least fixed4 alpha=.05 recall;
- v7 k=6/8/12 recall is no more than 0.03 below Brown-family wavelet at each k;
- pooled v7 alpha=.05 FPR <= 0.055;
- worst reporting-sector v7 alpha=.05 FPR <= 0.08;
- every upstream parser/source/comparator-reproduction gate passes;
- frozen v3 AUROC is reproduced.

v7 passes development only if every gate passes in both years.

## Prospective boundary

If v7 passes, the exact source and hashes are frozen before any prospective scientific scoring. SonotaCo **2016** remains the preregistered preferred prospective year. Before scientific access, 2016 must pass a separate transport/schema/eligibility audit and a source-only prospective-runner audit. No 2016 result may alter the margin, score, calibration, alpha, component definitions, or gates.
