# RFT v1 balanced sharded execution v2

Status: frozen engineering-only execution refinement before any v2 output. Scientific method changes: none.

Sharded v1 proved that independent frozen atom-bin work can complete durably, but the label-free prepared 2022 event counts exposed a severe execution imbalance under `bin_index mod 4`. Using the deterministic proxy `weight(bin)=event_count(bin)^2`, the four v1 shard loads were approximately 183M, 172M, 221M, and 412M.

v2 changes only which hosted runner computes each already-frozen 2° bin. It never splits a bin and never combines events across bins.

## Frozen assignment

From the exact normalized, target-excluded GMN 2022 event artifact produced by sharded-v1 run `31816118410` / artifact `9225100083`:

1. count events in every frozen RFT atom bin;
2. sort complete bins by `(-count^2, bin_index)`;
3. assign each complete bin in that order to the shard with the smallest current sum of `count^2`, breaking ties by shard index;
4. use exactly four shards.

This deterministic assignment is recomputed independently in every replica job from the unchanged base event coordinates. Frozen perturbation does not change the activity coordinate/bin identity.

The resulting base execution loads are approximately balanced at 247.35M, 247.34M, 247.34M, and 247.32M in the same proxy. This workload balancing uses no labels, truth, RFT score, candidate, or scientific outcome.

Everything after per-bin atom construction is identical to sharded v1: exact atom serialization, complete atom recombination per replica, unchanged frozen `build_tubes()` for both ownership modes, replica-number tube cache, and already-audited cached `generate_cached()`.

No RFT constant, distance, neighbor rule, component, medoid, transition, path ownership, perturbation, persistence, trimming, scoring, metric, ablation, threshold, or gate changes.

Firewall: GMN 2022 only; protected 20°–55° excluded; no GMN 2023, SonotaCo 2013/2014, OrbitTrace target data, MAARSY or DMS.
