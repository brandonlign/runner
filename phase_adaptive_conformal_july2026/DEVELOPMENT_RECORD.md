# Development record before untouched July 2026 confirmation

All results below use only retired data: 2019–2025 and January–June 2026. July 2026 was not downloaded or inspected.

## Failure that motivated the method

PR #34 tested minimum four-star diameter on untouched H1 2026. Its data gate passed, but one of four label-blind null batches produced pooled FPR 0.07227 and block FPR 0.12500. The power stage was skipped and PR #34 was closed.

The diagnosis was structural: taking the single minimum over 128 overlapping four-stars creates a volatile extreme-value tail.

## Score development

Eleven partition-invariant variants were screened. Averaging the three smallest center-plus-three-nearest star diameters gave the strongest balance of raw power and robustness.

On a full H1 2026 development panel with 144 showers, 1,728 weak positive windows, and 1,024 negatives:

- raw weak AUROC: **0.85737**;
- local-density AUROC: **0.83124**;
- k=4 recall under ordinary sector calibration: **0.30729** at 0.05 and **0.14062** at 0.01;
- minimum complex-fold AUROC: **0.82211**.

## Calibration development

Direct 60° sector ranks still varied between finite Monte Carlo batches. Nearest-center calibration reduced seasonal mismatch but produced discrete local ranks, which became over-conservative at alpha 0.01 after outer recalibration.

The selected mechanism therefore uses:

1. a continuous empirical-CDF interpolation among the 128 nearest inner-reference centers;
2. an independent outer conformal rank within the same 10° solar-longitude block.

The outer rank, not the interpolated inner coordinate, is the inferential p-value.

## Retired H1 2026 power result

With 512 inner windows, 512 outer windows, 256 negative windows per supported block, and eight positive replicates:

- weak AUROC: **0.86072**;
- pooled FPR: **0.04883** at 0.05 and **0.01074** at 0.01;
- worst-block FPR at 0.05: **0.06250**;
- fold AUROCs: **0.86799, 0.87445, 0.82739, 0.84502, 0.88719**.

Recall:

| k | p <= 0.05 | p <= 0.01 |
|---:|---:|---:|
| 4 | **0.28125** | **0.12674** |
| 6 | 0.57118 | 0.29167 |
| 8 | 0.81771 | 0.48090 |
| 12 | 0.94444 | 0.66667 |

## Multi-year label-blind stress test

The exact mechanism was then tested on all seven retired full years using independent inner, outer, and audit banks.

- odd years 2019/2021/2023/2025: pooled alpha-0.05 FPR **0.05859** and **0.04948** in two batches; alpha-0.01 **0.00651** and **0.00456**;
- even years 2020/2022/2024: pooled alpha-0.05 FPR **0.04080** and **0.05208**; alpha-0.01 **0.00347** and **0.01215**.

A single 64-window local block reached 0.125 in one 24-block batch, while the pooled result remained valid. That demonstrated why the July protocol evaluates persistent batch-level calibration rather than selecting methods for lucky maxima of small local samples.

No July result influenced the score, normalization, bank sizes, blocks, endpoints, or gates.
