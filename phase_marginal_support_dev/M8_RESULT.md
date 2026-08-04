# Eight-star phase-marginal support: full July development result

Runner workflow `30876291034` completed the exact full retired-July benchmark and preserved artifact `8879658376` with digest `sha256:c5f27fda22ac22cbaca3fb2e6ab8f9991eec7d84975a45f1c5d6bec538cbfa00`.

## Result

- included showers: **38**;
- weak positive windows: **912**;
- independent negative windows: **1,024**;
- candidate weak AUROC: **0.811203**;
- fixed local-density AUROC: **0.753064**;
- fixed DBSCAN AUROC: **0.744659**;
- negative FPR: **0.059570** at alpha 0.05 and **0.005859** at alpha 0.01;
- worst-block FPR at alpha 0.05: **0.082031**.

Recall:

| members | p <= 0.05 | p <= 0.01 |
|---:|---:|---:|
| 4 | **0.171053** | **0.055921** |
| 6 | **0.404605** | **0.098684** |
| 8 | **0.605263** | **0.243421** |
| 12 | **0.822368** | **0.463816** |

Fold AUROCs were **0.849266, 0.895264, 0.783546, 0.781743, and 0.747498**.

## Interpretation

Removing solar longitude from within-window member similarity was a real improvement. Relative to PR #48, the score improved AUROC, brought alpha-0.05 FPR under the frozen ceiling, increased every recall endpoint, and passed the k=4 alpha-0.01 gate.

It still did not clear the full prior standard: k=6 alpha-0.01 recall remained below 0.15 and k=8 reached 0.243421, just below 0.25. The fixed eight-star truncation still privileges one support scale. A separately specified multiscale candidate may adapt across four-, six-, and eight-member structures, but this exact scalar score is not authorized for confirmation or GhostStream application.
