# Phase-marginal mutual-star support: authoritative July development result

Runner workflow `30876291034` completed the full frozen July 2026 development benchmark. Evidence artifact `8879658376` was preserved with digest `sha256:c5f27fda22ac22cbaca3fb2e6ab8f9991eec7d84975a45f1c5d6bec538cbfa00`.

Exact sources:

- original PR #48 source SHA-256: `11f7590675cca5812566a39fa11e07de7a905c0a468c45ef184246cd65c9eec7`;
- phase-marginal wrapper/source SHA-256: `44d9bebe8ae330a64a40c9d6abf47ad3b74a1c3dd48a42fff04d1608b1f1efb5`.

## Result

The candidate substantially improved the prior July score while maintaining calibration:

- weak AUROC: **0.811203**;
- density / DBSCAN AUROC: **0.753064 / 0.744659**;
- independent-negative FPR at alpha 0.05 / 0.01: **0.059570 / 0.005859**;
- worst-block alpha-0.05 FPR: **0.082031**;
- fold AUROCs: **0.84927, 0.89526, 0.78355, 0.78174, 0.74750**.

Recall at alpha 0.05 / 0.01:

- k=4: **0.17105 / 0.05592**;
- k=6: **0.40461 / 0.09868**;
- k=8: **0.60526 / 0.24342**;
- k=12: **0.82237 / 0.46382**.

Fifteen of seventeen frozen gates passed. The two failures were:

- k=6 recall at alpha 0.01: **0.09868**, required at least **0.15**;
- k=8 recall at alpha 0.01: **0.24342**, required at least **0.25**.

Verdict: **`KILL_PHASE_MARGINAL_SUPPORT_DEVELOPMENT`**.

## Interpretation

Removing within-window solar-longitude distance was a real improvement: the candidate cleared all calibration, AUROC, fold, alpha-0.05, and k=4 alpha-0.01 gates. However, it still did not preserve the prospectively required stringent 1% sensitivity for six- and eight-member streams. The k=8 miss was narrow, but the k=6 miss was material.

No support count, feature scaling, calibration bank, seed, threshold, recall gate, or shower subset will be changed. July is retired and cannot confirm this candidate again. No 2018, external-survey, catalogue, or GhostStream application is authorized by this result.