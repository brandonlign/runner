# OrbitTrace fixed-scale topological modal hierarchy v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY OUTCOME.**

This is a zero-label structural diagnostic only. It cannot promote a paper method or open shower truth.

It follows the exact target-excluded evidence in PRs #1272–#1282. In particular, PR #1279 showed that fixed-physical-scale modal basins were substantially more cross-scale coherent than recurrent-EOM but formally failed one candidate non-collapse gate because sparse samples lost some supported modes. PRs #1280–#1282 showed that replacing this with generic multiparameter Persistable flattenings does not solve the real-GMN sparse-candidate problem.

The present diagnostic therefore keeps the **exact PR #1279 physical scale** and changes only mode handling: instead of discarding small local modes as separate basins, it constructs the complete topological mode-merging hierarchy at that same scale and exposes every supported hierarchy membership as a candidate. This is motivated by persistence-based mode clustering (Chazal, Guibas, Oudot & Skraba, JACM 2013 / ToMATo). It is not a MeanShift bandwidth rescue.

## 1. Firewall

Use only target-excluded GMN 2022+2023 geometry. Inclusive solar longitude `[20.0,55.0]` is removed before geometry.

Forbidden:

- OrbitTrace target information or target-region events;
- shower labels/truth in any statistic, fit, gate, or interpretation;
- SonotaCo scientific access;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- any result-informed radius, density transform, graph rule, hierarchy pruning, support, subset, salt, metric, or gate change.

## 2. Frozen nested subsets

Reuse the exact PR #1272 hash rule:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Use exactly four nested pairs:

- coarse denominator `128`, buckets `0,1,2,3` (~5.8k events);
- fine denominator `1024`, the same buckets (~0.7k events).

No other denominator, bucket, salt, or replicate is authorized.

## 3. Frozen physical embedding

Reuse PR #1279 exactly:

- `h_sol = 2 sin(5°/2)`;
- `h_rad = 2 sin(4°/2)`;
- `h_logv = ln(1.1)`.

For each normalized event define

`Z = (cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, ln(v_g)/h_logv)`.

No empirical standardization or reweighting is allowed.

Before all graph operations sort events by exact event ID.

## 4. Fixed-scale local field and graph

Use **one and only one radius: `r = 1.0` in Z-space**. This is not a newly selected bandwidth; it is the exact unit physical neighborhood inherited from PR #1279.

Construct the exact symmetric Euclidean radius graph with an edge between observations whose Z-distance is `<= 1.0`, including each observation itself in its neighborhood for density counting.

Define the density weight of event `i` as

`rho_i = |N_i| / n`,

where `N_i` is its exact radius-1 neighborhood including itself and `n` is subset size. The division by `n` is a monotone common rescaling and introduces no fitted parameter.

No kNN graph, adaptive radius, alternate kernel, Gaussian KDE, DTM, recurrence term, or density transform is allowed.

## 5. Topological mode hierarchy

Use GUDHI ToMATo only as the frozen implementation of the Chazal et al. mode-seeking/persistence-merging construction:

- `graph_type='manual'`;
- `density_type='manual'`;
- supply the exact symmetric radius-1 neighbor lists and `rho_i` weights;
- request **no flat cluster count and no merge threshold**.

The hierarchy consists of ToMATo leaf basins plus all internal merge nodes encoded by `leaf_labels_` and `children_`.

Reconstruct exact memberships bottom-up:

1. each leaf membership is the set of observations with that exact leaf label;
2. each internal node membership is the union of its two child memberships;
3. connected-component roots/infinite-persistence modes are retained like every other hierarchy node;
4. deduplicate exact memberships.

Every distinct hierarchy membership with at least **4** observations is an eligible candidate. Four is the project's established minimum evaluable support and is applied only after the hierarchy is constructed.

There is **no persistence threshold, no selected cluster count, no preferred hierarchy level, and no ranking** in this diagnostic.

## 6. Exact recurrent-EOM comparator

On every identical subset reconstruct selected recurrent-EOM HDBSCAN v1 unchanged:

- exact GEO6;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean;
- exact annual-normalized recurrent-EOM stability;
- exact FOSC/EOM extraction.

No truth is opened.

## 7. Cross-scale metric

For each bucket and method separately:

1. let `F` be fine-subset candidates;
2. restrict every coarse candidate to the exact fine event universe and discard restricted memberships below support 4;
3. deduplicate exact restricted memberships;
4. for each fine candidate, record the best Jaccard similarity to any restricted coarse candidate;
5. record candidate-unweighted mean and median best Jaccard, exact-match fraction, and candidate counts.

The **fine→coarse candidate-unweighted mean best Jaccard** is primary because the hypothesis is specifically that a sparse-survey modal family should remain identifiable inside the corresponding denser observation of the same population. The reverse coarse→fine direction is reported diagnostically but is not a frozen gate because this method intentionally exposes a hierarchy of nested candidate memberships rather than one flat partition.

## 8. Frozen interpretation gate

Return

`SUPPORTS_FIXED_SCALE_TOPOMODAL_HIERARCHY_CROSS_SCALE_COHERENCE`

iff all of the following hold:

1. at least one eligible topological-modal candidate exists in all eight subsets;
2. for every one of the four fine subsets, topological-modal candidate count is at least the exact recurrent-EOM candidate count;
3. pooled fine→coarse candidate-unweighted mean best Jaccard is strictly greater for the topological-modal hierarchy than recurrent-EOM;
4. median of the four bucket-level fine→coarse mean-best-Jaccards is strictly greater than recurrent-EOM; and
5. the topological-modal hierarchy has a strict fine→coarse mean-best-Jaccard win in at least three of four buckets.

Otherwise return

`REFUTES_FIXED_SCALE_TOPOMODAL_HIERARCHY_CROSS_SCALE_COHERENCE`.

There is no mixed verdict and no post-result rescue.

## 9. Consequence

A positive result establishes only that same-scale persistence merging fixes the sparse-mode structural bottleneck while preserving cross-scale family identity. It would authorize one separately frozen target-excluded GMN recovery/ranking successor before any shower truth is opened for that successor.

A negative result closes this exact fixed-scale radius-count + radius-graph + complete ToMATo hierarchy architecture. It may not be rescued after outcome by changing radius, physical scale, kernel/density estimator, graph, hierarchy subset, persistence threshold, support, subset, salt, metric, or gate.