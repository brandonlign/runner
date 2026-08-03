# Graph-threshold correction

The original Stage-0 run iterated candidate edge quantiles from strictest to most permissive and stopped at the first threshold satisfying the frozen null-cluster ceiling. Because the strictest threshold generally passes first, that implementation could unnecessarily suppress weak-stream recovery for every method.

The corrected run keeps the same candidate quantiles, null-cluster ceiling, data, folds, model, baselines, seeds, and decision gates. It changes only the search order so the selected graph threshold is the most permissive tested threshold that still satisfies the pre-established null-cluster ceiling. Pairwise matched-FPR and calibration results are unchanged by this correction.
