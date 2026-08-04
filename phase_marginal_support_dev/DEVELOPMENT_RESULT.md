# Phase-marginal mutual-star support: authoritative development no-go

Runner workflow `30876291034` completed the full retired-July benchmark. Artifact `8879658376` was preserved with digest `sha256:c5f27fda22ac22cbaca3fb2e6ab8f9991eec7d84975a45f1c5d6bec538cbfa00`.

## Result

The phase-marginal score improved overall discrimination and exactly-four-member strict-tail sensitivity:

- candidate weak AUROC: **0.811203**;
- density / DBSCAN: **0.753064 / 0.744659**;
- pooled FPR at 0.05 / 0.01: **0.059570 / 0.005859**;
- worst block FPR at 0.05: **0.082031**;
- five fold AUROCs: **0.849266, 0.895264, 0.783546, 0.781743, 0.747498**.

Recall:

| members | alpha 0.05 | alpha 0.01 |
|---:|---:|---:|
| 4 | 0.171053 | 0.055921 |
| 6 | 0.404605 | 0.098684 |
| 8 | 0.605263 | 0.243421 |
| 12 | 0.822368 | 0.463816 |

Fifteen of seventeen source-encoded gates passed. The exact formulation failed:

- k=6 recall at alpha 0.01: required 0.15, observed **0.098684**;
- k=8 recall at alpha 0.01: required 0.25, observed **0.243421**.

Verdict: **`KILL_PHASE_ADAPTIVE_JULY_POWER`**.

Removing solar longitude from within-window similarity rescued the k=4 strict-tail gate and raised AUROC, but averaging the eight tightest four-stars still did not preserve enough strict-tail evidence for six- and eight-member streams. No support count, feature set, calibration bank, KNN normalization, threshold, seed, comparator, fold, or endpoint will be changed after this result.

July is retired development data and cannot confirm any successor. This exact candidate is not authorized for GhostStream or a catalogue scan.
