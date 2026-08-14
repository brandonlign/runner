# RFT v1 compositional fast atom-equivalence audit v2

Status: frozen before execution. Engineering identity audit only; no scientific RFT endpoint is computed.

## Purpose

The original direct all-bin scalar-vs-batched atom audit already established exact equality through frozen bin 102 before hosted-runner cancellation. Frozen bin 103 (15,017 events) made the remaining direct audit prohibitively slow because both atomizers repeatedly used the original Python-heavy `pair_d` implementation.

A separate zero-endpoint audit has now independently established an operation-preserving faster implementation of the **ordered** frozen `pair_d`:

- authorizer run `31818476734`;
- artifact `9225971510`;
- digest `sha256:700795c3b9ccc261639b5136f97882879cbd11830fec79fad57c4eb3fc4f9ad4`;
- verdict `PASS_RFT_V1_FAST_ORDERED_PAIR_D_EQUIVALENCE_AUDIT`;
- 315,024 exact target-excluded GMN-2022 events;
- all 163 accessible atom bins represented;
- 110,954 deterministic ordered-pair comparisons;
- zero original-vs-fast float mismatches;
- reverse-pair reuse explicitly forbidden.

This v2 audit therefore composes two independent implementation identities rather than changing science:

1. install the exact fast ordered `pair_d` on the frozen RFT module;
2. run the **frozen scalar-query `atoms()`** and batched-query `_accelerated_atoms()` on identical complete frozen bins;
3. require exact atom identity.

Because the fast ordered `pair_d` has already been independently proven to return the same Python float as frozen `pair_d`, using it on both sides preserves every distance comparison, KNN sort key, reciprocal graph edge, component, medoid residual, and atom field while removing repeated unit-vector allocation overhead.

## Frozen identities

- RFT v1 science blob `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`;
- batched atomizer wrapper blob `8b8a9d373f908dbb32ac9a6b43addeaeb19bb8fa`;
- fast ordered pair source blob `5c6e914849a24bc2683c7e7e86e5f34f80834df4`;
- fast pair protocol blob `f1447d13804fe373a54026dab4708dac1ad922f2`;
- original atom-equivalence protocol blob `8c272987ac0247cd4299bf74370f03b405ec595e`.

## Exact audit

Use the exact normalized target-excluded GMN-2022 prepared events from sharded-equivalence run `31817540176` / artifact `9225656616`.

For every one of the 163 accessible frozen 2-degree atom bins:

1. require every batched `cKDTree.query_ball_point(transformed,r=1.02)` candidate set to equal the frozen scalar-query candidate set for every event;
2. install the exact fast ordered `pair_d` on the frozen module, with no reverse-pair cache;
3. compute `frozen atoms(rows)` and batched `_accelerated_atoms(mod,rows)` on the identical complete bin;
4. require complete ordered atom-list equality in count, `aid`, bin index, center, exact member tuple, `numpy.array_equal` radiant center vector, exact `logv`, and exact `medoid_residual`.

Execution may be deterministically sharded by complete frozen bins only. A bin may never be split.

## Pass rule

`PASS_RFT_V1_COMPOSITIONAL_FAST_ATOM_EQUIVALENCE` requires exact equality for all 163 accessible bins, no duplicate/omitted bin, and every candidate-set/atom-field assertion above.

This audit computes no tube, persistence, recovery metric, candidate score, or scientific endpoint.

## Firewall

GMN 2022 only; protected 20°–55° absent before audit; no GMN 2023, SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY or DMS access.
