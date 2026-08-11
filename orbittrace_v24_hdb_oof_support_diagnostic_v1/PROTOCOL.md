# OrbitTrace v24 HDB strict-OOF training-support diagnostic v1

## Role
Post-result diagnostic only after #1018 showed the exact radius-1 graph is extremely pure but too sparse to explain most v24 HDBSCAN misses, and after the obvious 71D target/loss variants failed. This diagnostic selects no successor and evaluates no new ranking.

## Frozen scientific replay
Use the exact immutable #950 v24 pretruth payload, exact annual F1 targets for the unchanged v22 best label, exact strict whole-shower five-fold assignment, exact #839 inverse-group weights, and the exact #839 ExtraTrees regression architecture for the two annual heads. Exact v24 HDBSCAN 2013/2014 fused metrics must reproduce before diagnostic interpretation.

## Support measurement
For each OOF fold and annual head separately, after fitting the exact v24 forest:
- define a training family as high-quality for year y iff its exact frozen annual target F1_y > 0.5, using the existing literature recovery threshold;
- for each held-out family and each tree, record whether the held-out family lands in a leaf containing at least one high-quality training family;
- annual `positive_leaf_support_fraction` is the fraction of trees satisfying that condition;
- also record the mean number of distinct high-quality strict shower groups sharing the held-out leaf across trees.

No distance metric, neighborhood radius, support threshold, feature transform, tree subset, class definition, or parameter is searched.

For HDBSCAN recoverable groups in each year, use the exact v24 fused order and the same annual recoverability definition as #1018. For each group report the earliest-ranked annual-recoverable family and that family's support measurements. Split summaries only by whether the group is surfaced within the already-frozen HDBSCAN budget (11 in 2013, 9 in 2014) or missed.

## Interpretation boundary
This diagnostic asks only whether missed high-quality HDBSCAN families occupy forest regions with less high-quality training support than surfaced recoverable families. It does not authorize a support-weighted score, OOD penalty/bonus, kNN model, leaf-proximity model, new feature, altered forest, alternate threshold, or literature evaluation. Any successor must be separately frozen after this diagnostic.

SonotaCo 2013/2014 remains exposed development-only. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar longitude 20-55 degrees remain inaccessible.
