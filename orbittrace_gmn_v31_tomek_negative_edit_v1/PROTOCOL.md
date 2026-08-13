# OrbitTrace GMN v31 Tomek negative-reference editing v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 successor to the passed `orbittrace_gmn_v31_principle_local_geometry_oof_v1` parent. It tests one structural change only: edit the nonpositive training-reference pool using opposite-class mutual-nearest-neighbor boundary pairs before applying the exact same v31 local Euclidean margin.

The protocol is frozen before the first technically valid outcome. SonotaCo 2013/2014 is not accessed to evaluate, tune, or select this method. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.

## Motivation fixed before outcome

The direct v31-principle GMN parent is the strongest demonstrated v31-lineage GMN method on the immutable 226 hard families:

- recovered@25 = 23;
- recovered@50 = 41;
- recovered@100 = 66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified known-shower count = 95.

Subsequent changes to annual aggregation, local-scale normalization, shrinkage Mahalanobis distance, physical feature-block consensus, strict-group mean references, and RRF fusion failed and remain closed. The surviving signal is therefore specifically the full-space strict-OOF Euclidean nearest-positive versus nearest-nonpositive geometry.

Tomek links are a classical nearest-neighbor boundary-editing construction: two training examples form a Tomek link when they are mutual nearest neighbors and belong to opposite classes. In imbalanced-class usage, removing the majority-class endpoint is a standard way to reduce class overlap while preserving minority examples. This maps directly onto the v31 reference problem because qualified positive references are the smaller class and nonpositive fragments can act as locally ambiguous nearest-negative anchors.

This successor does not tune a metric, radius, k, threshold, score weight, or fusion. It asks only whether removing these parameter-free opposite-class boundary negatives improves the already-passed v31 local geometry.

## Immutable parent science

Everything below remains exactly the passed parent:

- same 226 P19 hard-family candidates and memberships;
- GMN 2022+2023 only;
- protected 20°–55° removed before scientific operations;
- exact 23D intrinsic representation: 10 structural + 7 cohesion + 6 centroid-neighborhood;
- exact deterministic five strict whole-shower folds;
- fold-training z-score;
- positive/reference truth semantics;
- ordinary Euclidean distance;
- 1-nearest positive and 1-nearest nonpositive scoring;
- local margin `d_nonpositive - d_positive`;
- exact diversity lambda 0.8 / scale 1.0;
- exact equal 1-based rank-sum fusion with immutable hard-family order;
- exact metric and truth evaluator.

The exact parent must first reproduce:

- recovered@25 = 23;
- recovered@50 = 41;
- recovered@100 = 66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified known-shower count = 95.

## Sole successor change

Within each already-frozen OOF training fold, after the exact parent z-score is fitted on the training rows:

1. Compute all pairwise ordinary Euclidean distances among the standardized training references.
2. For every training reference, select its single nearest *other* training reference. Distance ties are broken deterministically by immutable hard-family rank, then family ID.
3. A pair is a `TOMEK_OPPOSITE_PAIR` iff the two references select each other and one is positive while the other is nonpositive.
4. Remove **only the nonpositive endpoint** of every `TOMEK_OPPOSITE_PAIR` from the nonpositive reference set.
5. Keep every positive reference, every non-Tomek nonpositive reference, the test rows, and all folds unchanged.
6. For each held-out row, compute the same parent distances to the nearest retained positive and retained nonpositive reference and the same margin `d_nonpositive - d_positive`.
7. Apply the exact parent diversity and equal-rank fusion unchanged.

If any fold would retain zero positive or zero nonpositive references after this fixed edit, the method fails closed. No fallback reference rule is allowed.

No iterative Tomek deletion is performed. Links are computed once from the original standardized training fold. No ENN, SMOTE, resampling, class weights, relabeling, positive deletion, alternative tie rule, or repeated cleaning is authorized.

## Frozen promotion gate

PASS requires every condition against the exact reproduced parent:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 dominant precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified known-shower count **= 95**;
7. all protected-data and provenance assertions pass.

The first technically valid outcome is binding. FAIL permanently closes this exact single-pass Tomek negative-reference edit. No positive-endpoint deletion, both-endpoint deletion, repeated Tomek editing, cross-class-only nearest-neighbor variant, k-neighbor generalization, distance threshold, alternative tie break, edited-nearest-neighbor rule, class weight, fusion change, or result-informed rescue is allowed.

## SonotaCo boundary

Only a GMN PASS may authorize a separately frozen one-shot SonotaCo 2013/2014 comparison against exact v31 and the literature comparators. SonotaCo remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation. The method may not be changed after a SonotaCo outcome.

## Firewall

Every execution must assert:

- `blind_exclusion = [20.0, 55.0]`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `sonotaco_2013_2014_access = false` during GMN development;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`.
