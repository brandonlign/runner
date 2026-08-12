# OrbitTrace GMN–SonotaCo nuisance-nullspace representation diagnostic v1

## Status

This protocol is frozen before the first result-bearing execution. This is a truth-free representation diagnostic, not a promoted shower-quality ranker and not external validation.

## Scientific motivation

The already-frozen GMN–SonotaCo generic-feature diagnostic found strong survey distinguishability in the existing 21D source-blind family representation. The question tested here is whether a small linear subspace carrying survey identity can be removed without materially destroying the within-survey candidate geometry.

This is deliberately distinct from v60. v60 changed fold-local coordinate scaling inside the SonotaCo v31 scientific ranker and failed binding development. This experiment does not use robust/MAD scaling, does not alter v31, and does not evaluate shower truth or literature comparators.

The design follows the general domain-adaptation principle of separating domain-specific from transferable representation directions, while explicitly guarding against the information-loss failure mode of non-invertible domain-invariant representations.

## Frozen inputs

Exactly the same truth-free inputs and candidate universes as `orbittrace_gmn_sonotaco_domainshift_diagnostic_v1`:

- target-excluded GMN 2022/2023 hard + P19 + P20: 4,504 families;
- canonical label-free SonotaCo 2013/2014 hard + P19 + P20: 334 families;
- the same 21 generic source-blind features in the same order;
- the exact deterministic five folds balanced within survey-domain × generator-source strata;
- exact frozen HGB domain classifier: learning rate 0.05, 250 iterations, 31 max leaves, L2 1.0, random state 20260809, inverse-domain-size fold-training weights.

No SonotaCo shower truth, matched literature rows, comparator outcomes, target identity, target-region events, MAARSY, or DMS may be loaded.

## Sole successor transform

For each OOF fold independently, using only that fold's training rows and survey identity:

1. Standardize each of the 21 coordinates by the pooled fold-training mean and population standard deviation. A zero standard deviation is replaced by 1.0. No robust scaling, clipping, quantile transform, rank transform, feature dropping, feature weighting, or parameter search is allowed.
2. Within each generator source `hard`, `p19`, and `p20`, compute the 21D difference between the SonotaCo and GMN fold-training means in standardized coordinates.
3. Stack the three difference vectors into a 3×21 matrix.
4. Compute its deterministic SVD and remove the complete numerical row-space with singular values greater than `max(singular_values) * 1e-12`. The removed nuisance rank is therefore fixed by exact numerical rank and cannot exceed 3. There is no selected component count.
5. Apply the orthogonal projection `z' = z - (z V^T) V` to both training and held-out rows, where rows of `V` are the retained right-singular nuisance directions.
6. Train the exact frozen HGB survey classifier on projected fold-training rows and predict the held-out rows.

The transform may use survey identity because this is a transductive unsupervised domain-adaptation diagnostic. It may not use shower labels, comparator outcomes, or any scientific target.

## Frozen no-truth structure-retention measurements

Structure is measured only on each held-out fold, comparing pooled-z-scored coordinates immediately before nuisance projection with the projected coordinates.

For each survey domain separately:

- Spearman correlation of all finite pairwise Euclidean distances among held-out rows;
- mean 10-nearest-neighbor retention fraction, with `k=min(10,n-1)` per held-out domain.

These metrics use no shower truth.

## Frozen gates

The experiment is a representation-level PASS only if all conditions hold on the first technically valid execution:

1. Exact baseline domain-classifier OOF ROC AUC reproduces within `1e-12` of `0.883569` when rounded source result is represented by the frozen diagnostic artifact's exact stored value; implementation must compare against the exact value read from that reproduced diagnostic output rather than hard-coding a truncated decimal.
2. Projected OOF ROC AUC is at least `0.10` lower than the reproduced baseline AUC.
3. GMN held-out pairwise-distance Spearman correlation is at least `0.90` after pooling all fold-held-out pair pairs by Fisher-z-safe arithmetic mean of per-fold correlations.
4. SonotaCo held-out pairwise-distance Spearman correlation is at least `0.90` by the same rule.
5. GMN mean held-out 10-NN retention is at least `0.70`.
6. SonotaCo mean held-out 10-NN retention is at least `0.70`.
7. Every fold has nuisance rank between 1 and 3 and all outputs are finite.

Failure of any gate permanently rejects this exact nuisance-nullspace v1. No rescue by changing standardization, source stratification, nuisance rank, SVD tolerance, classifier, folds, thresholds, neighborhood k, structure metric, feature subset, or adding another projection/alignment variant based on the result.

A PASS does **not** establish improved shower ranking. It only permits a separately frozen scientific successor to test whether this representation transfers useful structure into the exposed SonotaCo development benchmark.

## Protected-data firewall

- Protected solar-longitude exclusion remains `[20.0, 55.0]` at GMN source construction.
- SonotaCo shower truth access: false.
- Literature-comparator evaluation: false.
- Matched comparator rows used: false.
- OrbitTrace target-information access: false.
- Protected target-region events accessed: false.
- MAARSY scientific access: false.
- DMS scientific access: false.
- Post-result search or second transform: false.
