# OrbitTrace deterministic Persistable selector — synthetic feasibility audit v1

## Scientific role

This is a **synthetic-only, zero-meteor feasibility audit**. It does not evaluate an OrbitTrace successor and may not open GMN, SonotaCo, ASFN, EFN, AMOS, MAARSY, DMS, OrbitTrace target information, or any shower label.

The purpose is to determine whether the stable multiparameter clustering machinery of Rolle & Scoccola can be converted from its intended interactive parameter-selection workflow into one deterministic unsupervised rule before any meteor data are exposed to that rule.

The exact upstream implementation is pinned to `LuisScoccola/persistable` commit `7eb75b2e8d2fe5a18e49248aa7d1c97f829415be`.

## Deterministic parameter rule

For each input point cloud:

1. Construct `Persistable(X, n_neighbors="auto", n_jobs=1)` with its default uniform probability measure and Euclidean metric.
2. Compute the package's exact `_find_end()` and exact `persistable_interactive.compute_defaults(end, p._default_granularity())` values.
3. Use the package-default first and second vineyard slices from those defaults. No coordinate is supplied by OrbitTrace.
4. Compute the linear prominence vineyard with the package-default `GRANULARITY_PV` number of interpolation parameters.
5. At each vineyard position, sort bar prominences descending exactly as the package's `Vineyard._vineyard_to_vines()` does.
6. Inspect only gap numbers 2 through at most 15. Gap 1 is excluded because the package documentation states that the largest-vs-second-largest prominence gap is typically dominant/trivial; 15 is the package's default `MAX_VINES` display limit.
7. For gap `g`, at vineyard position `t`, define normalized separation

   `delta_g(t) = max(P_g(t) - P_{g+1}(t), 0) / max(P_1(t), 1e-15)`.

8. Select the gap with largest arithmetic mean `delta_g(t)` over **all** default vineyard positions. Ties go to the smaller gap number.
9. Select the vineyard position where that already-selected gap has maximum `delta_g(t)`. Ties go to the earliest position.
10. Use that position's exact interpolated slice and call `Persistable.cluster(n_clusters=g, start=..., end=..., flattening_mode="conservative", keep_low_persistence_clusters=False)`.

No parameter search, visualization, manual slice selection, truth-informed choice, alternate gap statistic, or fallback is allowed.

## Synthetic stress panel

Four deterministic replicates are generated. Each replicate first generates exactly 6,144 points in four dimensions from the same predeclared latent model:

- six Gaussian signal components;
- component weights `0.18, 0.15, 0.13, 0.11, 0.09, 0.07`;
- remaining probability mass is uniform structured background;
- component standard deviations `0.22, 0.28, 0.34, 0.40, 0.46, 0.52`;
- component centers are the fixed rows
  `(+2,0,0,0), (-2,0,0,0), (0,+2,0,0), (0,-2,0,0), (0,0,+2,0), (0,0,-2,0)`;
- uniform background is sampled from `[-4,4]^4`;
- NumPy PCG64 seeds are exactly `202608160, 202608161, 202608162, 202608163`.

The sparse sample is a deterministic nested subset: the first 768 generated points. Therefore labels on the sparse sample can be compared directly with the restriction of the 6,144-point clustering.

Synthetic latent labels are used **only as a secondary audit diagnostic**, never for parameter selection.

## Frozen feasibility gates

The selector passes this pre-meteor audit only if all conditions hold in all four replicates:

1. both dense and sparse runs return at least 2 non-noise clusters;
2. selected requested gap is in `[2,15]` with no fallback;
3. absolute dense-vs-sparse difference in returned non-noise cluster count is at most 2;
4. adjusted Rand index between sparse clustering and the dense clustering restricted to the same 768 points is at least `0.50`;
5. no NaN/Inf prominence, invalid slice, exception, manual intervention, or package-warning indicating insufficient fitted neighbors occurs.

Secondary truth ARI is reported but has no pass/fail role.

A PASS authorizes only a separately frozen **zero-label target-excluded GMN cross-scale diagnostic** using the exact same selector. A FAIL closes this exact automatic-selector rule; it may not be rescued on synthetic or meteor data by changing gap normalization, gap range, default slices, vineyard resolution, tie rules, n-neighbor policy, flattening mode, synthetic model, seeds, or gates.
