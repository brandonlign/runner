# OrbitTrace recurrent-EOM fixed-scale stress diagnostic v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY DIAGNOSTIC OUTCOME.**

This is a structural, zero-label diagnostic of the selected recurrent-EOM HDBSCAN v1 paper/development method. It is **not a successor method**, does not alter the selected method, does not define a promotion gate, and cannot promote any parameter or algorithm.

The diagnostic asks one narrow causal question raised by the already-recorded cross-survey limitation: does keeping HDBSCAN `min_cluster_size=10, min_samples=10` fixed cause ordinary-EOM and recurrent-EOM extraction to become increasingly indistinguishable when the same target-excluded GMN geometry is observed at much smaller sample sizes?

The result may support or weaken the hypothesis that fixed-count density resolution contributes to recurrent-EOM becoming mechanism-inactive on small surveys. It may motivate a future **independently derived method class**, but it may not be used to tune `k`, support counts, thinning fractions, score weights, thresholds, or any closed successor.

## 1. Scientific parent and firewall

Parent is exact selected recurrent-EOM HDBSCAN v1 on PR #1243:

- selected branch head at diagnostic branch creation: `0248177a2b4dc1f7a0969931d835097d3e86c06f`;
- recurrent-EOM kernel Git blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- parent GMN runner Git blob: `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`;
- binding full-GMN run: `31827903547`;
- target-excluded GMN counts: 2022 = 315024, 2023 = 423658, pooled = 738682.

Use target-excluded GMN 2022+2023 geometry only. The inclusive protected solar-longitude interval `[20.0,55.0]` remains excluded before geometry enters this diagnostic.

Forbidden throughout:

- OrbitTrace target information or target-region events;
- SonotaCo 2013/2014 scientific access;
- ASFN or EFN event-level re-access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- shower-label/truth use in any statistic or decision;
- method promotion or parameter selection from the outcome.

Previously recorded external **sample counts and mechanism-active/inactive status** may be referenced only in the later interpretation because they are already frozen project-level facts; no external rows or labels may be opened.

## 2. Exact parent representation and clustering

For every retained subset, use the exact selected parent configuration unchanged:

- GEO6 representation:
  `[cos(sol), sin(sol), sin(lon_sc) cos(beta), cos(lon_sc) cos(beta), sin(beta), vg/72]`;
- Euclidean distance;
- `min_cluster_size=10`;
- `min_samples=10`;
- `cluster_selection_method='eom'`;
- `cluster_selection_epsilon=0`;
- `allow_single_cluster=false`;
- one pooled fit over retained 2022+2023 events;
- ordinary EOM and exact recurrent-EOM extracted from that same condensed tree.

No representation, metric, HDBSCAN setting, recurrence formula, ranking rule, or feature scaling may change anywhere in this diagnostic.

## 3. Deterministic sampling rule

Define for each accessible event ID `eid`:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

For denominator `d`, bucket `b` retains an event iff:

`H(eid) mod d == b`.

All denominators are powers of two. Bucket `0` therefore forms an exactly nested sequence: membership at denominator `2d` implies membership at denominator `d`.

### Main nested sequence

Run bucket `0` at exactly:

`d = 8, 16, 32, 64, 128, 256, 512, 1024`.

These fractions are frozen because they provide a geometric sample-size sweep from roughly 9.2e4 down to roughly 7.2e2 pooled events without introducing an outcome-derived scale.

### Replicate buckets

At exactly `d = 64, 128, 512, 1024`, also run buckets `b = 1,2,3` in addition to the nested bucket `b=0`, yielding four deterministic disjoint replicate buckets at each anchor denominator.

No alternate denominator, salt, bucket, random seed, or extra replicate may be added after an outcome.

## 4. Zero-label structural outputs per fit

For each `(d,b)` fit persist only geometry/tree/extraction diagnostics:

1. retained pooled event count and annual counts;
2. exact non-self 10-nearest-neighbor GEO6 distance quantiles: median, 90th percentile, 99th percentile;
3. condensed-tree row count and unique cluster-node count;
4. ordinary-EOM selected-node count;
5. recurrent-EOM selected-node count;
6. exact ordinary/recurrent selected-node intersection and symmetric-difference counts;
7. selected-node Jaccard similarity;
8. `mechanism_active = (ordinary_selected_nodes != recurrent_selected_nodes)`;
9. exact ordinary/recurrent selected membership hashes and their intersection count;
10. count of hierarchy nodes with strictly positive recurrent quality;
11. count of hierarchy nodes with strictly positive annual contribution in both years.

No known-shower label, recovery count, precision, F1, MRR, v31 score, literature score, or target statistic is permitted.

## 5. Predeclared summary

Define:

- `ASFN_SIZE_BAND` = all eight replicate fits at denominators 64 and 128;
- `EFN_SIZE_BAND` = the four replicate fits at denominator 1024.

This naming only reflects their order-of-magnitude relation to already-recorded external sample counts; it does not access either external dataset.

Let `inactive_rate` be the fraction of fits in a band with `mechanism_active=false`.

The sole categorical diagnostic interpretation is frozen as:

- `SUPPORTS_FIXED_SCALE_INERTIA_HYPOTHESIS` if `inactive_rate >= 0.75` in both bands;
- `REFUTES_FIXED_SCALE_INERTIA_HYPOTHESIS` if `inactive_rate <= 0.25` in both bands;
- otherwise `MIXED_FIXED_SCALE_INERTIA_EVIDENCE`.

This categorical interpretation is **not** a method gate. Regardless of category, no `min_samples`, `min_cluster_size`, adaptive rule, score, threshold or successor is selected by this diagnostic.

The 10-NN distance growth and hierarchy-complexity curves are descriptive mechanism evidence only. No fitted exponent becomes a method parameter.

## 6. Relationship to prior thinning and #1271

This does not repeat the historical GMN thinning/subsample family-stability diagnostic. That closed diagnostic asked whether family persistence under thinning was useful as a **quality/ranking proxy**. This diagnostic never ranks families by thinning stability and never uses truth.

It also does not rescue recurrent local-BIC HDBSCAN v1 (#1271). #1271 changed the scientific hierarchy to `8/4` and added a local-BIC extraction quality. This diagnostic changes **nothing** about parent 10/10 HDBSCAN; it only asks what that fixed parent does when the accessible sample size is deterministically reduced.

No #1271 parameter, BIC term, support count, ranking, or outcome may be reused or tuned here.

## 7. Closure rule

After the first technically valid complete diagnostic:

- preserve all exact outputs and the categorical interpretation;
- do not rerun with changed scales/salts/buckets;
- do not turn a favorable-looking denominator into a successor parameter;
- do not access external scientific data from this diagnostic;
- any future method must have a separately written, independently motivated, pre-outcome protocol.

## 8. Required provenance fields

The result must record:

- protocol Git blob and implementation Git blob;
- execution commit;
- exact runtime/source hashes;
- sampling salt and all denominators/buckets;
- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `shower_truth_used=false`;
- `sonotaco_2013_2014_access=false`;
- `asfn_event_level_access=false`;
- `efn_event_level_access=false`;
- `amos_scientific_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `method_parameter_selection_from_result=false`.
