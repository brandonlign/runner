# OrbitTrace GMN v31 reciprocal-rank fusion v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 successor to the passed `orbittrace_gmn_v31_principle_local_geometry_oof_v1` parent. It tests one mechanism only: whether a top-sensitive reciprocal-rank aggregation preserves complementary evidence from the immutable hard-family order and the already-passed v31 local-geometry order better than the parent's linear equal rank-sum.

This protocol is frozen before the first technically valid outcome. SonotaCo 2013/2014 is not accessed to evaluate, tune, or select this successor. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.

## Motivation fixed before outcome

The parent GMN v31-principle method passed cleanly: recovered@100 59→66, recovered@50 38→41, top-100 dominant precision 0.6884631112636006→0.7229521515453452, MRR 0.046734076055452344→0.050244164168646674. Its successful scientific signal is the full 23D strict-OOF Euclidean nearest-positive versus nearest-nonpositive margin; annual-min, local-scale normalization, shrinkage Mahalanobis, and physical-block consensus successors all failed and remain closed.

The parent ends with an equal 1-based rank-sum of two complementary orders: the immutable P19 hard-family order and the v31 local-geometry order after the exact frozen diversity step. Equal rank-sum is Borda-like and penalizes a candidate linearly when one constituent places it poorly, even when the other constituent places it very highly.

Reciprocal Rank Fusion (Cormack, Clarke & Büttcher, SIGIR 2009, DOI 10.1145/1571941.1572114) was proposed as a simple robust aggregation of independent ranked lists using reciprocal rank contributions. This successor uses the literature-standard fixed offset `k=60`; there is no k search or GMN-tuned fusion parameter.

The exposed SonotaCo v31 internal-v19 diagnostic is contextual mechanism evidence only and does not determine the GMN rule, threshold, candidate identity, or parameter. The actual successor is evaluated and selected solely on the fixed target-excluded GMN development panel.

## Immutable parent science

Reproduce the exact parent on the same 226 hard families and require exact parent controls before evaluating the successor:

- candidate count: 226
- qualified known-shower universe: 95
- recovered@25: 23
- recovered@50: 41
- recovered@100: 66
- top-100 dominant precision: 0.7229521515453452
- MRR: 0.050244164168646674

Everything below is byte-for-byte/logically identical to the passed parent:

- GMN 2022+2023 only;
- protected 20°–55° removal before scientific operations;
- immutable 226 P19 hard-family candidate universe and memberships;
- exact 23D intrinsic feature representation: 10 structural + 7 cohesion + 6 centroid-neighborhood;
- explicit hard-rank feature excluded from the local-geometry representation;
- exact deterministic 5 strict whole-shower folds;
- fold-training z-score;
- positive reference definition = frozen qualified family semantics (`precision >= 0.5` and `overlap >= 4` for the best eligible recurrent shower);
- ordinary Euclidean 1-nearest positive and 1-nearest nonpositive reference distances;
- local margin `d_nonpositive - d_positive`;
- exact diversity step, lambda 0.8 and scale 1.0;
- all truth and metric semantics.

No feature, metric, scaling, reference, fold, diversity, candidate, membership, or truth rule changes.

## Sole successor change: fixed RRF aggregation

Let:

- `r_h(i)` = 1-based rank of candidate `i` in the immutable hard-family order;
- `r_g(i)` = 1-based rank of candidate `i` in the exact parent local-geometry order after diversity.

Fix `k = 60` before outcome.

Define

`RRF(i) = 1 / (60 + r_h(i)) + 1 / (60 + r_g(i))`.

Rank candidates by descending `RRF(i)`, then ascending `r_h(i)`, then deterministic family ID.

This is the only scientific change. No alternative k, no unshifted reciprocal score, no learned coefficient, no weighted RRF, no rank product, no harmonic/geometric mean, no max/min rule, and no post-result second fusion are authorized.

## Frozen GMN promotion gate

The successor is promotable only if every condition holds against the exact reproduced GMN v31 parent:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 dominant precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified known-shower count **= 95**;
7. all provenance and protected-data assertions pass.

A technically valid result is binding. If any gate fails, `GMN_V31_RRF_FUSION_V1` fails and this exact RRF fusion is permanently closed. No alternate k, weight, constituent normalization, cutoff, rank window, source exception, feature subset, metric, diversity setting, or result-informed rescue is allowed.

## SonotaCo boundary

Only a GMN PASS may authorize a separately frozen one-shot SonotaCo 2013/2014 comparison against exact v31 and the literature comparators. SonotaCo remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation. The successor may not be modified after a SonotaCo outcome.

## Firewall

Every execution must assert:

- `blind_exclusion = [20.0, 55.0]`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `sonotaco_2013_2014_access = false` during GMN development;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`.
