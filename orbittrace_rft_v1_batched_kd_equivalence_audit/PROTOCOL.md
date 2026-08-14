# RFT v1 batched-KD atom equivalence audit

Status: frozen before execution. Engineering identity audit only; no scientific RFT endpoint is computed.

## Purpose

The frozen RFT v1 atomizer calls SciPy `cKDTree.query_ball_point` once per event using an unchanged transformed coordinate and radius `1.02`. The engineering wrapper blob `8b8a9d373f908dbb32ac9a6b43addeaeb19bb8fa` replaces only those repeated scalar calls with one batched `query_ball_point` call per frozen 2-degree bin, after which the unchanged frozen exact `pair_d`, `(distance,event_id)` sort, reciprocal-KNN graph, connected components, medoid rule, and atom construction remain in force.

This audit must establish that the substitution is implementation-only on the exact target-excluded GMN 2022 development catalogue.

## Frozen identities

- frozen RFT science blob: `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`;
- cached engineering runner blob: `2a599c6e8247eb819a1090591d586526eda6c0c1`;
- batched-KD engineering wrapper blob: `8b8a9d373f908dbb32ac9a6b43addeaeb19bb8fa`;
- wrapper source commit: `9abdc2c80679b648c25aee33e03b1e3557613fdc`;
- #839 runtime utility SHA-256: `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`;
- v8 runtime-support SHA-256: `fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b`.

## Exact audit

After the existing 20°–55° exclusion and exact frozen event normalization, for every nonempty frozen atomization bin:

1. construct the identical frozen transformed array and `cKDTree`;
2. require every event's batched radius-query candidate **set** to equal the frozen scalar radius-query candidate set exactly;
3. run frozen scalar-query `atoms()` and the batched-query atomizer on the identical bin rows, with only exact memoization of repeated frozen `unit()` / `pair_d()` outputs to reduce duplicate computation;
4. require the complete ordered atom list to be identical in:
   - atom count and order;
   - `aid`;
   - `bin_index` and `center`;
   - exact member tuple;
   - `u` array by `numpy.array_equal`;
   - exact `logv` float;
   - exact `medoid_residual` float.

No tube construction, perturbation persistence, metrics, shower recovery, candidate score, truth endpoint, or continuation verdict is computed.

## Pass rule

`PASS_RFT_V1_BATCHED_KD_ATOM_EQUIVALENCE` requires exact equality for every accessible 2022 atomization bin and every atom field above. Any mismatch fails closed and the batched-KD wrapper cannot be used as scientific-equivalent execution.

## Firewall

- GMN 2022 only;
- protected solar longitude 20°–55° excluded before audit rows;
- GMN 2023 inaccessible;
- SonotaCo 2013/2014 inaccessible;
- OrbitTrace target information/events inaccessible;
- MAARSY and DMS inaccessible;
- labels may not enter any computed quantity and no scientific endpoint is produced.
