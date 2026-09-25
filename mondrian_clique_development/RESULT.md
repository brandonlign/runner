# Coverage-normalized Mondrian four-clique: authoritative retrospective development result

Runner workflow `30874712496` completed the full frozen four-panel matrix from source SHA-256 `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`.

This is a separate development formulation from PR #36. PR #36 remains killed under its uniform 20-stratum requirement. The present source prospectively required at least 20 supported 10° strata for complete-year panels and at least 12 for the fixed January–June 2026 panel before that spent H1 panel was scored.

GhostStream remained excluded by removing solar longitude 20.0°–55.0° before every stratum, pool, window, score, fold, and endpoint.

## Preserved evidence

- 2021 artifact `8879131406`, digest `sha256:0f4b08178a6e6d41bacdc77a3545aa29566b72d7655af5f43e48e8e401e69dbf`;
- 2024 artifact `8879128070`, digest `sha256:7a15fa328ac699ace0a23bed7098fd05ac630b51af5492660b8c1846fd699274`;
- 2025 artifact `8879127025`, digest `sha256:4d63d03101a2648be5c6978541971f5f8a5a27348b5fa77658e8c08cea69387b`;
- 2026 H1 artifact `8879118970`, digest `sha256:ad91185bfc7deb13d6e5220b9e87c185507f3b60c4bd197de119533e3c252e8c`.

Every panel passed every frozen feasibility, calibration, discrimination, fold, recall, and monotonicity gate.

## 2021 complete year

- supported 10° strata: **33**, required at least 20;
- eligible showers: **174**;
- clique weak AUROC: **0.79548**;
- split / density / DBSCAN AUROC: **0.79290 / 0.77037 / 0.75088**;
- pooled FPR at alpha 0.05 / 0.01: **0.03741 / 0.00947**;
- worst 60° reporting-sector FPR at alpha 0.05: **0.07813**;
- k=4 recall at alpha 0.05 / 0.01: **0.15661 / 0.05747**;
- five clique fold AUROCs: **0.83348, 0.77267, 0.77266, 0.78295, 0.81684**.

## 2024 complete year

- supported 10° strata: **33**, required at least 20;
- eligible showers: **135**;
- clique weak AUROC: **0.80697**;
- split / density / DBSCAN AUROC: **0.80602 / 0.78223 / 0.76377**;
- pooled FPR at alpha 0.05 / 0.01: **0.03835 / 0.00521**;
- worst reporting-sector FPR: **0.05729**;
- k=4 recall: **0.20370 / 0.06852**;
- five clique fold AUROCs: **0.81151, 0.78691, 0.79402, 0.82813, 0.81557**.

## 2025 complete year

- supported 10° strata: **33**, required at least 20;
- eligible showers: **181**;
- clique weak AUROC: **0.79197**;
- split / density / DBSCAN AUROC: **0.78681 / 0.76766 / 0.75386**;
- pooled FPR: **0.04924 / 0.00473**;
- worst reporting-sector FPR: **0.07552**;
- k=4 recall: **0.17680 / 0.07182**;
- five clique fold AUROCs: **0.82376, 0.79276, 0.80472, 0.77367, 0.76493**.

## January–June 2026 spent development panel

- supported 10° strata: **15**, required at least 12;
- eligible showers: **99**;
- clique weak AUROC: **0.84985**;
- split / density / DBSCAN AUROC: **0.84517 / 0.83445 / 0.80932**;
- pooled FPR: **0.04271 / 0.00833**;
- worst reporting-sector FPR: **0.06771**;
- k=4 recall: **0.22222 / 0.10606**;
- k=6 recall: **0.53788 / 0.32576**;
- k=8 recall: **0.70960 / 0.49747**;
- five clique fold AUROCs: **0.83040, 0.87869, 0.84700, 0.82488, 0.86592**.

The H1 panel is retrospective development evidence only because its coverage threshold was defined after PR #36 exposed the uniform-threshold feasibility problem. It cannot independently confirm the method.

## Outcome

Verdict: **`PASS_COVERAGE_NORMALIZED_MONDRIAN_DEVELOPMENT`**.

Across four heterogeneous panels, fixed 10° solar-phase calibration controlled pooled and conditional false positives while preserving the partition-invariant four-clique detector's exactly-four-member sensitivity. The result supports the method as a serious candidate, not a GhostStream result.

The protocol authorized a separately frozen unused-data confirmation. A complete-year 2018 confirmation is scientifically stronger than a one-month July 2026 snapshot because it tests the same full-cycle target population as the intended catalogue method and avoids a coverage-limited endpoint. No 2018 file, count, label, or score may be inspected until that separate protocol and data gate are committed.
