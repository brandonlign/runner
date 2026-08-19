# OrbitTrace M2D fixed4-seeded drift halo v1

## Scientific question

Can the broad, already-promoted support-resolved TopoModal + exact M2D discovery envelopes be given a useful event-level membership view by treating the independently motivated fixed4 consensus subset as a high-purity seed and then regrowing only events consistent with the seed's solar-longitude-conditioned radiant/speed drift?

This is a **dual-output event-membership architecture**. It does not change parent candidate existence, parent M2D membership, M2D score, rank, comparator capacity, or any primary discovery/literature result.

The previous exact fixed4-consensus core v1 is a scientific no-go as a final membership set because its HDBSCAN-side mean F1 retained only 59.5% of the parent despite substantially improving precision. That result motivates regrowth, but it does not choose any numerical parameter below.

## Frozen parent and seed

Primary discovery parent is the exact PR #1377 target-excluded M2D fairness pretruth:

`8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5`

The seed generator is imported **byte-for-byte** from the already-frozen fixed4-consensus v1 builder, Git blob:

`140f21736ea6615fe111e02d91eaa99b19422da7`

Only its exact seed semantics are reused:

- same immutable parent envelope/year;
- every event anchors once;
- exact frozen fixed4 anchor distance to every other same-envelope/year event;
- three nearest other events;
- canonical four-event quartet;
- retain quartet only when selected by at least two distinct anchors;
- annual seed is the union of retained quartets.

No fixed4 score threshold, calibration threshold, p-value, target information, or event outside the parent envelope enters the seed.

## Frozen drift-halo rule

Membership is fit independently for each parent candidate and year.

If an annual fixed4 seed contains fewer than four members, the annual halo is empty. Otherwise:

1. Compute the circular mean solar longitude and circular mean Sun-centered radiant longitude of the annual seed. Compute the arithmetic mean radiant latitude and geometric mean geocentric speed.
2. Use the exact inherited physical scales already used elsewhere in OrbitTrace:
   - solar-longitude predictor: wrapped signed offset / 5 deg;
   - Sun-centered radiant longitude response: wrapped signed offset / 4 deg;
   - radiant latitude response: offset / 4 deg;
   - speed response: `log(vg / geometric_mean_seed_vg) / log(1.1)`.
3. Fit an unweighted affine drift independently to the three response coordinates using design `[1, scaled_solar_longitude_offset]` and `numpy.linalg.lstsq(..., rcond=None)`, matching the pre-existing P12 linear-drift convention. If design rank is below two, the slope is exactly zero and the intercept is the arithmetic mean response.
4. Compute the three-dimensional seed drift residuals and fit one Oracle Approximating Shrinkage covariance (`sklearn.covariance.OAS`) to those residuals. This is the same shrinkage family already used by the frozen P12 drift-conditioned membership architecture; no covariance family is selected here.
5. For every event in the immutable parent envelope/year, compute its residual to the frozen annual drift fit and its squared Mahalanobis distance under the fitted OAS residual distribution.
6. Include the event in the annual halo iff its squared Mahalanobis distance is at most `chi2.ppf(0.95, df=3)`. The 95% confidence level is frozen from the established meteor-membership convention and the pre-existing OrbitTrace alpha=0.05 membership work; it is not selected from this development outcome.
7. All fixed4 seed members are retained explicitly even if finite-sample covariance fitting would place one outside the parametric 95% ellipsoid.
8. The candidate's reportable halo is the union of the two annual halos.

No alternate confidence level, robust clipping loop, background-density threshold, orbital term, mixture/component selection, recursive growth, event-size cap, rank change, or fallback to the full envelope is evaluated.

## Firewall

Development uses only the exact target-excluded GMN 2022/2023 universes already frozen in PR #1377. Solar longitude `[20 deg,55 deg]` is absent before this method receives geometry.

For every panel, the complete fixed4 seed, drift fit, OAS covariance, Mahalanobis distance, and halo event-ID set must be serialized and SHA-256 frozen before known-shower truth is reconstructed.

OrbitTrace canonical IDs, target coordinates, revealed rank-84/rank-82 families, target-region events, SonotaCo truth, and external-survey truth are prohibited from construction or selection.

## Frozen evaluation

Primary parent discovery remains unchanged by construction and must exactly reproduce the PR #1377 parent metrics.

The membership utility gate is same-discovery paired evaluation only: perform the unchanged annual Hungarian assignment using the parent envelopes at each exact comparator capacity. For every parent assignment with parent F1 > 0.5, evaluate that **same candidate's halo against that same shower**. Halo rematching cannot rescue the primary gate.

For Sugar and HDBSCAN routes separately, all must pass:

1. at least 20 parent-recovered paired assignments;
2. halo nonempty fraction >= 0.75;
3. mean halo precision >= 0.80;
4. mean halo precision strictly higher than parent mean precision;
5. mean halo F1 >= 0.75 x parent mean F1;
6. among nonempty halos, at least 50% have precision no lower than the parent;
7. mean halo F1 is strictly higher than the exact fixed4-seed mean F1 on the same paired assignments.

The last gate establishes that drift regrowth actually repairs the known fixed4-core recall loss rather than merely repackaging the rejected seed.

A rematched halo-catalogue evaluation and per-scale/per-year summaries are diagnostic only.

## Outcome boundary

A PASS authorizes one separately frozen no-retuning SonotaCo transfer using the exact same seed, scales, affine fit, OAS covariance, 95% chi-square region, seed retention, and utility gates. SonotaCo remains exposed transfer evidence, not pristine external validation.

Only after that transfer passes may the exact frozen halo rule be applied to the already-blind baseline M2D OrbitTrace ranking under a target-reference-absent Stage A followed by exact-ID-only Stage B.

A FAIL permanently closes this exact rule. No confidence-level change, covariance substitution, clipping, orbital feature, background term, seed threshold, year pooling, component split, halo expansion, or target-informed rescue is authorized from the same truth result.