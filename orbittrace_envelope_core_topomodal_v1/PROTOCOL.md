# Envelope-Core TopoModal (ECT) v1

## Why this architecture exists

BWM, CMR, FOCR, DCR, and PADCR establish a consistent failure pattern: hard refinement can make support-pruned families much smaller, but replacing the promoted family with a refined child loses true shower members. PADCR isolated this cleanly by restoring the exact support-pruned discovery ordering while keeping DCR memberships frozen: Sugar precision stayed essentially unchanged while recall fell materially. A single flat membership is therefore being asked to do two incompatible jobs—detect a complete shower and provide a high-purity extraction.

ECT v1 separates those jobs without changing the promoted benchmark method.

- **Detection envelope:** the exact promoted support-pruned TopoModal + M₂D parent membership and exact M₂D ordering.
- **Extraction core:** one deterministic nested core chosen from the already-frozen CMR catalogue inside that parent: highest exact CMR M₂D, tie by membership hash.
- The core never replaces, reranks, or changes the envelope.

This architecture is designed after the target-excluded GMN BWM/CMR/FOCR/DCR/PADCR development results. GMN 2022/2023 is exposed development evidence. OrbitTrace protected `[20°,55°]` events/canonical IDs/coordinates, the revealed target family, SonotaCo truth, and external-survey truth remain prohibited from construction.

## Frozen label-free construction

For each promoted support-pruned parent in the eight exact GMN sparse panels:

1. Preserve the parent event membership and promoted M₂D rank exactly.
2. Collect the already-frozen CMR v1 children whose frozen parent hash equals that parent.
3. Select exactly one nested core by highest exact CMR internal M₂D; break an exact score tie by core membership hash.
4. Require the core to be a subset of its envelope.
5. Emit a hierarchical candidate containing both `event_ids` (envelope) and `core_event_ids` (nested core).

No new geometric scale, modularity pass, growth rule, affinity threshold, size cutoff, score coefficient, target-derived parameter, or rescue search is introduced.

## Structural gate before hidden GMN extraction truth

The exact hierarchical catalogue is sealed before the core-utility truth test. The nested cores must be active and strictly reduce mean, p90, maximum, and size-biased top-budget family burden relative to their unchanged envelopes. Failure stops the truth job.

## Flat literature benchmark remains unchanged

The byte-frozen BWM/PR #1377 evaluator is run on the **envelopes only** through a membership-preserving compatibility projection. Because envelope memberships and ordering are exact support-pruned v1, every inherited route/scale metric must equal the promoted support-pruned baseline byte-for-byte at the metric level, and all ten inherited literature gates must pass. This is preservation of the existing flagship benchmark result, not a new flat-clustering win by the core.

## Paired extraction-core test

After the hierarchical catalogue is sealed, open the same target-excluded GMN development truth. For every panel/year/comparator capacity:

1. Perform the exact Hungarian assignment on the unchanged envelope F1 matrix.
2. Use the existing `F1 > 0.5` recovery threshold; no new recovery threshold is introduced.
3. For each recovered envelope-label assignment, evaluate the nested core against the **same assigned shower label**. The core is not allowed to rematch itself to a different shower.
4. Aggregate paired envelope/core precision, recall, and F1 for Sugar, HDBSCAN, d=128, and d=1024.

Binding core gates require, on each route and scale, both:

- strictly higher mean paired precision for the core than the envelope; and
- nonlower mean paired F1 for the core than the envelope.

This prevents a tiny-core purity trick: the core must become cleaner without reducing balanced extraction quality on already-recovered showers.

## Interpretation boundary

A GMN pass is development qualification only. The exact frozen hierarchical method must transfer to a non-GMN endpoint before any generalization claim. Only after successful frozen transfer may a full-GMN OrbitTrace run be used for characterization; it cannot be used to tune core selection or claim a newly blind rediscovery.
