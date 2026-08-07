# Execute frozen UKMON 2020/2021 pre-scientific structure audit

Execution-only child of PR #347.

This is the first allowed UKMON 2020/2021 HTTP access. It must use exactly 2020-08-14 and 2021-08-14 and may inspect only response/container structure, record-count >=5, and required-key membership. It may not read, convert, log, persist, summarize, compare, or use meteor scientific field values, orbname values, source-label values, or OrbitTrace target information. It may not run v8.
