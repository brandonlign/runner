# OrbitTrace v40 connected-component best-evidence representative selector v1

## Scientific role

Separately frozen exposed-SonotaCo development successor after exact v31, failed v36/v37/v38/v39, and the successful diagnostic #1072.

The current fixed candidate universe is already sufficient in principle for HDB superiority (#1050/#1053). #1064 froze a truth-free Sugar↔HDB radius-1 correspondence graph with 2,334 edges. #1066 showed recoverable-but-missed HDB groups often have better-ranked evidence on the other route, but v39 failed 0/4 because edgewise best-rank transfer copied favorable rank evidence onto large numbers of individual fragments.

Diagnostic #1072 then froze ordinary connected components of that exact graph before truth and found a structurally different mechanism:

- 196 total components over the 496 fixed candidates;
- 113 non-singleton components and 83 singleton components;
- zero non-singleton components mixing distinct strict shower labels after truth was opened diagnostically;
- 7/9 recoverable-but-missed HDB groups in 2013 and 7/9 in 2014 were predeclared component-closure opportunities, meaning another member of the same frozen physical component had a strictly better normalized exact-v31 rank percentile.

The exact HDB top prefixes already occupy unique components, so simple de-duplication of the current prefix is not the mechanism. v40 instead tests one canonical component-level response: **rank each frozen physical component once by its best exact-v31 evidence across either route, and emit only one representative from each component on each route before any secondary fragment from a component can appear**.

SonotaCo 2013/2014 remains exposed development only. A pass is not external validation.

## Immutable pre-truth component identity

Before any SonotaCo truth is loaded, restore the immutable #950 pretruth payload and rebuild exactly the #1064 radius-1 cross-route graph from the fixed annual centroids.

It must reproduce:

- Sugar candidates: 267;
- HDBSCAN candidates: 229;
- edges: 2,334;
- serialized graph SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`.

Using exactly those edges, form ordinary undirected connected components over all 496 route/family vertices, including singleton isolates, exactly as #1072:

- vertex token `sugar/<family_id>` or `hdbscan/<family_id>`;
- no within-route edges;
- no pruning, expansion, bridge removal, depth, or component-size rule;
- component ID is the lexicographically smallest canonical vertex token in the component.

The serialized component identity must reproduce #1072 pretruth component SHA-256 `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd` before truth is downloaded.

No radius, metric, edge, component, or membership search is authorized.

## Exact v31 parent computation

Only after the graph and component assignment are frozen may the immutable exposed SonotaCo truth be loaded.

Reproduce exact v31 independently for Sugar and HDBSCAN using:

- immutable #950 71D pretruth features and fixed family memberships;
- deterministic strict-whole-shower five-fold assignment shared across routes;
- fold-training mean and population-standard-deviation z-scoring, with zero standard deviation replaced by 1.0;
- annual positive reference definition `F1_y > 0.5` for the fixed best shower label;
- ordinary Euclidean `k=1` nearest annual-positive and annual-nonpositive references;
- annual local margin `d_nonpositive - d_positive`;
- exact annual `min` combiner;
- exact #839 diversity `lambda=0.8`, `scale=1.0`;
- one equal rank-sum with exact v19.

The exact v31 fused orders are the sole base quality orders.

Required parent controls:

- Sugar 2013: `0.2719801488280529 / 16`;
- Sugar 2014: `0.31529041952487225 / 17`;
- HDBSCAN 2013: `0.14888037368183737 / 9`;
- HDBSCAN 2014: `0.15198123772301594 / 9`.

Any mismatch is an engineering/provenance failure and yields no v40 scientific outcome.

## Sole v40 scientific change

Let route `r` contain `N_r` candidates and let `rank_r(i)` be candidate `i`'s one-indexed exact v31 fused rank on its own route.

Define the route-normalized exact-v31 percentile

`p_r(i) = (rank_r(i) - 1) / (N_r - 1)`.

For every frozen connected component `C`, define exactly one component evidence value

`E(C) = min p_r(i)`

over every Sugar or HDBSCAN member `i` of `C`.

Thus a component receives the best normalized exact-v31 evidence already present anywhere inside that pretruth-frozen physical component. No evidence is copied separately to every fragment.

For each route `r` and each component `C` having at least one member on route `r`, define exactly one route representative

`R_r(C) = the member of C on route r with the smallest exact v31 fused rank`.

Construct the v40 total order for route `r` in two deterministic phases:

1. **Primary component representatives.** Sort all components having a route-`r` member by `(E(C), rank_r(R_r(C)), component_id)` and emit exactly `R_r(C)` once in that order.
2. **Secondary fragments.** After every route-`r` component has emitted its representative, append all remaining route-`r` candidates in their original exact v31 fused order.

This creates a complete total order over the unchanged candidate universe. It is applied identically and independently to Sugar and HDBSCAN using the same frozen cross-route component assignment and the same formula.

The literature budgets are used only by the frozen evaluator after the total orders exist. They do not enter component evidence, representative choice, phase ordering, or tie-breaking.

## Why this is distinct from failed v39

v39 performed an OR-like edgewise transfer: many individual linked candidates inherited an opposite-route best percentile, which improved 153/229 HDB candidates and 129/267 Sugar candidates and destroyed tiny-budget recovery.

v40 never assigns a transferred score to every linked fragment. A physical connected component is ranked exactly once in the primary phase, and exactly one candidate from that component can consume a primary slot on a given route. Secondary fragments cannot appear until every route component has had one representative emitted.

This is component-level closure, not a weakened or thresholded v39 rescue.

## Binding development gate

Exactly one v40 total order per route is evaluated. The first technically valid result is binding.

For each of the four frozen SonotaCo literature panels, a win requires:

- candidate macro-F1 strictly greater than the frozen literature comparator; and
- candidate recovered `F1 > 0.5` shower count at least the literature comparator.

Development PASS requires 4/4 panel wins.

If v40 fails, this exact connected-component minimum-percentile evidence plus first-own-representative ordering is permanently rejected. No alternate component score, mean/median/harmonic aggregation, top-k member rule, route-specific exception, representative replacement, component-size weighting, transfer coefficient, rank window, budget-aware component cap, component pruning, secondary-fragment insertion rule, or post-result rescue is authorized within v40.

If v40 passes 4/4, freeze only the exact exposed-development reference material needed to reproduce its full-training application. A pass does not authorize protected validation or an external-superiority claim.

## Explicit non-search commitments

No:

- radius/metric/feature search;
- within-route graph edges;
- graph pruning or expansion;
- component-size threshold;
- alternate connected-component definition;
- component evidence aggregation search;
- best-k/mean/median/harmonic component rank search;
- representative-family search;
- route-specific rule;
- year- or budget-specific rule;
- transfer coefficient or threshold;
- overlap/Jaccard/distance weighting;
- graph propagation depth;
- candidate-generation or membership change;
- k/scaling/annual-combiner/diversity/fusion/source-quota search;
- oracle identity rule;
- post-result second search.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Truth-aware identities from #1050/#1053 may not enter the component assignment, component evidence, representative choice, or total order.
- Candidate generation and memberships remain unchanged.
