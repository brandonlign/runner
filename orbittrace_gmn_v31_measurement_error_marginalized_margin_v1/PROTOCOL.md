# OrbitTrace GMN v31 measurement-error marginalized margin v1

## Status

Binding target-excluded GMN 2022+2023 successor protocol. **This protocol is frozen before the first member-specific measurement package outcome and before any candidate ranking outcome.** The first technically valid scientific execution is binding.

No SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY, or DMS is authorized.

## Scientific question

Does integrating the already-successful v31 local-geometry margin over the reported measurement-error distribution improve recovery, rather than treating each measured radiant/speed as an exact point?

Meteor uncertainty literature already uses Gaussian radiant/speed clones to propagate observational errors into stream membership, and the project has an independently frozen Sugar-transfer implementation of that cloning convention. This successor therefore changes the **measurement model**, not the detector, family graph, distance metric, k, feature subset, reference definition, diversity parameters, or fusion weight.

This is distinct from the permanently closed uncertainty-inflated quartet line (#57/#61): uncertainty never enters quartet distances, detector scores, proposal generation, component construction, family linking, or membership. It is also distinct from the closed v31 margin-confidence fusion: there is no transform, cutoff, probability-of-positive-margin gate, confidence coefficient, or second score fused with the nominal margin. The candidate is the ordinary Monte Carlo expectation of the same v31 margin after re-measuring the physical coordinates.

## Immutable parent

Exact parent is `orbittrace_gmn_v31_principle_local_geometry_oof_v1/run_development.py`, Git blob `b4e2d72e532e47aa95ed335f690748423d11ea59`.

Parent controls that must reproduce before candidate interpretation:
- candidates: 226 immutable P19 hard families;
- feature dimension: 23;
- nearest k: 1;
- five deterministic whole-shower OOF folds;
- fold-training ordinary z-score;
- Euclidean reference distance;
- margin: `d_nonpositive - d_positive`;
- diversity lambda 0.8, scale 1.0;
- equal rank-sum with immutable P19 hard order;
- parent fused metrics: @25 **23**, @50 **41**, @100 **66**, top-100 dominant precision **0.7229521515453452**, MRR **0.050244164168646674**, qualified **95**.

No candidate generation, membership, family deletion, fold, truth/reference-definition, k, metric, feature selection, scaling, threshold, diversity, or fusion search.

## Frozen measurement package dependency

The scientific execution may use only the **first technically valid** output of `agent/orbittrace-gmn-v31-measurement-uncertainty-package-v1`, and only if its manifest verdict is `PASS_GMN_V31_MEASUREMENT_UNCERTAINTY_PACKAGE_V1`, it contains exactly the immutable 226-family member universe at 100% coverage, and its raw means reproduce the nominal canonical parent geometry at the package's predeclared <=1e-9 tolerance.

If that package fails, this successor is not executed and there is no package rescue.

## Frozen clone law

Inherit the already-frozen Sugar uncertainty core decoded SHA-256 `5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb`:
- clone iterations: **1000**;
- seed root: **20170209**;
- independent Gaussian RA and Dec draws from reported marginal standard deviations;
- exact frozen declination-reflection helper (including RA+180° pole reflection), not clipping;
- exact frozen positive-Gaussian Vg redraw helper;
- fixed J2000 obliquity **23.43928°**;
- solar longitude is unchanged by cloning.

Unique immutable member events are sorted by `(year,id)` and cloned **once per realization**, so an event shared by multiple families has the same cloned measurement everywhere in that realization.

For realization `r` in `0..999`, the RNG seed is fixed as the exact frozen Sugar `stable_seed(20170209, "GMN_V31_MEASUREMENT_ERROR_MARGINALIZED_MARGIN_V1", r)`. The tag and iteration convention are frozen here and are not searchable.

## Exact per-realization v31 representation

For every realization:

1. Convert each cloned RA/Dec/Vg to the canonical v31 physical row `(sol, sun_lon, ecl_lat, vg)` using the exact historical J2000 transform and half-open `wrap180` convention. Solar longitude is unchanged.
2. Preserve every family identity, event membership, detector/component/quartet/anchor quantities, year strengths, and hard order exactly.
3. Recompute each family's same-year pooled centroid from its cloned immutable members using the exact v8 statistic: circular mean for `sol` and `sun_lon`, median for `ecl_lat` and `vg`.
4. Recompute the exact 23D parent intrinsic representation from the cloned physical geometry:
   - exact parent structural indices 1..10; only their existing cross-year centroid-distance term is geometry-dependent, while detector/count/strength quantities remain immutable;
   - exact seven parent cohesion features from cloned members and cloned pooled centroids;
   - exact six parent centroid-neighbor features from the complete 226-family cloned centroid matrix.
5. Using the immutable parent truth/reference groups and deterministic five-fold split, recompute the parent OOF margin exactly: within each fold, fit the ordinary mean/std z-score on that realization's training rows only; set zero training standard deviations to 1; compute k=1 Euclidean nearest positive and nonpositive reference distances for each held-out family; margin is `d_nonpositive-d_positive`.

This produces one raw OOF margin per family per realization. No diversity selection or hard-order fusion is performed inside a realization.

## Sole candidate score

For family `i`, define

`m_bar_i = arithmetic mean of its 1000 raw OOF clone margins`.

This is the sole new local score. No median, trimmed mean, variance, standard error, sign probability, lower confidence bound, quantile, standardized margin, nominal/clone blend, reliability weight, or second statistic is computed for ranking.

After all 1000 expectations are sealed:
- apply the **unchanged parent diversity selection exactly once** to `m_bar`, using the **nominal parent centroid matrix** and frozen lambda 0.8 / scale 1.0;
- equal-rank fuse that local order with the immutable P19 hard order exactly as the parent does.

Using nominal centroids for diversity is deliberate: this successor marginalizes only the v31 local separation score while keeping the parent catalogue-level redundancy controller unchanged. Clone-specific diversity, expected centroid diversity, rank aggregation across clones, or any uncertainty-dependent diversity penalty is outside this protocol.

## Required audits before truth metrics

Before candidate performance is inspected:
- exact parent nominal feature matrix, nominal margin, local order, fused order, and parent metrics reproduce their immutable hashes/controls;
- package manifest and package SHA are pinned;
- Sugar clone core SHA and helper source semantics reproduce;
- all 1000 clone feature matrices and margins are finite;
- no family/member/fold/reference universe changes;
- 20°–55° remains absent;
- Monte Carlo iteration count, seed root/tag, clone law, centroid statistic, feature definition, k, scaling, distance, diversity, and fusion are exactly those above.

The expected-margin vector and candidate orders are hashed **before** evaluation metrics are emitted.

## Binding promotion gate

PASS requires all:
- recovery@25 >= **23**;
- recovery@50 >= **41**;
- recovery@100 > **66**;
- top-100 dominant precision >= **0.7229521515453452**;
- MRR >= **0.050244164168646674**;
- qualified matches = **95**;
- all provenance/firewall audits pass.

Otherwise verdict is `FAIL_GMN_V31_MEASUREMENT_ERROR_MARGINALIZED_MARGIN_V1`.

A FAIL permanently closes this exact expected-margin measurement-marginalization formulation and nearby result-motivated rescues: alternate clone count, seed ensemble, uncertainty multiplier, covariance invention, nominal/clone blend, mean/median/quantile/LB/sign-probability statistic, uncertainty weighting, feature subset, fixed-vs-cloned centroid choice, clone-specific diversity, diversity change, k/metric/scaling/fold/reference change, or fusion change. No SonotaCo benchmark follows a FAIL.

A PASS authorizes only a separately frozen next-stage compatibility decision; it does not make SonotaCo external validation.