# P2 matched literature — HDBSCAN 2023 blind-safe artifact provenance

This addendum is frozen before any P2 development verdict or P2 matched-literature execution.

The original exact-row v8 protocol named HDBSCAN-2023 assignment SHA-256 `7dbb920532f7dc429a6cd5961d80d480c5ff53c0122cf6e9ec04638c0730ed60` from workflow `31076062060`. Before P1/P2 execution, the existing exact-row benchmark later established an independently verified blind-safe HDBSCAN-2023 assignment artifact from workflow `31226945294`, SHA-256 `35f629b1dff4d04cdc13aa8224171ec1ab8e06b52836900d66ff978b5c235761`.

The already-frozen exact-row final entrypoint at commit `ffe8351b9ee8df4418fb4926fab782d66180e276`, file `orbittrace_literature_matched_v8/run_exact_row_final.py`, documents the change exactly: it overrides only `ASSIGNMENT_SHA256["hdbscan"][2023]` to the blind-safe SHA and states that no v8, comparator, metric, label or decision parameter changes. P1's preregistered matched-literature execution also used this blind-safe artifact.

P2 therefore must use the same blind-safe HDBSCAN-2023 artifact. This is a pre-existing provenance correction, not a comparator choice based on P2 outcome. The exact row count remains 26,460 and the pairwise universe is still defined solely by the frozen assignment IDs.

No competitor cluster value, known-shower truth value, target-region event or OrbitTrace target information is accessed by this addendum.