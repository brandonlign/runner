# OrbitTrace support-free recurrent log-FOSC v1 — frozen GMN protocol

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SCIENTIFIC OUTCOME.**

This is a new hierarchy/extraction successor to the currently selected recurrent-EOM HDBSCAN v1 paper/development method. It is motivated by three already-frozen, zero-label structural findings that were obtained without shower truth:

1. PR #1272: exact HDBSCAN `10/10` becomes recurrence-inert as the same target-excluded GMN geometry is reduced to small-survey sample sizes;
2. PR #1273: at ~700 events the inertia is a **joint** finite-support bottleneck—neither core smoothing nor cluster-size condensation alone explains it;
3. PR #1274: on an ordinary support-free Euclidean single-link tree, the dimensionless branch lifetime `log(d_parent/d_form)` is materially less sample-size-sensitive than raw linkage scale in all four frozen branch-size strata.

A separate implementation-equivalence audit proved that HDBSCAN 0.8.43 with `min_samples=1`, `min_cluster_size=2`, exact Boruvka MST, and no approximate MST reproduces the exact sklearn Euclidean single-link hierarchy on all eight frozen #1274 subsets. Those library values are **mechanical tree-construction settings only**; they do not define a scientific support scale and no condensation output is used.

The successor therefore removes the two fixed scientific support scales identified by #1272/#1273 and applies the already-selected recurrent-EOM principle to a scale-normalized branch lifetime on the uncondensed single-link hierarchy.

It is **not** a rescue of failed recurrent local-BIC HDBSCAN #1271. It does not use #1271's 8/4 hierarchy, intrinsic-dimension multiplier, harmonic annual combiner, BIC penalty, condensed-tree alive-mass statistic, candidate ranking, or any post-result change to that closed architecture.

## 1. Parent and development corpus

Scientific parent/comparator is exact selected recurrent-EOM HDBSCAN v1:

- selected branch: `agent/orbittrace-recurrent-eom-sonotaco-v31-benchmark-v1`;
- selected head at protocol freeze: `0248177a2b4dc1f7a0969931d835097d3e86c06f`;
- exact recurrent kernel blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- exact parent runner blob: `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`;
- binding parent GMN run: `31827903547`.

Development data are exact target-excluded GMN 2022+2023 only. The inclusive protected solar-longitude interval `[20.0,55.0]` is removed before any scientific geometry is constructed.

No target information, target-region events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, or DMS may be accessed during GMN selection.

## 2. Representation

Use the exact selected-parent GEO6 representation unchanged:

`[cos(sol), sin(sol), sin(lon_sc) cos(beta), cos(lon_sc) cos(beta), sin(beta), vg/72]`.

Use Euclidean distance. No z-scoring, local scaling, learned feature weight, orbit element, trajectory feature, exposure correction, or label-derived feature is allowed.

## 3. Support-free hierarchy

Construct exactly one pooled 2022+2023 ordinary Euclidean single-link hierarchy on all retained GEO6 points.

The scientific hierarchy is the **uncondensed single-link tree**. It has no `min_samples`, `min_cluster_size`, epsilon, density threshold, or k-nearest-neighbor support parameter.

For scalable execution the exact frozen implementation route is:

- HDBSCAN 0.8.43;
- `min_samples=1`;
- `min_cluster_size=2` only because the library requires an integer >=2;
- `algorithm='boruvka_kdtree'`;
- `approx_min_span_tree=false`;
- `gen_min_span_tree=true`;
- read only `single_linkage_tree_` / equivalent exact uncondensed hierarchy;
- ignore HDBSCAN condensed-tree labels and cluster extraction completely.

The exact equivalence audit run `31930681256` is implementation provenance only and must be reproduced synthetically/source-wise before scientific activation.

## 4. Scale-free local branch lifetime

Orient the agglomerative single-link tree from leaves toward the root.

For each non-root internal branch/node `C`:

- `d_form(C) > 0` is the Euclidean linkage distance at which its two child components merge to form `C`;
- `d_parent(C) >= d_form(C)` is the linkage distance at which `C` merges into its parent;
- `n_y(C)` is the exact number of descendant events from year `y`;
- `N_y` is the total retained event count in year `y`.

Define the dimensionless branch lifetime

`ell(C) = ln(d_parent(C) / d_form(C))`.

If required distances are nonfinite, nonpositive, or violate linkage monotonicity, fail closed. Exact equal-distance branches have `ell=0`.

Multiplying every GEO6 distance by a positive constant leaves `ell` unchanged. No persistence threshold is introduced.

## 5. Ordinary and recurrent local qualities

For audit/comparator purposes define pooled ordinary log-mass

`O(C) = (n(C) / N) * ell(C)`.

For each observing year define annual normalized log-mass

`E_y(C) = (n_y(C) / N_y) * ell(C)`.

The sole scientific recurrent quality is the exact parent principle

`R(C) = min(E_2022(C), E_2023(C))`.

Thus a branch receives positive recurrent quality only when both years contribute descendants and the branch has positive scale-free lifetime. There is no harmonic mean, density synchrony term, year weight, exposure correction, BIC penalty, intrinsic-dimension factor, ECDF transform, significance cutoff, or score blend.

## 6. Scientific branch eligibility

A branch is eligible for scientific flat extraction iff:

- it is a non-root internal node;
- it has at least **4 total descendant events**;
- `R(C) > 0`.

The four-event floor is frozen from the long-standing OrbitTrace weak-stream recovery convention used before this successor: established-shower recovery requires at least four overlapping meteors. It is not chosen from #1274 or any successor outcome and cannot be altered after outcome.

No per-year minimum count is imposed beyond the positive-recurrent-quality condition. This avoids converting recurrence into the hard `4+4`, `5+5`, reciprocal-majority, or other breadth-destroying constraints that are already closed elsewhere in the lineage.

