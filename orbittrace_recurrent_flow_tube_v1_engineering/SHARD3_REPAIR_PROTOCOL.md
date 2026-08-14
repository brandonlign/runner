# RFT v1 targeted shard-3 execution repair

Status: frozen engineering fallback before any repair output. Scientific method changes: **none**. The activation condition is now satisfied: original sharded-v1 run `31816118410` job `94818490990` (`atoms (1,3)`) was cancelled by hosted-runner infrastructure after about 25 minutes with no Python exception and no atom artifact.

## Purpose

Sharded-v1 already preserves every successful atom artifact durably. Its original execution partition is `bin_index mod 4`. The failed shard is dominated by frozen bin 103 (15,017 events), so recomputing successful shard-0/1/2 work or merely repartitioning whole bins does not solve the actual bottleneck.

This repair reuses exact successful shard-0/1/2 atom artifacts from run `31816118410`, computes only the same complete original shard-3 bins, and uses the independently audited operation-preserving fast ordered `pair_d` implementation to remove Python/array overhead inside the unchanged atomizer.

## Exact repair partition

For the exact normalized target-excluded GMN 2022 event artifact `rft-sharded-input` from run `31816118410` / artifact `9225100083`:

1. select exactly the frozen atom bins satisfying `bin_index mod 4 == 3`;
2. count events in each such complete bin from the unperturbed normalized events;
3. sort those complete bins by `(-event_count^2, bin_index)`;
4. assign them greedily to exactly three repair pieces by smallest accumulated `event_count^2`, tie-breaking by piece index;
5. never split a frozen atom bin;
6. frozen perturbation replicas preserve `coord`, so this exact bin assignment is reused unchanged for replicas 0–16.

Each repair-piece job runs the same batched exact atomizer wrapper blob `8b8a9d373f908dbb32ac9a6b43addeaeb19bb8fa` with frozen RFT science blob `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`.

## Authorized exact ordered `pair_d` substitution

The repair may use only fast-pair source blob `5c6e914849a24bc2683c7e7e86e5f34f80834df4` under `FAST_PAIR_D_PROTOCOL.md` blob `f1447d13804fe373a54026dab4708dac1ad922f2`.

Independent zero-endpoint authorizer:
- run `31818476734`;
- job `94825741801`;
- artifact `9225971510`;
- artifact digest `sha256:700795c3b9ccc261639b5136f97882879cbd11830fec79fad57c4eb3fc4f9ad4`;
- verdict `PASS_RFT_V1_FAST_ORDERED_PAIR_D_EQUIVALENCE_AUDIT`;
- exact prepared events 315,024 across all 163 accessible bins;
- 110,954 deterministic ordered pair comparisons;
- zero original-vs-fast float mismatches;
- reverse-pair reuse remains forbidden.

The repair retains an ordered `(id(a),id(b))` value cache. No `(b,a)` reuse is permitted.

## Exact reconstruction

For each replica, the three repair pieces are merged into the exact original shard-3 atom set. The merge requires:
- piece bin sets are disjoint;
- their union equals every and only `bin_index mod 4 == 3` bin;
- atom IDs are unique;
- each atom's own `bin_index` belongs to the piece that produced it.

The reconstructed original shard-3 atom file is combined with the already-produced original shard-0/1/2 files, and unchanged frozen `build_tubes()` plus the already-audited cached downstream evaluator are used exactly as in sharded-v1.

No RFT constant, scientific distance formula, KNN rule, bin, graph, component, medoid rule, tube transition, ownership, perturbation, persistence, trimming, scoring, ablation, threshold, metric, or gate changes.

## Firewall

GMN 2022 only. Protected 20°–55° is already excluded in the immutable prepared input. No GMN 2023, SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY or DMS access.
