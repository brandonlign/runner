# OrbitTrace topomodal support-resolved cut v1

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This successor addresses the specific hierarchy-selection problem established by the preceding closed experiments without modifying their outcomes:

- reporting every eligible #1284 hierarchy node gave strong sparse known-stream coverage but poor early ordering because nested versions compete for rank;
- reporting only finite dying-mode supports collapsed under thinning because many useful stream-scale merged/surviving nodes were discarded.

The new architecture chooses a deterministic **non-overlapping cut** through the unchanged #1284 ToMATo hierarchy. A split is considered reportable only when both child branches already satisfy the pre-existing support-4 reporting floor. Otherwise the merged parent is retained. This is a new candidate-selection semantics, not a reranking rescue of either closed successor.

## 1. Firewall

Use only target-excluded GMN 2022+2023 development data. Inclusive solar longitude `[20.0,55.0]` is removed before all geometry, hierarchy, selection, ranking, and truth operations.

Forbidden: OrbitTrace target information/events; SonotaCo scientific access; ASFN/EFN event-level access; AMOS scientific access; MAARSY/DMS scientific access; and any result-informed change to geometry, radius, density, support floor, cut rule, score, tie-break, panels, metrics, budget, or gates.

## 2. Sparse panels

Reuse exactly `ORBITTRACE_SCALE_STRESS_V1`:

`H(eid)=uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Exactly denominator `128` and `1024`, buckets `0,1,2,3`. No other replicate or thinning panel.

## 3. Underlying hierarchy — exact #1284

Use unchanged:

- `h_sol=2 sin(5°/2)`;
- `h_rad=2 sin(4°/2)`;
- `h_logv=ln(1.1)`;
- physical six-dimensional embedding from #1284;
- exact symmetric Euclidean radius graph `r=1.0`, including self;
- `rho_i=|N_i|/n` including self;
- GUDHI `3.12.0` manual ToMATo;
- complete leaf/internal/root hierarchy;
- minimum reportable support `4`.

Before truth, the complete eligible hierarchy and recurrent-EOM comparator memberships must exactly reproduce the authoritative #1284 structural artifact (`31955621864`, SHA-256 `e8cf7d92e96db9a1c99578f6efc63baf1534b94ab975e94f789fa6bc4a718497`).

## 4. Support-resolved hierarchy cut

Reconstruct the binary hierarchy from `leaf_labels_` and `children_`. Process each connected-component root independently.

Define recursively `CUT(node)`:

1. If `node` is a leaf, emit `node` iff its support is at least `4`; otherwise emit nothing.
2. If `node` has children `a,b` and **both** `|a|>=4` and `|b|>=4`, return `CUT(a) union CUT(b)`.
3. Otherwise, emit `node` iff `|node|>=4`.

No lookahead, score comparison, density test, prominence threshold, global cluster count, optimization, or label information is used in the cut.

Required zero-label invariants:

- every emitted candidate is an exact node of the #1284 hierarchy;
- every emitted candidate has support >=4;
- emitted candidates are pairwise disjoint;
- within every root with support >=4, emitted candidates partition all events in that root except events belonging only to sub-4 roots, which produce no candidate;
- no emitted candidate is ancestor/descendant of another emitted candidate;
- applying the rule twice to the same frozen hierarchy gives the identical membership set.

This locally support-resolved cut is distinct from the previously closed flat global-count/Persistable selectors: it does not choose a global number of clusters and does not search a flattening ladder.

## 5. Frozen ranking

The cut removes nested rank competition. Rank the resulting disjoint candidates using one intrinsic modal contrast.

For each hierarchy node maintain the active mode exactly as in the audited death-support reconstruction:

- leaf active mode is the event with maximum `rho`; exact ties use lexicographically smallest event ID;
- at a merge, the child with larger active-mode peak survives; exact ties use lexicographically smaller active-mode key.

For an emitted candidate `C`, let:

- `peak(C)` = inherited active-mode peak density;
- `outside_merge(C)` = the merge level at which `C` merges into its parent;
- for a connected-component root, `outside_merge(C)=0`.

Merge levels are reconstructed from the same GUDHI persistence diagram/active-mode pairing and must reproduce the finite diagram within absolute tolerance `1e-12` before truth.

Define

`modal_contrast(C)=peak(C)-outside_merge(C)`.

Require finite `modal_contrast>=0` up to `1e-12` numerical tolerance.

Rank by:

1. decreasing `modal_contrast`;
2. deterministic `family_hash` ascending.

No support, raw size, root flag, recurrence, year balance, map equation, previous rank, learned score, or fitted weighting is permitted as a tie-break or secondary feature.

## 6. Comparator and equal budget

Reconstruct selected recurrent-EOM HDBSCAN v1 unchanged and reproduce #1284 comparator memberships before truth.

For each subset define

`K=min(successor_candidate_count,recurrent_candidate_count)`.

Evaluate both methods on exactly their first `K` candidates. Complete-list metrics are diagnostics only. `K<1` in any subset is a binding FAIL.

## 7. Immutable prelabel

Before shower truth, write and hash `TOPOMODAL_SUPPORT_RESOLVED_CUT_V1_PRELABEL.json` containing all eight event-universe hashes, full-hierarchy verification, cut memberships, modal contrasts/ranks, comparator memberships/ranks, provenance, and firewall flags. Truth evaluation may consume only this immutable prelabel; candidate generation/ranking may not rerun after truth.

## 8. Truth semantics and frozen gates

Use the selected parent's unchanged `metrics(...)` semantics separately for each year: annual shower eligibility >=4 events; positive match precision >=0.5 and overlap >=4; report qualified matches, recovered@25/@50/@100/@500, top-100 dominant precision, MRR, and median top-500 fragmentation.

For each scale aggregate across its 8 bucket-year panels. Return `PASS_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1` iff all ten gates hold:

Fine (`d=1024`):
1. successor qualified total strictly greater than comparator;
2. qualified nonloss in >=6/8 panels;
3. MRR mean >= comparator;
4. precision mean >= comparator;
5. fragmentation mean <= comparator.

Coarse (`d=128`):
6. successor qualified total >= comparator;
7. qualified nonloss in >=6/8 panels;
8. MRR mean >= comparator;
9. precision mean >= comparator;
10. fragmentation mean <= comparator.

Otherwise `FAIL_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1`.

## 9. Closure

A PASS would justify engineering the same support-resolved topology for full-GMN scaling and then freezing a full-catalog comparison. A FAIL permanently closes this exact cut rule + modal-contrast ranking. Do not change support 4, add a global selector, alter root handling, swap ranking, blend scores, change budget, or relax gates after truth.
