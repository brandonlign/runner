# Cross-year-core HDBSCAN v1 — strict scalable-equivalence audit result

**Engineering result: POSITIVE. Scientific result: NONE.**

The exact scalable Boruvka adapter passed the separately frozen strict audit against the already-passed dense mathematical reference.

- binding workflow run: `31847169035`
- binding artifact: `9236301386`
- artifact digest: `sha256:0e62fceabca5ddf166a4ff62b303c2c70ba5b0a300f49e63becec20de48faf2d`
- execution commit: `36c8aa7d4c66a897ce03d08bdadc2e042b87ae05`
- result JSON SHA-256: `46076d15466f79aeb0b48f0638f5cd36c509024f5ad29f6e4c08925c5997f115`
- verdict: `PASS_CROSSYEAR_CORE_BORUVKA_EXACTNESS_AUDIT_V1`
- absolute tolerance frozen before execution: `1e-12`

All five frozen synthetic fixtures passed the complete comparison contract: opposite-year core distances, MST edge-weight multiset, single-linkage merge distance/component size, canonical descendant-ID condensed-tree structure, recurrent-EOM selected partition, and complete recurrent-EOM candidate order/membership/stability. The exact-distance-tie fixture also passed an independent deterministic Boruvka rerun.

Maximum observed absolute core/MST-weight deltas were numerical roundoff only:

- recurrent clusters + noise: `2.220446049250313e-16` / `2.220446049250313e-16`;
- one-year-only dense: `8.881784197001252e-16` / `8.881784197001252e-16`;
- unequal year sizes: `2.220446049250313e-16` / `2.220446049250313e-16`;
- exact-distance ties: `0.0` / `0.0`;
- nested density: `2.220446049250313e-16` / `2.220446049250313e-16`.

This is stronger than comparing only MST filtration or condensed-tree score multisets: the strict audit canonicalized each condensed cluster by its exact descendant event-ID set and also compared the final recurrent-EOM catalogue ordering.

No GMN catalogue or shower truth, SonotaCo, AMOS, OrbitTrace target information/events, MAARSY, or DMS was accessed. This PASS satisfies the scalable-implementation prerequisite only. It does not itself authorize the first GMN scientific endpoint; the one-shot GMN runner and workflow still require source/firewall audit and an explicit pre-outcome activation.