## 7. FOSC-style flat extraction on the binary tree

Use a deterministic bottom-up dynamic program with local additive quality `R`.

For each node `C`, let `B(C)` be the best total recurrent quality obtainable from its subtree under the flat-clustering constraint that selected branches cannot overlap ancestrally.

- For leaves, `B=0`.
- For an internal node, first compute the sum of the best child-subtree objectives.
- If `C` is scientifically eligible and `R(C) >= sum_child_B`, select `C`, set `B(C)=R(C)`, and remove all selected descendants from the flat solution.
- Otherwise keep the selected child-subtree solution and set `B(C)=sum_child_B`.
- The global root is never selectable; its child-subtree solutions define the final flat catalogue.

Exact ties therefore choose the parent branch, matching the parsimony direction of EOM/FOSC rather than fragmenting a tied solution.

The same dynamic program with `O(C)` and the same four-event floor defines an **ordinary log-FOSC structural comparator only**. It is not a paper comparator and is never evaluated with shower truth.

## 8. Candidate ranking

Rank the final recurrent flat catalogue by exactly:

1. descending `R(C)`;
2. descending total descendant count `n(C)`;
3. lexicographic SHA-256 of the sorted member-event IDs.

No parent score, v31 score, ordinary quality, density score, trajectory score, BIC term, or fused rank enters the order.

## 9. Mandatory pretruth small-survey structural gate

Before hidden GMN shower truth can be opened, run the exact already-frozen #1272 hash subsets using the same salt:

`H(eid)=uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

Use exactly:

- denominator 128, buckets 0,1,2,3;
- denominator 1024, buckets 0,1,2,3.

For each subset construct the exact support-free tree and compute both ordinary log-FOSC and recurrent log-FOSC flat solutions.

Define `mechanism_active` iff the exact selected branch/member-set solution differs between ordinary and recurrent extraction.

The structural gate passes iff:

- recurrent mechanism is active in at least `3/4` denominator-128 buckets; and
- recurrent mechanism is active in at least `3/4` denominator-1024 buckets; and
- every selected recurrent candidate has >=4 members and positive `R`; and
- all eight runs are deterministic under exact rerun/hash audit.

The `3/4` threshold is inherited from #1272's preregistered 0.75 mechanism-inactivity criterion; it is not chosen from this successor's outcome.

A structural FAIL closes this exact successor **before truth**. No GMN shower labels may be opened and no support/quality/eligibility/ranking rescue is allowed.

## 10. Full-GMN pretruth freeze

Only after the structural gate passes:

1. reproduce the exact binding recurrent-EOM parent candidate memberships/order from a fresh parent fit;
2. construct the successor full-GMN support-free hierarchy and recurrent flat solution;
3. persist and SHA-256 freeze before truth:
   - exact retained event/annual counts;
   - full single-link tree hash;
   - every internal node's children, `d_form`, `d_parent`, member count, annual counts, `ell`, `E_2022`, `E_2023`, `R`, and eligibility;
   - exact selected node IDs;
   - exact candidate memberships and complete order;
   - ordinary log-FOSC structural solution;
   - mechanism-activity status relative to ordinary log-FOSC and relative to parent recurrent-EOM membership/order;
   - firewall declarations.

No shower label, known-shower identity, recovery statistic, precision, MRR, fragmentation, or comparator outcome may enter hierarchy construction, extraction, or ranking.

## 11. Binding GMN scientific gate

After the complete successor order is hash-frozen, evaluate exact parent and successor with the already-established annual GMN evaluator.

For **each** of 2022 and 2023 the successor must satisfy all of:

- recovered@50 not lower than recurrent-EOM;
- recovered@100 not lower;
- top-100 dominant precision not lower;
- MRR not lower;
- median top-500 fragmentation not higher.

Additionally:

- recovered@100 must be strictly higher in at least one of the two years;
- the successor selected membership/order solution must differ from recurrent-EOM (`mechanism_active=true`).

PASS token:

`PASS_SUPPORT_FREE_RECURRENT_LOG_FOSC_V1_GMN_DEVELOPMENT`

Otherwise:

`FAIL_SUPPORT_FREE_RECURRENT_LOG_FOSC_V1_GMN_DEVELOPMENT`.

The first technically valid outcome is binding.

## 12. Post-outcome rule

On any structural or GMN FAIL, permanently close this exact architecture. Do not change:

- four-event floor;
- annual normalization;
- hard minimum recurrence combiner;
- logarithm or branch-lifetime definition;
- tree linkage;
- GEO6 representation;
- tie direction;
- rank order;
- structural gate;
- scientific gate;
- add a BIC/penalty/p-value/ECDF/blend after seeing the result.

A PASS authorizes only a separately frozen prospective comparison on the already-exposed SonotaCo 2013/2014 validation benchmark. It does not authorize ASFN/EFN reuse, AMOS access, or target access.

## 13. Novelty / claim discipline

Single-linkage clustering, minimum-spanning-tree hierarchies, persistence/lifetime ideas, HDBSCAN/FOSC, and cluster-tree pruning all have substantial prior art. No first-ever claim is authorized from this protocol.

If the method succeeds, the defensible methodological contribution to investigate is narrower: combining a support-free pooled single-link hierarchy with a dimensionless multiplicative branch-lifetime quality and repeated-observation annual normalization/minimum inside a local additive flat-extraction objective for meteoroid-stream discovery.

A formal literature screen is required before any novelty claim.

## 14. Absolute firewall

- `blind_exclusion=[20.0,55.0]`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `sonotaco_2013_2014_access=false` during GMN selection
- `asfn_event_level_access=false`
- `efn_event_level_access=false`
- `amos_scientific_access=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- `post_result_parameter_search=false`
