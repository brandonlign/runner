# OrbitTrace annual sync-density persistence flattening v1 — frozen protocol

## Status

**FROZEN BEFORE IMPLEMENTATION, BEFORE ZERO-LABEL STRUCTURAL OUTCOME, AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This is a genuinely distinct candidate-topology architecture motivated by two already-closed, independently implemented two-year density persistence methods:

- bivariate-density component persistence v1;
- annual-density bifiltration GMN ranking v1.

Both produced the same qualitative result: very large gains in first-hit ranking quality and dominant precision, but catastrophic fragmentation because every persistent threshold-state component was allowed to become a catalogue candidate. This successor does **not** rerank or prune either failed exact-state catalogue. Instead it constructs a new one-parameter simultaneous-density hierarchy and applies persistence-based flattening to obtain one pairwise-disjoint broad clustering at the already-frozen equal catalogue budget.

The persistence-based flattening mechanism is the conservative algorithm of Rolle & Scoccola, *Stable and Consistent Density-Based Clustering via Multiparameter Persistence* (JMLR 25, 2024), through the upstream `FilteredGraph` implementation in `LuisScoccola/persistable` commit `7eb75b2e8d2fe5a18e49248aa7d1c97f829415be`.

## 1. Firewall and scientific role

Stage 1 is **zero-label target-excluded GMN structural development only**.

Use only the eight already-frozen nested GMN 2022+2023 sparse panels. Inclusive solar longitude `[20.0,55.0]` remains excluded upstream.

Forbidden during Stage 1:

- any shower label, shower identity, truth-derived score, or known-shower match;
- OrbitTrace target information or target-region events;
- SonotaCo 2013/2014 scientific access;
- ASFN/EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- parameter search over graph radius, annual combiner, flattening mode, cluster count, support floor, ranking score, or scale/bucket-specific behavior.

A conditional Stage 2 may access only the established target-excluded GMN 2022/2023 development truth after the complete successor catalogue has been serialized and its Stage-1 gates have passed.

## 2. Immutable endpoint universe, comparator, and budgets

Use the exact successful pretruth endpoint package created before the annual-density bifiltration truth attempt:

- source workflow run `32037435314`;
- artifact `9291169452`;
- artifact name `orbittrace-annual-density-bifiltration-gmn-ranking-v1-prelabel`;
- exact `BIFILTRATION_GMN_RANKING_V1_PRELABEL.json` SHA-256:
  `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`.

That zero-label file supplies, and this successor must reproduce exactly:

- the event-ID universe for every panel and year;
- the complete Recurrent-EOM comparator memberships and order;
- equal-budget `K` for each panel.

Frozen K values:

- d=128 buckets 0..3: `29,35,38,33`;
- d=1024 buckets 0..3: `8,5,6,9`.

No comparator, subset, or K may be recomputed from a current runtime.

The later bifiltration truth result is **not** an input to construction.

## 3. Fixed physical graph and simultaneous annual-density filtration

For each frozen panel independently:

1. Restore the exact normalized target-excluded events for the frozen event IDs.
2. Sort events by stable event ID.
3. Use exact recurrent-EOM GEO6 geometry:
   `(cos(sol), sin(sol), sin(lon)cos(lat), cos(lon)cos(lat), sin(lat), vg/72)`.
4. Construct the exact undirected Euclidean radius-1 graph. Radius is fixed at `1.0`; self-neighbors are not graph edges; each undirected edge is represented once with lower integer endpoint first.
5. Let `N22,N23` be the exact panel event counts from 2022 and 2023.
6. For each event i, let `d22(i),d23(i)` be the numbers of radius-1 neighbors **including i itself when its own year matches**, exactly as in the already-frozen annual-density bifiltration construction.
7. Define normalized annual local densities
   `rho22(i)=d22(i)/N22`, `rho23(i)=d23(i)/N23`.
8. Define the sole simultaneous recurrence coordinate
   `rho_sync(i)=min(rho22(i),rho23(i))`.

There is no annual weight, soft minimum, harmonic/geometric mean, smoothing, density transform, bandwidth, fitted scale, or year-specific rule.

### Filtered graph

Use `persistable.FilteredGraph` from exact upstream commit
`7eb75b2e8d2fe5a18e49248aa7d1c97f829415be`.

Define vertex filtration value
`f(i) = -rho_sync(i)`.

For every frozen radius-1 edge `(i,j)`, define
`f(i,j)=max(f(i),f(j))`.

Thus every edge appears no earlier than both endpoints, as required by `FilteredGraph`.

Use finite filtration interval:

- `start = min_i f(i)`;
- `end = 0.0`.

Events with `rho_sync=0` enter exactly at the excluded end boundary and therefore cannot create or bridge a positive simultaneous-density cluster.

No alternate diagonal/slice, graph scale, or filtration transform is authorized.

## 4. Persistence-based flattening at the frozen catalogue budget

For each panel call exactly:

`FilteredGraph(...).persistence_based_flattening(K, flattening_mode="conservative", keep_low_persistence_clusters=False)`.

The requested number of clusters is **not selected from the barcode or from truth**. It is the already-frozen equal comparator budget K.

This is scientifically distinct from the closed Persistable automatic-selector and persistence-ladder lanes:

- no automatic prominence-gap cluster-count selector exists;
- no package-default 2-parameter slice is used;
- no union over requested counts exists;
- the input hierarchy is the fixed radius-1 simultaneous annual-density graph defined above.

If Persistable returns fewer than K non-noise clusters, Stage 1 fails. There is no fallback.

