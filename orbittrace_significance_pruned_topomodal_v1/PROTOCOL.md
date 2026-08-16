# OrbitTrace significance-pruned fixed-graph topomodal v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This successor addresses the single remaining failure exposed by the recent fixed-graph ToMATo truth sequence: complete-hierarchy candidate construction is highly sample-size coherent and recovers substantially more known streams than recurrent-EOM, but the correct hierarchy level is not surfaced early enough by intrinsic ranking. The exact latest rank-density fixed-graph successor passed both structural generalization gates plus every recovery, purity, and fragmentation gate and failed only the two MRR gates.

The present method therefore changes **candidate extraction itself**, not the post-hoc ordering of an unchanged hierarchy. It uses a label-free graph permutation null to merge modal branches whose observed prominence is not distinguishable from chance alignment between the frozen survey-relative density ranks and the frozen physical neighborhood graph. Only the statistically simplified modal partition becomes the candidate set.

This is not a rescue of the older `orbittrace_null_calibrated_persistence_v1`: that closed method kept exactly the same 2,094 selected families and used null outputs only to rerank those already-selected families. Here the null is upstream of candidate existence and changes the modal partition.

This is also not a rescue of the closed rank-density MST/EOM lane: no MST, upper-level-set point tree, branch mass×lifetime objective, or EOM/FOSC pruning is used.

The first technically valid result is binding. No post-result threshold, permutation count, density support, graph scale, ranking, or gate change is permitted.

## 1. Firewall

Use only target-excluded GMN 2022+2023 development data.

Remove inclusive solar longitude `[20.0,55.0]` before geometry, density estimation, graph construction, null generation, hierarchy fitting, candidate extraction, structural comparison, ranking, or truth evaluation.

Forbidden:

- OrbitTrace target information or target-region events;
- SonotaCo event/truth access during GMN development;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- orbital elements in candidate construction;
- known-shower labels in null calibration, extraction, or ranking;
- result-informed alpha, permutation count, k, graph radius, physical scale, density transform, support floor, root treatment, ranking, metric, or gate changes.

## 2. Exact sparse panels

Reuse exactly `ORBITTRACE_SCALE_STRESS_V1`:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Eight pooled target-excluded GMN 2022+2023 subsets only:

- denominator `128`, buckets `0,1,2,3`;
- denominator `1024`, buckets `0,1,2,3`.

No additional subset, salt, bootstrap, or replicate is authorized.

## 3. Density coordinate — frozen support-4 empirical rank

For each pooled subset independently reconstruct selected-parent GEO6:

`X = (cos(sol), sin(sol), sin(sun_lon)cos(ecl_lat), cos(sun_lon)cos(ecl_lat), sin(ecl_lat), vg/72)`.

Compute exact Euclidean distance `r3(i)` to the third nearest **other** event. Sort ascending `(r3(i), event_id)` and assign unique one-based rank `rank_i` and

`q_i = 1 - rank_i/(n+1)`.

This is the exact support-4 survey-relative density rank already frozen before outcome in the earlier rank-density work. No alternate k, annual split, ECDF convention, tie rule, smoothing, local scaling, or density fusion is authorized.

## 4. Fixed physical graph — exact #1284 geometry

Construct the exact #1284 embedding:

- `h_sol = 2 sin(5 deg/2)`;
- `h_rad = 2 sin(4 deg/2)`;
- `h_logv = ln(1.1)`;
- `Z = [cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, log(vg)/h_logv]`.

Construct the exact symmetric Euclidean radius graph at `r=1.0`, including self in stored neighbor lists exactly as #1284.

The graph supplies connectivity only. No kNN graph, MST, mutual reachability, adaptive radius, local scaling, or alternate bandwidth is permitted.

## 5. Observed ToMATo hierarchy

Fit GUDHI `3.12.0` ToMATo with:

- `graph_type='manual'` using the frozen physical radius graph;
- `density_type='manual'` using observed `q_i`.

Before any null or truth calculation, verify:

- leaf labels partition the event set;
- `len(diagram_) == len(children_)`;
- finite prominence is `birth - death >=0`;
- every finite diagram birth matches exactly one initial mode/leaf peak `max(q_i)` to numerical tolerance `1e-12`;
- the number of unmatched leaf peaks equals the number of connected-component roots reported by `max_weight_per_cc_`.

