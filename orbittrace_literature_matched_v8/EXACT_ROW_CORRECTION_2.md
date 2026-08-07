# Exact-row correction 2 — classify HDBSCAN-2023 legacy completeness gates

Blind-safe HDBSCAN-2023 run `31226968008` executed the exact frozen method after the preregistered pre-label 20°–55° insertion from `EXACT_ROW_CORRECTION_1.md`. Its runner returned `FAIL_SONOTACO_2023_HDBSCAN_ONE_SHOT_TRANSFER`.

The failure is not accepted or discarded based on performance. Before the emitted assignments may be used, a separate audit must enforce the following fixed interpretation:

1. The only permitted false legacy gates are `exact_row_count` and `all_rows_parsed`, because the original transfer expected the unblinded raw-row count and the blind-safe insertion necessarily removes rows before the old counter.
2. Every other emitted gate must be true, including exact archive hash, header integrity, frozen HDBSCAN version/parameters, nonempty quality catalogue, and completed primary/full clustering.
3. The emitted full-catalogue assignment file must exist, have unique deterministic `SNM2023:<raw-row-index>` IDs, and every assigned ID must resolve to a solar longitude outside 20°–55°. This audit must not read `Shower` or any other label field.
4. The number of removed raw rows must equal the independently audited SonotaCo-2023 blind-removal count already produced by the validated label-safe parser: 2,237. No row may be added back.
5. The assignment SHA-256 and exact assignment count are provenance outputs, not tunable values. They may be inserted into the exact-row workflow only after this audit passes.
6. No HDBSCAN parameter, quality cut, feature transform, cluster selection rule, evaluation gate, v8 parameter, or `delta >= 0.10` comparison criterion may change.

If any condition above fails, HDBSCAN-2023 remains unusable for the exact-row blind-safe benchmark and the comparison must be reported as technically blocked rather than repaired further from performance feedback.

No OrbitTrace target coordinate, identity, member, excluded-interval label/content, or final target result may be accessed.
