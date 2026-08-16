# OrbitTrace topomodal density excess-mass cut v1 — frozen protocol

## Scientific question

The #1284 fixed-radius ToMATo hierarchy repeatedly beats recurrent-EOM on sparse known-stream recovery, purity, fragmentation, and sample-size stability, while every tested scalar ordering of the complete hierarchy has lost MRR. This successor changes the architecture rather than the ranking feature:

> select one optimal non-overlapping flat set directly from the #1284 density hierarchy by maximizing total density-level excess mass.

The idea is structurally analogous to HDBSCAN's Excess-of-Mass principle, but it is applied to #1284's fixed physical radius graph and ToMATo merge tree, not to HDBSCAN mutual-reachability or its condensed tree. Campello et al. formalized flat selection by maximizing overall cluster stability over a density hierarchy; HDBSCAN's standard `eom` selector implements that principle. This protocol freezes a ToMATo-specific discrete density-level stability and dynamic-program flat selection before any outcome.

## Firewall

- GMN development data remain exactly target-excluded 2022+2023.
- Inclusive solar longitude 20°–55° is excluded before geometry, density, hierarchy, selection, rank, and truth.
- OrbitTrace target information/events remain inaccessible.
- Shower truth is inaccessible during the zero-label structural diagnostic and any later prelabel generation.
- SonotaCo 2013/2014, ASFN/EFN event-level data, AMOS, MAARSY, and DMS are inaccessible.
- No result-informed threshold, support, stability transform, tie rule, graph radius, density, or rank rescue is allowed.

## Immutable inputs

Use the exact original #1284 pretruth payload only for membership/comparator auditing:

- `TOPOMODAL_SPARSE_RECOVERY_V1_PRELABEL.json`
- SHA-256 `db608f84bf333d18d624199f2d31c27b4183ee3a75a3d930cef4b9766a19d4de`

Use the exact sparse universe manifest:

- `ORBITTRACE_EXACT_1284_SPARSE_UNIVERSE_MANIFEST_V1`
- SHA-256 `3ed5c33216d7d1cf2cbc703da088b3a86132e50532fb996cfe475d7f6052d7f8`

Use the same eight deterministic panels: denominator 128 and 1024, buckets 0–3.

## Exact #1284 hierarchy

For each panel reconstruct exactly:

- Sun-centered geometry used by #1284;
- physical embedding with `h_sol=2 sin(5°/2)`, `h_rad=2 sin(4°/2)`, `h_logv=ln(1.1)`;
- exact symmetric Euclidean radius-1 graph including self;
- density `rho_i = |N_i| / n`;
- GUDHI 3.12 manual-graph/manual-density ToMATo merge tree;
- support floor 4.

Before selection, the complete pooled candidate-membership summary must reproduce the original #1284 pretruth payload exactly on all eight panels. The finite persistence diagram reconstructed from active modes and merge levels must match GUDHI to absolute tolerance `1e-12`.

Any mismatch is an engineering no-result only.

## ToMATo density-level stability

Reconstruct for every hierarchy node:

- `members(node)`;
- `parent(node)` and immediate children;
- `active_peak(node)`: density of the surviving modal peak for that node, with exact equal-density ties resolved by lexicographically smallest event ID;
- for every internal merge node, `merge_level(node)`: the density level at which its two child branches merge, recovered as the dying child's active peak minus its matched GUDHI prominence.

Define the node's density-level lifetime:

- `lower(node) = 0` for a root, otherwise `merge_level(parent(node))`;
- `upper(node) = active_peak(node)` for a leaf;
- `upper(node) = merge_level(node)` for an internal node.

Require `upper(node) >= lower(node)` to numerical tolerance; clamp only negative roundoff within `1e-12` to zero.

For every reportable node with support >=4 define discrete excess mass

`S(node) = sum_{i in members(node)} max(0, min(rho_i, upper(node)) - lower(node))`.

This is the integrated density-level membership mass over exactly the interval during which the node exists as that hierarchy state. No size normalization, logarithm, exponent, weight, background correction, or persistence multiplier is allowed.

## Flat-set dynamic program

For each connected-component root independently compute the maximum-total-stability reportable antichain.

For a node `v`:

- `self_score(v) = S(v)` if `support(v)>=4`, otherwise selection of `v` is forbidden;
- `child_score(v) = sum(best_score(c) for each immediate child c)`; sub-support leaves contribute zero through their subtree if no reportable descendant exists;
- choose `v` itself iff it is reportable and `self_score(v) >= child_score(v)`;
- otherwise choose the union of each child's optimal selected set.

The `>=` tie rule is frozen before outcome and favors the coarser parent, minimizing unnecessary fragmentation under exact objective ties.

The selected nodes across all roots must be pairwise disjoint and every selected membership must be an exact member of the original complete #1284 hierarchy.

## Intrinsic selected-candidate order

The flat selection changes the candidate universe. For evaluation order selected candidates by exactly:

1. `S(node)` descending;
2. `family_hash` ascending for exact ties.

No root priority, old #1284 rank, persistence, member count, annual confirmation, station support, orbital score, HDBSCAN score, or fusion term enters the order.

## Stage 1 — zero-label structural gate

Truth remains inaccessible. On all eight panels report selected candidate count and selected-node statistics, then compare d1024 candidate memberships to d128 candidates restricted to the same fine event IDs using the already-established fine→coarse best-Jaccard metric.

The exact Stage-1 promotion gates are:

1. pooled selected fine→coarse mean-best Jaccard strictly greater than recurrent-EOM;
2. median-bucket selected fine→coarse mean-best Jaccard strictly greater than recurrent-EOM;
3. selected strict Jaccard wins in at least 3/4 buckets;
4. selected candidate set nonempty in all eight panels;
5. exact #1284 complete-hierarchy membership audit passes in all eight panels;
6. reconstructed ToMATo persistence diagram matches to `1e-12` in all eight panels.

If any gate fails, close this exact EOM-selection lane without shower truth.

Candidate count relative to recurrent-EOM is reporting-only at Stage 1; a scientifically useful flat selector may legitimately emit fewer candidates.

## Stage 2 — conditional truth protocol, frozen now

If and only if all six Stage-1 gates pass, serialize the selected candidates before truth and evaluate at equal candidate budget

`K = min(number of selected candidates, number of recurrent-EOM candidates)`

on each sparse panel, truncating **both** methods to K. K is determined solely by pretruth candidate counts.

Use the same 16 annual known-stream panels and the same ten performance gates:

Fine d1024:
1. qualified total strictly greater than recurrent-EOM at equal K;
2. qualified nonlower in at least 6/8 annual panels;
3. mean MRR not lower;
4. mean top-100 dominant precision not lower;
5. mean fragmentation not higher.

Coarse d128:
6. qualified total not lower;
7. qualified nonlower in at least 6/8 annual panels;
8. mean MRR not lower;
9. mean top-100 dominant precision not lower;
10. mean fragmentation not higher.

All ten must pass. The first technically valid truth outcome is binding.

## Closure / no-rescue rule

A structural failure closes the lane without truth. A valid truth failure closes the architecture. Specifically forbidden after outcome: changing the stability integral, using support×lifespan, mean rather than summed excess mass, normalizing by support, selecting descendants on ties, root suppression, minimum-stability thresholds, persistence blending, alternate graph scales, different support floors, annual/station/orbit fusion, or result-informed reranking.

A PASS would authorize only a separately frozen portability/scalability stage. It does not authorize protected-target access or external event-level truth.
