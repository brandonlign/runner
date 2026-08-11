# OrbitTrace v31 radius-1 candidate-graph surfacing diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only. Exact v31 is the strongest HDBSCAN-2014 near miss, while #1040/#1043 show that representative choice inside already-surfaced shower groups cannot close the remaining HDBSCAN deficits and v35 shows that averaging truth groups into prototypes destroys useful geometry. This diagnostic asks a different question: whether the already-frozen, label-free radius-1 candidate-neighborhood graph contains high-ranked neighboring families that could plausibly carry evidence toward globally missed recoverable shower groups without compressing their family-level structure.

It does not define or evaluate a propagated score, reranking rule, graph model, successor, or parameter.

## Immutable graph reconstruction before truth

Use the exact immutable #950/v24 pretruth payload. `centroids.npy` contains, for each family and each of the two years in order, `[sol, sun_lon, ecl_lat, log(vg)]`. Reconstruct the exact #843/#v22 radius-1 two-year graph directly from those immutable centroids.

For two annual centroids `a,b`, use the exact preserved fixed4 support-wrapper metric:

- `d_sol = wrap180(a.sol-b.sol)/4`;
- `d_lon = wrap180(a.sun_lon-b.sun_lon) * cos(radians((a.ecl_lat+b.ecl_lat)/2)) / 2`;
- `d_lat = (a.ecl_lat-b.ecl_lat)/2`;
- `d_vg = (a.vg-b.vg)/2`, where `vg = exp(log(vg))` from the immutable centroid matrix;
- annual distance is Euclidean norm of those four terms;
- pair distance is the maximum annual distance across the two years;
- an undirected edge exists iff pair distance `<= 1.0`.

Self is included only in adjacency, never as an edge. No radius or metric alternative is evaluated.

Before exposed truth is interpreted, the reconstructed graph must reproduce the immutable v22 graph descriptors exactly (within `1e-12`) for every family:

- column 67 = `log1p(direct degree)`;
- column 68 = `log1p(direct neighbors from a different generator source)`;
- column 69 = number of distinct other generator sources among self+direct neighbors.

Failure of any graph-feature identity gate is technical and yields no diagnostic result.

## Immutable v31 replay

After graph identity is frozen, load the already-exposed SonotaCo truth and reconstruct exact v31 under the immutable #950 payload: shared strict whole-shower five-fold assignment across Sugar/HDBSCAN, fold-local arithmetic mean and population standard deviation across all 71 features, ordinary Euclidean k=1 nearest annual-positive (`F1_y>0.5`) and annual-nonpositive distances, margin `d_nonpositive-d_positive`, annual `min`, exact #839 diversity `lambda=0.8, scale=1.0`, and exact v19 equal-rank-sum fusion.

Exact HDBSCAN controls must reproduce:

- 2013 macro-F1 `0.14888037368183737`, recovery `9`, budget `11`;
- 2014 macro-F1 `0.15198123772301594`, recovery `9`, budget `9`.

## Group-level diagnostic

Use the unchanged v22/v24 fixed best recurrent label and annual F1. For each year, an annual-recoverable strict shower group contains at least one HDB family with annual F1 strictly greater than 0.5. Its representative is the annual-positive family from that group having the earliest exact-v31 final rank, stable family ID tie-break. A group is `surfaced` iff that representative rank is within the frozen HDB comparator budget.

For each annual-recoverable group, inspect the union of direct radius-1 graph neighbors of all annual-positive families belonging to that group. Report:

- representative exact-v31 rank and raw two-year v31 margin score;
- best exact-v31 final rank among that graph-neighbor union;
- best raw v31 margin score among that graph-neighbor union;
- rank uplift = representative rank minus best-neighbor rank;
- whether the best-ranked neighbor belongs to the same strict truth group, another strict shower group, or a `NEG/...` group;
- whether any direct neighbor lies inside the frozen HDB top budget;
- direct-neighbor count and number of distinct neighbor truth groups.

Summarize surfaced and missed annual-recoverable groups separately using medians and counts. In particular report, among missed groups, how many have any direct graph neighbor inside the top budget and how many have a best-ranked neighbor from a different truth group.

## Global graph-purity diagnostic

For all radius-1 HDB edges after truth is loaded, classify endpoints by unchanged strict truth group. Report:

- total edges;
- edges whose two endpoints share the same strict `SHOWER/<label>` group;
- edges joining different strict shower groups;
- edges involving at least one `NEG/...` endpoint;
- corresponding fractions.

This truth-aware purity summary is diagnostic only; truth never enters graph construction.

## Interpretation boundary

A later graph-propagation successor is scientifically motivated only if missed recoverable groups commonly possess substantially better-ranked direct label-free neighbors while the graph has enough same-group purity to make local propagation plausible. If missed groups usually lack strong direct neighbors, or graph neighborhoods are dominated by cross-group/NEG links, direct radius-1 propagation is not justified.

No numeric pass threshold is selected here. No propagated score, max/mean neighbor aggregation, blend weight, hop count, radius, source rule, graph neural method, or reranking is evaluated. Any successor must be separately named and frozen after this result.

SonotaCo 2013/2014 remains exposed development-only. No MAARSY, DMS, OrbitTrace target information, target-region events, or protected solar-longitude 20°–55° content may be accessed.