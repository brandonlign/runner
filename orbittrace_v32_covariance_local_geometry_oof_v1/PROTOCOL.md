# OrbitTrace v32 covariance-aware strict-OOF local-geometry margin ranker v1

## Scientific role

Separately frozen exposed-SonotaCo development successor after v31 failed 4/4 while producing the closest current HDBSCAN-2014 result. v31 showed that the exact #1021 local-support signal is useful but ordinary independently standardized Euclidean geometry still loses HDBSCAN. Diagnostic #1028 then showed that the full-space positive-support gap is distributed across the frozen representation and that the 34D raw-#839 plus 30D relative-noncategorical blocks dominate ordinary Euclidean squared distance. Those two blocks are structurally correlated because the latter is deterministically derived from the former. This motivates one covariance-aware geometry, not feature deletion or block weighting.

SonotaCo 2013/2014 remains exposed development-only.

## Sole scientific change from v31

Everything in v31 is fixed except the distance metric.

For each deterministic strict whole-shower OOF fold, compute from the complete fold-training 71D feature matrix only:

1. the ordinary arithmetic mean vector;
2. the population covariance matrix (`ddof=0`);
3. its Moore-Penrose pseudoinverse using pinned NumPy `np.linalg.pinv(covariance, hermitian=True)` with the library default numerical tolerance and no user-specified regularization or cutoff.

For held-out vector `x` and training reference `r`, the sole distance is the standard generalized Mahalanobis distance

`sqrt((x-r)^T covariance_pinv (x-r))`.

No separate z-score is applied: covariance normalization itself handles scale and correlation. The pseudoinverse is used only because the 71D representation contains deterministic/near-deterministic correlations; no ridge, shrinkage, diagonal blend, eigenvalue floor, whitening rank, or tolerance is searched or manually chosen.

For each year independently, retain the exact v31 labels and k=1 rule:

- annual-positive iff the unchanged fixed-family annual F1 is strictly greater than the frozen literature recovery threshold 0.5;
- annual-nonpositive otherwise;
- `margin_y = d_nearest_nonpositive - d_nearest_positive`.

The sole two-year score remains `min(margin_2013, margin_2014)`.

## Everything else frozen

- exact immutable #950/v22 71D pretruth features, memberships, family IDs, candidate universes, and centroids;
- exact Sugar+HDBSCAN shared strict `SHOWER/<label>` whole-shower five-fold assignment;
- held-out shower groups absent from all training references;
- exact k=1 positive and k=1 nonpositive reference rule;
- exact 0.5 annual recovery threshold inherited from the evaluator;
- exact #839 diversity `lambda=0.8`, `scale=1.0`;
- exact frozen v19 order and one parameter-free equal rank-sum fusion;
- only that fused order is a promotion candidate;
- exact equal-budget one-to-one annual literature evaluator and pairwise superiority semantics.

## Binding gate

The first technically valid execution is binding. PASS requires all four Sugar/HDBSCAN 2013/2014 panels to satisfy simultaneously:

- candidate macro-F1 strictly greater than the corresponding literature comparator; and
- candidate recovered-`F1>0.5` shower count at least the comparator count.

Otherwise this exact covariance-aware k=1 local-geometry formulation is a permanent no-go. Failure does not authorize ridge/shrinkage, covariance blending, alternate pseudoinverse tolerance, alternate k, alternate annual combiner, block deletion/weighting, metric search, diversity/fusion search, or route-specific rescue.

A full exposed-development reference payload may freeze only after a 4/4 OOF PASS; in-sample full-fit scores cannot determine promotion.

No MAARSY, DMS, OrbitTrace target information, target-region event, or protected solar-longitude 20°–55° content may be accessed.