Every returned non-noise cluster must contain at least the already-established reporting floor of 4 events. A smaller cluster causes Stage-1 failure; it is not silently dropped.

## 5. Frozen candidate order

Persistence flattening determines memberships but not a scientifically meaningful catalogue order, so ordering is frozen here before outcome.

For every returned cluster C define:

- `birth(C) = min_{i in C} f(i)`;
- `boundary(C) = min f(i,j)` over all frozen radius-1 edges with exactly one endpoint in C;
- if C has no boundary edge before the filtration end, `boundary(C)=0.0`;
- `prominence(C)=boundary(C)-birth(C)`.

Require `prominence(C) >= 0` up to numerical tolerance `1e-15` used only as an integrity check.

Order the K candidates exactly by:

1. descending `prominence(C)`;
2. descending member count;
3. ascending SHA-256 of the newline-sorted event IDs.

No truth, Recurrent-EOM rank, closed bifiltration persistence-area rank, or support-cut rank enters this order.

## 6. Mandatory Stage-1 zero-label authorization

Before any shower truth is opened, persist `ANNUAL_SYNC_DENSITY_PF_V1_PRELABEL.json` containing all exact memberships, ranks, event universes, density/graph summaries, package/source hashes, and firewall state.

All of the following must pass:

1. `immutable_endpoint_source`: original endpoint prelabel SHA, panel event universes, Recurrent memberships/order, and K reproduce exactly.
2. `persistable_source_pin`: upstream commit and `persistable/persistable.py` blob reproduce the pinned implementation.
3. `requested_returned_k_all_8`: exactly K non-noise clusters are returned in every panel.
4. `support_floor_all`: every returned candidate has at least 4 members.
5. `pairwise_disjoint_all`: PF candidate memberships are pairwise disjoint in every panel.
6. `membership_universe_all`: every candidate member belongs to the exact frozen panel universe.
7. `graph_connectivity_all`: every candidate induces one connected component in the frozen radius-1 graph.
8. `deterministic_repeat_all`: a second conservative PF call on the identical filtered graph returns the identical set of canonical membership hashes.
9. `year_swap_invariance_all`: swapping the names 2022 and 2023 leaves every `rho_sync` value and canonical PF membership set unchanged.
10. `prominence_integrity_all`: every frozen candidate prominence is finite/nonnegative and the serialized order exactly follows the frozen key.
11. `cross_scale_nonlower_4_of_4`: on each nested bucket, fine top-K mean-best-Jaccard to coarse top-K restricted to the fine universe is at least Recurrent-EOM's value.
12. `cross_scale_mean_not_lower`: the unweighted mean of the four PF bucket scores is at least the Recurrent-EOM mean.

Cross-scale computation is label-free: restrict each coarse candidate to the exact corresponding fine universe, discard restricted supports below 4, deduplicate exact memberships, and average each fine candidate's maximum Jaccard against the restricted coarse list.

Only `PASS_ANNUAL_SYNC_DENSITY_PF_V1_PRETRUTH` authorizes Stage 2.

A Stage-1 FAIL permanently closes this exact architecture before truth. It does not authorize a radius change, annual combiner change, other Persistable flattening mode, altered end boundary, changed K, dropped small clusters, different order, or relaxed coherence gate.

## 7. Conditional binding Stage-2 truth endpoint

If and only if Stage 1 passes, freeze a separate evaluator against the exact serialized Stage-1 prelabel **before** opening shower labels.

Use the established target-excluded GMN annual matching semantics:

- annual eligible shower has >=4 events in the panel/year;
- a positive candidate match requires overlap >=4 and precision >=0.5;
- exact equal budget K;
- report qualified matches, recovered@25/@50/@100/@500, dominant precision, fragmentation, historical conditional MRR, and corrected zero-filled eligible-query MRR.

The preregistered ranking metric is the corrected zero-filled eligible-query MRR:

`MRR_zero = (1/|E|) sum_{q in E} RR(q)`,

with `RR(q)=1/r_q` for a recovered eligible shower and `0` when unrecovered.

Historical conditional-on-recovered MRR is diagnostic only.

### Fine d=1024 gates

1. qualified total strictly greater than Recurrent-EOM;
2. qualified matches nonlower in at least 6/8 annual panels;
3. mean zero-filled MRR at least Recurrent-EOM;
4. mean top-100 dominant precision at least Recurrent-EOM;
5. mean fragmentation no higher than Recurrent-EOM.

### Coarse d=128 gates

6. qualified total at least Recurrent-EOM;
7. qualified matches nonlower in at least 6/8 annual panels;
8. mean zero-filled MRR at least Recurrent-EOM;
9. mean top-100 dominant precision at least Recurrent-EOM;
10. mean fragmentation no higher than Recurrent-EOM.

All ten are mandatory. The first technically valid truth result is binding and returns exactly:

- `PASS_ANNUAL_SYNC_DENSITY_PF_V1`, or
- `FAIL_ANNUAL_SYNC_DENSITY_PF_V1`.

## 8. Closure / no-rescue rule

A valid FAIL closes this exact simultaneous-density persistence-flattening architecture. Do not rescue it by changing:

- radius 1.0;
- `min(rho22,rho23)`;
- annual normalization;
- graph representation;
- filtration sign/transform;
- conservative flattening;
- K;
- support 4;
- prominence definition/order;
- scale/bucket/year-specific behavior;
- truth metric or gates;
- candidate mixing with Recurrent-EOM, TopoModal, bifiltration exact states, or support-cut.

Any later method must be genuinely distinct and separately frozen before truth.
