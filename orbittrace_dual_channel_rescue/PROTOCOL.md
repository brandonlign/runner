# OrbitTrace dual-channel minimum-rescue development

## Motivation

The prospective SonotaCo 2021 sparse-tail augmentation preserved calibration and improved k=4 recall, but its combined continuous statistic reduced weak-stream AUROC from 0.817915 for the Brown-family wavelet core to 0.780377. That result freezes the conclusion that fixed4 evidence must not replace or perturb the primary continuous ranking.

The revised architecture therefore has two outputs:

1. **Primary ranking:** the unchanged `brown2010_wavelet_episode_core` score.
2. **Sparse rescue flag:** an episode is additionally detected only when the fixed4 empirical upper-tail p-value equals the minimum attainable value under 128 calibration episodes.

## Frozen rule

Calibration count: `128`.

Minimum empirical p-value:

`p_min = 1 / (128 + 1) = 1 / 129`.

At reporting alpha `0.05`:

`detected = (p_wavelet <= 0.05) OR (p_fixed4 <= 1/129)`.

The continuous ranking is exactly the wavelet score and is never replaced, averaged, reweighted, transformed, or reordered by fixed4.

## Development evidence

Use only already exposed episode-record artifacts from SonotaCo 2025, 2023, 2022, and 2021. No raw meteor catalogue is opened in development. There is no threshold grid and no alternative combiner.

A development pass requires:

- exact wavelet ranking preservation in every corpus;
- strictly positive k=4 recall gain in every corpus;
- mean k=4 recall gain at least 0.02;
- no recall loss for any tested member count;
- overall false-positive-rate increase no greater than 0.01 in any corpus;
- worst-sector false-positive-rate increase no greater than 0.02 in any corpus;
- all record hashes and method identifiers verified.

## Prospective boundary

SonotaCo 2020 is reserved as the sole prospective validation corpus. No 2020 archive, labels, episodes, component scores, or endpoint values may be opened during development.

A development pass authorizes only a separately frozen SonotaCo 2020 transport audit, eligibility audit, runner source audit, and one-shot prospective validation. It does not authorize an OrbitTrace application or a discovery claim.
