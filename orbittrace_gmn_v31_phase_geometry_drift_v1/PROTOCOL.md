# Frozen protocol — GMN v31 phase–geometry drift recurrence v1

## Scientific role

This is a **target-excluded GMN 2022/2023 development successor** to frozen v31. It is selected outside SonotaCo under the post-v60 stopping rule. The first technically valid result under this protocol is binding.

Protected solar longitude `[20°,55°]`, OrbitTrace target information/events, SonotaCo 2013/2014, MAARSY, and DMS must remain inaccessible.

## Scientific motivation and closure boundary

A recurrent meteor shower is expected to exhibit a repeatable local relationship between activity phase and radiant/velocity geometry: as solar longitude advances through a shower, the Sun-centered radiant and geocentric speed can drift systematically. This conditional phase→geometry relation is physically different from merely asking whether two years have similar marginal activity profiles or similar unconditional member-cloud shape.

This successor therefore does **not** reopen any closed lane:

- no activity-profile KS or alternate activity distribution statistic;
- no radial-coherence statistic or radial transform;
- no centroid-width ratio;
- no annual count/component balance;
- no member-balance deletion/reweighting;
- no directional second-moment/covariance morphology variant from the now-closed directional-morphology v1 lane;
- no support-overlap/family-linking successor;
- no v32–v60 metric/reference/scaling/fusion/diversity/component-transfer rescue.

The sole new observable is a one-number discrepancy between two independently estimated annual **phase–geometry drift vectors**.

## Immutable parent and inputs

Use the exact target-excluded v31 development package already used by the binding recent successors.

Required identities:

- candidate count = 226;
- parent dimension = 23;
- parent feature SHA-256 = `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- centroid SHA-256 = `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent OOF-margin SHA-256 = `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
- P19 prelabel SHA-256 = `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`;
- v8 result SHA-256 = `fa8f52cf046ced499a378cc6b7d04c52ef92bf0fa3f801049211d190f1c3919b`;
- offline manifest SHA-256 = `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- active ranker source SHA-256 = `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`.

Exact v31 control must reproduce:

- @25 = 23
- @50 = 41
- @100 = 66
- top-100 dominant precision = 0.7229521515453452
- MRR = 0.050244164168646674
- qualified = 95

Exact immutable hard-order control must reproduce:

- @25 = 21
- @50 = 38
- @100 = 59
- top-100 dominant precision = 0.6884631112636006
- MRR = 0.046734076055452344
- qualified = 95

## Sole new coordinate

For each family and each year `y ∈ {2022,2023}`, use its fixed annual centroid `c_y` and its already-fixed annual member events.

For each member event `e`, define fixed activity-phase offset

`x(e,y) = signed_delta(sol_e, sol_c_y) / 4°`,

where `signed_delta` wraps into `[-180°,180°)`.

Define the signed fixed4-scaled geometric residual vector

`r(e,y) = [ signed_delta(sun_lon_e,sun_lon_c_y)/4°, (ecl_lat_e-ecl_lat_c_y)/4°, log(Vg_e/Vg_c_y)/log(1.10) ]`.

All speeds must be positive and finite.

Fit one ordinary through-origin multivariate least-squares drift vector per year:

`b_y = sum_e x(e,y) * r(e,y) / sum_e x(e,y)^2`.

If the exact denominator is zero, the frozen convention is `b_y = [0,0,0]`. There is no intercept because both phase and geometry are expressed relative to the already-fixed annual centroid.

The **only appended feature** is

`phase_geometry_drift_discrepancy = || b_2022 - b_2023 ||_2`.

No axis-specific drift features, sign flips, slope angles, cosine similarity, slope-magnitude ratio, intercept, robust regression, ridge/shrinkage, phase clipping/windowing, minimum-span threshold, member weighting, uncertainty weighting, nonlinear drift, polynomial term, or alternate normalization is permitted.

The exact 226×23 parent matrix becomes exactly 226×24 by appending this one coordinate.

## Frozen learner and ranking

No downstream change from exact target-excluded v31:

1. immutable strict five-fold groups and labels;
2. fold-training ordinary mean/std z-score, zero std → 1;
3. Euclidean k=1 nearest positive and nearest nonpositive training references;
4. OOF margin `d_nonpositive - d_positive`;
5. inherited diversity order `(lambda=0.8, scale=1.0)`;
6. equal 1-based rank-sum fusion with immutable hard order;
7. unchanged GMN development evaluator.

No feature, transform, metric, k, scaling, reference, diversity, fusion, threshold, candidate, source, fold, or evaluator search is allowed.

## Binding promotion gates

PASS requires every gate on the first technically valid outcome:

- recovered@100 > 66;
- recovered@50 >= 41;
- recovered@25 >= 23;
- top-100 dominant precision >= 0.7229521515453452;
- MRR >= 0.050244164168646674;
- qualified matches = 95.

PASS would authorize only a separately frozen SonotaCo development benchmark. FAIL permanently closes this exact phase–geometry linear-drift discrepancy lane; it does not authorize slope-axis, normalization, regression, weighting, nonlinear, threshold, metric, or fusion rescues chosen from the outcome.

## Firewall and technical invalidation

Execution must verify the inherited inclusive blind exclusion `[20.0,55.0]` before accepting any result and must record:

- `sonotaco_2013_2014_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- `post_result_second_search = false`.

A changed immutable input, failure to reproduce the exact parent controls/hashes, missing member/centroid, nonfinite residual, firewall violation, or implementation failure is a technical invalidation rather than a scientific outcome.