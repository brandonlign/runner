# RFT v1 targeted shard-3 execution repair

Status: frozen engineering fallback before any repair output. Scientific method changes: **none**. Do not activate unless the original sharded-v1 run `31816118410` fails because one or more `bin_index mod 4 == 3` atom jobs do not complete.

## Purpose

Sharded-v1 already preserves every successful atom artifact durably. Its original execution partition is `bin_index mod 4`. If only shard 3 exceeds hosted-runner limits, recomputing the successful shards would add cost without scientific value.

This repair therefore reuses exact successful shard-0/1/2 atom artifacts from run `31816118410` and replaces only the execution scheduling of the same complete shard-3 bins.

## Exact repair partition

For the exact normalized target-excluded GMN 2022 event artifact `rft-sharded-input` from run `31816118410` / artifact `9225100083`:

1. select exactly the frozen atom bins satisfying `bin_index mod 4 == 3`;
2. count events in each such complete bin from the unperturbed normalized events;
3. sort those complete bins by `(-event_count^2, bin_index)`;
4. assign them greedily to exactly three repair pieces by smallest accumulated `event_count^2`, tie-breaking by piece index;
5. never split a frozen atom bin;
6. frozen perturbation replicas preserve `coord`, so this exact bin assignment is reused unchanged for replicas 0–16.

Each repair-piece job runs the same batched exact atomizer wrapper blob `8b8a9d373f908dbb32ac9a6b43addeaeb19bb8fa` with the frozen RFT science blob `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`.

For each replica, the three repair pieces are merged into the exact original shard-3 atom set. The merge requires:
- piece bin sets are disjoint;
- their union equals every and only `bin_index mod 4 == 3` bin;
- atom IDs are unique;
- each atom's own `bin_index` belongs to the piece that produced it.

The reconstructed original shard-3 atom file is then combined with the already-produced original shard-0/1/2 files, and unchanged frozen `build_tubes()` plus the already-audited cached downstream evaluator are used exactly as in sharded-v1.

No RFT constant, distance, KNN rule, bin, graph, component, medoid, tube transition, ownership, perturbation, persistence, trimming, scoring, ablation, threshold, metric, or gate changes.

## Firewall

GMN 2022 only. Protected 20°–55° is already excluded in the immutable prepared input. No GMN 2023, SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY or DMS access.
