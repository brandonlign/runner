# OrbitTrace v6 exact-equivalent performance optimization

This branch is implementation-only. It must not alter any scientific detector rule, proposal budget, event universe, score, calibration, membership, component, recurrence, ranking, gate, or blind boundary.

Optimization order:

1. Reuse the already source-audited 2022/2023 parallel year checkpoint/replay path from PR #499.
2. Identify the exact scalar hotspot in `exact_rescore_window_v6` from the immutable v6 source SHA-256 `a139802f328e0721a6b48b9b41e098660d03e0e218cec49f1d6251981a2828c9`.
3. Add deterministic intra-year acceleration only behind bounded scalar-vs-fast exact-output equivalence tests.
4. Preserve stable proposal order and all tie semantics.
5. Keep hash-pinned checkpoints so completed expensive work survives infrastructure failure.
6. No target-containing execution is authorized.

The cancelled sequential run `31270206927` is a technical/user-cancelled no-result and supplies no scientific feedback to this optimization.
