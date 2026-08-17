# OrbitTrace v41 multiplicity-calibrated component evidence v1

## Scientific role

Separately frozen exposed-SonotaCo development successor after binding v40 failed 2/4 and diagnostic #1083 identified a specific structural bias in v40's component evidence.

v40 used the minimum normalized exact-v31 rank percentile among all Sugar/HDB members of a frozen connected component. It improved HDB 2013 to `0.1609800149 / 10` but damaged HDB 2014 and moved 105/229 HDB families upward. Diagnostic #1083 then tested the best-of-many explanation without evaluating a new order. In all three frozen component universes, component size was negatively correlated with raw `p_min`, and the canonical minimum-order-statistic transform `q=1-(1-p_min)^m` reduced the absolute size correlation. For HDB-bearing components the frozen Spearman correlation changed from about `-0.5079564` to `-0.2349490`.

v41 tests exactly that one preregistered calibration as a successor. It does not search among component statistics or alter the graph, components, representatives, v31, candidates, memberships, or literature budgets.

SonotaCo 2013/2014 remains EXPOSED DEVELOPMENT ONLY. A 4/4 result is not external validation.

## Immutable pretruth graph and components

Before any exposed truth is loaded, reproduce exactly the inherited #1064/#1072 objects from immutable #950 pretruth centroids:

- Sugar families: 267;
- HDB families: 229;
- radius-1 cross-route graph edges: 2,334;
- graph SHA-256: `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`;
- ordinary undirected connected components over all 496 bipartite vertices;
- component count 196 = 113 non-singleton + 83 singleton;
- component SHA-256: `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd`.

The graph uses the exact #1049 annual four-coordinate distance and radius 1.0. No within-route edges, pruning, expansion, radius search, component-size threshold, or alternative closure is allowed.

## Immutable exact v31 base ranking

After the graph/component identities are frozen, load the immutable exposed SonotaCo truth and reproduce exact v31 on both routes using the unchanged 71D strict-whole-shower OOF local geometry, annual `F1>0.5` positives, Euclidean `k=1` positive-vs-nonpositive margin, annual `min`, exact #839 diversity `lambda=0.8 / scale=1.0`, and one equal rank-sum with exact v19.

Required exact parent controls:

- Sugar 2013: `0.2719801488280529 / 16`;
- Sugar 2014: `0.31529041952487225 / 17`;
- HDB 2013: `0.14888037368183737 / 9`;
- HDB 2014: `0.15198123772301594 / 9`.

Any mismatch is an engineering/provenance failure, not a scientific v41 outcome.

## Sole v41 scientific change

For each frozen connected component `C`, let `m(C)` be its total number of Sugar + HDB members. For each member `i` on route `R`, with route family count `N_R` and one-indexed exact v31 fused rank `r_R(i)`, define

`p_R(i) = (r_R(i)-1)/(N_R-1)`.

As in v40, define the raw component minimum

`p_min(C) = min_i p_R(i)`

over every Sugar/HDB member in the component.

v41 replaces v40's raw component evidence with exactly the canonical calibration preregistered in #1083:

`q(C) = 1 - (1 - p_min(C)) ** m(C)`.

Lower is better. No independence claim is made for real components; the formula is used only as the fixed minimum-order-statistic calibration tested diagnostically in #1083.

For each route separately, preserve v40's representative policy exactly:

- the route representative of component `C` is the own-route member with the smallest exact v31 fused rank;
- all route-component representatives are emitted first, ordered by `(q(C), representative own-route v31 rank, component_id)`;
- after every route component has emitted one representative, all remaining fragments are appended in their original exact v31 fused order.

The same rule is applied symmetrically to Sugar and HDB. Year and literature budget are not used to construct the orders.

## Explicit non-search commitments

v41 has no:

- effective component-size fit;
- exponent, coefficient, pseudocount, temperature, clipping, or alternative calibration;
- raw/calibrated interpolation or blend;
- route-specific, year-specific, or budget-specific rule;
- threshold or rank window;
- alternate component evidence aggregation;
- alternate representative definition;
- alternate secondary-fragment insertion;
- graph radius/metric/edge/component search;
- feature/model/target/k/scaling/annual-combiner search;
- diversity/fusion/source-quota search;
- candidate generation or membership change;
- truth-aware oracle identity use;
- post-result rescue within v41.

The first technically valid v41 outcome is binding.

## Binding development gate

Evaluate exactly one v41 total order per route at the existing frozen literature budgets. A panel wins only if candidate macro-F1 is strictly greater than literature and recovered `F1>0.5` shower count is at least literature.

v41 passes exposed development only with 4/4 panel wins.

If v41 fails, this exact multiplicity-calibrated component-evidence ordering is permanently rejected. No fitted effective `m`, softer exponent, mixture with raw `p_min`, route-specific calibration, or other in-place rescue is authorized. Any successor requires a new diagnostic or genuinely distinct mechanism.

If v41 passes, freeze the exact exposed-development reference/application package but do not call the result external validation and do not automatically access any protected external dataset.

## Firewall

- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- SonotaCo remains `EXPOSED_DEVELOPMENT_ONLY`.
- Truth-aware identities from #1050/#1053/#1071 cannot enter graph construction, component calibration, ordering, or freeze.
