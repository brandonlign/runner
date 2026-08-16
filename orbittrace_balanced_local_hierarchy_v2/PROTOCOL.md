# OrbitTrace balanced cross-year local hierarchy v2 — frozen protocol

## Why v2 exists
Balanced local graph v1 failed its label-free structural gate because a hard `s<=1` connectivity cut percolated: 705,796 of 738,682 events entered one component. V1 is permanently failed and is not retuned.

V2 keeps the same survey-relative geometry but removes the hard connectivity cut entirely. It uses the full reciprocal cross-year edge-weight hierarchy and standard EOM persistence to select components *before* the background graph merges.

## Scientific goal
Test a detector whose family formation is based on dimensionless, survey-local cross-year geometry rather than absolute survey density, with a direct rationale for cross-survey transfer.

This is not a reranker, member veto, threshold search, conformal rule, or target-specific mechanism.

## Data/firewall
- GMN 2022+2023 development geometry only.
- Solar longitude 20°–55° excluded before all method operations.
- OrbitTrace target information forbidden.
- Stage 0 uses no known-shower label values.
- SonotaCo 2013/2014, ASFN, EFN, AMOS, MAARSY, DMS are not accessed.

## Representation and inherited constants
Use exact inherited GEO6:

`[cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72]`

- `k=10`, inherited from current HDBSCAN `min_samples=10`.
- `min_cluster_size=10`, inherited from the current detector.
- Exact `hdbscan==0.8.43` tree condensation/EOM implementation is pinned.

No feature fitting, axis-weight search, uncertainty proxy, learned metric, epsilon, persistence threshold, or max-cluster-size tuning is allowed.

## Survey-local reciprocal edge geometry
For every event `i`, same-year local scale `r_i` is its distance to the 10th other event in the same year.

For every 2022 event query its 10 nearest 2023 events, and vice versa. Keep only reciprocal cross-year top-10 pairs.

For every reciprocal pair `(i,j)`, define

`s_ij = d_ij / sqrt(r_i*r_j)`.

Unlike v1, **no edge is removed by an `s` threshold**.

## Deterministic hierarchy
1. Build the undirected sparse graph containing every reciprocal pair weighted by `s_ij`.
2. Compute its minimum-spanning forest.
3. If the reciprocal graph has multiple disconnected components, connect their smallest stable event-index representatives in deterministic order using virtual edges of distance `+infinity`. These edges only create a global lambda=0 root structure; they do not create finite-density scientific connections.
4. Sort MST/virtual edges by `(distance, endpoint_1, endpoint_2)`.
5. Convert the resulting `N-1` edge list to the standard HDBSCAN single-linkage tree using the pinned `hdbscan._hdbscan_linkage.label` implementation.
6. Condense/select with pinned HDBSCAN EOM, `min_cluster_size=10`, `allow_single_cluster=False`, `cluster_selection_epsilon=0`, `cluster_selection_persistence=0`, `max_cluster_size=0`.

The scientific metric is therefore the reciprocal local-scale hierarchy itself; HDBSCAN is used only for standard tree condensation/EOM selection on this custom deterministic graph.

## Frozen candidate ranking
For each selected EOM cluster compute its returned cluster persistence plus year support. Rank lexicographically by:
1. larger HDBSCAN cluster persistence;
2. larger `min(n_2022,n_2023)`;
3. larger cross-year balance `2*min(n_2022,n_2023)/(n_2022+n_2023)`;
4. larger member count;
5. stable SHA256 family ID.

No known-shower labels enter selection or ranking.

## Stage 0 label-free structural gate
Freeze the full ordered memberships before any known-shower label is indexed.

PASS requires:
- at least 100 selected candidate families;
- largest selected family <=1% of all accessible events;
- largest selected family <=5% of all events assigned to selected families;
- at least one finite reciprocal edge and at least two raw reciprocal-graph connected components, proving the hierarchy is nontrivial;
- no target/external firewall violation.

A Stage-0 failure kills v2. No post-result graph/rank/EOM parameter tuning is authorized.

## Binding Stage 1 GMN gate
Only after Stage 0 passes, evaluate the exact frozen candidate order/memberships against the already-used target-excluded GMN known-shower labels.

Relative to density-synchronous recurrent-EOM (2022 @100=89, 2023 @100=90, total=179), PASS requires:
- total recovered@100 >=184 (+5);
- each year: recovered@50 and @100 not lower;
- each year: top-100 dominant precision and MRR not lower;
- each year: median top-500 fragmentation not higher;
- all reproducibility/firewall checks pass.

Anything else FAILS. No rescue/tuning after truth.

## Transfer rule
A GMN PASS earns exactly one separately frozen exposed-SonotaCo transfer benchmark against the frozen literature comparators. Broad generalization still requires a genuinely untouched external dataset.