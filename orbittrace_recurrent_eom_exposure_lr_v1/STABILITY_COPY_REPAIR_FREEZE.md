# Exposure-likelihood recurrent-EOM v1 — stability-copy repair freeze

## Classification of first activation

Workflow run `31893198240`, artifact `9249207235`, stopped before `RECURRENT_EOM_EXPOSURE_LR_V1_PRELABEL.json` or `RECURRENT_EOM_EXPOSURE_LR_V1_GMN_DEVELOPMENT.json` existed.

All source pins, synthetic likelihood-ratio audit, exact binding recurrent-EOM evidence, target-excluded event counts, and fresh recurrent-parent HDBSCAN reproduction passed. The runner then computed the exposure-weighted stability and called the exact HDBSCAN `get_clusters` pathway through `eom_labels`. It stopped while constructing provenance candidates with:

`RuntimeError: compact exposure-LR labels do not map to selected nodes`

No shower-truth evaluation or scientific verdict occurred.

## Root cause

HDBSCAN 0.8.43's `get_clusters` EOM implementation performs dynamic programming by mutating the supplied stability dictionary in place when child-subtree stability exceeds a node's original scalar stability. The frozen OrbitTrace helper `selected_eom_nodes` is a pure-Python mirror intended to start from the **original** scalar stability field, but the failed runner called it only after the same dictionary had already been passed to `eom_labels` / `get_clusters`.

This ordering was harmless for the promoted recurrent-EOM parent but becomes material when the exposure-likelihood weight makes many node stabilities extremely small or exactly zero. The HDBSCAN scientific label extraction itself is authoritative and had already run; the later provenance helper was operating on a mutated dynamic-programming dictionary.

This is an engineering/provenance call-order error, not an exposure-model outcome. The first activation is a technical no-result.

## Exact authorized repair

The original frozen scientific runner blob remains preserved. The clean-retry wrapper may replace exactly this two-line sequence:

```python
successor_labels = eom_labels(tree, exposure_stability)
successor_nodes = selected_eom_nodes(tree, exposure_stability)
```

with:

```python
successor_nodes = selected_eom_nodes(tree, dict(exposure_stability))
successor_labels = eom_labels(tree, dict(exposure_stability))
```

The two copies ensure:

1. provenance node selection sees the original frozen `E_exp` scalar field;
2. HDBSCAN receives the same original scalar field and may perform its normal in-place EOM dynamic programming without altering provenance inputs.

No exposure likelihood, global exposure probability, descendant count, hierarchy, HDBSCAN setting, recurrent stability, EOM comparison, label assignment, candidate ranking, metric, gate, dataset, or scientific threshold changes.

The wrapper must assert the old sequence occurs exactly once and make no other text change. The first technically valid clean-retry GMN result remains binding under the original protocol.