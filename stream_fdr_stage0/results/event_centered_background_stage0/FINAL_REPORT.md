# Event-centered robust-background confirmation — final no-go

Authoritative runner workflow: `30846255818`

Artifact: `event-centered-background-stage0` (`8868817380`)

Artifact digest: `sha256:431d8c4f5d7a63be5e8eb24d5512c24ed6110b4e99d054bfaa0fc63fea6a0241`

## Verdict

**KILL_EVENT_CENTERED_ROBUST_BACKGROUND_DIRECTION**

The authorized redesign replaced fixed voxels with signed local Poisson-deviance fields evaluated at every observed meteor center and searched radii `{0.8,1.0,1.2}`. The same low-rank plus column-group-sparse background hypothesis was retained. GhostStream was excluded.

## Null behavior

- primary FPR: **0.023**;
- Wilson 95% interval: **[0.008, 0.067]**.

## Power failure

| Condition | robust sparse | strongest baseline |
|---|---:|---:|
| recurring sparse | 0.052 | 0.146 recurrent deviance |
| recurring moderate | 0.052 | 0.385 pooled deviance |
| intermittent | 0.000 | 0.042 recurrent deviance |
| late onset | 0.010 | 0.031 pooled deviance |
| diffuse recurring | 0.000 | 0.000 |
| drifting recurring | 0.000 | 0.031 |
| strong recurring | 0.010 | 0.906 recurrent raw |

Sparse recurring gain was **-0.094**, paired-bootstrap 95% **[-0.177, -0.021]**.

## Controls

- one-year-artifact acceptance: **0.021**;
- broad-ridge acceptance: **0.021**;
- M2026-A1: not accepted; primary score **0.000** versus threshold **0.276**, with no annual sparse support.

## Interpretation

The representation correction removed voxel quantization but did not restore power. The robust decomposition systematically classifies compact recurring stream evidence as low-rank background rather than sparse residual. This is intrinsic to the chosen low-rank plus column-group-sparse formulation, not a grid artifact.

The robust-background decomposition direction is therefore closed. No second representation redesign, lambda tuning, radius tuning, or GhostStream application is authorized.
