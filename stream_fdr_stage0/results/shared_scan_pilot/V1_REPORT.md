# Shared-support surrogate pilot v1

Authoritative runner workflow: `30842040756`

Artifact: `shared-support-stage0-surrogate` (`8867191188`)

Artifact digest: `sha256:bc7bb6026234ed7d02d7483eeff292e057ba2201192ce2d789f5091468c3e35e`

## Verdict

**KILL_OR_REDESIGN_SHARED_NETWORK_FORMULATION**

The frozen primary score was the leave-one-network-out sum of network-specific Poisson excess evidence. GhostStream was excluded.

## Central radius 1.0

| Method | Null FPR | Balanced recovery | Heterogeneous recovery | Three-network recovery | GMN-only acceptance | Strong recovery |
|---|---:|---:|---:|---:|---:|---:|
| shared_loo | 0.056 | 0.906 | 0.844 | 0.750 | 0.031 | 1.000 |
| pooled | 0.000 | 0.750 | 0.656 | 0.469 | 0.094 | 0.969 |
| max_network | 0.056 | 0.000 | 0.062 | 0.000 | 0.906 | 0.875 |
| second_network | 0.000 | 0.031 | 0.000 | 0.062 | 0.031 | 0.906 |
| shared_sum | 0.028 | 0.719 | 0.719 | 0.656 | 0.156 | 0.969 |

The primary method passed the false-positive, weak-signal gain, single-network-artifact, strong-signal, and external-control gates.

## Failure

The alternate-scale stability gate failed. Primary recovery changed as follows:

| Radius | Balanced | Heterogeneous | Three-network | GMN-only acceptance |
|---|---:|---:|---:|---:|
| 0.8 | 0.969 | 1.000 | 1.000 | 0.000 |
| 1.0 | 0.906 | 0.844 | 0.750 | 0.000 located / 0.031 accepted |
| 1.2 | 0.438 | 0.562 | 0.031 | 0.000 |

Worst frozen alternate-radius drop: **0.406**, exceeding the allowed 0.20.

## External control

At radius 1.0, the primary method accepted the untouched M2026-A1 control. Its top component was 0.426 standardized units from the published reference; score 31.019 versus threshold 19.621.

## Interpretation

The cross-network evidence hypothesis remains plausible, but a fixed-radius formulation is not robust enough. The only permitted redesign is a prespecified multiscale scan whose null calibration includes the complete scale search. Selecting radius 0.8 or 1.0 after observing these results is prohibited.
