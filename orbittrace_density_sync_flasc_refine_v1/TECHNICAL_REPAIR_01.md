# Density-sync FLASC refinement v1 — technical repair 01

First attempted run `31921945971` is a **technical no-result**. It aborted before FLASC branch detection, prelabel freeze, or known-shower evaluation because `HDBSCAN(branch_detection_data=True)` reconstructed 2076 density-synchronous EOM candidates instead of the frozen winner's exact 2094. No scientific metric was produced and no method outcome was observed.

Root cause is the convenience flag: HDBSCAN internally forces `gen_min_span_tree=True` when `branch_detection_data=True`. The frozen v1 protocol requires exact reconstruction of the 2094/179 parent before any branch refinement, so accepting the altered 2076 parent is forbidden.

The only authorized repair is an implementation adapter with unchanged science:

1. fit the exact baseline HDBSCAN exactly as the 179 winner did (`branch_detection_data=False`, `gen_min_span_tree=False`);
2. require exact 2094 candidate count and exact frozen ordered-membership SHA before any FLASC support computation;
3. generate the mutual-reachability MST separately with HDBSCAN's own `_hdbscan_boruvka_kdtree` using the same GEO6 matrix and exact frozen HDBSCAN density parameters (`min_samples=10`, Euclidean, alpha 1, leaf size 40, approximate MST enabled, core-distance jobs 4);
4. generate `BranchDetectionData` directly from the same GEO6 matrix, the **exact density-synchronous winner labels**, the exact parent condensed tree, and `min_samples=10`;
5. attach only those support objects to the already-verified exact parent model and invoke the same frozen `detect_branches_in_clusters` call with explicit exact winner labels/probabilities.

This does not change the FLASC branch graph definition, parent candidates, branch settings, substitution rule, ranking rule, evaluator, firewalls, or binding gate. It only avoids a library convenience flag that perturbed the prerequisite parent fit.

No retry using the 2076 parent is authorized. No core/full switch, two-sided branch labeling, branch-size/persistence tuning, parent+branch union, branch quota, score blend, reranking rescue, geometry change, or HDBSCAN parameter tuning is authorized.