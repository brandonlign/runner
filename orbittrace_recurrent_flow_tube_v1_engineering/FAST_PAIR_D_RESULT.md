# RFT v1 exact fast ordered `pair_d` equivalence result

**PASS — zero-endpoint engineering identity audit.**

Binding audit:
- workflow run `31818476734`;
- job `94825741801`;
- artifact `9225971510`;
- artifact digest `sha256:700795c3b9ccc261639b5136f97882879cbd11830fec79fad57c4eb3fc4f9ad4`.

Frozen identities:
- RFT v1 science blob `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`;
- fast-pair implementation blob `5c6e914849a24bc2683c7e7e86e5f34f80834df4`;
- protocol blob `f1447d13804fe373a54026dab4708dac1ad922f2`.

Verdict: `PASS_RFT_V1_FAST_ORDERED_PAIR_D_EQUIVALENCE_AUDIT`.

The audit used the exact prepared target-excluded GMN 2022 execution input:
- events: **315,024**;
- accessible frozen atom bins: **163**;
- deterministic ordered pair comparisons: **110,954**;
- original frozen and operation-preserving fast `pair_d` Python floats: **bit-for-bit equal on every comparison**.

The comparisons span every accessible atom bin and include deterministic cross-bin-position probe pairs plus short-index-neighbor pairs in both directions. Reverse-pair reuse remains explicitly unauthorized because `(a,b)` and `(b,a)` can differ at floating precision.

No atoms, tubes, labels, RFT candidate scores, recovery metrics, or scientific endpoint were computed by this audit. GMN 2023, SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY and DMS remained inaccessible; protected 20°–55° was absent from the prepared events.

This PASS authorizes use of the operation-preserving fast ordered `pair_d` only as an engineering substitution under the exact rules in `FAST_PAIR_D_PROTOCOL.md`. It does not authorize any scientific conclusion by itself.
