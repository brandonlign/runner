# Robust background-decomposition Stage 0

Verdict: **KILL_OR_REDESIGN_ROBUST_BACKGROUND_DECOMPOSITION**

The primary method decomposes the seven-year phase-space count matrix into a low-rank background and a column-group-sparse residual. GhostStream was excluded.

## Null behavior

| Method | FPR | Wilson 95% |
|---|---:|---|
| robust_group_sparse | 0.039 | [0.016798610797803704, 0.08818702076683686] |
| pooled_raw | 0.062 | [0.03200692569506119, 0.11848791104425865] |
| recurrent_raw | 0.055 | [0.026740201381346355, 0.10858490029974707] |
| median_residual | 0.070 | [0.03742976830393997, 0.12823480349360633] |
| svd_residual | 0.117 | [0.07231682349355734, 0.18436615865334754] |

## Recovery and artifact acceptance

| Condition | robust sparse | pooled raw | recurrent raw | median residual | SVD residual |
|---|---:|---:|---:|---:|---:|
| recurring_sparse | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| recurring_moderate | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| intermittent | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| late_onset | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| diffuse_recurring | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| drifting_recurring | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| strong_recurring | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| one_year_artifact | 0.104 | 0.031 | 0.021 | 0.104 | 0.135 |
| broad_recurring_ridge | 0.010 | 0.250 | 0.229 | 0.198 | 0.302 |

## Sparse recurring comparison

- primary recovery: 0.000
- strongest baseline: `pooled_raw` at 0.000
- paired gain: 0.000
- paired-bootstrap 95%: [0.0, 0.0]

## Frozen gates

- PASS — `null_rate_le_0_10`
- PASS — `null_wilson_upper_le_0_15`
- FAIL — `sparse_gain_ge_0_10`
- FAIL — `sparse_bootstrap_lower_gt_0`
- FAIL — `moderate_recovery_ge_0_70`
- FAIL — `intermittent_recovery_ge_0_40`
- FAIL — `late_recovery_ge_0_40`
- FAIL — `diffuse_recovery_ge_0_35`
- FAIL — `drifting_recovery_ge_0_40`
- FAIL — `strong_recovery_ge_0_90`
- FAIL — `artifact_acceptance_le_0_10`
- PASS — `ridge_acceptance_le_0_15`
- FAIL — `m2026_accepted_near_reference`
- PASS — `every_recurring_condition_not_inferior_by_0_10`

## External M2026-A1 control

- accepted: False
- near reference: False
- distance: 9.071
- score / threshold: 0.314 / 2.131
- annual support: 4