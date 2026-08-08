# OrbitTrace v6 global exact-chunk acceleration

This is a second implementation-only acceleration layer. It is based on the source-audited center-sharded executor in PR #506 and remains **dormant** while that executor is running.

The scientific method is unchanged: frozen v6 source SHA-256 `a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9`, exact two-line repaired source SHA-256 `257aab9d0f4d710a1b62af6088cfb9c0939062018d44dbacd074b4e7898eaa24`, years 2022/2023, solar-longitude exclusion 20°–55°, proposal cap 512/window, identical calibration/scoring/membership/components/recurrence/ranking/gates.

## Why a second layer exists

Center-level sharding cannot split one unusually expensive center. The cancelled sequential log showed, for example, a 2023 center with 21,089 exact proposals. Even if every other center runs in parallel, that one center alone creates a large wall-clock floor.

## Exact chunk rule

After the already-audited preparation stage has frozen `records_by_center`, each center's **already sorted** proposal records are split only by deterministic contiguous index ranges of at most 512 records:

`[0:512], [512:1024], ...`

Every chunk is passed to the original repaired `exact_rescore_window_v6` unchanged, with the exact same complete `window_events`, `event_lookup`, `support`, and `base` objects the full-center call would receive. No scorer is rewritten and no event/proposal is omitted.

Tasks from both 2022 and 2023 are then greedily balanced across 16 global shards using the label-free cost estimate `chunk proposal count × exact window event count`. A shard may contain tasks from both years.

For replay, chunk outputs are ordered by `(year, center, start_index)`, required to cover each original center contiguously with no gap/overlap, concatenated, and required to reproduce the exact original proposal-anchor order before they can enter the unchanged repaired `scan_year_v6` replay.

## Equivalence requirement before scientific use

This design may not replace the currently running center-sharded executor until a separate implementation-equivalence check demonstrates that, on target-excluded data and without labels, a complete center scored in one call is identical to concatenating deterministic chunk calls. Any mismatch permanently blocks this acceleration implementation until the implementation error is found; scientific thresholds may not be changed.

The purpose is purely computational: remove the largest-single-center wall-clock floor. It does not authorize any target-containing execution or any scientific retuning.
