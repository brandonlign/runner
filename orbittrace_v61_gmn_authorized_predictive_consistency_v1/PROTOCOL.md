# OrbitTrace v61 GMN-authorized predictive-consistency fusion v1

## Authorization and role

This is the first SonotaCo benchmark successor authorized **outside SonotaCo** after the v60 development closure.

The sole scientific authorizer is target-excluded GMN run `31560470070`, artifact `9127584643`, which returned `PASS_GMN_PREDICTIVE_CONSISTENCY_SIGNAL` under a protocol frozen before outcome. Exact GMN changes relative to the immutable hard baseline were recovered@100 `59 -> 62`, recovered@50 `38 -> 39`, top-100 dominant precision `0.6884631112636006 -> 0.7145192896079117`, and MRR `0.046734076055452344 -> 0.04907166615045645`. GMN prelabel SHA-256 was `af936dab0ac0e13ec27de74d220cdff8b586dd0a81a1f60157dc26d60818ffa0`.

This protocol is frozen before any new SonotaCo payload inspection or benchmark view for v61. SonotaCo 2013/2014 remains **EXPOSED DEVELOPMENT ONLY**, never external validation.

## Parent

Parent is exact v31 strict-OOF local-geometry-margin OOF, source blob `917e3cd6f9310ca1282e0efa58ed0924d03ed4da`.

All v31 candidate generation, immutable memberships, 71D representation, strict whole-shower folds, annual labels, local-geometry score, #839 diversity, v19 fusion, fixed comparator budgets, matching evaluator, and literature summaries remain unchanged. v61 does not retrain v31 and does not change candidate membership.

## Candidate-internal predictive score

For each route independently (`sugar`, `hdbscan`) and each candidate family, compute the **same physical predictive rule that passed GMN**, using only pretruth candidate-member observables.

For each year 2013 and 2014:

1. Use member solar longitude, solar-centered radiant longitude, ecliptic latitude, and positive geocentric speed.
2. If annual membership has at least four events, perform deterministic leave-one-out ordinary least squares. For each held-out event, train on the remaining annual members with design `[1, signed_delta_solar_longitude / 10 deg]` and response `[radiant unit-vector x,y,z, log(vg)]`.
3. Normalize predicted radiant to unit length and evaluate held-out residual exactly as `hypot(radiant_angle / 3 deg, abs(delta_log_vg) / log(1.08))`.
4. If annual membership has fewer than four events, use that annual candidate's static centroid residual as predictive residual and mark learned fraction zero. No candidate is deleted.
5. Candidate predictive summary is worst-year q90, worst-year median, worst event residual, worst-year static q90, q90 gain (`static_q90 - predictive_q90`), and learned-member fraction.

The predictive order is exactly:

`(lower worst-year predictive q90, lower worst-year predictive median, higher q90 gain, family_id)`.

No orbital elements enter this feature.

## Transfer feasibility rule

The v61 workflow may inspect the already-frozen **pretruth** candidate payload only after this protocol and scientific evaluator are frozen. That inspection is implementation compatibility only.

If the immutable pretruth payload does not contain, or cannot deterministically reconstruct without exposed truth, the four observables for every candidate member needed by the exact GMN rule, v61 terminates as `INAPPLICABLE_PRETRUTH_OBSERVABLES` before truth is loaded. The score may not be replaced by 71D proxies, centroid-only approximations, source features, orbital features, or any other substitute.

## Frozen fusion

First reproduce exact v31 route orders and all four v31 panel controls.

For each route, convert exact v31 order and predictive order to 1-based ranks over the identical candidate universe. The sole v61 order is:

`(v31_rank + predictive_rank, v31_rank, family_id)`.

Sugar and HDBSCAN use the same rule. No weight, coefficient, threshold, route-specific exception, year-specific exception, rank window, source quota, diversity change, candidate deletion, or secondary rescue is permitted.

## Binding benchmark gate

The first technically valid v61 benchmark result is binding. PASS requires all four literature pair gates:

- candidate macro-F1 strictly greater than the frozen literature comparator macro-F1; and
- candidate recovered F1>0.5 count greater than or equal to the frozen literature comparator recovered count.

for Sugar 2013, Sugar 2014, HDBSCAN 2013, and HDBSCAN 2014.

If the first technically valid result is FAIL, this exact v31 + predictive equal-rank fusion is permanently closed. Do not alter weights, tie rules, predictive summaries, annual fallback, regression form, physical scales, budgets, or route handling after outcome.

## Firewall

- Protected OrbitTrace solar longitude 20 deg to 55 deg remains inaccessible.
- OrbitTrace target information and target-region events remain inaccessible.
- MAARSY and DMS remain inaccessible.
- SonotaCo truth must not load until the complete pretruth predictive orders and their hashes have been written and checked.
- SonotaCo role remains EXPOSED DEVELOPMENT ONLY.
