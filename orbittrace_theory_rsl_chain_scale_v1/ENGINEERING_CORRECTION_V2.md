# Engineering correction v2 — exact mathematical RSL tree, no scientific result yet

This supersedes only the implementation plan in `ENGINEERING_CORRECTION_V1.md`; it does not change the frozen scientific RSL definition or any structural metric/gate.

## Why v1 could not be used

Initial run `31933011464` failed on the very first subset before emitting any structural subset row or result JSON because the public `hdbscan.robust_single_linkage(..., algorithm='boruvka_kdtree')` path returned a linkage array with nonmonotone row distances.

Source inspection of the pinned `hdbscan==0.8.43` algorithm family shows the relevant distinction:

- the intended robust-single-link mathematical distance is mutual reachability with the frozen `k(n)` and `alpha`;
- HDBSCAN's exact generic path computes `mutual_reachability(distance_matrix, min_samples, alpha)`, constructs the MST, **sorts MST edges by weight**, and only then labels the linkage tree;
- the robust-single-link Boruvka wrapper reaches the same KD-tree/Boruvka construction family but the returned linkage representation encountered by the frozen diagnostic was not monotone.

The diagnostic therefore switches only the hierarchy *implementation* to the exact pairwise generic mutual-reachability path:

`HDBSCAN(min_cluster_size=2, min_samples=k(n), alpha=sqrt(2), metric='euclidean', algorithm='generic')`

and reads only its `single_linkage_tree_`.

`min_cluster_size=2` affects only HDBSCAN's downstream flat/condensed output, which is discarded; the single-link hierarchy itself is determined before condensation by the frozen mutual-reachability `k(n), alpha` rule.

This exact generic implementation is computationally feasible for the already-frozen ~5.8k/~0.7k diagnostic subsets. No full-GMN scientific endpoint is run here.

Unchanged:

- `k(n)=ceil(6 ln n)`;
- `alpha=sqrt(2)`;
- Euclidean GEO6;
- exact eight subsets;
- root-chain metric;
- mass-weighted split-imbalance metric;
- branch-lifetime scale test;
- 7/8 sign gate and all other frozen interpretation clauses;
- all protected-data restrictions.

No previous scientific outcome exists for this protocol, so this is an engineering no-result correction, not a scientific retry or parameter rescue.
