# Exposure-likelihood recurrent-EOM v1 — HDBSCAN label-map repair freeze

## Classification of clean retry #2

Workflow run `31893573442`, artifact `9249235489`, stopped before either `RECURRENT_EOM_EXPOSURE_LR_V1_PRELABEL.json` or `RECURRENT_EOM_EXPOSURE_LR_V1_GMN_DEVELOPMENT.json` existed.

The exact scientific protocol/implementation, zero-truth exposure-likelihood audit, target-excluded event counts, binding recurrent-EOM artifact hashes, fresh recurrent-parent selected nodes, and complete 2,097 recurrent parent candidates all passed. The previously frozen stability-copy repair also executed exactly. The run then stopped during **successor output provenance construction** with:

`RuntimeError: compact exposure-LR labels do not map to selected nodes`

No successor prelabel catalogue was persisted, no shower-truth metrics were evaluated, and no scientific PASS/FAIL verdict was produced. Run `31893573442` is therefore a technical no-result.

## Root cause

HDBSCAN 0.8.43 creates its flat-cluster label map from the EOM-selected cluster IDs as:

`cluster_map = {c: n for n, c in enumerate(sorted(list(clusters)))}`

and then labels points through that map. The authoritative flat label integer therefore indexes the **sorted EOM-selected-node list**. A selected internal node can nevertheless receive no final data-point label after HDBSCAN's labelling logic, so the set of observed nonnegative labels need not equal the complete contiguous range `0..len(selected_nodes)-1`.

The frozen successor runner incorrectly asserted that every EOM-selected node must appear as a nonempty final flat cluster. That assertion is a provenance/output-construction assumption, not part of the exposure-likelihood scientific method or HDBSCAN's label assignment.

## Exact authorized repair

The original frozen scientific runner blob `649403c547d6854b26bbd772076974b80eea77b9` remains preserved.

A clean-retry wrapper may make exactly two mechanical repairs to an in-memory runtime copy:

### Repair A — already frozen stability-copy ordering

Replace exactly:

```python
successor_labels = eom_labels(tree, exposure_stability)
successor_nodes = selected_eom_nodes(tree, exposure_stability)
```

with:

```python
successor_nodes = selected_eom_nodes(tree, dict(exposure_stability))
successor_labels = eom_labels(tree, dict(exposure_stability))
```

### Repair B — authoritative HDBSCAN label-to-node mapping

In `make_successor_candidates`, replace the assumption that observed labels equal all contiguous selected-node indices with the following output construction:

1. require `nodes` to be sorted ascending, matching HDBSCAN's `cluster_map` construction;
2. compute the sorted set of observed nonnegative flat labels;
3. require every observed label `lab` to satisfy `0 <= lab < len(nodes)`;
4. map each observed label to `node = nodes[lab]`;
5. create a candidate only for those observed labels, using exactly the events for which authoritative HDBSCAN output `labels == lab`;
6. preserve every raw EOM-selected node separately in the prelabel `successor_selected_nodes` provenance field, even if it receives no final flat-cluster events.

No synthetic candidate is created for an unobserved selected node. No point label is changed. No cluster node is added, removed, merged, or split by the repair. The candidate catalogue is simply the nonempty flat-cluster output already emitted by HDBSCAN.

The repair must not alter:

- the global-exposure probability;
- node annual descendant counts;
- Bernoulli likelihood ratio or KL divergence;
- `W_exp` or `E_exp`;
- HDBSCAN hierarchy/settings;
- EOM dynamic-programming comparisons;
- authoritative `eom_labels` output;
- recurrent-EOM parent reconstruction;
- successor ranking keys;
- evaluation metrics or frozen promotion gate;
- any dataset, truth, feature, or threshold.

The wrapper must assert every authorized source fragment occurs exactly once and make no other textual change. The first technically valid clean-retry result after this repair remains the binding scientific endpoint under the original protocol blob `99073e4605122922599076a6d7464093df118123`.