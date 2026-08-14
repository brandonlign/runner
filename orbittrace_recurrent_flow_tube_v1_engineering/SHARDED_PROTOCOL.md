# RFT v1 sharded execution protocol

Status: frozen engineering execution plan before any sharded output. Scientific method changes: **none**.

The frozen RFT v1 source remains Git blob `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`; cached downstream evaluator remains blob `2a599c6e8247eb819a1090591d586526eda6c0c1`; batched exact atomizer wrapper remains blob `8b8a9d373f908dbb32ac9a6b43addeaeb19bb8fa`.

## Reason

Repeated monolithic hosted-runner attempts are receiving infrastructure shutdown signals after about eight minutes, before a replica completes. RFT's frozen construction is naturally separable:

- `atoms()` never links events across its fixed 2° solar-longitude bins;
- perturbation replicas 0–16 are independent until persistence comparison;
- `build_tubes()` consumes only the complete atom list for one replica;
- the four frozen evaluations consume the same replica tube cache.

## Exact map/reduce execution

1. Parse and normalize the exact target-excluded GMN 2022 catalogue once using the frozen runtime. Preserve normalized events and hidden 2022 labels as an intermediate execution artifact. No scientific endpoint is computed.
2. For each frozen replica `r=0..16`, construct the exact replica event rows (`r=0` unchanged; `r>0` exact frozen `perturb(events,r)`).
3. Partition only by frozen atom-bin identity: `bin_index mod 4`. Each event belongs to exactly one of four execution shards. Because frozen atomization has no cross-bin edges, calling the exact batched atomizer on a shard is equivalent to calling it on the whole replica and retaining those bins.
4. Recombine the four atom shards for each replica. Require exactly one record per atom ID. Reconstruct frozen `Atom` objects and call the **unchanged frozen** `build_tubes()` twice (`ownership=True/False`). Serialize exact tube fields.
5. Recombine the 17 replica tube artifacts in replica-number order. Call the already-audited cached `generate_cached()` for the exact four preregistered modes and then the unchanged frozen metrics/viability logic.

No threshold, metric, distance, KNN, bin width, component rule, medoid rule, transition, ownership, perturbation, persistence, trim, score, candidate rule, ablation, or gate changes.

## Execution invariants

- replica set exactly `0..16`;
- shard set exactly `0..3`;
- each normalized event appears in exactly one atom shard for each replica by fixed bin modulo;
- combined atom IDs unique within each replica;
- tube construction receives every atom from all four shards and no other atom;
- final tube cache contains exactly both ownership modes for every replica;
- final evaluation uses exact cached-generate blob `2a599c...`, whose downstream semantics passed independent audit run `31815566243` / artifact `9224847857`;
- sharded output remains engineering/non-authoritative until atomization equivalence and execution provenance are accepted.

## Firewall

GMN 2022 only. Protected 20°–55° excluded before intermediate events. GMN 2023, SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY and DMS inaccessible.