Because `q_i` values are unique, mode peaks are unique. This gives an unambiguous mapping from each finite persistence pair to the mode that dies and distinguishes finite modes from root/infinite modes without using labels.

## 6. Frozen graph-permutation null

### Scientific null

Condition on both:

- the exact observed fixed physical radius graph;
- the exact observed empirical density-rank multiset `{q_i}`.

Destroy only their eventwise alignment by permuting the q values over graph vertices.

This tests whether an observed finite modal prominence exceeds what can arise from accidental placement of the same survey-relative density ranks on the same survey-specific physical connectivity graph. It does not simulate shower truth and does not alter survey geometry or density marginals.

### Deterministic Monte Carlo design

Use exactly `B=199` permutations per sparse subset.

For replicate `b=1..199`, seed NumPy `PCG64` with

`uint64_be(SHA256('ORBITTRACE_SIGPRUNE_TM_V1|' + denominator + '|' + bucket + '|' + b)[0:8])`.

Generate one exact permutation of the observed q vector with `Generator(PCG64(seed)).permutation(q)`.

Fit a fresh GUDHI 3.12.0 manual-graph/manual-density ToMATo model on the unchanged observed graph and permuted q. Record only

`M_b = max(diagram_[:,0]-diagram_[:,1])`,

or `0.0` if the finite diagram is empty.

No null candidate memberships, known labels, or truth metrics enter calibration.

### Frozen familywise threshold

Use one-sided familywise `alpha=0.05` with the exact Monte Carlo max-statistic rule.

For any observed finite prominence `p`, define

`p_FWER(p) = (1 + #{b: M_b >= p}) / (B+1)`.

A finite mode is significant iff `p_FWER <= 0.05`.

With `B=199`, this is equivalent to strict

`p > tau`,

where `tau` is the **10th largest** value among the 199 null maxima. Equality does not survive, making the rule conservative under ties.

No alternate alpha, quantile interpolation, pseudocount, tail, multiple-testing correction, or adaptive B is authorized.

## 7. Significance-pruned candidate extraction

Set the observed ToMATo model's `merge_threshold_ = tau` exactly.

Use the resulting GUDHI `labels_` as the statistically simplified modal partition. Insignificant finite modes are therefore merged by ToMATo before candidates exist; finite modes with prominence `>tau` remain distinct.

For every final label:

1. collect its exact event membership;
2. identify all initial leaves represented in that final cluster;
3. identify the surviving mode as the initial leaf with largest q peak in that final cluster;
4. verify that the survivor is either:
   - a root/infinite mode, or
   - a finite mode with prominence strictly `>tau` and `p_FWER<=0.05`;
5. require candidate membership size `>=4` only after the simplified partition is formed.

No complete-hierarchy ancestors/descendants are additionally reported. No fallback to the unpruned hierarchy is allowed if candidate count is small.

Candidate prefix: `SPTM1`.

## 8. Frozen candidate ranking

The null supplies calibrated evidence only for finite mode contrasts. Root/infinite modes have no finite death contrast and therefore no finite max-statistic p-value.

Rank candidates lexicographically:

1. **finite significant-mode candidates first**;
2. finite candidates by ascending exact `p_FWER`, then decreasing observed finite prominence, then decreasing survivor peak q, then family hash;
3. root/infinite candidates only after all calibrated finite candidates, by decreasing survivor peak q, then decreasing member count, then family hash.

This ranking contains no fitted weight or result-informed blend. Within finite candidates, p-value and prominence are monotone expressions of the same preregistered max-statistic evidence.

If no finite mode is significant, root candidates are still reported according to the frozen root rule; this does not change alpha or create a fallback hierarchy.

## 9. Exact recurrent-EOM comparator

On each identical sparse subset reconstruct selected recurrent-EOM HDBSCAN v1 unchanged:

- GEO6;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean;
- ordinary condensed hierarchy;
- annual-normalized recurrent-EOM contribution;
- exact FOSC/EOM extraction;
- parent ranking by recurrent stability, ordinary stability, member count, deterministic family ID.

Comparator candidate summaries must reproduce the immutable #1284 structural artifact before truth opens.

## 10. Immutable prelabel boundary

Before known-shower truth is loaded, serialize and SHA-256 seal for every sparse panel:

