# OrbitTrace GMN v31 margin-confidence fusion v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 successor to the passed `orbittrace_gmn_v31_principle_local_geometry_oof_v1` parent. It tests exactly one mechanism: whether the already-frozen strict-OOF local-geometry leg should influence the final rank **in proportion to the strength of its own held-out nearest-class evidence**, instead of receiving equal influence for every candidate.

This protocol is frozen before the first technically valid outcome. SonotaCo 2013/2014 is not accessed to evaluate, tune, or select this successor. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.

## Motivation fixed before outcome

The GMN v31-principle parent passed cleanly on the fixed 226-family hard universe:

- recovered@25: 23
- recovered@50: 41
- recovered@100: 66
- top-100 dominant precision: 0.7229521515453452
- MRR: 0.050244164168646674
- qualified known-shower universe: 95

The successful scientific signal is the full 23D strict-whole-shower-OOF nearest-positive versus nearest-nonpositive Euclidean margin. Annual-min, local-scale relative-margin, shrinkage-Mahalanobis, and physical-block consensus variants failed and remain closed. The fixed RRF(k=60) fusion successor also failed, dropping recovered@100 from 66 to 63 and MRR from 0.050244164168646674 to 0.04975933624473349; alternate RRF constants or weights are closed.

The parent currently gives its immutable P19 hard-family order and the diversified local-geometry order equal linear rank influence for every family. Yet the local leg already produces a natural per-family OOF evidence magnitude: `|d_nonpositive - d_positive|`. A held-out family with a margin extremely close to zero has weak local class separation; a family with a large-magnitude margin has stronger local separation in either direction. This successor tests whether that **existing OOF evidence magnitude**, used only as a candidate-specific reliability weight, improves the final fusion without changing the geometry itself.

The exposed SonotaCo v31 constituent-disagreement diagnostic is contextual mechanism evidence only. It does not supply a threshold, family identity, coefficient, or parameter to this GMN successor.

## Immutable parent science

Before evaluating the successor, reproduce the exact parent and require:

- candidate count = 226
- feature dimension = 23
- qualified matches = 95
- recovered@25 = 23
- recovered@50 = 41
- recovered@100 = 66
- top-100 dominant precision = 0.7229521515453452
- MRR = 0.050244164168646674

Everything below remains exactly the passed parent:

- GMN 2022+2023 only;
- protected 20°–55° removed before scientific operations;
- immutable 226 P19 hard-family candidate universe and memberships;
- exact 23D intrinsic representation: 10 structural + 7 cohesion + 6 centroid-neighborhood;
- explicit hard-rank feature excluded from the local representation;
- exact deterministic five strict whole-shower folds;
- fold-training mean/population-standard-deviation z-score;
- positive-reference semantics unchanged;
- ordinary Euclidean distance;
- `k=1` nearest positive and nearest nonpositive reference;
- raw local margin `m_i = d_nonpositive - d_positive`;
- exact diversity step (`lambda=0.8`, `scale=1.0`);
- exact truth and metric semantics.

No feature, distance, k, scaling, fold, reference class, diversity setting, candidate, membership, or truth rule changes.

## Sole successor change: parameter-free margin-confidence interpolation

Let:

- `r_h(i)` be candidate `i`'s 1-based rank in the immutable hard-family order;
- `r_g(i)` be candidate `i`'s 1-based rank in the exact diversified local-geometry order;
- `m_i` be the exact raw strict-OOF local margin already computed by the parent before diversity;
- `N = 226`.

### 1. Parameter-free confidence

Compute `a_i = |m_i|`.

Across all 226 held-out OOF margins, assign each `a_i` its ordinary ascending average rank `R_i` (smallest magnitude rank 1, largest magnitude rank N; exact ties receive their average rank). Define

`c_i = (R_i - 1) / (N - 1)`.

Thus `c_i` is in `[0,1]`, is monotone only in the magnitude of already-frozen OOF evidence, uses no outcome-selected threshold, and contains no fitted coefficient. If the confidence vector is nonfinite, incomplete, or all margin magnitudes are identical, the run fails closed.

### 2. Candidate-specific interpolation

Convert constituent ranks to normalized rank utilities:

`u_h(i) = (N - r_h(i)) / (N - 1)`

`u_g(i) = (N - r_g(i)) / (N - 1)`.

The parent's equal-rank-fusion utility is

`u_parent(i) = (u_h(i) + u_g(i)) / 2`.

Define the sole successor utility

`u_conf(i) = (1 - c_i) * u_h(i) + c_i * u_parent(i)`.

Equivalently, weak-magnitude local evidence leaves the candidate near the immutable hard order, while strong-magnitude local evidence approaches—but never exceeds—the exact parent's equal local influence. Rank descending by `u_conf`, tie-broken by ascending immutable hard rank and then deterministic family ID.

This is the only scientific change. The raw margin itself is not transformed or reranked as a geometry score; no margin sign threshold, learned confidence model, calibration fit, coefficient, temperature, exponent, clipping, alternate percentile definition, source/year rule, or budget-specific rule exists.

## Frozen GMN promotion gate

The successor is promotable only if **every** condition holds against the exact reproduced GMN v31 parent:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 dominant precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified known-shower count **= 95**;
7. all pre-fusion scientific-state hashes/objects reproduce exactly;
8. all protected-data/firewall assertions pass.

The first technically valid result is binding. If any gate fails, `GMN_V31_MARGIN_CONFIDENCE_FUSION_V1` fails and this exact mechanism is permanently closed. No alternate confidence transform, absolute-margin cutoff, signed-margin cutoff, quantile binning, learned calibration, coefficient, interpolation endpoint, constituent weight, feature/metric/scaling/diversity change, or post-result rescue is authorized.

## SonotaCo boundary

Only a GMN PASS may authorize a separately frozen one-shot SonotaCo 2013/2014 comparison against exact v31 and the literature comparators. SonotaCo remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation. A later SonotaCo outcome may not be used to modify this successor.

## Firewall

Every execution must assert:

- `blind_exclusion = [20.0, 55.0]`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `sonotaco_2013_2014_access = false` during GMN development;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`.
