# Nested Core Atlas (NCA) v1

## Motivation

BWM, CMR, FOCR, DCR, and parent-anchored DCR established a consistent failure mode: smaller hard memberships can remove contamination, but substituting those memberships for the promoted support-pruned TopoModal + M2D parent destroys too much shower recall. PADCR additionally showed that restoring the exact promoted parent order does not solve the loss, so the remaining problem is representation rather than ranking.

NCA v1 therefore separates **discovery envelope** from **nested extraction structure**. It does not replace a promoted parent.

## Frozen GMN construction

For every exact promoted support-pruned parent in each target-excluded GMN development panel:

1. Preserve the parent `event_ids`, parent M2D score, and parent rank exactly. This parent is the only top-level discovery object and consumes exactly one candidate slot.
2. Reuse every already-frozen BWM seed belonging to that parent from the CMR v1 pretruth lineage.
3. Reuse the exact already-frozen one-shot CMR regrowth attached to each seed. Each branch is `BWM seed ⊆ CMR regrown core ⊆ promoted parent`.
4. Sort branches only within the parent by the inherited frozen CMR internal M2D descending, then membership hash. This local ordering cannot change the parent discovery rank or comparator capacity.
5. The first branch is exposed as a deterministic `primary` extraction view, but **all** branches remain part of the atlas. No branch is allowed to displace another top-level parent.

No new geometric scale, modularity run, affinity threshold, majority threshold, size cutoff, score blend, branch-count cap, or fitted parameter is introduced.

## Structural gate before GMN truth

The exact atlas must be sealed before the frozen GMN evaluator is allowed to open shower truth. Pretruth must verify:

- top-level parent identities/order are copied exactly;
- every seed/core containment invariant holds;
- nested structure is active;
- the primary CMR view has lower mean, p90, and maximum top-budget membership than the parent envelopes;
- the primary BWM seed view is smaller on mean than the primary CMR view;
- protected OrbitTrace information and SonotaCo truth were not accessed.

## GMN development evaluation

The flat literature benchmark continues to score only the exact parent envelopes under the byte-frozen PR #1377/BWM evaluator. NCA is required to reproduce promoted support-pruned metrics exactly and therefore preserve both published-config Sugar and HDBSCAN wins. Nested branches are not counted as extra flat candidate slots.

This is a representation qualification, not a claim that the child extraction itself has generalized. GMN 2022/2023 is development-exposed.

## Required next step

A GMN identity PASS authorizes **only** exact frozen transfer of the NCA construction to the SonotaCo common universe. SonotaCo candidate/core construction must seal before SonotaCo truth. Only after that external transfer may the already-revealed full-GMN OrbitTrace family be characterized. Any such target-containing run is post-reveal characterization, not a new blind rediscovery.
