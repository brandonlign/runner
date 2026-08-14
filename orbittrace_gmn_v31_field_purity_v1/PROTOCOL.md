# Frozen protocol — GMN v31 raw-field neighborhood purity recurrence v1

## Scientific role

Target-excluded GMN 2022/2023 development successor to exact v31, selected entirely outside SonotaCo. The first technically valid outcome is binding. Protected solar longitude `[20°,55°]`, OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, and DMS remain inaccessible.

## Scientific motivation

Exact v31 already describes candidate-internal structure (event/anchor/quartet/component counts, annual strengths, annual member balance, centroid recurrence, member-distance quantiles) and candidate-centroid crowding. It does **not** ask whether a candidate is locally distinguishable from the full meteor field.

A real stream family should occupy the closest local neighborhood around its annual centroid in both years more consistently than an accidental association embedded in unrelated field meteors. The new observable is therefore a label-free, threshold-free local field-purity statistic using the full target-excluded annual scan.

This is not an alternate radial/activity/tensor/drift/energy statistic, not a count-balance rescue, not MST/topology, not support-overlap family linking, and not a v32–v60 metric/reference/fusion rescue.

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

Exact v31 fused control: @25 `23`, @50 `41`, @100 `66`, top-100 precision `0.7229521515453452`, MRR `0.050244164168646674`, qualified `95`.

Exact hard-order control: @25 `21`, @50 `38`, @100 `59`, top-100 precision `0.6884631112636006`, MRR `0.046734076055452344`, qualified `95`.

## Sole new coordinate

For family `f` and year `y`, let `n_y` be its already-fixed annual member count and `c_y` its already-fixed annual centroid. Let `U_y` be **all** events in the inherited target-excluded GMN annual scan for year `y`.

Use the detector's fixed physical centroid metric exactly:

`d(e,c)^2 = (Δsol/10°)^2 + (Δsun_lon/4°)^2 + (Δecl_lat/4°)^2 + (log(Vg_e/Vg_c)/log(1.10))^2`,

with both angular differences wrapped to `[-180°,180°)` and positive finite speeds required.

Order all events in `U_y` by `(d(e,c_y), event_id)` and take the first exactly `n_y` events. Define

`purity_y = (# of those n_y events that are members of f in year y) / n_y`.

Because the neighborhood size is the candidate's own fixed annual membership size, there is no radius or k hyperparameter.

The **only appended feature** is

`field_neighborhood_purity = min(purity_2022, purity_2023)`.

The strict minimum is fixed because recurrence requires local field contrast in both independent years, matching the project's established persistence semantics.

No radius threshold, alternate neighborhood size, k multiplier, mean/geometric-mean/max annual combiner, background annulus, density ratio, member-distance normalization, source/month stratification, label use, uncertainty weighting, event weighting, exclusion of other candidates, local classifier, or alternate metric is permitted.

The exact 226×23 parent matrix becomes exactly 226×24.

## Frozen learner/ranking

Everything downstream remains exact target-excluded v31:

1. immutable strict five-fold groups and labels;
2. fold-training ordinary mean/std z-score, zero std → 1;
3. ordinary Euclidean k=1 nearest-positive / nearest-nonpositive training distance;
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

PASS authorizes only a separately frozen SonotaCo development benchmark. FAIL permanently closes this exact same-size raw-field neighborhood-purity mechanism and does not authorize radius/k/combiner/density/background/metric/fusion rescues selected from the result.

## Firewall and technical invalidation

Execution must verify the inherited blind `[20.0,55.0]` and record false for `sonotaco_2013_2014_access`, `target_information_access`, `target_region_events_accessed`, `maarsy_scientific_access`, `dms_scientific_access`, and `post_result_second_search`.

Any immutable-input mismatch, parent-control mismatch, missing annual member/centroid, member absent from the annual scan, invalid speed/distance, annual scan smaller than `n_y`, or firewall violation is technical invalidation rather than a scientific outcome.