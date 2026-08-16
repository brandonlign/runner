# OrbitTrace topomodal canonical death-support v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This is the next truth-bearing successor after the exact intrinsic-all-node ranking and exact map-equation-all-node ranking both failed their frozen MRR gates while the fixed-scale ToMATo candidate hierarchy repeatedly beat recurrent-EOM on sparse known-stream coverage and purity.

This successor does **not** modify the #1284 physical graph, density, ToMATo hierarchy, radius, support floor, sample panels, truth semantics, or promotion standard. It changes candidate semantics: instead of reporting every eligible hierarchy node, it reports one canonical support for each **finite ToMATo persistence feature**—the losing mode's component immediately before that mode dies into a stronger mode.

This is intentionally **not called an antichain**: canonical death supports can still be nested across different persistence features. The scientific hypothesis is narrower: redundant intermediate hierarchy nodes, rather than the fixed-scale modal generator itself, caused stream-bearing families to be displaced in the early ranks.

## 1. Firewall

Use only target-excluded GMN 2022+2023 development data. Inclusive solar longitude `[20.0,55.0]` is removed before geometry, graph construction, hierarchy construction, candidate selection, ranking, or truth evaluation.

Forbidden:

- OrbitTrace target information or target-region events;
- SonotaCo scientific access;
- ASFN or EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- result-informed changes to radius, coordinate scales, density, graph, mode-survival rule, finite/infinite feature treatment, support floor, persistence score, ranking, sample panels, truth metric, candidate budget, or gates.

No external benchmark is authorized by this sparse-development experiment.

## 2. Exact sparse panels

Reuse exactly the existing target-excluded `ORBITTRACE_SCALE_STRESS_V1` deterministic subsets:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Evaluate exactly:

- coarse denominator `128`, buckets `0,1,2,3`;
- fine denominator `1024`, buckets `0,1,2,3`.

No new salt, denominator, bucket, replicate, bootstrap, or panel is permitted.

## 3. Underlying ToMATo hierarchy — unchanged from #1284

Use exactly:

- `h_sol = 2 sin(5°/2)`;
- `h_rad = 2 sin(4°/2)`;
- `h_logv = ln(1.1)`;
- `Z = (cos(sol)/h_sol, sin(sol)/h_sol, cos(lat)cos(lon)/h_rad, cos(lat)sin(lon)/h_rad, sin(lat)/h_rad, ln(v_g)/h_logv)`;
- exact symmetric Euclidean radius graph at `r=1.0`, including self-neighbor;
- `rho_i = |N_i| / n` including self;
- GUDHI `3.12.0` `Tomato(graph_type='manual', density_type='manual')`;
- exact `leaf_labels_`, `children_`, `diagram_`, and connected-component roots;
- minimum candidate support `4`, applied only after the full hierarchy exists.

Before any truth access, reconstruct the **complete** leaf + internal + root membership hierarchy exactly as #1284 did and require its candidate count and complete sorted `(family_hash, member_count, first_node, is_root)` rows to match the authoritative #1284 artifact for every subset. A mismatch aborts before truth.

## 4. Canonical finite-feature support

### 4.1 Active-mode lineage

Each ToMATo leaf begins with one active mode. For each leaf, define:

