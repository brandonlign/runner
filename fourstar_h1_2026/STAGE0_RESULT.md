# Partition-invariant four-star coherence: H1 2026 result

## Authoritative execution

Runner workflow `30873567936` executed the frozen January–June 2026 sequence from commit `ada1badc51e3a730a35a4aee28eeb2f15046e082`.

Preserved artifacts:

- data audit: artifact `8878701296`, digest `sha256:05284bc1910b6ab0993d8924b3719a5314d9644d65c16daca78b70d413a5251c`;
- label-blind null audit: artifact `8878729205`, digest `sha256:e8fc4d9648d60d8f64b959fea347564e7757891bdbe15c697f0d6ee4c7ed5fe5`.

The frozen derived null source had SHA-256 `0db9b71f16b6fe13e202b5b10d5fd5c1b79d51d05786b47efb95bf086ec761c3`.

## Data gate

Every frozen H1 2026 data gate passed:

- eligible showers: **167**;
- strong showers: **91**;
- eligible complex units: **161**;
- multi-shower complex units: **6**;
- quality sporadic events: **274,308**;
- selected labeled events: **26,574**;
- selected sporadic events: **30,000**;
- selected-event completeness: **1.000**.

After removing the frozen GhostStream blind interval, the null audit retained **23,715** sporadic events across four supported 60-degree sectors.

## Label-blind null result

The four fixed batches produced:

| Batch | Pooled FPR at 0.05 | Pooled FPR at 0.01 | Worst-sector FPR at 0.05 |
|---:|---:|---:|---:|
| 0 | 0.02930 | 0.00586 | 0.05469 |
| 1 | **0.07227** | 0.00586 | **0.12500** |
| 2 | 0.03906 | 0.00586 | 0.06250 |
| 3 | 0.03711 | 0.00195 | 0.04688 |

Batch 1 failed both frozen alpha-0.05 gates:

- pooled FPR **0.07227**, above the **0.060** ceiling;
- sector `2026:5` FPR **0.12500**, above the **0.120** ceiling.

All alpha-0.01 gates passed. Three of four batches passed every calibration endpoint, but the protocol required all batches.

Verdict: **`KILL_H1_2026_FOURSTAR_NULL`**.

## Interpretation

Removing the reference/query split restored exactly-four-member power on development data, but the minimum four-point diameter is an extreme-value statistic over 128 overlapping candidate stars. Its upper tail remained too sensitive to finite empirical-window variation in the untouched 2026 background. This is a null-calibration failure, so no established-shower power score is eligible for inspection and the power job was skipped.

No batch, sector, seed, threshold, month, score, or calibration count will be changed. The candidate must not be applied to GhostStream.
