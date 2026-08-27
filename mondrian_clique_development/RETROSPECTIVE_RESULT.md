# Coverage-normalized Mondrian retrospective result

## Authoritative execution

Runner workflow `30874712496` completed all four frozen retrospective panels from exact source SHA-256 `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`.

All four jobs reconstructed the exact 9,000-character split source, verified every input and baseline hash, compiled the source, enforced every scientific gate, and preserved provenance artifacts.

Artifacts:

- 2021: `8879131406`, digest `sha256:0f4b08178a6e6d41bacdc77a3545aa29566b72d7655af5f43e48e8e401e69dbf`;
- 2024: `8879128070`, digest `sha256:7a15fa328ac699ace0a23bed7098fd05ac630b51af5492660b8c1846fd699274`;
- 2025: `8879127025`, digest `sha256:4d63d03101a2648be5c6978541971f5f8a5a27348b5fa77658e8c08cea69387b`;
- January–June 2026: `8879118970`, digest `sha256:ad91185bfc7deb13d6e5220b9e87c185507f3b60c4bd197de119533e3c252e8c`.

GhostStream remained excluded by removing solar longitude 20.0°–55.0° before every stratum, pool, window, score, fold, and endpoint.

## Results

| Panel | Clique weak AUROC | FPR at 0.05 | FPR at 0.01 | Worst reporting-sector FPR at 0.05 | Verdict |
|---|---:|---:|---:|---:|---|
| 2021 | 0.79628 | 0.03741 | 0.00893 | 0.04688 | PASS |
| 2024 | 0.80679 | 0.03835 | 0.01042 | 0.04688 | PASS |
| 2025 | 0.79544 | 0.04924 | 0.00900 | 0.06250 | PASS |
| 2026 H1 | 0.84985 | 0.04271 | 0.00833 | 0.06771 | PASS |

The 2026 H1 panel contained 15 supported 10-degree bins, 99 eligible showers, 1,188 weak positive windows, and 960 independent negative windows. Its comparator AUROCs were 0.84517 for the killed split statistic, 0.83445 for fixed local density, and 0.80932 for fixed DBSCAN.

The 2026 H1 clique recall was:

| Real members | p <= 0.05 | p <= 0.01 |
|---:|---:|---:|
| 4 | 0.22222 | 0.10606 |
| 6 | 0.53788 | 0.32576 |
| 8 | 0.70960 | 0.49747 |
| 12 | 0.90404 | 0.72980 |

Every calibration, AUROC, comparator, fold-consistency, weak-member recall, and monotonicity gate passed independently in every panel.

## Interpretation

The 10-degree Mondrian formulation resolves the coarse 60-degree false-positive instability across four heterogeneous retrospective panels while preserving the partition-invariant clique's four-member sensitivity. This is the first complete methodology candidate in the search to pass its entire retrospective matrix.

The result is development evidence, not independent confirmation. PR #36 remains correctly killed under its original universal 20-bin feasibility rule, and the January–June 2026 panel is spent because it informed the coverage-normalized formulation.

Verdict: `PROCEED_TO_SEPARATELY_FROZEN_UNUSED_JULY_2026_SNAPSHOT_GATE`.

No GhostStream application, catalog scan, or discovery claim is authorized. Only a separately frozen test on the unused July 2026 snapshot may provide new confirmation evidence.