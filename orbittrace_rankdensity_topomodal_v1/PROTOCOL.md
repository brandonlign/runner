# OrbitTrace rank-density fixed-graph topomodal v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This successor is motivated only by two zero-label findings established before the recent topomodal truth experiments:

1. PR #1277 showed that the same event's **local-density ordering** is unusually stable under ~8x deterministic thinning even though absolute local scale changes strongly. Across frozen supports 4/8/16/32, raw local-compactness rank had median paired Spearman `0.8530/0.8845/0.8950/0.8938` (overall ~`0.8891`).
2. PR #1278 then showed that putting the exact support-4 empirical density rank on a Euclidean MST/EOM topology fails cross-scale membership coherence. Its binding interpretation attributed the failure to reorganizing point-tree topology, not to collapse of the rank coordinate.
3. Independently, PR #1284 established a much more sample-size-coherent **fixed physical radius graph + ToMATo modal hierarchy**, with pooled fine->coarse candidate Jaccard `0.8067062037` versus recurrent-EOM `0.6152941107`, 4/4 wins.

The present experiment tests the direct synthesis implied by those pre-truth structural results: keep the stable survey-relative local-density rank as the density coordinate, but place it on #1284's fixed physical graph and ToMATo topology instead of the closed MST/EOM topology.

This is **not** a rerank or fusion of the failed #1284 truth outputs, lineage variants, recurrent-density successor, or bivariate-density result. The density field changes upstream and therefore changes the modal hierarchy itself. No result from those truth experiments selects a threshold, weight, k, graph scale, score blend, or gate here.

The first technically valid outcome is binding. No post-result rescue is permitted.

## 1. Firewall

Use only target-excluded GMN 2022+2023 development data.

Remove inclusive solar longitude `[20.0,55.0]` before any geometry, nearest-neighbor calculation, physical graph, density rank, hierarchy, candidate generation, ranking, structural comparison, or truth evaluation.

Forbidden:

- OrbitTrace target information or target-region events;
- SonotaCo event/truth access during the GMN experiment;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- orbital elements in candidate construction;
- known-shower labels in candidate construction/ranking;
- result-informed k, graph radius, physical scale, density transform, hierarchy subset, support floor, score, tie-break, metric, or gate modification.

## 2. Exact sparse development panels

Reuse exactly `ORBITTRACE_SCALE_STRESS_V1`:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Evaluate exactly eight pooled target-excluded GMN 2022+2023 subsets:

- denominator `128`, buckets `0,1,2,3` (~5.8k events each);
- denominator `1024`, buckets `0,1,2,3` (~0.7k events each).

No additional denominator, bucket, salt, bootstrap, or replicate is authorized.

## 3. Survey-relative local-density coordinate — exact pre-existing support-4 definition

For each pooled sparse subset independently, reconstruct exact parent GEO6:

`X = (cos(sol), sin(sol), sin(sun_lon)cos(ecl_lat), cos(sun_lon)cos(ecl_lat), sin(ecl_lat), vg/72)`.

For every event compute exact Euclidean distance `r3(i)` to its **third nearest other event** in GEO6.

The third-neighbor anchor is not newly selected here. It is the exact support-4 local-density rank coordinate already frozen in PR #1278, itself motivated before outcome by the project's established minimum evaluable shower support of four events.

Sort all events from locally densest to sparsest by ascending:

`(r3(i), event_id)`.

Assign deterministic one-based rank `rank_i` and empirical density level

`q_i = 1 - rank_i/(n+1)`.

Thus every `q_i` is unique and strictly in `(0,1)`, larger means denser, and every subset has the same empirical set of density levels regardless of absolute sample density.

No alternate k, ECDF convention, tie handling, annual split, local normalization, smoothing, or density fusion is authorized.

### Pretruth provenance audit

The workflow must pin and audit the exact historical PR #1277/#1278 source/protocol blobs that define the support-4 rank coordinate. A small deterministic synthetic fixture must independently verify third-other-neighbor indexing and exact `(r3,event_id)` ordering before scientific prelabel generation.

## 4. Fixed physical graph — exact #1284 topology