- event-universe hash and annual totals;
- r3, q, density-order hashes;
- physical graph configuration/hash and degree summaries;
- all 199 deterministic null-max prominences and their ordered SHA-256;
- `tau` and exact alpha/B rule;
- observed finite-mode birth/prominence mapping audit;
- simplified final memberships, survivor-mode metadata, p-values/prominences, root status, and final ranks;
- comparator memberships/ranks;
- candidate-budget sufficiency;
- frozen cross-scale metrics below;
- all source/artifact/firewall hashes.

Write `SIGNIFICANCE_PRUNED_TOPOMODAL_V1_PRELABEL.json`, verify it in a separate workflow step, and only then load truth.

A technical failure before seal is an engineering no-result. Any repair must preserve every scientific definition above exactly.

## 11. Frozen cross-scale generalization gates

Reuse the exact #1284 fine→coarse candidate-mean Jaccard semantics.

For each bucket:

- restrict denominator-128 candidates to the nested denominator-1024 event universe;
- discard restricted memberships below support 4;
- for each fine candidate compute maximum Jaccard against retained restricted coarse candidates;
- compute identical exact recurrent-EOM comparator metric.

Require before truth:

**S1.** successor pooled fine→coarse mean-best-Jaccard strictly greater than recurrent-EOM;

**S2.** successor strict fine→coarse bucket wins in at least `3/4` buckets.

These gates are frozen in the prelabel and never influence alpha or extraction.

## 12. Truth semantics and equal budget

After prelabel seal only, use the selected recurrent-EOM parent's existing `metrics(...)` function unchanged, separately for 2022 and 2023 within every pooled subset.

For each subset let `K` equal the number of recurrent-EOM candidates.

Promotion requires at least K successor candidates before truth. Evaluate:

- all K parent candidates;
- exactly the first K frozen successor candidates.

If successor candidate count is below K in any panel, candidate-budget sufficiency fails and the final promotion verdict is automatically FAIL; no padding from the discarded hierarchy is permitted.

Truth semantics remain exactly:

- eligible shower >=4 annual events;
- positive match only at precision >=0.5 and overlap >=4;
- qualified matches;
- recovered@25/@50/@100/@500;
- top-100 dominant precision;
- MRR;
- median top-500 fragmentation.

## 13. Frozen truth gates

Use the same ten gates as the recent fixed-graph truth sequence.

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

## 14. Promotion verdict

Return

`PASS_SIGNIFICANCE_PRUNED_TOPOMODAL_V1`

iff:

- candidate budget is sufficient in all eight sparse subsets;
- structural gates S1-S2 both pass;
- truth gates T1-T10 all pass.

Otherwise return

`FAIL_SIGNIFICANCE_PRUNED_TOPOMODAL_V1`.

There is no partial promotion, alpha rescue, root-rule rescue, relaxed candidate budget, or alternate ranking after result.

## 15. Distinction from closed lanes

This architecture is not:

- complete #1284/rank-density ToMATo plus another ranking score: the candidate set itself is changed by prelabel null significance;
- `null_calibrated_persistence_v1`: that kept its candidate membership universe identical and applied post-selection family ranking calibration;
- rank-density MST/EOM: no MST, mass×lifetime quality, upper-level-set point tree, or EOM/FOSC objective;
- bivariate density persistence: no annual density lattice or exact threshold-state enumeration;
- recurrent-density topomodal: no annual minimum scalarization;
- lineage/map-equation/cut variants: no post-hoc hierarchy scheduling, overlap quota, or disjoint cut;
- generic thinning persistence: null calibration is on mode prominence conditional on the fixed physical graph, not repeated data thinning.

## 16. Conditional exposed SonotaCo transfer

Before the first technically valid GMN truth result, freeze a separate conditional SonotaCo 2013/2014 transfer protocol using the exact historical four-panel evaluator and selected recurrent-EOM controls. Execute only if GMN returns full PASS.

SonotaCo remains EXPOSED DEVELOPMENT ONLY.

## 17. Interpretation

A PASS would establish a method that uses a survey-relative density field, fixed physical topology, and label-free statistical mode significance to produce a compact candidate set that simultaneously:

- generalizes under ~8x sample-size change;
- beats recurrent-EOM recovery at equal reporting budget;
- matches or beats recurrent-EOM early ranking/MRR;
- preserves purity and fragmentation.

A FAIL closes this exact support-4 q density + fixed radius-1 graph + 199-permutation max-prominence FWER 0.05 simplification + frozen ranking architecture. Do not rescue via B, alpha, permutation target, k, graph scale, support, root handling, p-value tie rules, or alternate hierarchy output.