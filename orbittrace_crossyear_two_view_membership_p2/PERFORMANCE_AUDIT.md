# P2 D_SH batching performance audit

Source-only implementation audit. No meteor catalogue, label value, target-region event, or OrbitTrace target information may be accessed.

The scientific P2 protocol is unchanged. The exact R1-preserved Southworth-Hawkins comparator remains SHA-256 `85cd11afbdebc4a0315ebf1daf42d10d4993d7ab088dd05301e3234b18340a5a` and P2 still uses the minimum exact D_SH from each candidate to immutable opposite-year source seeds.

This audit tests only whether changing the internal candidate batch size passed to the exact comparator changes any returned minimum D_SH value. The frozen P2 runner currently uses a cap of 512. Candidate batching is an execution detail, not a scientific threshold.

A batching optimization is admissible only if deterministic synthetic-orbit tests produce bitwise-identical outputs against the current 512-batch implementation. No scientific data or P2 outcome may choose the batch rule.
