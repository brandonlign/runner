# OrbitTrace v6 exact-sharded acceleration protocol

This is implementation-only acceleration of the already-frozen, target-excluded v3-primary catalogue v6 development execution. It does **not** alter a detector score, proposal rule, proposal cap, calibration rule, membership definition, component rule, recurrence rule, family ranking, threshold, scientific gate, blind exclusion, or target-access boundary.

The prior authoritative sequential execution (run `31270206927`) was cancelled by the user before a scientific result existed because the scalar exact-rescore stage was projected to require many additional hours. Cancellation is a technical no-result, not a scientific PASS or FAIL.

## Immutable scientific identity

- frozen v6 source SHA-256: `a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9`
- exact two-line component-construction repair only
- repaired source SHA-256: `257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24`
- years: 2022 and 2023
- blind exclusion: solar longitude 20°–55°
- proposal cap: 512/window, maximum 36,864 primary proposals/year

## Acceleration decomposition

1. Parse the target-excluded catalogue once. Real hidden labels are discarded and are never serialized into the cache. Scan rows retain only the parser's `iau=0`, `complex_key=HIDDEN` sentinels; calibration rows retain only `iau=0`, `complex_key=SPORADIC`.
2. Run the original repaired `scan_year_v6` proposal/calibration prefix independently for 2022 and 2023. The original `proposal_window_v6` is called unchanged. Its exact return objects are copied and hash-bound for later replay. Execution stops at the first call to the original `exact_rescore_window_v6`, after the frozen code has completed all proposal windows and global proposal-anchor deduplication.
3. Partition exact-rescore window centers into eight deterministic shards per year. Greedy balancing uses the label-free estimated scalar work `proposal_count × exact_window_event_count`, with deterministic center/shard tie handling.
4. Execute 16 independent `(year, shard)` jobs. For every assigned center, each job calls the **original repaired `exact_rescore_window_v6` function unchanged**. No distance formula, nearest-neighbor tie rule, fixed4 score, v3 score, or p-value calculation is reimplemented or approximated.
5. Replay each year through the original repaired `scan_year_v6`. Exact calibration outputs and original proposal-window outputs captured in step 2 are replayed only after input fingerprints/hashes match. Exact-rescore outputs from step 4 are replayed only after proposal-anchor order and exact window-event IDs match. All post-exact p-values, detection logic, anchor caps, and component construction execute inside the original repaired function.
6. Produce the same `orbittrace-v6-development-year-checkpoint-v1` format used by the already-source-audited PR #499 fallback.
7. Replay the two year checkpoints through the inherited, unchanged `combine_with_checkpoints.py`, which calls the original repaired `main()`. The original `main()` performs final catalogue parsing, family construction, hidden-label evaluation, preregistered scientific gates, reporting, and verdict.

## Equivalence / fail-closed rules

Every serialized stage has a SHA-256 sidecar. Catalogue rows, calibration rows, source identities, proposal call fingerprints, exact proposal-anchor order, exact window event IDs, shard coverage, and year replay order are checked before reuse. Any mismatch is a technical failure and produces no scientific verdict.

The acceleration may not prune proposals, reduce rescue candidates, reduce calibration, approximate distance calculations, alter stable nearest/tie handling, change the 512 proposal cap, change recurrence/ranking/gates, or expose OrbitTrace target information.

## Performance objective

The previous execution used one scalar exact-rescore loop and processed years sequentially. This executor runs years in parallel and distributes unchanged scalar exact-rescore calls across 16 balanced Actions jobs. Wall time should therefore be governed approximately by the heaviest shard instead of the sum of both years' exact windows, while retaining the same scientific computation.
