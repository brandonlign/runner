# PhysCore-HDBSCAN v1 — frozen matched-literature characterization

## Purpose

Characterize the already-frozen `PASS_PHYSCORE_HDBSCAN_V1_DEVELOPMENT` method against the two remaining representative literature families already used by OrbitTrace: Sugar uncertainty-aware DBSCAN and Rudawska-Jenniskens D_SH single linkage.

This protocol does not alter PhysCore-HDBSCAN v1. The direct exact published-HDBSCAN superiority result from workflow `31988198562` remains binding and separate.

## Frozen method transfer

For each comparator/year pair, run the exact archived published catalogue-HDBSCAN source (`a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2`, HDBSCAN 0.8.44, min_cluster_size/min_samples 100, Euclidean EOM) on that comparator's exact already-frozen pairwise row universe. Then apply the exact PhysCore v1 physical-core rule from `orbittrace_physcore_hdbscan_v1/run_pretruth.py` without changing any scientific constant or logic.

The transfer adapter may remove only the original direct-test assertion that parent family count must equal 11/9, because other pairwise row universes naturally yield different published-HDBSCAN family counts. Before any new truth is opened, the adapter must reproduce the frozen direct PhysCore 2013/2014 memberships exactly on the original HDBSCAN row universes.

PhysCore family order remains the exact parent HDBSCAN native-family order. It emits exactly one refined family per parent family.

## Comparators

Use already-frozen outputs:
- Sugar 2013/2014 from workflow `31984184708` (`orbittrace-topomodal-literature-sugar-*-v1-r3`);
- D_SH 2013/2014 from workflow `31984080540` (`orbittrace-topomodal-literature-dsh-*-v1-r2`).

No literature parameter may be changed.

## Matched evaluation

For each pair/year, let `B` be the literature comparator's frozen natural family count. Evaluate the first `min(B, N_physcore)` frozen PhysCore families against all `B` literature families using the exact same eligible-known-shower definition (native mapped shower support >=4), Hungarian one-to-one F1, macro-F1, and recovered-shower count at F1>0.5 used in the prior flagship matched-literature benchmark.

This preserves the established comparator-defined reporting budget. If PhysCore naturally emits fewer than `B` families, no synthetic or duplicated candidates are added.

A panel is a WIN only if PhysCore macro-F1 is strictly greater than the literature comparator and PhysCore recovered F1>0.5 is at least the literature count.

`PASS_PHYSCORE_MATCHED_LITERATURE_V1` requires all four Sugar/D_SH year panels to be WIN. The already-binding direct published-HDBSCAN 2/2 PASS is reported alongside, but is not rerun or reinterpreted here.

## Pretruth firewall

Before truth:
- exact rows, exact published-HDBSCAN parent outputs, exact PhysCore transfer outputs, exact Sugar/D_SH outputs, source hashes, and candidate order are frozen;
- transfer equivalence on the original HDBSCAN pairwise universes passes exactly;
- protected `[20°,55°]` remains absent;
- no truth-bearing field is accepted by candidate generation.

The first technically valid outcome is binding. No method, order, budget, comparator, metric, mapping, threshold, or panel may be changed in response to the result.

SonotaCo 2013/2014 remains EXPOSED DEVELOPMENT ONLY. OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.
