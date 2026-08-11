# OrbitTrace v31 cross-route connected-component closure diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only after exact v31 and the binding failure of v39.

The current fixed HDB candidate universe is already sufficient to beat both HDBSCAN literature panels at the exact budgets (#1050), while #1053 localized the remaining v31 deficit to a small number of shower-group substitutions. Candidate generation and same-group representative choice are therefore not the main blocker.

The cross-route diagnostic chain established a new truth-free structural relation:

- #1064 froze a radius-1 Sugar↔HDB graph before truth with 2,334 edges; after truth, 2,308/2,334 edges joined the same strict shower group, zero joined different shower groups, and 26 involved a NEG family.
- #1066 found that recoverable-but-missed HDB groups are often specifically under-ranked relative to their radius-1 Sugar counterparts.
- v39 then failed 0/4 because unrestricted best-neighbor rank transfer affected most of the candidate universe (153/229 HDB families improved), demonstrating that **edgewise score propagation is too broad**.

The remaining graph mechanism explicitly left open by #1049 is canonical **connected-component closure**: use the frozen high-purity correspondence edges only to infer which fixed candidate fragments may belong to one latent physical structure, without propagating a rank value across every edge.

This diagnostic asks whether connected components of the already-frozen cross-route radius-1 graph are scientifically clean enough and budget-relevant enough to justify one later component-aware selector. It evaluates no new candidate order, score, component score, de-duplication rule, fusion, selector, cutoff, or successor.

## Immutable graph and v31 base

Rebuild exactly the #1064 pretruth radius-1 cross-route graph from the immutable #950 centroids **before truth is loaded**. It must reproduce:

- Sugar families: 267;
- HDB families: 229;
- cross-route edges: 2,334;
- serialized graph SHA-256: `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`.

The radius, metric, centroids, annual geometry, and candidate memberships are immutable and not searched.

On that bipartite graph, define connected components deterministically over all 496 fixed route-family vertices, including isolated singleton vertices. Components use ordinary undirected transitive closure of the frozen edges and no additional radius, within-route edge, graph depth, pruning, or size rule. A component ID is the lexicographically smallest canonical vertex token among its members, where tokens are `sugar/<family_id>` and `hdbscan/<family_id>`.

Only after the graph and component assignments are serialized with `truth_accessed=false` may the immutable exposed SonotaCo truth be loaded.

After truth is loaded, reproduce exact v31 independently for both routes using the unchanged #950 71D strict-whole-shower five-fold local-geometry method, exact #839 diversity, and equal rank-sum with frozen v19. Required controls:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDBSCAN 2013 `0.14888037368183737 / 9`;
- HDBSCAN 2014 `0.15198123772301594 / 9`.

Any graph/component/v31 identity mismatch is an engineering/provenance failure and yields no scientific diagnostic result.

## Frozen post-truth component diagnostics

Truth is used only after component identity is frozen, and only for the following descriptive questions.

### 1. Component physical purity

Assign each fixed family its strict diagnostic group exactly as in v31 (`SHOWER/<best fixed shower label>` for positive shower-associated families; route/family-specific `NEG/...` otherwise).

For every non-singleton connected component report:

- Sugar member count;
- HDB member count;
- total member count;
- number of distinct strict shower labels among `SHOWER/...` members;
- whether it contains any NEG member;
- whether it contains members from more than one strict shower label.

Globally report the number/fraction of non-singleton components that mix more than one strict shower label. NEG members are reported separately and do not themselves count as an alternate shower label.

### 2. Exact HDB budget component occupancy

For exact v31 HDB prefixes at literature budgets 11 (2013) and 9 (2014), report:

- number of unique frozen connected components represented;
- number of duplicate component slots (`budget - unique components`);
- each repeated component and its selected HDB family IDs/ranks.

This is descriptive only. No slot is removed or replaced.

### 3. Recoverable-group component coverage

For each year, enumerate exactly the HDB strict shower groups having at least one fixed candidate with annual `F1 > 0.5`, as in #1046/#1064. For each group:

- define its diagnostic representative as its earliest annual-recoverable HDB candidate in exact v31 fused order;
- preserve surfaced/missed status at the exact HDB literature budget;
- record the representative's frozen connected component;
- record the best exact v31 HDB rank among **all HDB members of that component**;
- record the best exact v31 Sugar rank among **all Sugar members of that component**, if any;
- record whether any HDB member of that component is already inside the HDB budget;
- record whether any Sugar member of that component is inside the same-sized Sugar prefix (11/9) and the frozen Sugar literature budget (34/46).

Then report separately for surfaced and missed recoverable groups:

- linked-to-non-singleton-component count;
- count whose component is already represented in the HDB budget;
- median best HDB component-member rank;
- median best Sugar component-member rank where present.

### 4. Component closure opportunity count

For each year define one purely diagnostic category, **component-closure opportunity**, for a recoverable-but-missed HDB group whose representative belongs to a non-singleton frozen component and whose component contains at least one member (Sugar or HDB) with a normalized exact v31 rank percentile strictly better than the representative's own HDB percentile.

Normalized rank percentiles are fixed as `(rank-1)/(N_route-1)` with `N_sugar=267`, `N_hdb=229`.

Report the count/fraction and full rows of missed groups satisfying this category. This does not define a successor score or threshold; it only asks whether transitive physical correspondence contains route evidence that the missed representative itself lacks.

## Interpretation boundary

Connected-component closure is a justified next mechanism only if BOTH conditions hold:

1. the frozen non-singleton components do not mix distinct strict shower labels (zero multi-shower components); and
2. in each year, at least one recoverable-but-missed HDB group is a component-closure opportunity.

No minimum count beyond one, no component-size threshold, and no performance estimate is selected.

If either condition fails, cross-route component closure is closed as the next ranking mechanism.

If both conditions hold, a successor still requires a separate scientific freeze. This diagnostic does not authorize a component score, best-rank transfer, de-duplication policy, one-per-component rule, representative rule, graph propagation, rank fusion, or budget-aware selection.

## Explicit non-search commitments

No:

- radius/metric/feature search;
- additional within-route edges;
- graph pruning or expansion;
- component-size threshold;
- component score or rank aggregation;
- best/mean/median/harmonic rank selector;
- hard one-per-component selection;
- component support bonus;
- graph propagation depth;
- cross-route transfer coefficient;
- overlap/Jaccard/distance weighting;
- budget-specific successor;
- new candidate generation or membership change;
- post-result second diagnostic statistic search.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- No truth-aware identity from #1050/#1053 may be hard-coded into components or any future rank rule.
- No new rank, score, selector, fusion, or successor is evaluated by this diagnostic.
