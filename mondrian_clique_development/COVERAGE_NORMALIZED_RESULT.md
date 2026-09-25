# Coverage-normalized Mondrian four-clique: authoritative retrospective result

Runner workflow `30874712496` completed the full frozen 2021/2024/2025/January–June-2026 matrix from source SHA-256 `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`.

This is the distinct calendar-aware feasibility formulation frozen in PR #38. PR #36 remains killed under its original all-panels-at-least-20-strata rule. No scientific score, 10° boundary, calibration count, seed, comparator, fold, endpoint, threshold, or gate was changed.

GhostStream remained excluded by removing solar longitude 20.0°–55.0° before every stratum, pool, window, score, fold, and endpoint.

## Preserved evidence

- 2021 artifact `8879131406`, digest `sha256:0f4b08178a6e6d41bacdc77a3545aa29566b72d7655af5f43e48e8e401e69dbf`;
- 2024 artifact `8879128070`, digest `sha256:7a15fa328ac699ace0a23bed7098fd05ac630b51af5492660b8c1846fd699274`;
- 2025 artifact `8879127025`, digest `sha256:4d63d03101a2648be5c6978541971f5f8a5a27348b5fa77658e8c08cea69387b`;
- 2026 H1 artifact `8879118970`, digest `sha256:ad91185bfc7deb13d6e5220b9e87c185507f3b60c4bd197de119533e3c252e8c`.

## Frozen panel results

| Panel | Supported 10° strata | Weak AUROC | FPR 0.05 | FPR 0.01 | Worst 60° FPR | k=4 recall 0.05 | k=4 recall 0.01 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 33 | 0.79548 | 0.03741 | 0.00947 | 0.07813 | 0.15661 | 0.05747 |
| 2024 | 33 | 0.80697 | 0.03835 | 0.00521 | 0.05729 | 0.20370 | 0.06852 |
| 2025 | 33 | 0.79197 | 0.04924 | 0.00473 | 0.07552 | 0.17680 | 0.07182 |
| 2026 H1 | 15 | 0.84985 | 0.04271 | 0.00833 | 0.06771 | 0.22222 | 0.10606 |

The H1 panel contained 99 eligible showers, 1,188 weak positive windows, and 960 independent negative windows. Its fixed comparators were:

- killed split statistic: **0.84517**;
- radius-2.5 local density: **0.83445**;
- DBSCAN: **0.80932**.

Its five complete complex-disjoint clique AUROCs were **0.83040, 0.87869, 0.84700, 0.82488, 0.86592**.

H1 recall was:

| Members | p <= 0.05 | p <= 0.01 |
|---:|---:|---:|
| 4 | 0.22222 | 0.10606 |
| 6 | 0.53788 | 0.32576 |
| 8 | 0.70960 | 0.49747 |
| 12 | 0.90404 | 0.72980 |

Every frozen calibration, discrimination, comparator-proximity, fold, k=4/k=6/k=8 recall, and monotonicity gate passed independently in all four panels.

## Interpretation

The failure mode in PR #32 was conditional nonstationarity from pooling six times more solar phase than the search neighborhood required. Globally anchored 10° Mondrian calibration removes that inflation while preserving the partition-invariant quartet signal. The result is consistent across three complete years and one heterogeneous partial-year panel, with pooled FPR below nominal 0.05 in every panel and no weak-power collapse.

Verdict: **`PASS_COVERAGE_NORMALIZED_MONDRIAN_DEVELOPMENT`**.

This retrospective pass does not authorize a GhostStream application or catalogue scan. It authorizes only a pre-frozen untouched confirmation. PR #39 independently reserved complete-year 2018 before any 2018 file, count, checksum, label, score, or feasibility result was inspected; that one-shot confirmation is the next active stage.
