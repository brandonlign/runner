# OrbitTrace Dual-Year Reciprocal HDBSCAN v1 — frozen protocol

## Status and independence

Frozen before the first technically valid scientific outcome.

This is a **separate structural HDBSCAN successor**, not a repair or retune of recurrent-EOM v1. Its motivation is intrinsic to the algorithm: recurrent-EOM v1 balances observing years only at HDBSCAN's flat-cluster selection stage, while the underlying mutual-reachability hierarchy has already been estimated from the pooled event density. If annual survey sampling densities differ, pooled density estimation can influence the hierarchy before recurrent EOM is applied.

The already-exposed GMN 2020/2021 retrospective result is **not** used to choose this mechanism, any numerical parameter, any ranking key, or any gate, and GMN 2020/2021 is not accessed by this experiment. The permanent development set remains target-excluded GMN 2022+2023.

Scientific firewall:

- protected solar longitude `[20°,55°]` removed before labels, clustering, matching, ranking, or evaluation;
- no OrbitTrace target information or target-region event;
- no MAARSY or DMS scientific access;
- no SonotaCo 2013/2014 access during development;
- no result-informed threshold, weight, feature, metric, `k`, blend, or hyperparameter rescue.

## 1. Inherited HDBSCAN object

Each observing year is clustered **independently** with exactly the promoted recurrent-EOM parent HDBSCAN settings and GEO6 representation:

`[cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72]`

Frozen settings:

- `min_cluster_size = 10`;
- `min_samples = 10`;
- Euclidean metric;
- standard HDBSCAN excess-of-mass (`eom`) extraction;
- `cluster_selection_epsilon = 0`;
- `allow_single_cluster = false`;
- no z-score normalization;
- no probability trimming or soft assignment.

No HDBSCAN setting is searched or changed from recurrent-EOM v1.

## 2. Sole new mechanism: reciprocal cross-year coupling

Let the ordinary EOM-selected HDBSCAN clusters in 2022 be `A_i` and those in 2023 be `B_j`.

For every selected annual cluster, compute its arithmetic centroid in the **same six-dimensional GEO6 coordinates** used by HDBSCAN. No new feature or rescaling is introduced.

Using ordinary Euclidean distance in GEO6:

- each `A_i` chooses its nearest `B_j` centroid;
- each `B_j` chooses its nearest `A_i` centroid;
- retain a pair `(A_i,B_j)` **iff the nearest-neighbor relation is reciprocal**.

There is:

- no distance cutoff;
- no maximum-separation threshold;
- no `k` beyond nearest (`k=1`, inherent to reciprocal-nearest matching);
- no Hungarian/optimal-transport weighting;
- no one-to-many rescue;
- no unmatched-cluster rescue.

Each retained pair becomes one recurrent family with exact member set `A_i ∪ B_j`.

This changes where annual density is estimated: unlike recurrent-EOM v1, neither annual HDBSCAN hierarchy can be dominated by the other year's catalogue density.

## 3. Frozen family score and rank

For selected annual cluster `C_y`, let ordinary HDBSCAN EOM stability be `S_y(C_y)` and let `N_y` be the total accessible event count in that year.

Define normalized annual stability:

`Z_y(C_y) = S_y(C_y) / N_y`.

For reciprocal pair `(A_i,B_j)`, define the sole primary score:

`Z_rec(A_i,B_j) = min(Z_2022(A_i), Z_2023(B_j))`.

Candidate ranking is frozen lexicographically:

1. descending `Z_rec`;
2. ascending annual-centroid GEO6 distance;
3. descending total exact member count;
4. ascending deterministic member-hash family ID.

No weighted stability average, distance penalty weight, score product, learned ranker, v31 fusion, or post-hoc diversity rerank is authorized.

## 4. Binding parent

The primary comparator is exact promoted **recurrent-EOM HDBSCAN v1** executed on the same target-excluded GMN 2022+2023 rows in the same process, with its frozen source `recurrent_eom.py` blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`.

The parent uses one pooled HDBSCAN hierarchy and recurrent EOM exactly as already promoted. Its candidate ranking remains descending recurrent stability, ordinary stability, member count, deterministic family ID.

Vanilla pooled HDBSCAN may be reported descriptively but cannot substitute for recurrent-EOM v1 as the primary gate.

## 5. Prelabel freeze

Known-shower labels must remain unused until all of the following are serialized:

- both annual HDBSCAN selected-node sets;
- every annual cluster exact membership;
- every reciprocal pair;
- every dual-year family exact membership;
- full dual-year family order;
- full recurrent-EOM-v1 parent membership/order.

The serialized prelabel payload SHA-256 is frozen before the hidden shower map is inspected.

## 6. Evaluation

Use the exact promoted recurrent-EOM GMN family-evaluation semantics, separately in each year from the same pooled family order:

- eligible known shower: at least 4 accessible labelled events in that year;
- candidate positive for a shower only when dominant precision `>=0.5` and overlap `>=4`;
- report recovered @25/@50/@100/@500, top-100 dominant precision, MRR, full-catalogue qualified matches, and median top-500 fragmentation.

For annual evaluation, restrict each dual-year family to member IDs belonging to that year; its prelabel pooled rank cannot change.

## 7. Binding development gate

Use the **same no-regression structure** that recurrent-EOM v1 had to satisfy when it replaced vanilla HDBSCAN, now with recurrent-EOM v1 as parent.

Dual-Year Reciprocal HDBSCAN v1 passes only if:

1. recovered@100 is strictly higher than recurrent-EOM v1 in at least one year and not lower in the other;
2. recovered@50 is not lower in either year;
3. top-100 dominant precision is not lower in either year;
4. MRR is not lower in either year;
5. median top-500 fragmentation is not higher in either year;
6. the successor family membership/order differs from recurrent-EOM v1, proving the mechanism is active.

Pass token:

`PASS_DUAL_YEAR_RECIPROCAL_HDBSCAN_V1_GMN_DEVELOPMENT`

Otherwise:

`FAIL_DUAL_YEAR_RECIPROCAL_HDBSCAN_V1_GMN_DEVELOPMENT`.

The first technically valid outcome is binding. Failure permanently closes this exact successor. No centroid alternative, matching threshold, one-to-many matching, score combiner, HDBSCAN parameter, representation, ranking key, or gate may be changed in response.

A PASS authorizes only a separately frozen exposed SonotaCo comparator against the current recurrent-EOM/v31 controls; it does not authorize target access.

## 8. Claim boundary

If successful, the intended methodological claim is **independently estimated annual HDBSCAN density hierarchies coupled by parameter-free reciprocal-nearest recurrent families**. HDBSCAN remains explicitly cited as the parent algorithm.
