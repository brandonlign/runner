# Four-star candidate development record

All development below used only 2019, 2021, 2023, and 2025, with solar longitude 20.0°–55.0° removed. The 2020/2022/2024 confirmation results from PR #31 were used only to identify the structural exactly-four-member limitation and are retired from further confirmation.

## Mechanistic motivation

The PR #31 statistic randomly partitions each 128-event window into 64 reference and 64 query events. A true four-member stream contributes strongly only when enough members land on both sides of a split. Median aggregation across eight splits improves stability but can discard a small stream that is unfavorable in more than half of the partitions.

The replacement removes the partition entirely. Every event acts as a center, its three nearest neighbors form a four-event candidate, and the tightest candidate diameter is scored.

## Development screen

A fixed screen compared:

- the PR #31 split statistic;
- minimum third-neighbor radius;
- minimum center-plus-three-nearest four-point diameter;
- Bonferroni unions of the split and partition-invariant statistics.

The four-point diameter was selected because it improved the target k=4 endpoint without sacrificing overall discrimination. The unions were rejected because multiplicity correction erased the rescue.

## Full frozen odd-year development result

Using 512 calibration windows and 256 independent negative windows per year-sector, four positive replicates, 181 eligible showers, and all five complex folds:

- weak AUROC: **0.80742**;
- PR #31 split AUROC on the same regenerated panel: **0.80217**;
- fixed local-density AUROC: **0.77999**;
- pooled FPR: **0.04850** at 0.05 and **0.01025** at 0.01;
- worst-sector FPR at 0.05: **0.08203**;
- fold AUROCs: **0.82970, 0.80364, 0.79501, 0.80037, 0.80835**.

Recall:

| k | p ≤ 0.05 | p ≤ 0.01 |
|---:|---:|---:|
| 4 | **0.16561** | **0.06051** |
| 6 | 0.33240 | 0.16959 |
| 8 | 0.46377 | 0.28941 |
| 12 | 0.66083 | 0.45422 |

The candidate cleared every continuation threshold later frozen in the H1 2026 protocol. No H1 2026 file, label, score, or count was inspected during candidate selection.
