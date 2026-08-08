# OrbitTrace exact-rescore fanout v3 — work-unit performance layer

## Scope

Infrastructure/source freeze only. This layer changes no detector score, calibration, proposal, membership, component, recurrence, family, ranking, gate, event row, target exclusion, or truth access. It exists only to remove the residual straggler observed in fanout v2 when one very expensive exact-rescore center dominates an otherwise proposal-count-balanced shard.

## Reused immutable boundary

V3 begins from the exact fanout-v2 preexact checkpoint. Therefore it inherits:

- the exact repaired catalogue-v6 source identity;
- target-excluded scan/calibration row hashes;
- immutable ordered center list;
- immutable per-center proposal records and record hashes;
- immutable per-center window event IDs and hashes;
- no hidden known-shower labels in the checkpoint.

No v3 stage regenerates proposals or changes a center window.

## Work-unit rule

For each center, split its already-frozen ordered proposal-record list into contiguous slices of at most **512 records**. The 512-record boundary is execution-only and cannot affect scientific output: every slice is passed to the unchanged `exact_rescore_window_v6` with the complete original center event window, and slices are concatenated back in exact original record order before replay.

The deterministic scheduling cost proxy is:

`slice_record_count × center_window_event_count`.

This is label-free and uses only preexact checkpoint structure. It more closely tracks the dominant pairwise exact-rescore work than proposal count alone.

Work units are assigned to independent shards by deterministic longest-processing-time greedy scheduling, with ties by center, slice start, then shard index. Shard assignment may change wall-clock time only.

## Integrity requirements

Every execution must prove:

1. exact preexact checkpoint SHA sidecar passes;
2. repaired-source SHA equals the preexact identity;
3. scan/calibration row hashes exactly match preexact;
4. target interval 20°–55° remains absent;
5. every center's complete frozen proposal list and event-window hashes match;
6. every work unit is a contiguous exact slice, with no gap/overlap and full center coverage;
7. every slice output preserves proposal-anchor order exactly;
8. all expected work-unit shards are present exactly once;
9. concatenated per-center outputs preserve the complete original proposal-anchor order exactly;
10. no labels are evaluated during work-unit execution or combination.

## Replay boundary

The combiner emits one synthetic `orbittrace-v6-exact-center-shard-v2` payload containing the complete reconstructed `exact_by_center` map. The already source-audited fanout-v2 `replay_exact_year.py` then consumes this payload unchanged. This intentionally avoids creating a second implementation of scientific year replay.

## Scientific equivalence

The only admissible claim is execution equivalence: v3 must call the exact original scientific exact-rescore function on a partition of the same ordered records and reconstruct the identical center-wise output order before the immutable v2 replay. Any mismatch is an infrastructure failure and yields no scientific result.

No target-containing execution is authorized by this branch.