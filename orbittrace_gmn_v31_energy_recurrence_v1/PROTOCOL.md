# Frozen protocol — GMN v31 multivariate energy recurrence v1

## Scientific role

Target-excluded GMN 2022/2023 development successor to exact v31, selected entirely outside SonotaCo. The first technically valid result is binding. Protected solar longitude `[20°,55°]`, OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, and DMS remain inaccessible.

## Scientific motivation and distinctness

A genuinely recurrent stream should reproduce the **full local distribution** of radiant/velocity geometry across independent years, not only its centroid, radial-distance distribution, covariance tensor, activity profile, or linear drift with activity phase.

This successor therefore uses a single canonical multivariate two-sample discrepancy: empirical energy distance between the 2022 and 2023 member clouds in the already-established fixed4 physical geometry.

It does not reopen the closed lanes for radial-coherence statistics, activity-profile statistics, centroid/width ratios, directional covariance/morphology summaries, phase–geometry drift regression, annual counts/component balance, member-balance de-aliasing, support-overlap family linking, MST/topology, or any v32–v60 metric/reference/scaling/fusion rescue.

## Immutable parent and inputs

Use the exact target-excluded v31 package and controls:

- candidate count = 226;
- parent dimension = 23;
- parent feature SHA-256 = `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- centroid SHA-256 = `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent OOF-margin SHA-256 = `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- P19 prelabel SHA-256 = `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`;
- v8 result SHA-256 = `fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b`;
- offline manifest SHA-256 = `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- active ranker source SHA-256 = `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`.

Exact v31 control:

- @25 = 23
- @50 = 41
- @100 = 66
- top-100 dominant precision = 0.7229521515453452
- MRR = 0.050244164168646674
- qualified = 95

Exact hard-order control:

- @25 = 21
- @50 = 38
- @100 = 59
- top-100 dominant precision = 0.6884631112636006
- MRR = 0.046734076055452344
- qualified = 95

## Sole new coordinate

For each family, use its already-fixed annual member events. Choose the fixed 2022 annual centroid only as a common coordinate origin; because energy distance depends only on pairwise differences, this origin choice has no scientific effect.

Map every member event `e` to

`z(e) = [ signed_delta(sun_lon_e, sun_lon_c2022)/4°, (ecl_lat_e-ecl_lat_c2022)/4°, log(Vg_e/Vg_c2022)/log(1.10) ]`.

All speeds must be positive and finite. `signed_delta` wraps into `[-180°,180°)`.

Let `X` be the equally weighted empirical cloud for 2022 and `Y` the equally weighted empirical cloud for 2023. With ordinary Euclidean distance `d` in this fixed three-dimensional geometry, define the standard empirical energy-distance squared statistic

`E = 2*mean_{x∈X,y∈Y} d(x,y) - mean_{x,x'∈X} d(x,x') - mean_{y,y'∈Y} d(y,y')`.

The within-year means include diagonal self-pairs, exactly matching the equally weighted empirical-distribution definition. Numerical values in `[-1e-12,0)` are clamped to zero; a value below `-1e-12` is technical invalidation.

The **only appended feature** is `multivariate_energy_recurrence = sqrt(E)`.

No alternate exponent, squared-only version, unbiased U-statistic, Wasserstein/MMD/KS variant, radial projection, axis decomposition, bandwidth/kernel, trimming, weighting, sample-size correction, centroid alignment, whitening, covariance normalization, activity-phase coordinate, or feature blend is permitted.

The exact 226×23 parent representation becomes exactly 226×24.

## Frozen learner/ranking

Everything downstream remains exact target-excluded v31:

1. immutable strict five-fold groups and labels;
2. fold-training ordinary mean/std z-score, zero std → 1;
3. ordinary Euclidean k=1 distance to nearest positive and nearest nonpositive training family;
4. OOF margin `d_nonpositive-d_positive`;
5. inherited diversity `(lambda=0.8, scale=1.0)`;
6. equal 1-based rank-sum fusion with immutable hard order;
7. unchanged GMN development evaluator.

No feature, transform, metric, k, scaling, reference, diversity, fusion, threshold, candidate, source, fold, or evaluator search is allowed.

## Binding promotion gates

PASS requires all on the first technically valid result:

- recovered@100 > 66;
- recovered@50 >= 41;
- recovered@25 >= 23;
- top-100 dominant precision >= 0.7229521515453452;
- MRR >= 0.050244164168646674;
- qualified matches = 95.

PASS authorizes only a separately frozen SonotaCo development benchmark. FAIL permanently closes this exact multivariate empirical-energy recurrence lane and does not authorize alternate two-sample statistics, transforms, alignment, weighting, metrics, or fusion rescues chosen from the result.

## Firewall

Execution must record all as false: `sonotaco_2013_2014_access`, `target_information_access`, `target_region_events_accessed`, `maarsy_scientific_access`, `dms_scientific_access`, `post_result_second_search`. Any immutable-input mismatch, parent-control mismatch, invalid member/centroid/speed, nonfinite statistic, materially negative energy statistic, or firewall violation is technical invalidation, not a scientific result.