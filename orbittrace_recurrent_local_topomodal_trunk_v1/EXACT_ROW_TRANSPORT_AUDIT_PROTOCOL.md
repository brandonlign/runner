# Recurrent local TopoModal trunk v1 — exact full-row transport audit

## Status

**FROZEN ZERO-LABEL ENGINEERING AUDIT BEFORE EXECUTION.**

The scientific method remains the original frozen local-trunk protocol and implementation. This audit tests only a memory-transport replacement for the Python radius-neighbor container.

## Motivation

The original frozen implementation materializes every radius-neighbor row for a parent simultaneously before passing the manual graph to GUDHI ToMATo. Multiple hosted runs have disappeared during the first giant parent before a prelabel or truth result existed. A previous experimental transport that omitted strictly lower-density neighbor rows did not reach a usable equivalence verdict and is not authorized here.

The transport tested here performs **no graph pruning whatsoever**.

For each event `i`, whenever GUDHI requests neighbor row `i`, the transport returns exactly:

`cKDTree.query_ball_point(z[i], r=1.0, p=2.0, eps=0.0, return_sorted=True)`

with every returned integer neighbor retained. Density is computed independently from exact `return_length=True` counts at the same radius. Thus the logical manual graph, graph symmetry, radius, event ordering, and density vector are unchanged; only simultaneous Python storage of all rows is avoided.

## Frozen sources

- scientific protocol blob: `de8d040a1f9d3b0825ce56532efd5950acefc689`;
- original prelabel builder blob: `cd3fb15263fd4b2e38e4b413ece9b347b64816d5`;
- existing row-transport support helper blob: `79cc2e51929fd60f8e17faec4c1b04c19e43010e`;
- exact density-synchronous parent prelabel SHA-256: `efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993`;
- exact parent count: `2094`.

## Audit sample

Compare original `build_prelabel.local_trunk()` against the exact full-row transport on:

1. every parent with member count `<=256` — expected `2027` parent slots; and
2. fixed stress rank `13`, whose parent has `4193` members in the frozen parent catalogue.

The sample is fixed before execution and uses no shower truth.

The giant ranks that caused hosted-runner loss are intentionally not executed through the memory-heavy original implementation in this audit; exact full-row identity there is guaranteed by the transport's direct unfiltered row query, not inferred from a pruned graph.

## Required equivalence

For every audited parent require exact equality of:

- final event-ID list;
- complete topology-summary dictionary;
- all degree summaries;
- leaf/internal/root counts;
- anchor identity/density;
- every anchor-chain membership and hash;
- annual support counts;
- decision token;
- final membership hash.

No numeric tolerance or post-hoc exception is allowed.

Additionally the transport must assert that GUDHI requested exactly one neighbor row per event, and each returned row contains self and only valid indices. No filtering or reordering beyond the frozen `return_sorted=True` query is permitted.

## Interpretation

`PASS_LOCAL_TRUNK_EXACT_ROW_TRANSPORT_AUDIT` authorizes only a technical execution of the already-frozen 2,094-parent prelabel through the exact full-row transport, followed by the unchanged frozen truth evaluator after immutable prelabel sealing.

Any audit mismatch blocks this transport. No scientific parameter, graph edge, ranking, support condition, gate, target access, or external-data access may be changed.
