# Stratified-core HDBSCAN v1 Boruvka initialization repair

**Classification: engineering-only equivalence repair after zero-truth no-result. The frozen scientific core-distance rule is unchanged.**

Audit 2 showed that replacing `core_distance_arr` in a `min_samples=0` Boruvka instance and immediately calling `spanning_tree()` does not reproduce standard HDBSCAN under ordinary pooled core distances. Upstream HDBSCAN 0.8.43 explains the difference: `_compute_bounds()` normally uses the `min_samples+1` pooled nearest-neighbor query to seed a first approximate-Boruvka candidate edge for each point when it can prove that the candidate mutual-reachability distance equals that point's core distance, then invokes compiled `update_components()` before the public `spanning_tree()` loop.

## Authorized initialization repair

Retain the frozen public-core-array injection path and the unchanged compiled HDBSCAN Boruvka continuation, but recreate the omitted first-pass state under the supplied injected core vector:

1. Build the same pooled Euclidean `KDTree(X, leaf_size=40)`.
2. Query the same `min_samples+1 = 11` nearest pooled rows with `dualtree=True, breadth_first=True`; this query is for HDBSCAN initialization only and does not define the stratified core.
3. Construct `KDTreeBoruvkaAlgorithm` with `min_samples=0`, alpha 1, internal leaf size 13, `approx_min_span_tree=True`, `n_jobs=1` so no constructor candidate edge is scientifically committed.
4. Overwrite its public `core_distance_arr` in place with the supplied Euclidean core vector squared, exactly as frozen.
5. Recreate HDBSCAN 0.8.43's first shortcut candidate rule using the injected reduced core vector and the pooled 11-NN indices:
   - for each point `n`, scan those 11 indices in returned order;
   - skip exact self `m==n`;
   - choose the first `m` satisfying `core_rdist[m] <= core_rdist[n]`;
   - set public `candidate_point[n]=n`, `candidate_neighbor[n]=m`, `candidate_distance[n]=core_rdist[n]`;
   - otherwise leave the constructor's no-candidate state unchanged.
6. Set the public Boruvka `bounds` vector temporarily to exactly zero. Since root-to-root reduced distance is zero and the compiled traversal condition is strict `< bound`, the first public `spanning_tree()` traversal is forced to make no changes; its immediately following compiled `update_components()` therefore consumes exactly the recreated shortcut candidates.
7. The following no-candidate iteration clears stale successful candidate endpoints and, because it merges no components, HDBSCAN's unchanged approximate `update_components()` resets bounds to DBL_MAX. Subsequent iterations then use the unchanged compiled dual-tree Boruvka continuation on the injected core vector.
8. Sort MST edges and construct linkage/condensed tree exactly as already frozen.

This is authorized only if zero-truth synthetic ordinary-core injection reproduces standard forced `boruvka_kdtree` HDBSCAN exactly. Full-GMN ordinary-core/recurrent-parent equivalence remains mandatory before scientific truth evaluation.

No change is authorized to:
- `k_year=5`;
- exact-self exclusion / duplicate-other inclusion;
- `core_strat=max(d_2022,d_2023)`;
- mutual-reachability definition;
- HDBSCAN `min_cluster_size=10`, `min_samples=10`, alpha, metric, leaf sizes, or approximation setting;
- recurrent-EOM extraction/ranking;
- development evaluator or gate.
