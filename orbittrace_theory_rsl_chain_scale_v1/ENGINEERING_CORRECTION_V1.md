# Engineering correction v1 — no scientific result

Initial run `31933011464` reached the first frozen subset only and then stopped before emitting any structural subset row, comparison, gate, or result JSON.

The exact exception was:

`RuntimeError: nonmonotone linkage distances`

This arose from `hdbscan.robust_single_linkage(..., algorithm='boruvka_kdtree')` returning a linkage array whose rows were not globally ordered by merge distance. The frozen diagnostic correctly failed closed before interpreting the hierarchy.

This is an engineering no-result only:

- no shower truth was opened;
- no protected target information/events were accessed;
- no structural metric, gate, or scientific verdict was emitted;
- `k(n)=ceil(6 ln n)`, `alpha=sqrt(2)`, GEO6, subsets, branch-size bands, structural metrics, and frozen interpretation gate remain unchanged.

Before any rerun, a separate zero-label implementation-equivalence audit must establish that the scalable HDBSCAN mutual-reachability single-link tree with the same `min_samples=k(n)` and `alpha=sqrt(2)` reproduces the public robust-single-link reference hierarchy generated through the package's generic path on predeclared frozen subsets. Only after exact branch/distance equivalence may the scalable sorted-tree implementation replace the technically malformed Boruvka-returned linkage representation.

This correction is implementation-only and does not authorize any scientific method alteration or parameter change.
