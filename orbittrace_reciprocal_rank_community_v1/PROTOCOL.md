# OrbitTrace Reciprocal Rank Communities v1 — frozen development protocol

## Scientific role

This is a separately named successor created after:

1. fixed-scale TopoModal beat Sugar and classical D_SH but lost narrowly to the exact published catalogue-HDBSCAN benchmark on exposed SonotaCo 2013/2014; and
2. Compact Mixture v1 failed decisively against that HDBSCAN benchmark.

All predecessor results remain binding. This successor does not rescue or modify either predecessor.

SonotaCo 2013/2014 remains **EXPOSED DEVELOPMENT ONLY**. A pass here is development evidence, not external validation.

## Motivation

Compact Mixture v1 showed that forcing the full meteor catalogue into a global hard parametric partition loses too much stream structure. HDBSCAN's advantage is plausibly its ability to follow non-Gaussian shapes and heterogeneous local density.

v1 therefore tests a fundamentally different architecture:

**represent each annual catalogue as a locally adaptive reciprocal-neighbor graph and detect stream-like modules by global graph community structure rather than a density hierarchy or parametric mixture.**

The graph uses reciprocal *ranks*, not absolute local density, so sampling density changes affect the neighborhood order less directly than fixed distance or fixed minimum-cluster-size rules.

This method does not use DBSCAN/HDBSCAN connectivity, mutual reachability, MST condensation, EOM, ToMATo, Gaussian mixtures, D-criteria, local Poisson shells, orbital elements, station metadata, uncertainty fields, shower labels, or target information.

## Relation to prior methods

Mutual k-nearest-neighbor graphs and modularity community detection are established general-purpose ideas. The scientific hypothesis tested here is the OrbitTrace-specific construction combining:

- the fixed physical meteor embedding below;
- a sample-size-derived neighborhood order;
- mutual-neighbor admission;
- reciprocal-rank edge weights;
- a single standard modularity partition;
- modularity-contribution candidate ordering.

This protocol does not claim that nearest-neighbor graphs or modularity themselves are new.

## Frozen input

Use the exact HDBSCAN-compatible, truth-free SonotaCo 2013 and 2014 annual row universes from the prior matched-literature benchmark.

The protected solar-longitude interval `[20°,55°]` is excluded inclusively upstream.

Only these fields enter detection:

- `id` for membership bookkeeping;
- `sol`;
- `sun_lon`;
- `ecl_lat`;
- `vg`.

No `iau`, truth/shower field, orbit, uncertainty, station metadata, year-as-feature, or target information enters graph construction or ranking.

Unlike TopoModal and Compact Mixture, v1 fits each annual catalogue independently because the published HDBSCAN comparator is itself an annual catalogue method. The algorithm/rule is identical between years.

## Frozen physical embedding

For each event:

`[cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, log(vg)/h_logv]`

where:

- `h_sol = 2 sin(5°/2)`;
- `h_rad = 2 sin(4°/2)`;
- `h_logv = ln(1.1)`.

This is the same truth-independent physical geometry frozen for TopoModal.

## Frozen neighborhood rule

For a catalogue of `n` events define

`k(n) = ceil(log2(n))`.

For each event, compute its `k` nearest other events in Euclidean distance in the physical embedding.

An undirected edge `(i,j)` exists iff:

- `j` is among the top-`k` neighbors of `i`; and
- `i` is among the top-`k` neighbors of `j`.

Let `r_ij` be the 1-based rank of `j` in `i`'s neighbor list and `r_ji` the reciprocal rank. Give the edge frozen weight

`w_ij = 1 / sqrt(r_ij r_ji)`.

Distance ties, if any, are resolved by ascending row index after distance. No distance threshold or density estimate is used.

## Frozen partition

Create one weighted undirected graph containing all catalogue events, including isolated vertices.

Partition it once with NetworkX Louvain modularity optimization using:

- edge attribute `weight`;
- resolution `1.0`;
- convergence threshold `1e-7`;
- seed `20260816`.

No resolution scan, consensus ensemble, multiscale search, repeated-seed selection, or HDBSCAN-informed partition choice is allowed.

Runtime is frozen to:

- NumPy `2.3.5`;
- SciPy `1.17.0`;
- scikit-learn `1.8.0`;
- NetworkX `3.6.1`.

## Frozen candidate construction and order

A community is reportable iff it has annual support of at least 4 events.

For graph total edge weight `m`, community internal edge weight `W_C`, and weighted volume `V_C`, define its additive Newman-Girvan modularity contribution

`Q_C = W_C/m - (V_C/(2m))^2`.

Rank reportable communities by descending `Q_C`. Resolve exact ties only by SHA-256 of sorted event IDs.

No truth, HDBSCAN overlap, annual recurrence, orbital coherence, external quality score, or post-partition metric changes this order.

## Frozen HDBSCAN comparison

Reuse byte-for-byte the exact published catalogue-HDBSCAN outputs already frozen by the prior literature benchmark.

For each year independently:

1. let `B` equal the complete HDBSCAN family count for that year;
2. take the first `B` Reciprocal Rank Communities in the frozen annual order;
3. use the identical frozen truth map and Hungarian maximum-F1 evaluation used previously.

Eligible known showers remain those with at least 4 events in the exact annual row universe.

A year is a win iff:

- Reciprocal Rank Communities macro-F1 is strictly greater than HDBSCAN macro-F1; and
- recovered showers with assigned F1 > 0.5 are at least the HDBSCAN count.

`PASS_RECIPROCAL_RANK_COMMUNITY_V1_HDBSCAN_DEVELOPMENT` requires wins in both 2013 and 2014. Any other valid result is `FAIL_RECIPROCAL_RANK_COMMUNITY_V1_HDBSCAN_DEVELOPMENT`.

## Pretruth structural audit

Before any v1 truth access, the exact implementation must satisfy on both years:

- `k(n)` equals the frozen formula;
- reciprocal graph has more edges than vertices;
- partition contains more than one community;
- reportable candidate capacity is at least the exact HDBSCAN budget;
- total weighted modularity is finite and positive;
- candidate ranks are contiguous and deterministic.

These gates are structural only and contain no shower truth.

## Scientific firewall and closure

Source, protocol, candidate catalogues/orders, row hashes, exact HDBSCAN outputs, and evaluation rule are hash-frozen before truth opens.

After the first technically valid v1 outcome:

- no `k` formula, edge rule, weight, Louvain resolution/threshold/seed, support floor, candidate score, feature, metric, budget, or tie rule may be changed as a v1 rescue;
- failure closes this exact architecture;
- success advances the exact frozen architecture to a separately preregistered target-excluded GMN scale/generalization test.

Protected `[20°,55°]`, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.
