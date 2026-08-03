# Stage-1 runner result

Status: **killed by the frozen complex-held-out power gate**.

Runner commit: `4d112d330263a76ad2548429f72e95ac0b5c7e14`

Workflow run: `30862291835`

Artifact: `local-conformal-coherence-power-stage1` (`8874842323`)

Artifact digest: `sha256:380261e8b3064e62d91815312e7cb6a4c9e571c6037bacb4b74901b04d354088`

## Frozen result

- supported year-sectors: 24
- eligible established showers: 181
- positive windows: 10,048
- weak positive windows: 7,536
- untouched negative windows: 6,144
- candidate weak AUROC: 0.80094
- fixed local-density AUROC: 0.77483
- fixed DBSCAN AUROC: 0.75780
- pooled untouched-negative FPR at alpha 0.05, local/global: 0.05241 / 0.05029
- pooled untouched-negative FPR at alpha 0.01, local/global: 0.01042 / 0.01058
- worst year-sector FPR at alpha 0.05, local/global: 0.16797 / 0.31250
- failed local year-sector: `2019:1`, with 43 of 256 untouched negative windows below the nominal 0.05 threshold

## Recall

| Stream members | p <= 0.05 | p <= 0.01 |
|---:|---:|---:|
| 4 | 0.15486 | 0.06051 |
| 6 | 0.33161 | 0.19268 |
| 8 | 0.48607 | 0.31887 |
| 12 | 0.70939 | 0.52707 |

## Complex-fold weak AUROC

- fold 0: 0.81345
- fold 1: 0.79968
- fold 2: 0.79040
- fold 3: 0.79880
- fold 4: 0.80206

Fifteen of sixteen frozen gates passed. The sole failure was `worst_group_fpr_005_le_012`: the observed worst local year-sector rate was 0.16797, above the predeclared 0.120 ceiling.

## Verdict

`KILL_LOCAL_CONFORMAL_COHERENCE_POWER`

The strong power result does not override the failed conditional-calibration gate. No threshold relaxation, sector removal, recalibration, score modification, or GhostStream application is permitted on this formulation.

Artifact report SHA-256: `2ff6368341367917859298dc52e3d317ed9cff2eca549a130aa8d8e1a6c1e46a`

Artifact JSON SHA-256: `3f3e50f9461aa0a17b5b0d771ed2cb9fb85e234b3d88512635663f47604b7287`
