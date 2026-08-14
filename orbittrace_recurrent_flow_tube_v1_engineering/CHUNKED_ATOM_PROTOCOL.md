# RFT v1 bounded-memory chunked atomizer protocol

Status: frozen engineering-only implementation refinement before any chunked-atom output. Scientific method changes: **none**.

## Motivation

Frozen bin 103 contains 15,017 target-excluded GMN-2022 events. The prior batched engineering atomizer materializes every `cKDTree.query_ball_point(..., r=1.02)` candidate list for the whole bin simultaneously. A zero-endpoint local profile of the exact prepared bin exhausted the analysis process while materializing that all-row candidate-list object, identifying memory pressure rather than a scientific bottleneck.

The current fast shard-3 job also places every computed ordered `pair_d(a,b)` value in an unbounded dictionary. That is useful on ordinary bins but unnecessary for exactness and can retain millions of Python objects on the giant bin.

## Exact bounded-memory substitution

For each unchanged frozen atomization bin:

1. construct the identical transformed array and identical `cKDTree` once;
2. process query rows in deterministic contiguous chunks of exactly 128 rows, with the final chunk shorter as needed;
3. for chunk `[start:end)`, call the same `tree.query_ball_point(transformed[start:end], r=1.02)`;
4. process every returned row candidate list immediately in ascending original row index;
5. for each candidate list, compute the exact authorized ordered fast `pair_d` float from source blob `5c6e914849a24bc2683c7e7e86e5f34f80834df4`, retain candidates with `d <= 1.0 + 1e-12`, and sort by the unchanged `(distance,event_id)` key before frozen KNN truncation;
6. discard that chunk's raw radius-candidate lists before requesting the next chunk;
7. retain only the frozen KNN neighbor lists, reciprocal adjacency, components, and final atoms.

The chunked atomizer does **not** cache pair-distance values globally. It may cache only each event's exact frozen singleton `unit()` vector through the already-audited fast-pair implementation. Ordered pair distances are recomputed when the frozen medoid step asks for them; the returned float is unchanged.

Chunk boundaries cannot alter a radius query: SciPy evaluates each query point independently against the same tree/radius. Candidate-list order cannot alter RFT because the frozen algorithm immediately recomputes exact ordered distances and sorts by `(distance,event_id)`.

## Required zero-endpoint audit

Before authoritative scientific use, establish on the exact prepared target-excluded GMN-2022 events that:

- for every accessible bin and every row, chunked-query candidate **sets** equal frozen scalar-query candidate sets;
- on deterministic ordinary bins spanning the catalogue, complete chunked atoms equal frozen scalar-query atoms field-for-field using the independently authorized exact fast ordered `pair_d` on both sides;
- on giant bin 103 specifically, every row's chunked-query candidate set equals its frozen scalar-query candidate set; then run both scalar-query and chunked-query atomizers with the same exact authorized fast ordered `pair_d` and require complete atom equality if runtime permits. If direct full-bin equality cannot complete because scalar-query scheduling remains an infrastructure problem, candidate-set identity plus deterministic unchanged downstream operations may be documented only as an engineering proof, not silently promoted to a scientific authorization.

## Frozen identities

- RFT science blob `a5d5371f0c30a9c57ee4d8756ea41f454cd86301`;
- exact fast ordered pair source blob `5c6e914849a24bc2683c7e7e86e5f34f80834df4`;
- fast-pair equivalence authorizer run `31818476734`, artifact `9225971510`, digest `sha256:700795c3b9ccc261639b5136f97882879cbd11830fec79fad57c4eb3fc4f9ad4`;
- chunk size exactly 128 query rows.

No reverse-pair reuse, approximate distance, query-radius change, bin split, KNN change, graph/component/medoid change, or floating arithmetic change is authorized.

## Firewall

GMN 2022 only; protected 20°–55° absent before execution; no GMN 2023, SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY or DMS access.
