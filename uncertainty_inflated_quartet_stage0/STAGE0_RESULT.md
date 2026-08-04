# Uncertainty-inflated exact quartet: authoritative Stage-0 result

Runner workflow `30876245185` completed the full frozen 2019/2021/2023/2025 development screen. Evidence artifact `8879692918` was preserved with digest `sha256:ce21072ec27034b279eeff65276af3d919988d636a20b7c2f9e058859bb4f933`.

## Result

The uncertainty-aware statistic produced a real but modest improvement over the uninflated quartet:

- weak AUROC: **0.77223**;
- exact quartet / anchored quartet / LCC: **0.76921 / 0.77016 / 0.77363**;
- density / DBSCAN: **0.76978 / 0.74248**;
- quality-only ablation AUROC: **0.51139**, ruling out measurement quality as a useful label proxy.

Calibration and recall:

- pooled FPR at alpha 0.05 / 0.01: **0.05078 / 0.00586**;
- worst year-sector alpha-0.05 FPR: **0.14062**;
- k=4 recall: **0.17576 / 0.06288** at alpha 0.05 / 0.01;
- k=6 recall: **0.32955 / 0.15833**;
- k=8 recall: **0.48106 / 0.25682**;
- k=12 recall: **0.68693 / 0.46733**.

Fold AUROCs were **0.77616, 0.74782, 0.82847, 0.78409, 0.72415**.

Fifteen of eighteen frozen gates passed. The failures were:

- worst-sector FPR **0.14062**, required at most **0.120**;
- weak AUROC **0.77223**, required at least **0.80**;
- only three of five folds reached **0.75**, required at least four.

Verdict: **`KILL_UNCERTAINTY_INFLATED_QUARTET`**.

## Interpretation

Reported event uncertainties contain genuine physical information: uncertainty inflation improved k=4 sensitivity, stringent-tail recall, and weak AUROC over the exact quartet, while the quality-only ablation stayed at chance. The gain was nevertheless too small to overcome conditional background instability or the frozen absolute and fold-robustness requirements.

No uncertainty multiplier, covariance rule, feature scale, sector, seed, fold, threshold, or gate will be changed. No confirmation-year, external-survey, catalogue, or GhostStream application is authorized by this result.