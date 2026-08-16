# OrbitTrace relative-neighborhood topomodal scale diagnostic v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY DIAGNOSTIC OUTCOME.**

This is a zero-label structural diagnostic only. It cannot open shower truth or promote a paper method.

## Scientific motivation

PR #1284 established a strong sample-size-generalizing candidate architecture from one fixed physical scale: an exact radius-1 physical graph, radius-count density, and the complete ToMATo mode-merging hierarchy. Its descendants repeatedly recover substantially more known showers at ~700 and ~5.8k events with higher purity and fragmentation 1, but multiple frozen ranking/extraction rules still place those recovered showers later than recurrent-EOM.

One plausible structural cause is that the dense radius graph contains many locally redundant edges. Those edges do not change local radius-count density, but they can change upper-level-set connectivity and therefore where modal basins merge. This diagnostic asks whether a **parameter-free relative-neighborhood pruning of the already-frozen physical graph** produces a more sample-size-coherent modal hierarchy while preserving #1284's proven density coordinate.

This is not a connected-component clustering test. The relative-neighborhood graph retains a spanning skeleton within ordinary Euclidean components; the scientific object being tested is the resulting **density merge hierarchy**, not raw graph components.

This is distinct from the closed MST/rank-density/single-link lanes: edge lengths are not used as a hierarchy level or persistence score. The hierarchy level remains the exact #1284 radius-count density field; only the neighborhood relation supplied to ToMATo changes.

## 1. Firewall

Use only target-excluded GMN 2022+2023 geometry. Remove inclusive solar longitude `[20.0,55.0]` before geometry.

Forbidden:

- OrbitTrace target information or target-region events;
- shower labels/truth in any graph, density, hierarchy, candidate, gate, or interpretation;
- SonotaCo scientific access;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- result-informed graph rule, inequality/tie rule, radius, physical scale, density, support, persistence threshold, hierarchy cut, candidate rank, subset, salt, metric, or gate change.

## 2. Frozen nested subsets

Reuse exact PR #1272 identity rule:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Use exactly four nested pairs:

- coarse denominator `128`, buckets `0,1,2,3`;
- fine denominator `1024`, the same buckets.

No other denominator, bucket, salt, or replicate is authorized.

## 3. Exact #1284 physical embedding and radius neighborhoods

Reuse without modification:

- `h_sol = 2 sin(5°/2)`;
- `h_rad = 2 sin(4°/2)`;
- `h_logv = ln(1.1)`;
- `Z = (cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, ln(v_g)/h_logv)`;
- sort observations by exact event ID;
- exact Euclidean radius `r=1.0`, `eps=0`.

Construct the exact symmetric radius-1 neighborhood lists including self exactly as #1284.

## 4. Density is frozen to #1284

For every observation `i`, retain the exact #1284 density

`rho_i = |N_1(i)| / n`,

where `N_1(i)` is the original radius-1 neighborhood including self.

**RNG pruning must not alter `rho`.**

No kNN density, RNG-degree density, empirical rank, annual density, recurrence coordinate, smoothing, transform, or rescaling is authorized.

## 5. Exact radius-capped relative-neighborhood graph

Consider every distinct undirected #1284 radius edge `{i,j}` with `d_ij <= 1`.

Retain `{i,j}` iff there exists **no** third observation `k != i,j` satisfying both

`d(i,k) < d(i,j)` and `d(j,k) < d(i,j)`.

Equivalently, retain the edge iff the open relative-neighborhood lune is empty. The inequalities are strictly `<`; exact equal-distance witnesses do not prune an edge.

Because every tested edge has `d_ij <= 1`, any valid witness must lie within the original radius-1 neighborhoods of both endpoints. Therefore the implementation must search the exact intersection `N_1(i) ∩ N_1(j)` and is not permitted to approximate or truncate witness search.

The manual ToMATo neighborhood list for each observation is exactly:

- self; plus
- every endpoint connected by a retained RNG edge.

Verify exact symmetry and self-inclusion.

No Gabriel graph, kNN graph, MST-only graph, Delaunay approximation, edge weight, adaptive radius, epsilon tolerance, or stochastic pruning is authorized.

## 6. ToMATo hierarchy

Use GUDHI `3.12.0`, `Tomato(graph_type='manual', density_type='manual')`, with:

- manual graph = exact self+RNG neighborhood lists above;
- manual weights = unchanged #1284 `rho`.

Fit once per frozen subset.

Reconstruct the complete ToMATo merge hierarchy exactly as #1284:

- every leaf basin;
- every internal merged membership;
- every root/component membership;
- exact membership deduplication;
- report every unique membership with support >=4.

There is no prominence threshold, cluster-count target, flat cut, EOM pruning, root exclusion, ranking, or truth-informed extraction.

## 7. Exact recurrent-EOM comparator

On every same subset reconstruct exact recurrent-EOM HDBSCAN v1 unchanged:

- GEO6;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean;
- exact annual-normalized recurrent-EOM kernel;
- exact FOSC/EOM extraction.

No truth is opened.

## 8. Cross-scale metric

Reuse PR #1284 exactly.

For each bucket and each method:

1. let `F` be fine-subset candidates;
2. restrict every coarse candidate to the exact fine event universe;
3. discard restricted memberships below support 4;
4. deduplicate exact restricted memberships;
5. for every fine candidate compute best Jaccard similarity to any retained restricted coarse candidate;
6. record candidate-unweighted mean/median best Jaccard, exact-match fraction, and candidate counts.

Primary metric: fine→coarse candidate-unweighted mean best Jaccard.

Also report, without adding a gate, the exact #1284 historical structural controls:

- pooled fine→coarse Jaccard `0.8067062037`;
- median bucket score `0.8129624258`;
- strict wins vs recurrent-EOM `4/4`.

These are descriptive predecessor controls only and cannot change the frozen gate below.

## 9. Frozen interpretation gate

Return

`SUPPORTS_RNG_TOPOMODAL_CROSS_SCALE_COHERENCE`

iff all five conditions hold:

1. RNG-ToMATo produces at least one eligible candidate in all eight subsets;
2. in every fine subset, RNG-ToMATo candidate count is at least exact recurrent-EOM candidate count;
3. pooled fine→coarse candidate-unweighted mean best Jaccard is strictly greater than recurrent-EOM;
4. median of the four bucket-level fine→coarse mean-best-Jaccards is strictly greater than recurrent-EOM; and
5. RNG-ToMATo has a strict bucket-level mean-best-Jaccard win over recurrent-EOM in at least three of four buckets.

Otherwise return

`REFUTES_RNG_TOPOMODAL_CROSS_SCALE_COHERENCE`.

No mixed verdict and no post-result rescue.

## 10. Consequence

A positive result establishes only zero-label structural viability and authorizes one separately frozen target-excluded GMN truth-bearing successor. Before truth opens, that successor must freeze its exact candidate-ordering/extraction semantics and all promotion gates independently.

A negative result permanently closes this exact radius-capped RNG + unchanged #1284 radius-density + complete ToMATo hierarchy architecture. It may not be rescued by changing the RNG inequality, using Gabriel/Delaunay/kNN variants, changing radius/physical scales/density/support, adding persistence cuts, changing subsets/salt, or relaxing gates from the outcome.