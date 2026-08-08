# P1 succession guard

This is an execution-authorization addendum only. It does not change the frozen P1 scientific source, parameters, membership model, evaluator, gates, or claim boundary.

P1 may execute only after one of these two preregistered predecessor outcomes:

1. `V6_FAIL`: the exact repaired/fanout-equivalent v3-primary catalogue-v6 target-excluded development artifact has verdict `FAIL_V3_PRIMARY_CATALOGUE_V6_DEVELOPMENT`; or
2. `LITERATURE_NO_SUPERIORITY`: v6 passed development, then the frozen matched Sugar/HDBSCAN adjudication completed with classification `NO_LITERATURE_SUPERIORITY`.

P1 may not execute after a technical/integrity failure, a cancelled/no-result v6 run, a literature result that establishes `SPARSE_STREAM_SUPERIORITY` or `BROAD_CATALOGUE_SUPERIORITY`, or from a manually asserted prerequisite.

Activation is an execution-only child containing exactly one file `orbittrace_probabilistic_membership_p1/RUN_GUARDED.md` with exactly three lines:

1. `EXECUTE_FROZEN_P1_AFTER_PREREQUISITE`
2. either `V6_FAIL` or `LITERATURE_NO_SUPERIORITY`
3. the numeric GitHub Actions workflow run ID containing the prerequisite artifact

The workflow itself downloads and verifies that artifact before reconstructing the exact frozen P1 source SHA-256 `e7847e067bab8d07038c998359ccbf0ca6e2ccf257f27f27f4aef999cc7a0508`.
