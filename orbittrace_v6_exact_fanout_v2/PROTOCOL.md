# OrbitTrace v6 exact-rescore fanout v2

Implementation-only performance architecture. No detector science may change.

## Exact decomposition

The immutable repaired `scan_year_v6` has a strict phase boundary: it completes calibration, all 72 proposal windows, cross-window anchor deduplication, and construction of `records_by_center` before calling `exact_rescore_window_v6` for each center. Downstream p-values, channel selection, caps, components, family construction, evaluation, gates and verdict occur after exact outputs exist.

Fanout v2 exploits only that boundary:

1. **Preexact capture** calls the original repaired `scan_year_v6` and monkeypatches only `exact_rescore_window_v6` to capture its already-deduplicated exact inputs `(records, ordered window event IDs)` per center. The capture returns no scored records and its downstream empty result is discarded. No labels or scientific verdict are saved.
2. **Exact center shards** reconstruct the exact target-excluded scan, verify its canonical row hash, reconstruct each captured window in the identical event order, and call the original repaired `exact_rescore_window_v6`. The already-proven contiguous multiprocessing wrapper may execute that immutable scalar function within a shard.
3. **Year replay** calls the original repaired `scan_year_v6` again. Its exact-rescore call is replaced only by a strict replay function that requires the proposal-record hash and ordered window-event hash to equal the preexact capture before returning the previously computed exact output. Thus the original function still performs all post-exact p-values, channel decisions, caps and component construction.
4. The resulting normal per-year checkpoints feed the already-audited cross-year checkpoint replay, where the unchanged repaired `main()` performs recurrent-family construction, evaluation, gates and verdict.

## Integrity requirements

- Frozen v6 source SHA-256 remains `a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9`.
- Repaired source remains the exact reversible two-line component-construction repair with SHA-256 `257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24`.
- Proposal cap remains 512/window and annual primary proposal budget 36,864/year.
- No proposal, distance, score, threshold, tie rule, member rule, recurrence rule, ranking or gate is reimplemented in the exact shard stage.
- Exact outputs must preserve captured proposal-anchor order.
- Solar longitude 20°–55° remains excluded before all stages; hidden labels are never serialized into preexact/exact/year checkpoints.
- Any mismatch in source, scan rows, calibration rows, captured records, window-event order, shard coverage or replay order is a technical failure, not a scientific result.

This branch does not authorize a target-containing run.
