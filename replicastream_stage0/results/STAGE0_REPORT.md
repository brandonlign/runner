# ReplicaStream Stage-0 result

**Verdict:** `KILL_OR_REDESIGN_REPLICASTREAM`

This is a frozen kill test of an empirically calibrated partial-conjunction order-statistic detector. It is not a GhostStream result and was not applied to GhostStream.

## Weak-signal comparison (4 and 6 meteors per active year)

- Pooled recurrent recovery: 0.720
- ReplicaStream recurrent recovery: 0.660
- Pooled one-year-artifact detection: 0.640
- Pooled-plus-annual-confirmation recurrent recovery: 0.860
- Pooled-plus-annual-confirmation artifact detection: 0.140
- ReplicaStream one-year-artifact detection: 0.000
- Replicability-margin gain versus best baseline: -0.060
- ReplicaStream shared-structure null FWER: 0.560

## Frozen gates

- PASS — `ideal_null_fwer_at_most_0_15`
- FAIL — `weak_recurrent_power_loss_vs_best_baseline_at_most_0_10`
- PASS — `weak_transient_detection_at_most_0_20`
- FAIL — `shared_structure_null_fwer_at_most_0_20`
- FAIL — `replicability_margin_gain_vs_best_baseline_at_least_0_15`
- PASS — `strong_recurrent_power_no_material_collapse_vs_best_baseline`

## Interpretation

The method is useful only if it preserves recurrent weak-stream power while rejecting equally strong one-year concentrations that can fool a stacked virtual-year search and remains calibrated under a common smooth annual observing artifact. Passing Stage 0 permits a parent-shower-disjoint benchmark and comparison against held-out-year confirmation; it does not establish novelty or justify applying the method to GhostStream.
