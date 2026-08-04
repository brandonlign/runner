# Untouched even-year power result

## Authoritative execution

Runner workflow `30871987866` completed the full frozen benchmark from source SHA-256 `8c69bddb7e8bd52694f32f62a5e105a0fda4ca330734d55704ee26e0d0faff1c`.

Artifact `8878235001` was preserved with digest `sha256:0d07cfc8f7bfa39545d367068e23355671fc801bf93f64da5785614831def11a`.

All source, data, audit, Stage-0, baseline-payload, and baseline-source hashes passed before any power computation. GhostStream remained blinded by removing solar longitude 20.0°–55.0° before all pools, windows, scores, folds, and endpoints.

## Result

The untouched confirmation panel used 2020, 2022, and 2024:

- 18 supported year-sectors;
- 136 eligible established showers after the blind interval;
- 4,848 weak positive windows;
- 4,608 independent empirical-background negative windows.

Performance:

- candidate weak AUROC: **0.80147**;
- fixed local-density AUROC: **0.78145**;
- fixed DBSCAN AUROC: **0.76541**;
- pooled false-positive rate at alpha 0.05: **0.04861**;
- pooled false-positive rate at alpha 0.01: **0.01237**;
- worst year-sector false-positive rate at alpha 0.05: **0.07422**.

Every complex fold passed comfortably:

- fold 0: **0.82357**;
- fold 1: **0.81068**;
- fold 2: **0.78451**;
- fold 3: **0.77525**;
- fold 4: **0.81104**.

Recall by injected real-member count:

| Members | p <= 0.05 | p <= 0.01 |
|---:|---:|---:|
| 4 | **0.13428** | **0.03651** |
| 6 | 0.31559 | 0.15842 |
| 8 | 0.49257 | 0.29084 |
| 12 | 0.70545 | 0.49938 |

## Frozen gate outcome

Thirteen of fifteen gates passed. The two failures were both the prospectively frozen four-member endpoints:

- recall at alpha 0.05 was **0.13428**, below the required **0.15**;
- recall at alpha 0.01 was **0.03651**, below the required **0.05**.

No calibration, AUROC, comparator, fold-consistency, k=6, k=8, or monotonicity gate failed.

Verdict: `KILL_EMPIRICAL_WINDOW_LCC_POWER`.

## Interpretation

The same-corpus empirical-window repair genuinely solved the conditional false-alarm instability from PR #23 and generalized to untouched years. The unchanged cross-fitted score also generalized in AUROC and beat both fixed comparators in every fold.

Its remaining limitation is structural at exactly four members. A 64/64 reference-query split requires a favorable allocation of the four coherent events before the second-neighbor/top-two statistic can express the full signal; median aggregation across eight splits sacrifices some four-member sensitivity in exchange for stable calibration.

The exact formulation is killed under its frozen protocol. Do not lower the recall thresholds, replace seeds, alter the split aggregator, change neighbor count, or reapply it to GhostStream.

A separately frozen method may investigate a partition-invariant four-point coherence statistic, but it must be treated as a new method and validated without reusing these confirmation labels for model or threshold selection.
