# Envelope Multi-Core Union (EMCU) v1

## Motivation

ECT v1 established that parent-preserving hierarchical extraction contains a real purity signal: its deterministic top CMR core raised paired precision on Sugar, HDBSCAN, d=128, and d=1024, but lost too much recall and therefore lowered paired F1 everywhere. The next question is whether that lost recall is distributed across the other already-frozen within-parent CMR modes.

EMCU v1 makes one exact change from ECT: the extraction view is the **set union of every already-frozen CMR regrown branch belonging to the parent**, rather than the single highest-M2D branch.

## Frozen method

For each exact promoted support-pruned TopoModal + M2D parent:

1. Preserve the parent `event_ids`, parent M2D score, and parent rank exactly. The parent remains the sole top-level discovery envelope and consumes one candidate slot.
2. Take all CMR v1 candidates from sealed pretruth SHA-256 `8b77e80f305c6f47fc70b359bf03ebadcd6263b5d5ee6a6b9c30efda658bffcb` whose `cmr_parent_family_hash` equals this parent.
3. Define the extraction membership as the ordinary set union of those frozen CMR `event_ids`.
4. The union cannot recruit any new event and must remain a subset of the parent.
5. No child rank, child score, branch count, or size enters the union rule. Every frozen branch contributes equally by membership inclusion.

There is no new geometric scale, modularity run, regrowth rule, threshold, coefficient, size cutoff, branch cap, target-derived parameter, or post-result selection.

## Pretruth structural gate

Before GMN truth, the exact envelope/union catalogue must be sealed and must verify:

- envelope memberships and order are exactly the promoted support-pruned catalogue;
- every union is nonempty, support >=4, and contained in its envelope;
- at least one top-budget envelope is strictly shrunk;
- pooled top-budget extraction mean, p90, and maximum member counts are all strictly below the envelopes;
- protected OrbitTrace information and SonotaCo truth were not accessed.

## Binding GMN development evaluation

Use the exact byte-frozen ECT paired evaluator from PR #1391 semantics.

- Flat literature comparison scores **envelopes only** and must reproduce support-pruned TopoModal + M2D exactly, preserving all ten established literature gates.
- For extraction utility, perform the unchanged envelope Hungarian assignment first.
- Consider only envelope assignments with `F1 > 0.5`.
- Evaluate the EMCU extraction against that same assigned shower label; no rematching is allowed.
- On Sugar, HDBSCAN, d=128, and d=1024, extraction must have strictly higher paired precision and nonlower paired F1 than the envelopes.

GMN 2022/2023 is development-exposed. A PASS authorizes exact frozen SonotaCo transfer only. A FAIL freezes EMCU v1; no subset-of-branches, vote-count, overlap-count, branch-score, or size-threshold rescue sweep is authorized.

OrbitTrace protected `[20°,55°]` events/canonical IDs/coordinates, the revealed target family, SonotaCo truth, and external-survey truth are prohibited during construction. Any later target-containing full-GMN run is characterization only.
