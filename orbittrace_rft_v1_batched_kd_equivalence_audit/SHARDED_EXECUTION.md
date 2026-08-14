# Sharded execution of the frozen RFT batched-KD atom equivalence audit

Status: engineering execution freeze before any sharded-equivalence output. The scientific/identity criterion remains exactly the frozen `PROTOCOL.md`: every accessible GMN-2022 atomization bin must have identical scalar-vs-batched KD candidate sets and identical complete atom fields.

The original all-bin audit run `31815261478` was terminated by hosted-runner infrastructure after bins 0–102 had passed exact equality; no mismatch occurred. This execution changes only scheduling.

## Deterministic complete-bin sharding

- Parse the same exact target-excluded GMN 2022 catalogue using the same frozen runtime and normalize events identically.
- Compute frozen 2-degree atom-bin event counts from normalized events only.
- Use exactly 8 execution shards.
- Sort complete bins by `(-event_count^2, bin_index)` and greedily assign each complete bin to the shard with the smallest accumulated `event_count^2`, tie-breaking by shard index.
- Never split a frozen atom bin and never mix events between bins.
- Each shard applies the exact frozen equivalence criterion independently to every assigned bin.
- A final reduce step requires that the union of passed bin indices equals the full accessible bin set exactly, with no duplicates or omissions, and that all shard verdicts pass.

The `event_count^2` balance proxy is execution-only, truth-free, and selected solely to shorten hosted-runner jobs. It does not alter atomization, candidate sets, exact `pair_d`, KNN sorting, components, medoids, or any atom field.

No tube construction, persistence, RFT metric, shower-recovery score, candidate score, or scientific endpoint is computed. GMN 2023, SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY and DMS remain inaccessible. Protected solar longitude 20°–55° is removed before audit events.