Separately from GEO6 density estimation, construct the exact #1284 physical embedding:

- `h_sol = 2 sin(5 deg / 2)`;
- `h_rad = 2 sin(4 deg / 2)`;
- `h_logv = ln(1.1)`;

`Z = [cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, log(vg)/h_logv]`.

Construct the exact symmetric Euclidean radius graph at `r=1.0`, including self in each stored neighbor list exactly as #1284.

The physical graph supplies **connectivity only**. Radius degree does not enter the new density value. No kNN graph, MST, mutual reachability, local scaling, adaptive radius, or alternate bandwidth is permitted.

## 5. Rank-density ToMATo hierarchy

Fit GUDHI `3.12.0` ToMATo with:

- `graph_type='manual'` using the exact #1284 radius graph;
- `density_type='manual'` using the frozen `q_i` vector.

Expose the complete hierarchy exactly as #1284:

- every leaf basin;
- every internal merge-node membership;
- every connected-component root membership;
- exact membership deduplication;
- report candidates only after hierarchy construction when membership size >=4.

No prominence threshold, chosen cluster count, flattening, EOM pruning, persistence cutoff, lineage quota, or disjoint cut is allowed.

Candidate prefix: `RDTM1`.

## 6. Frozen intrinsic ranking

Use the exact intrinsic ToMATo ranking semantics frozen **before truth** in `orbittrace_topomodal_sparse_recovery_v1` (source blob `752df8212ce601227f6e9170b0fe994ba06b515d`, commit `312b1b718ae105813de242355142a74e7d377d65`), applied to this successor's own q-density hierarchy.

Specifically:

- obtain the finite ToMATo prominence sequence exactly as the pinned source;
- reconstruct unique hierarchy parents exactly as the pinned source;
- for every eligible node compute root status, peak density, mean density, and finite prominence span exactly as the pinned source;
- rank roots first by decreasing peak density, then mean density, then member count, then family hash;
- rank non-roots by decreasing prominence span, then peak density, then mean density, then member count, then family hash.

No new ranking feature, learned score, recurrence bonus, candidate-size coefficient, overlap penalty, diversity schedule, or post-hoc blend is permitted.

The workflow must pin the historical source blob and verify that a zero-data fixture reproduces its lexicographic ranking contract before scientific execution.

## 7. Exact recurrent-EOM comparator

On each identical subset reconstruct selected recurrent-EOM HDBSCAN v1 unchanged:

- GEO6 exactly;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean;
- ordinary condensed hierarchy;
- exact annual-normalized recurrent-EOM contribution;
- exact FOSC/EOM extraction;
- selected-parent ranking by recurrent stability, ordinary stability, member count, deterministic family ID.

Before truth, comparator candidate membership/count summaries must reproduce the immutable #1284 structural artifact for all eight panels.

## 8. Immutable prelabel boundary

Before known-shower truth is loaded, serialize and SHA-256 seal for every panel:

- event-universe hash and annual totals;
- exact GEO6 `r3` vector hash and q-rank hash;
- exact physical graph configuration, edge/degree summaries, and graph hash;
- complete rank-density ToMATo candidate memberships, hierarchy metadata, score fields, and final ranks;
- comparator memberships and ranks;
- source/artifact hashes and firewall flags;
- candidate-budget sufficiency;
- cross-scale structural comparison data described below.

Write `RANKDENSITY_TOPOMODAL_V1_PRELABEL.json`, verify SHA-256 in a separate workflow step, and only then evaluate shower labels. Candidate generation/ranking may not be rerun after truth.

A technical failure before the sealed prelabel exists is an engineering no-result. Any repair must preserve all scientific definitions above exactly.

## 9. Frozen cross-scale generalization test

Because the project goal requires sample-size generalization, this successor has a direct zero-label structural gate in addition to the unchanged truth gates.

Reuse the exact nested-membership metric from the #1284 structural program. For each bucket:

1. denominator-1024 is the fine event universe `F`;
2. restrict each denominator-128 candidate membership to `F` and discard restricted memberships with fewer than four events;
3. for every fine candidate, compute its maximum Jaccard with any retained restricted coarse candidate;
4. compute the same quantity for exact recurrent-EOM;
5. aggregate with the exact #1284 candidate-mean convention and pooled convention.

Frozen structural requirements:

**S1.** successor pooled fine->coarse mean-best-Jaccard must be strictly greater than recurrent-EOM;

**S2.** successor must have strictly greater bucket-level fine->coarse mean-best-Jaccard in at least `3/4` buckets.

These metrics are computed and frozen in the prelabel before truth. They do not alter candidate generation or ranking.

## 10. Truth semantics and equal reporting budget

After prelabel seal only, use the selected recurrent-EOM parent's existing `metrics(...)` semantics unchanged, separately for 2022 and 2023 within every pooled subset.

For each subset let `K` be the number of recurrent-EOM candidates. Require the successor to have at least K reportable candidates before truth. Evaluate:

- all K recurrent-EOM candidates;
- exactly the first K frozen successor candidates.

Annual truth semantics remain:

- shower eligibility >=4 events;
- positive candidate/shower match requires precision >=0.5 and overlap >=4;
- qualified matches;
- recovered@25/@50/@100/@500;
- top-100 dominant precision;
- MRR;
- median top-500 fragmentation.

## 11. Frozen truth gates

Use exactly the same ten sparse truth gates as the prior topomodal experiments.

### Fine sparse scale d=1024

T1. successor qualified total strictly greater than recurrent-EOM;
T2. qualified matches nonlower in at least 6/8 annual panels;
T3. mean MRR not lower;
T4. mean top-100 dominant precision not lower;
T5. mean fragmentation not higher.

### Coarse scale d=128

T6. successor qualified total not lower;
T7. qualified matches nonlower in at least 6/8 annual panels;
T8. mean MRR not lower;
T9. mean top-100 dominant precision not lower;
T10. mean fragmentation not higher.

## 12. Promotion verdict

Return

`PASS_RANKDENSITY_TOPOMODAL_V1`

iff:

- candidate budget is sufficient in all eight panels;
- both structural generalization gates S1-S2 pass;
- all ten truth gates T1-T10 pass.

Otherwise return

`FAIL_RANKDENSITY_TOPOMODAL_V1`.

There is no mixed promotion verdict and no post-result rescue.

## 13. Why this is not a closed lane

This architecture is distinct from:

- PR #1278 rank-density MST/EOM: same pre-established q coordinate, but that closed method used a Euclidean MST upper-level-set tree and EOM pruning; this successor uses the separately established fixed physical radius graph and complete ToMATo modal hierarchy, with no MST or EOM pruning;
- #1284 pooled radius-count topomodal: same physical graph/topology family, but the density field here is the survey-relative support-4 GEO6 rank coordinate rather than absolute radius-neighbor count/n; therefore hierarchy construction changes upstream;
- recurrent-density topomodal: no annual density minimum or annual scalarization occurs here;
- bivariate density persistence: no annual threshold lattice, exact-state support area, or multiparameter fragmentation occurs here;
- lineage/map-equation variants: no post-hoc scheduling or secondary rank score is applied to #1284 candidates.

## 14. Conditional exposed SonotaCo transfer

Before the first technically valid GMN truth outcome, freeze a separate conditional SonotaCo 2013/2014 transfer protocol using the exact historical four-panel evaluator and selected recurrent-EOM controls. Execute only on full GMN PASS.

SonotaCo remains EXPOSED DEVELOPMENT ONLY.

## 15. Interpretation

A PASS would be the first architecture in this sequence to combine all of:

- a support-free/fixed-physical candidate topology that remains coherent under ~8x sample-size change;
- superior sparse known-stream recovery at equal reporting budget;
- noninferior early ranking/MRR;
- noninferior purity and fragmentation.

A FAIL closes this exact support-4 GEO6 empirical-rank + fixed #1284 graph + complete ToMATo hierarchy + inherited intrinsic ranking architecture. Do not rescue via k changes, physical scale changes, rank transforms, annual variants, selected prominence levels, ranking blends, or relaxed gates.