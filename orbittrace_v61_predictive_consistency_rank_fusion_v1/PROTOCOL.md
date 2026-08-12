# OrbitTrace v61 predictive-consistency rank fusion v1

## Scientific role

This is one **GMN-authorized transferable successor to frozen v31**. It is not a SonotaCo-driven v31 micro-rescue. The architecture is motivated and fixed by the target-excluded GMN predictive-consistency diagnostic before any v61 SonotaCo outcome is computed.

Authorizing GMN run: `31560470070`, artifact `9127584643`, artifact digest `sha256:038b6696a806460226ce3696632d282e539476c62440e84497995374671120ce`.

Binding GMN result: `PASS_GMN_PREDICTIVE_CONSISTENCY_SIGNAL` with the fixed equal-rank fusion improving recovered@100 `59 -> 62`, recovered@50 `38 -> 39`, top-100 dominant precision `0.6884631112636006 -> 0.7145192896079117`, and MRR `0.046734076055452344 -> 0.04907166615045645`. The GMN prelabel SHA-256 is `af936dab0ac0e13ec27de74d220cdff8b586dd0a81a1f60157dc26d60818ffa0`.

SonotaCo 2013/2014 remains **EXPOSED DEVELOPMENT ONLY**. A v61 success is not pristine external validation.

## Immutable parent and candidate universes

The parent is exact original v31 local-geometry-margin OOF. Its original workflow run is `31449126218`, artifact `9085657207`, artifact digest `sha256:6a5c791dcab88bba956205e3453b8357631510aaff5ca9c4b2e29ef6208a9577`.

The exact v31 fused parent orders must be supplied by the provenance-only parent-order reconstruction and must hash to:

- Sugar: `5b3d27e11079f36148bbfb8bfdab60882fae380143fcfd84c6dc290c53295aae` over 267 families.
- HDBSCAN: `85ac3f29a443c35b3812cf28c99ef13474fc3e0455458e20b41cec64d942073d` over 229 families.

Candidate generation and memberships are immutable v22/v24/v31 pretruth payloads from artifact `9074742322`, exact zip SHA-256 `d940fa255804866f14bc34b1d72467d17adddcfb7d82c954ed5a8d1668aa307a`. No candidate is added, removed, merged, split, or rematched.

## Label-free SonotaCo rows and firewall

The predictive score uses only the already-frozen label-free SonotaCo preparation artifact `9050107352`, exact zip SHA-256 `1296d757b5ea1dd94f9c9077fd769fdc8f00ec06d0881d8548fd1df4608344cc`.

Its manifest must state `PASS_FINAL_SONOTACO_LABEL_FREE_PREPARATION`, `shower_truth_accessed=false`, `target_information_access=false`, `maarsy_scientific_access=false`, and `target_region_retained=false`.

Before feature construction, the implementation must fail closed if any row has solar longitude in protected interval **20 deg to 55 deg inclusive**. OrbitTrace target information, target-region events, MAARSY, and DMS remain inaccessible.

Although the preserved label-free rows carry additional historical fields, v61 is permitted to read only event ID, year, solar longitude, solar-centered radiant longitude, ecliptic latitude, and positive geocentric speed. Orbital elements, IAU fields, uncertainty fields, and any source/truth-like field do not enter the score.

## Frozen candidate-internal predictive score

For each route, family, and year 2013/2014 separately:

1. Select the immutable family member event IDs for that year and resolve them against the same route/year label-free row panel. Every member must resolve exactly once.
2. Use the immutable v31 centroid matrix annual solar-longitude coordinate as the regression center: column 0 for 2013 and column 4 for 2014. The frozen centroid matrix construction is `[sol, sun_lon, ecl_lat, log(vg)]` for each year.
3. If annual membership has at least four events, perform deterministic leave-one-out ordinary least squares. For each held-out event fit the remaining annual members with design `[1, signed_delta_solar_longitude / 10 deg]` and response `[radiant unit-vector x, y, z, log(vg)]`.
4. Normalize the predicted radiant vector and score the held-out event by `hypot(radiant_angle / 3 deg, abs(delta_log_vg) / log(1.08))`.
5. If annual membership has fewer than four events, use the static annual member centroid residual instead: normalized mean radiant unit vector plus mean log(vg). Mark that year as unlearned. No family is deleted.
6. Summarize each family by worst annual predictive q90, worst annual predictive median, worst event residual, worst annual static q90, predictive q90 gain (`static_q90 - predictive_q90`), and learned-member fraction.

The complete feature rows and predictive orders must be serialized and hashed **before SonotaCo truth is downloaded or opened**.

## Sole v61 ranking rule

For each route, predictive order is exactly:

`(lower worst_annual_predictive_q90, lower worst_annual_predictive_median, higher q90_gain, family_id)`.

There is one fusion only. Convert the exact frozen v31 parent order and the predictive order to 1-based ranks and sort by:

`(v31_rank + predictive_rank, v31_rank, family_id)`.

There is no coefficient, threshold, score calibration, source quota, diversity pass, candidate deletion, route-specific rule, budget-specific rule, rank product, sequential rescue, alternate annual combiner, alternate regression, feature subset, or parameter search.

## Binding SonotaCo gate

Only after the v61 pretruth artifact and fused-order hashes are fixed may the already-exposed truth artifact `9069505548`, exact zip SHA-256 `cdea3297c234b0b3a8f09c2208649c8607bb3e9a9004d299f6dcc18536ebb797`, be opened.

The first technically valid v61 evaluation is binding. PASS requires **all four** Sugar/HDBSCAN 2013/2014 literature comparator pairs to satisfy:

- candidate macro-F1 strictly greater than the frozen literature macro-F1; and
- candidate recovered `F1 > 0.5` count at least the frozen literature recovered count.

All four panels must pass. Otherwise verdict is FAIL and this exact v61 predictive-consistency plus v31 equal-rank-fusion transfer is permanently rejected. No post-result weighting, threshold, feature, route, diversity, regression, or fusion rescue is authorized.

## Claim boundary

A PASS would establish an exposed-development SonotaCo method that beats the frozen Sugar and HDBSCAN literature comparators on all four matched panels under this protocol. It would not make SonotaCo pristine validation and would not authorize protected OrbitTrace target access, MAARSY, or DMS.
