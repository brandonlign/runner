# Stream-tube Stage-0 result

**Verdict:** `KILL_OR_REDESIGN_STREAM_TUBE`

This is a coarse kill test of a physically constrained drifting stream-tube matched-filter bank. It is not a final GhostStream method and was not applied to GhostStream.

## Main comparison

- Static weak-stream recovery (k=6,8 average): 0.450
- Drift-tube weak-stream recovery (k=6,8 average): 0.500
- Weak-stream gain: +0.050
- Static strong-stream recovery (k=12,20 average): 0.475
- Drift-tube strong-stream recovery (k=12,20 average): 0.575

## Error control

- Drift-tube ideal-null probability of any false detection: 0.050
- Drift-tube sharp-null-mismatch probability of any false detection: 1.000

## Frozen gates

- PASS — `ideal_null_fwer_at_most_0_15`
- FAIL — `weak_recovery_gain_at_least_0_10`
- PASS — `strong_recovery_no_material_collapse`
- FAIL — `mismatch_fwer_at_most_0_20`

## Interpretation

Continuation requires a material recovery gain at matched catalog-level false-alarm control, no collapse for stronger streams, and robustness to a sharper-than-calibration sporadic background. Any failed gate means the present formulation is not suitable for GhostStream and must be killed or redesigned before further work.
