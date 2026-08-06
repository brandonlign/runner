# OrbitTrace sparse-tail augmentation development

## Scientific motivation

Across the frozen SonotaCo episode benchmarks, the Brown-family wavelet score has the stronger overall AUROC and stronger k>=6 recovery, while fixed4 remains consistently stronger for the sparsest k=4 episodes and generally has lower false-positive rates. The symmetric Tippett union improved balanced recall but did not prospectively exceed wavelet AUROC on SonotaCo 2022.

This stage develops a narrower revision: wavelet remains the primary evidence channel, and fixed4 may replace it only when fixed4 evidence is sufficiently stronger.

## Frozen score family

For marginal empirical survival p-values `p_w` and `p_f`, define

`T_m = max(-log(p_w), -log(p_f) - m)`.

The nonnegative margin `m` penalizes the fixed4 branch. A fixed4 signal therefore changes the ranking only when its log-evidence exceeds wavelet log-evidence by more than `m`.

The complete candidate grid is frozen as:

`m in {0.00, 0.25, 0.50, 0.75, 1.00}`.

No weight, nonlinear transform, support estimate, shower-specific value, solar-longitude-specific value, or additional combiner may be tested in this development stage.

## Development evidence

Only already exposed and checksum-pinned record artifacts are used:

- SonotaCo 2025 wavelet comparison, artifact `8969020016`, ZIP SHA-256 `c8d72fa8b051da05c0e4701a48302f97bf53232bd623df30a6953e05b8522232`;
- SonotaCo 2023 wavelet transfer, artifact `8969274303`, ZIP SHA-256 `d00faaf9d781b988bbab0af09e1e27ddf0a824be63f96778bf295b4bf56c404b`;
- SonotaCo 2022 prospective hybrid validation, artifact `8970137965`, ZIP SHA-256 `5cc0404f486e7ca060349345e42b042201a0a4732dfe680c98b1243d0ae1da43`.

No meteor catalogue is opened in development. The record-level p-values and episode identities were already exposed by the completed frozen analyses.

## Selection endpoint

For every corpus and margin:

1. weak AUROC is calculated using k=4, 6, and 8 positive episodes versus all held-out negative episodes;
2. empirical alpha=.05 recall is calculated at the corpus-specific 95th percentile of negative `T_m`;
3. all metrics use the exact same records for every margin.

Margins are ranked lexicographically by:

1. largest minimum weak-AUROC improvement over wavelet across all three corpora;
2. largest mean weak-AUROC improvement;
3. largest mean k=4 recall improvement;
4. smaller margin.

Development passes only if the selected margin improves weak AUROC over wavelet in every corpus and improves mean k=4 recall without reducing mean k=6 or k=8 recall by more than 0.02.

## Final calibrated method

A development pass freezes the selected margin and authorizes a separate implementation in which paired leave-one-out calibration episodes are transformed to `T_m`, and the target statistic is assigned a final empirical p-value against the transformed null distribution. This preserves the same bin-wise calibration logic used for the earlier hybrid.

## Prospective boundary

SonotaCo 2021 is reserved as the sole prospective validation corpus. No 2021 label, fixed4 score, wavelet coefficient, episode endpoint, or candidate score may be accessed before:

- the development artifact and SHA-256 are frozen;
- the selected margin is committed;
- the final calibrated implementation and promotion gates are frozen.

The prospective method may be promoted only if it exceeds wavelet weak AUROC on 2021, improves k=4 recall at alpha=.05, does not fall below both components at any k, and preserves calibrated false-positive control. A failure is final for this formulation.

This work does not modify or erase fixed4, wavelet, Tippett-hybrid, catalogue-wrapper, or OrbitTrace results.