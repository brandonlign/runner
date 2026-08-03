# Simulation-calibrated common-origin Stage-0 surrogate

**Decision:** `KILL_OR_REDESIGN_COMMON_ORIGIN_METRIC`

## Frozen central result

- Learned TPR at matched 1% FPR: **0.856**
- Best baseline TPR at matched 1% FPR: **0.967**
- Pair TPR gain: **-0.111**
- Learned weak-stream recovery (k=4,6,8): **0.000**
- Best baseline weak-stream recovery: **0.058**
- Weak-stream recovery gain: **-0.058**
- Expected calibration error: **0.117**
- FPR after transferring the calibration threshold to unseen parents: **0.592**

## Gates

- `pair_tpr_gain_at_1pct_fpr_at_least_0.05`: **False**
- `weak_stream_recovery_gain_at_least_0.10`: **False**
- `ece_at_most_0.10`: **False**
- `calibration_threshold_transfer_fpr_at_most_0.03`: **False**
- `no_collapse_across_noise_sensitivity`: **False**

## Pair benchmark by method

| Method | TPR | FPR | Precision |
|---|---:|---:|---:|
| d_sh | 0.967 | 0.010 | 0.990 |
| d_d | 0.967 | 0.010 | 0.990 |
| d_n | 0.949 | 0.010 | 0.989 |
| geo_std | 0.868 | 0.010 | 0.988 |
| orbit_std | 0.942 | 0.010 | 0.989 |
| learned | 0.856 | 0.008 | 0.990 |

## Interpretation boundary

This is an empirical orbit-perturbation surrogate based on published mean shower solutions and literature-proposed parent associations. It is not a broad forward N-body stream simulation, does not prove parentage, and cannot by itself support a novelty or physical calibration claim.

The learned score did not clear the frozen surrogate gates. Do not attach it to GhostStream or invest in a full dynamical simulator without a separately justified redesign.
