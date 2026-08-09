# OrbitTrace v6 exact-rescore fanout v2

Implementation-only performance architecture. No detector science may change.

## Exact decomposition

The immutable repaired `scan_year_v6` has a strict phase boundary: it completes calibration, all 72 proposal windows, cross-window anchor deduplication, and construction of `records_by_center` before calling `exact_rescore_window_v6` for each center. Downstream p-values, channel selection, caps, components, family construction, evaluation, gates and verdict occur after exact outputs exist.

Fanout v2 exploits only that boundary:

1. **Preexact capture** calls the original repaired `scan_year_v6` and monkeypatches only `exact_rescore_window_v6` to capture its already-deduplicated exact inputs `(records, ordered window event IDs)` per center. The capture returns no scored records and its downstream empty result is discarded. No labels or scientific verdict are saved.
2. **Exact center shards** reconstruct the exact target-excluded scan, verify its canonical row hash, reconstruct each captured window in the identical event order, and call the original repaired `exact_rescore_window_v6`. The already-proven contiguous multiprocessing wrapper may execute that immutable scalar function within a shard.
3. **Year replay** calls the original repaired `scan_year_v6` again. Its exact-rescore call is replaced only by a strict replay function. The replay requires identical ordered window-event IDs and identical ordered scientific proposal identity `(proposal_anchor_id, bin, window_center)` before returning the previously computed exact output. Full proposal-record byte equality remains diagnostic but is not a scientific gate because source inspection proves the remaining proposal-stage fields are overwritten by exact rescoring or are non-scientific diagnostics. Saved exact outputs must carry the same scientific proposal identity and may be realigned only by unique immutable proposal-anchor ID if deserialized ordering differs.
4. The resulting normal per-year checkpoints feed the already-audited cross-year checkpoint replay, where the unchanged repaired `main()` performs recurrent-family construction, evaluation, gates and verdict.

## Technical replay repair chronology

The first authoritative 2022 replay attempt failed before any year checkpoint, family construction, label evaluation, gate, or scientific verdict because the replay required canonical equality of the entire proposal dictionaries. All 72 proposal windows had reproduced the same event/scored/selected/global counts before that failure. The 2023 replay completed successfully.

Before retrying 2022, the frozen source was inspected rather than weakening any scientific identity requirement. Exact `exact_rescore_window_v6` obtains geometry from the immutable window/event lookup and consumes `proposal_anchor_id` from each proposal record; it overwrites proposal Brown score, fixed4 score, v3 score, v3 representative/top anchors, v3 members, proposal members, and the exact-rescore flag. Frozen post-exact adjudication uses the exact output's `bin` plus exact scores/members and proposal-anchor ID for deterministic ties. Therefore the replay now fails closed on any change to ordered `(proposal_anchor_id, bin, window_center)` or window-event IDs, while merely recording byte drift in overwritten proposal-stage diagnostic fields. This correction was made after a technical no-result only and changes no scientific value, ordering, score, member assignment, threshold, calibration, recurrence, family, ranking, or gate.

## Integrity requirements

- Frozen v6 source SHA-256 remains `a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9`.
- Repaired source remains the exact reversible two-line component-construction repair with SHA-256 `257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24`.
- Proposal cap remains 512/window and annual primary proposal budget 36,864/year.
- No proposal, distance, score, threshold, tie rule, member rule, recurrence rule, ranking or gate is reimplemented in the exact shard stage.
- Exact outputs must cover the exact captured proposal-anchor set and be returned in current scientific proposal order.
- Solar longitude 20°–55° remains excluded before all stages; hidden labels are never serialized into preexact/exact/year checkpoints.
- Any mismatch in source, scan rows, calibration rows, ordered scientific proposal identity, window-event order, shard coverage or replay order is a technical failure, not a scientific result.

This branch does not authorize a target-containing run.
