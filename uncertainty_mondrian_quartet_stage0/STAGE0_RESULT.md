# Uncertainty-inflated exact quartet with fixed 10° Mondrian calibration: authoritative result

Runner workflow `30876961929` completed the full frozen 2019/2021/2023/2025 development benchmark. Artifact `8880229146` was preserved with digest `sha256:08e904eff1b4dbcb177a9ec4c94210c8dbc6451755fa6a955c633134c1d9416b`.

The exact frozen composition source SHA-256 was `7aad1aadd9ae3674abd9c175ae141982ab4463d7e63520fed9660fbfcc12b9c6`.

## Frozen panel

- supported 10° year-bins: **131** — 32 in 2019 and 33 in each of 2021, 2023, and 2025;
- independent audit negatives: **8,384**;
- weak positive windows: **3,960**;
- total positive windows: **5,276**.

## Result

Weak-window AUROC:

- uncertainty-inflated exact quartet: **0.773846**;
- uninflated exact quartet: **0.769665**;
- anchored quartet: **0.769120**;
- LCC: **0.776915**;
- density / DBSCAN: **0.769888 / 0.758685**;
- quality-only ablation: **0.508451**.

Calibration:

- pooled candidate FPR at alpha 0.05 / 0.01: **0.046636 / 0.006799**;
- worst year-by-60° reporting-sector FPR at alpha 0.05: **0.067708**;
- diagnostic worst individual 10°-bin FPR: **0.125000**.

Candidate recall at alpha 0.05 / 0.01:

- k=4: **0.183333 / 0.069697**;
- k=6: **0.389394 / 0.206061**;
- k=8: **0.558333 / 0.346970**;
- k=12: **0.753040 / 0.546353**.

Uninflated exact-quartet k=4 recall was **0.179545 / 0.071970**. Thus uncertainty inflation gained modestly at alpha 0.05 but lost slightly at alpha 0.01.

Candidate fold AUROCs were **0.779576, 0.769558, 0.807529, 0.761749, 0.750737**.

## Frozen-gate outcome

Twenty-eight of thirty gates passed. The two failures were:

- candidate weak AUROC **0.773846**, required at least **0.80**;
- candidate k=4 recall at alpha 0.01 was **0.002273 below** the uninflated exact quartet, while the protocol required a gain of at least **0.005**.

Every calibration, support, quality-ablation, comparator-proximity, fold, absolute recall, k=6/k=8 preservation, and monotonicity gate passed.

Verdict: **`KILL_UNCERTAINTY_MONDRIAN_QUARTET`**.

## Interpretation

The 10° Mondrian mechanism fully repaired the coarse-sector calibration failure from PR #57. Reported uncertainties also contain some real information: the candidate slightly improved weak AUROC and alpha-0.05 k=4 recall over the uninflated exact quartet, while the quality-only ablation stayed at chance. However, the heuristic distance inflation did not produce a robust strict-tail advantage and did not reach the frozen absolute AUROC standard.

No uncertainty multiplier, equation, bin width, support rule, calibration count, seed, clique size, feature scale, comparator, fold, threshold, or endpoint will be changed. No August confirmation, SonotaCo confirmation, catalogue scan, or GhostStream application is authorized by this result.