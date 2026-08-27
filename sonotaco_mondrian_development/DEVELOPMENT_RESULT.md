# SonotaCo 2025 Mondrian quartet: authoritative external-survey result

Runner workflow `30877614736` completed the frozen SonotaCo 2025 development benchmark from external-adapter source SHA-256 `5e6d7a6545d83902362cc06c2fae5d285ae92eb2e8e1d7d42fd9769862ebf518`, exact PR #14 baseline source SHA-256 `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`, and exact PR #38 scorer source SHA-256 `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`.

Artifact `8880096952` was preserved with digest `sha256:4a1e50c5bc6ffddb3509e4d207ed6f94ac9c3eaf6435101a58f6c4ad77472d06`.

## Result

- supported 10-degree bins: **32**;
- eligible native shower codes: **34**;
- weak positive / negative windows: **408 / 2,048**;
- candidate weak AUROC: **0.773812**;
- fixed split / density / DBSCAN AUROC: **0.756654 / 0.753978 / 0.749487**;
- pooled FPR at p <=0.05 / 0.01: **0.041016 / 0.006836**;
- worst 60-degree reporting-sector FPR at p <=0.05: **0.054688**.

Recall:

- k=4: **0.139706 / 0.036765** at p <=0.05 / 0.01;
- k=6: **0.389706 / 0.169118**;
- k=8: **0.566176 / 0.264706**;
- k=12: **0.889706 / 0.617647**.

Every parser, calibration, AUROC, comparator, fold, k=6, k=8, and monotonicity gate passed. The exact formulation failed only:

- k=4 recall at p <=0.05 required 0.15; observed **0.139706**;
- k=4 recall at p <=0.01 required 0.05; observed **0.036765**.

Verdict: **`KILL_SONOTACO_2025_MONDRIAN_DEVELOPMENT`**.

## Interpretation

The coverage-normalized Mondrian quartet transfers across surveys in calibration and overall discrimination, and it outperforms all fixed comparators on SonotaCo. Its structural exactly-four-member weakness also transfers: the external survey independently reproduces the same sparse-limit limitation that motivated this methodology branch.

No label mapping, quality rule, score, window width, bin width, calibration count, seed, comparator, fold, threshold, recall requirement, or survey year will be changed. SonotaCo 2024 remains untouched and is not authorized for confirmation because the development formulation did not pass every frozen gate. No GhostStream or catalogue application is authorized.
