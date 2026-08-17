# OrbitTrace bipartite bicore recurrence scale v1 — frozen zero-label protocol

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SCIENTIFIC OUTCOME FOR THIS MECHANISM.**

This is a zero-label structural screen only. It does not open GMN shower truth and cannot authorize SonotaCo, OrbitTrace target access, or full-GMN promotion by itself.

The current full-GMN development champion is density-synchronous recurrent-EOM HDBSCAN v1 (#1263). Its exact frozen result shows that GEO6, pooled HDBSCAN geometry, and nearly all selected memberships remain strong, but the subsequent sparse TopoModal/bifiltration experiments expose a separate structural problem: pooled candidate hierarchies either recover many distinct streams with weak first-hit ordering or concentrate catalogue budget on a few recurrent structures. Repeated one-to-one/reciprocal cross-year matchers also lose coverage.

This successor therefore tests a genuinely different object before labels: **many-to-many cross-year density as a bipartite core**, with no pooled same-year edges and no one-to-one assignment.

## Independent motivation

Dense-subgraph mining on bipartite graphs commonly represents two entity types explicitly and uses `(alpha,beta)`-core / density decompositions to identify mutually supported many-to-many communities rather than projecting the graph or forcing pairwise assignments. This architecture is adopted here because the two years are naturally the two vertex types.

The exact scientific constants below are inherited from pre-existing OrbitTrace methodology rather than selected from any bipartite outcome:

- exact GEO6 physical embedding inherited unchanged by #1263;
- exact radius `1.0` from the fixed-scale sparse physical graph used before this protocol;
- exact minimum support `4`, the long-frozen candidate/qualified-stream support floor used throughout the sparse evaluation framework.

No alternative bicore order, radius, distance transform, edge weight, density score, or threshold is eligible in v1.

## Firewall and source universe

Use only target-excluded GMN 2022+2023.

The inclusive solar-longitude interval `[20.0,55.0]` must be removed by the already-audited parser before geometry, graph construction, peeling, serialization, or any later evaluation. No protected event may enter memory after parser normalization.

Forbidden throughout this screen:

- GMN shower labels / hidden truth;
- OrbitTrace target information, target events, coordinates, membership, activity result, or rank;
- SonotaCo 2013/2014 scientific access;
- ASFN/EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- orbital elements or orbital distances;
- station metadata or uncertainty metadata;
- any post-result change to graph radius, core order, support, panel construction, or gates.

The sparse event universes and equal-budget reference counts are taken only from the already-sealed zero-label endpoint artifact from run `32037435314`:

- artifact `9291169452`;
- artifact digest `sha256:af497634e100883b0448737465e27b4e523ffa85f48979c829125e95acfc58ac`;
- exact `BIFILTRATION_GMN_RANKING_V1_PRELABEL.json` SHA-256 `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`.

That artifact contains no shower truth and fixes the eight `ORBITTRACE_SCALE_STRESS_V1` panels:

- denominators `128` and `1024`;
- buckets `0,1,2,3`;
- exact annual event-ID universes;
- reference candidate capacities `K = 29,35,38,33` at `d=128` and `K = 8,5,6,9` at `d=1024`.

These K values are used only as a **zero-label capacity floor** in Stage 1. They are not a truth comparator and do not replace #1263 as the required parent for any later full-GMN scientific gate.

## Exact physical graph

For each sparse panel independently:

1. Reconstruct exactly the target-excluded normalized events from the frozen GMN runtime.
2. Sort events by stable event ID.
3. Compute the exact inherited six-dimensional GEO6 embedding using the frozen recurrent-EOM parent geometry implementation; #1263 explicitly leaves this geometry unchanged.
4. Build a Euclidean `cKDTree` radius query at exactly `r=1.0`, `p=2`, `eps=0`.
5. **Discard every self edge and every same-year edge.** Retain an undirected edge only between one 2022 event and one 2023 event whose exact GEO6 distance is at most `1.0`.

The resulting graph is strictly bipartite. No pooled/same-year connectedness can create a family.

## Frozen symmetric `(4,4)` bicore

Starting from all panel vertices and all frozen cross-year edges, iteratively peel vertices until convergence:

- remove a 2022 vertex if its current number of active 2023 neighbors is less than `4`;
- remove a 2023 vertex if its current number of active 2022 neighbors is less than `4`;
- after each deletion update opposite-year degrees;
- deletion processing order is lexicographic event ID, but the final core must be verified order-invariant by a second reverse-ID peeling pass.

No event may be restored after deletion. No within-year edge, halo, nearest-neighbor fallback, orphan rescue, core-number search, or second support threshold is allowed.

The value `4` is not tuned: it is the inherited minimum stream-support constant. Here it has the direct recurrence interpretation that every retained event must have at least four physically compatible observations in the opposite year.

## Candidate families

After bicore convergence, candidate families are the ordinary connected components of the surviving **bipartite** graph.

Every emitted family must therefore satisfy by construction:

- at least four 2022 events;
- at least four 2023 events;
- every retained event has active opposite-year degree at least four;
- graph connectivity using cross-year edges only;
- pairwise event-disjoint family memberships.

Families are serialized in deterministic diagnostic order only:

1. decreasing `min(n_2022,n_2023)`;
2. decreasing number of surviving cross-year edges;
3. decreasing total member count;
4. ascending membership SHA-256.

**This order is not authorized for shower-truth evaluation.** Stage 1 tests only structural viability. If Stage 1 passes, a separate ranking/evaluation protocol must be motivated and frozen before any shower label is opened.

## Cross-scale structural test

Use the established nested `d=1024` fine and `d=128` coarse panels with the same bucket ID.

For each fine family, restrict every coarse family to the exact fine event universe, discard restricted memberships that no longer contain at least four events from each year, deduplicate identical restricted memberships, and compute the fine family's best Jaccard overlap with any remaining coarse family.

The bucket score is the mean of those best Jaccards across all fine families. Compute the same established mean-best-Jaccard score for the immutable recurrent-EOM reference candidates stored in the sealed endpoint artifact.

This comparator is a zero-label stability reference only.

## Frozen Stage-1 gates

All gates are mandatory:

1. `immutable_endpoint_source`: exact sealed endpoint artifact SHA reproduces.
2. `strict_bipartite_graph_all`: every retained graph edge joins different years and has GEO6 distance `<=1.0`.
3. `bicore_degree_floor_all`: every emitted-family event has surviving opposite-year degree `>=4`.
4. `annual_support_floor_all`: every family has at least four members from each year.
5. `pairwise_disjoint_all`: no event appears in more than one family in a panel.
6. `crossyear_connected_all`: every family is connected using only surviving cross-year edges.
7. `peeling_order_invariance_all`: lexicographic and reverse-lexicographic peeling produce identical active event sets and family membership hashes.
8. `year_swap_invariance_all`: exchanging only the year labels 2022<->2023 leaves family memberships identical.
9. `capacity_at_least_reference_k_all_8`: family count is at least the frozen reference K in every sparse panel.
10. `cross_scale_nonlower_4_of_4`: bicore mean-best-Jaccard is at least the recurrent reference in every nested bucket.
11. `cross_scale_mean_not_lower`: mean bicore cross-scale score across four buckets is at least the recurrent reference mean.
12. `firewall`: no truth, target, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, DMS, orbital, station, or uncertainty information is accessed.

PASS verdict:

`PASS_BIPARTITE_BICORE_RECURRENCE_SCALE_V1_PRETRUTH`

Otherwise:

`FAIL_BIPARTITE_BICORE_RECURRENCE_SCALE_V1_PRETRUTH`

## Promotion / closure boundary

A Stage-1 PASS means only that many-to-many cross-year bicore topology is structurally viable enough to justify a separately frozen target-excluded GMN scientific ranking/comparison against **#1263**. It does not authorize shower truth automatically; the Stage-2 ranking and gates must be frozen first using only this zero-label structural output and independent scientific motivation.

A Stage-1 FAIL permanently closes this exact radius-1 symmetric `(4,4)` bicore architecture. Do not rescue by testing `(2,2)`, `(3,3)`, `(5,5)`, asymmetric `(alpha,beta)`, alternate radii, soft degree, edge weights, butterfly/bitruss thresholds, same-year edges, halo expansion, nearest-neighbor fallback, component splitting, or a different capacity gate from the observed result. Any such future mechanism would require a genuinely independent preregistration and motivation, not a v1 repair.
