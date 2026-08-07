# Execute frozen UKMON 2020/2021 structure transport correction

Execution-only child of PR #349.

The first structure failure remains preserved. This rerun changes only transport handling by reusing the pre-existing frozen daily-to-four-period fallback. It may inspect record key membership only after top-level list transport succeeds. It may not inspect, convert, log, persist, compare, summarize, hash, or use meteor scientific field values, orbname values, source labels, or OrbitTrace target information, and it may not run v8.
