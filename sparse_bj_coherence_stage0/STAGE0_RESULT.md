# Sparse Berk–Jones coherence: authoritative Stage-0 result

Runner workflow `30875315589` completed the frozen 2019/2021/2023/2025 development preflight from source SHA-256 `90b550ee4f682d05a81b1b6a6ea5e8ca6c2d3264b4dee5769e213dca95ef7de6`.

Artifact `8879360076` was preserved with digest `sha256:d6f005242a3bd133f01f927f98897afda7da4866c626f6ddb986071195f6854c`.

## Result

- sparse Berk–Jones weak AUROC: **0.73590**;
- exact K4 comparator: **0.76013**;
- unchanged LCC: **0.76384**;
- local density: **0.76688**;
- DBSCAN analogue: **0.73486**;
- pooled FPR at 0.05: **0.05339**;
- worst year-sector FPR at 0.05: **0.18750**;
- k=4 recall at p ≤0.05: **0.12424**;
- k=6 recall: **0.29091**;
- k=8 recall: **0.44848**.

Only pooled calibration and k=6/k=8 preservation passed. The candidate failed worst-stratum calibration, the 0.80 AUROC gate, preservation against LCC, the density comparator, k=4 recall, and k=4 gain.

Verdict: **`KILL_SPARSE_BERK_JONES_PREFLIGHT`**.

The adaptive sparse order-statistic scan did not recover more four-member signal than the simpler coherence scores and reduced overall discrimination. No subset-size limit, normalization, calibration count, threshold, seed, or gate will be changed, and no confirmation-year or GhostStream application is authorized.