- `mode_peak = max(rho_i)` over points in that leaf;
- `mode_key = lexicographically smallest event ID among points in that leaf attaining `mode_peak` within exact floating equality.

Process `children_` in its native merge order. Each child node carries the active mode inherited from its surviving descendant.

At a merge of child nodes `a,b`:

- the child with larger active `mode_peak` survives;
- if peaks are exactly equal, the child with lexicographically smaller active `mode_key` survives;
- the other child is the **dying child**;
- the new parent inherits the surviving child's active mode.

The candidate associated with that finite persistence event is exactly the dying child's membership immediately before the merge.

No ancestor, descendant, union, trimming, split, or alternative support is considered for that persistence event.

### 4.2 Infinite features are not detection candidates

Connected-component survivors correspond to ToMATo's infinite persistence points. They are **not reported as stream candidates** in this detector. The detector's scientific object is a finite local density-mode feature that is distinguishable from a stronger enclosing/background mode; an entire disconnected graph component has no observed finite death level and therefore has no comparable finite prominence.

This rule is frozen before truth. Do not later add roots because a result is weak.

### 4.3 Persistence score

Let `P = sort(diagram_[:,0] - diagram_[:,1])` ascending.

Require `len(P) == len(children_)`. The `i`th `children_` merge is assigned `P[i]`; this is the same native merge/prominence ordering already used and zero-label-audited in the prior #1284 successors.

For the dying child at merge `i`, define

`persistence = P[i]`.

Emit the dying-child membership iff its support is at least `4`.

Exact duplicate memberships are forbidden; any duplicate is an engineering abort, not a deduplication choice.

Rank emitted candidates by:

1. decreasing `persistence`;
2. deterministic `family_hash` ascending as the sole tie-break.

No root flag, density, size, recurrence, year balance, map-equation score, previous rank, learned model, or fitted weight is used.

## 5. Zero-label hierarchy/persistence invariants

Before truth, require all of the following:

1. every emitted support is exactly one membership node in the full #1284 hierarchy;
2. every finite merge contributes exactly one dying child before the support-4 filter;
3. a node can die at most once;
4. each connected component has exactly one final surviving active mode and it is not emitted as a finite feature;
5. `number_of_finite_deaths == len(children_) == len(diagram_)`;
6. assigned prominences are finite and nonnegative;
7. for every distinct prominence threshold `t`, ToMATo's own `merge_threshold_=t` cluster count equals `count(P > t) + n_connected_components`;
8. using each leaf's active peak and assigned prominence, the multiset of reconstructed finite persistence pairs `(birth=dying_mode_peak, death=dying_mode_peak-persistence)` matches the multiset of `diagram_` rows within absolute tolerance `1e-12` after lexicographic sorting.

Invariant 8 makes the survival/death interpretation an audited reconstruction of ToMATo's persistence features rather than an arbitrary tree orientation. Failure of any invariant is an engineering no-result before labels are opened.

## 6. Recurrent-EOM comparator — unchanged

On each identical subset reconstruct selected recurrent-EOM HDBSCAN v1 exactly:

- GEO6 unchanged;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean;
- ordinary condensed tree;
- annual-normalized recurrent EOM;
- FOSC/EOM selection using recurrent stability.

Rank comparator candidates exactly as the selected parent:

1. decreasing recurrent stability;
2. decreasing ordinary stability;
3. decreasing member count;
4. deterministic family ID.

Its unordered memberships must match the authoritative #1284 comparator rows before truth.

## 7. Immutable prelabel boundary

For all eight subsets, before any shower truth is evaluated, persist:

- event-universe hash;
- complete #1284 hierarchy verification summary;
- every canonical finite-feature candidate's event IDs, dying node, active mode peak/key, persistence, family hash, and final rank;
- every recurrent-EOM candidate membership and rank;
- source/artifact hashes and firewall flags.

Write `TOPOMODAL_DEATH_SUPPORT_V1_PRELABEL.json`, compute SHA-256, print it, and verify it in a separate workflow step. Candidate construction/ranking may not run again after truth opens.

## 8. Equal candidate-reporting budget

For each subset let

`K = min(number_of_canonical_successor_candidates, number_of_recurrent_EOM_candidates)`.

Evaluate **both** methods at exactly their first `K` candidates. This prevents either method from gaining recovery simply by outputting more candidates.

Also report each method's complete-list metrics only as diagnostics; complete-list metrics are never promotion gates.

Require `K >= 1` in all eight subsets or return a binding FAIL (not an engineering error).

## 9. Truth metric — unchanged parent semantics

Use the selected recurrent-EOM parent's existing `metrics(...)` function unchanged, separately for 2022 and 2023 inside every pooled subset.

- annual shower eligibility: at least 4 events in that subset-year;
- positive candidate/shower match: precision `>=0.5` and overlap `>=4`;
- report qualified matches, recovered@25/@50/@100/@500, top-100 dominant precision, MRR, and median top-500 fragmentation.

## 10. Frozen promotion gates

There are 16 bucket-year panels. For each sample scale aggregate equal-budget metrics across its 8 panels:

- `qualified_total = sum(qualified_matches)`;
- `mrr_mean = mean(MRR)`;
- `precision_mean = mean(top100_dominant_precision)`;
- `fragmentation_mean = mean(fragmentation_median_top500)`;
- panelwise qualified-match nonloss/win counts.

Return

`PASS_TOPOMODAL_DEATH_SUPPORT_V1`

iff all ten gates hold:

### Fine scale (`d=1024`)

1. successor `qualified_total` is strictly greater than recurrent-EOM;
2. successor has at least as many qualified matches in at least `6/8` panels;
3. successor `mrr_mean` is at least recurrent-EOM;
4. successor `precision_mean` is at least recurrent-EOM;
5. successor `fragmentation_mean` is no higher than recurrent-EOM.

### Coarse scale (`d=128`)

6. successor `qualified_total` is at least recurrent-EOM;
7. successor has at least as many qualified matches in at least `6/8` panels;
8. successor `mrr_mean` is at least recurrent-EOM;
9. successor `precision_mean` is at least recurrent-EOM;
10. successor `fragmentation_mean` is no higher than recurrent-EOM.

Otherwise return

`FAIL_TOPOMODAL_DEATH_SUPPORT_V1`.

These are the same scientific dimensions as the prior sparse tests; the equal-budget definition is predeclared here because the new candidate semantics can legitimately produce fewer candidates than recurrent-EOM.

## 11. Interpretation / closure

A PASS would show that #1284's sample-size-stable modal hierarchy can be converted into a sparse-survey detector that also beats recurrent-EOM on known-stream recovery/ranking without reporting every intermediate hierarchy node. Only then is full-catalog scaling worth engineering and separately preregistering.

A FAIL closes this exact `fixed-scale ToMATo + finite-feature death-support + persistence ranking` architecture. Do not add roots, change the dying-child rule, modify the support floor, use a different persistence convention, add a second score, alter candidate budget, or relax gates after truth.
