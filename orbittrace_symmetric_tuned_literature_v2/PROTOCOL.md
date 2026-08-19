# OrbitTrace symmetric tuned literature benchmark v2

## Question

Does recurrent-EOM outperform Sugar-style uncertainty-aware DBSCAN and catalogue HDBSCAN when all three methods receive the same event universe, the same temporal information, the same development labels, a method-native hyperparameter search, and the same test evaluator?

## Common event universe

For each of SonotaCo 2013 and 2014, use the exact intersection of event IDs present in both frozen literature-comparator routes. Merge only fields already present in the two frozen row payloads. All three algorithms receive the identical pooled 2013+2014 common-event universe before any fold-specific scoring.

## Two-fold cross-year design

- Fold A: tune on 2013 truth, evaluate only on 2014 truth.
- Fold B: tune on 2014 truth, evaluate only on 2013 truth.

The pooled 2013+2014 event geometry is label-free and identical for every method in both folds. Only the development-year labels may choose hyperparameters in each fold. The opposite-year labels may not influence selection.

## Method-native tuning

### recurrent-EOM

Exact recurrent-EOM objective and GEO6 representation. Search only HDBSCAN finite-support settings:

`(min_cluster_size,min_samples) = (5,5), (10,5), (10,10), (20,10), (20,20), (40,20), (40,40), (80,40), (80,80)`.

The recurrence combiner remains the published/frozen annual minimum; it is not changed.

### catalogue HDBSCAN

Use the frozen 2025 comparator feature transform. Search the same finite-support grid as recurrent-EOM, and both native cluster-selection modes `eom` and `leaf`.

### Sugar-style uncertainty-aware DBSCAN

Use the frozen Sugar uncertainty source, six-dimensional feature transform, Gaussian uncertainty clones, overlap merger, hard assignment, fourth-neighbour calculation, and DBSCAN implementation. Keep `min_samples=5`, and search the dataset-dependent fourth-neighbour epsilon percentile over:

`10, 15, 20, 23, 25, 30, 35` percent.

Use 100 uncertainty-clone catalogues during development-grid selection and 1000 clones for the final selected configuration in each fold. The final 1000-clone rerun is label-free and occurs only after the percentile has been selected from the development year.

## Common tuning objective

Every candidate catalogue is ranked by its native label-free confidence/stability score. Evaluate the same Hungarian one-to-one shower F1 at common candidate budgets `K = 10, 20, 30, 40`.

Primary development objective: maximize mean macro-F1 across those four budgets. Tie-breakers, in order: total recovered showers across the four budgets, macro-F1 at K=40, then the earlier/simpler grid entry.

## Test reporting

For the opposite-year test labels, report the full K=10/20/30/40 curve plus native complete-catalogue macro-F1. Aggregate the two test folds by mean budget-curve macro-F1 (primary), mean K=40 macro-F1, total recovered showers at K=40, and mean native macro-F1.

No method receives a different truth definition, evaluator, temporal window, event subset, or candidate budget.

## Frozen implementation identities

The recurrent-EOM kernel file must have Git blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`. Sugar candidate construction in the executed driver calls the comparator source's own `transferred_epsilon`, `clone_feature_matrix`, `dbscan_clusters`, `OverlapGraphMerger`, and `hard_assignment` primitives; only the preregistered epsilon percentile and development/final clone counts vary. Catalogue HDBSCAN uses the frozen comparator feature transform and the explicitly declared support/selection grid above.

## Interpretation

This benchmark is a symmetric tuned comparison. It does not assume recurrent-EOM wins. The method with the highest two-fold mean test budget-curve macro-F1 is the primary benchmark winner; all underlying fold/configuration results remain reported regardless of outcome.
