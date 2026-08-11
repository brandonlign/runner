# OrbitTrace v24 HDB regression-leaf dilution diagnostic v1

## Scientific role

Post-result diagnostic only. No successor method, score, order, threshold, model, or parameter is selected here.

PR #1020 reproduced exact v24 HDB performance and showed that surfaced recoverable groups occupy exact-v24 leaves with more high-quality training support in aggregate. But several of the strongest missed families still land in leaves containing high-quality training families in most trees (for example support fractions above 0.9). Therefore simple support presence is not sufficient to explain regression shrinkage.

This diagnostic asks one narrower question: **when high-quality training examples are present in the exact v24 leaves, are they diluted by much larger low-quality training weight, causing the regression leaf mean to remain low?**

## Frozen replay

Reuse the exact immutable PR #950 v22 71D payload, exact annual F1 targets for the unchanged v22 best label, exact strict whole-shower five-fold assignment, exact #839 inverse-group sample weights, and exact #839 ExtraTrees regression architecture for both annual heads. Exact v24 HDB 2013/2014 fused metrics must reproduce before any diagnostic result is interpreted.

## Frozen leaf measurements

For each OOF fold and annual head separately, after fitting the exact v24 forest:

1. define a high-quality training family as exact annual F1 > 0.5, using the existing literature recovery threshold;
2. for every tree and every training leaf, compute:
   - total inherited #839 sample weight in that leaf;
   - high-quality inherited sample weight in that leaf;
   - `positive_weight_fraction = positive_weight / total_weight`;
   - inherited-weighted mean annual F1 in that leaf;
3. for every held-out family, across all exact v24 trees record:
   - `positive_leaf_support_fraction`: fraction of trees whose held-out leaf contains any high-quality training weight (exactly the #1020 support concept);
   - `positive_weight_fraction_mean`: mean positive-weight fraction over all trees;
   - `positive_weight_fraction_given_supported_leaf_mean`: mean positive-weight fraction only over trees with nonzero high-quality weight (0 if no tree is supported);
   - `leaf_target_mean`: mean inherited-weighted training annual-F1 mean across trees; this must reproduce the corresponding exact forest prediction to numerical tolerance;
   - `dilution_gap = positive_leaf_support_fraction - positive_weight_fraction_mean`.

No leaf-size threshold, purity cutoff, tree subset, alternate class threshold, target transform, weight transform, feature transform, or parameter search is allowed.

## HDB group comparison

For each year, define an HDB annual-recoverable strict shower group exactly as in #1018/#1020: at least one HDB family in that group has exact annual F1 > 0.5. Represent each group by its annual-recoverable family with the earliest exact v24 final rank, stable family ID tie-break. A group is surfaced iff that representative lies within the already-frozen HDB budget (11 in 2013, 9 in 2014).

For surfaced and missed representatives report only predeclared summaries:

- group count;
- median positive-leaf support fraction;
- median positive-weight fraction;
- median positive-weight fraction conditional on a supported leaf;
- median dilution gap;
- median exact v24 annual forest prediction;
- median exact v24 final rank.

All representative rows are retained, including the exact family ID, annual F1, fold, support, purity, dilution, prediction, and rank.

## Interpretation boundary

This diagnostic can establish whether the remaining v24 regression shrinkage is consistent with **leaf dilution**: high-quality examples are frequently present but carry only a small fraction of leaf training weight. It does not authorize a leaf-purity score, exceedance-probability score, quantile/max leaf statistic, altered regression target, new forest, or literature evaluation. Any successor must be separately frozen after this diagnostic.

SonotaCo 2013/2014 remains exposed development-only. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar-longitude 20°–55° content remain inaccessible.