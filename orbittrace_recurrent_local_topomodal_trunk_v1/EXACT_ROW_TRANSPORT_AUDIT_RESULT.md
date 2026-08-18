# Recurrent local TopoModal trunk v1 — exact full-row transport audit result

## Status

**PASS_LOCAL_TRUNK_EXACT_ROW_TRANSPORT_AUDIT — ENGINEERING ONLY**

This is not a detector result and does not alter the frozen local-trunk scientific method.

## Binding audit

- workflow run: `32191528958`
- artifact: `9344433367` (`orbittrace-local-trunk-exact-full-row-transport-audit-v1`)
- artifact digest: `sha256:8b9712352417fb1583b9e06cde3c0e460c699ac2d6dada1dbe924b03dc2b68e4`
- audit result SHA-256: `6a64f8a3b733bdb50986027d837ae82c6598c364b8dbddea1deea3f5ca7c0692`
- execution head: `e270f2196bfa3b9cc76b8aebc3f9394ff7db1b69`

The audit compared the original frozen `build_prelabel.local_trunk()` against the exact full-row transport on:

- every parent with `member_count <= 256`: `2027` parent slots;
- fixed stress rank `13`: `4193` members;
- total unique audited parents: `2028` of `2094`.

Every audited parent matched exactly in final event IDs and the complete topology-summary dictionary. No tolerance, shower truth, target information, or external scientific data was used.

## Why the transport is semantically neutral

The transport does not prune, filter, weight, reorder, or approximate graph edges. For each event row requested by GUDHI it returns the complete exact sorted `cKDTree.query_ball_point(..., r=1.0, p=2.0, eps=0.0)` neighbor list. Density uses exact same-radius neighbor counts. Therefore the logical manual radius graph and density vector are the same frozen scientific inputs; only simultaneous Python storage of all graph rows is avoided.

The audit confirms that this transport reproduces the original implementation exactly across 2,028 manageable parent slots, including a 4,193-member stress parent. The remaining giant parents are not compared through the memory-heavy original implementation because that implementation repeatedly caused hosted-runner loss before any prelabel was produced; their graph rows remain exact by construction in the full-row transport.

## Authorization

This PASS authorizes exactly one technical execution of the already-frozen 2,094-parent local-trunk prelabel through `technical_exact_full_row_transport.py`, followed by the unchanged frozen truth evaluator only after immutable prelabel sealing.

It does not authorize any radius/support/anchor/trunk/rank/candidate/gate change, graph pruning, target access, external-data access, or post-result parameter search.
