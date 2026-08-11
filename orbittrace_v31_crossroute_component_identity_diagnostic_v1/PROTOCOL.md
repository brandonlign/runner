# OrbitTrace v31 cross-route component-identity diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only after binding v39 failed 0/4.

The frozen #1064 Sugar↔HDB radius-1 relation is exceptionally edge-pure: 2,308/2,334 edges join the same strict shower group, zero join different strict shower groups, and 26 involve a NEG family after truth is opened diagnostically. #1066 showed useful route-rank disagreement, but v39's symmetric best-rank transfer then moved large numbers of candidates and failed badly. This suggests that a good rank attached to one physical structure may have propagated to multiple fragments of that same structure.

This diagnostic asks whether the **connected components of the exact frozen pre-truth radius-1 bipartite graph** are themselves a clean truth-free surrogate for physical shower identity, and whether exact v31's tiny HDB prefixes spend scarce slots on multiple candidates from the same such component while recoverable missed groups occupy components absent from the prefix.

No component-deduplicated order, representative selector, replacement rule, new score, rerank, fusion, cutoff, or successor is evaluated here.

## Frozen pre-truth component construction

Before SonotaCo truth is loaded:

1. Restore the immutable #950 Sugar/HDB pretruth payload.
2. Rebuild exactly the #1064 radius-1 Sugar↔HDB graph from immutable annual centroids.
3. Require serialized graph SHA-256 `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`, 267 Sugar families, 229 HDB families, and 2,334 cross-route edges.
4. Form ordinary undirected connected components on the bipartite node set `SUGAR/<family_id>` and `HDB/<family_id>` using exactly those edges. Isolated candidates are singleton components.
5. Define a deterministic component ID as SHA-256 of the newline-joined lexicographically sorted node keys in that component.
6. Write the complete candidate→component assignment before any truth is loaded.

No radius, metric, hop count, edge filter, component-size threshold, NEG handling, route weighting, or alternative connectivity rule is searched or selected.

## Exact v31 reproduction

After the pretruth graph and component assignment are frozen, load the immutable exposed SonotaCo truth and reproduce exact v31 on both routes:

- immutable #950 71D features and fixed memberships;
- deterministic strict-whole-shower five-fold assignment shared across routes;
- fold-training mean / population-standard-deviation z-scoring, zero standard deviation -> 1.0;
- annual positive reference `F1_y > 0.5` for the fixed best shower label;
- ordinary Euclidean `k=1` local margin `d_nonpositive-d_positive`;
- annual `min` combiner;
- exact #839 diversity `lambda=0.8`, `scale=1.0`;
- one equal rank-sum with exact v19.

Required parent controls:

- Sugar 2013: `0.2719801488280529 / 16`;
- Sugar 2014: `0.31529041952487225 / 17`;
- HDB 2013: `0.14888037368183737 / 9`;
- HDB 2014: `0.15198123772301594 / 9`.

Any mismatch is an engineering/provenance failure and yields no diagnostic result.

## Truth-aware diagnostic summaries only

Truth is used only after the component assignment is frozen.

For every candidate, assign the same strict truth group convention used by #1064: `SHOWER/<best_label>` when a best label exists, otherwise route-specific `NEG/...`.

### Component truth purity

For every frozen component report:

- Sugar/HDB member counts;
- number of distinct non-NEG strict shower groups represented;
- whether any NEG candidate is present;
- whether the component is `STRICT_SHOWER_PURE`, defined as containing at most one distinct non-NEG strict shower group.

Report the number of components with more than one strict shower group and the number of candidates contained in such components.

### HDB fixed-budget component occupancy

For HDB 2013 budget 11 and HDB 2014 budget 9, using the exact v31 fused order:

- number of unique frozen components represented in the prefix;
- duplicate component slots = budget minus unique-component count;
- multiplicities of repeated components.

For every annual-recoverable strict HDB shower group (`annual F1 > 0.5`), choose its highest-ranked exact-v31 HDB family as the fixed representative and report:

- whether it is surfaced by the HDB prefix;
- its frozen component ID;
- whether that component is already represented in the HDB prefix.

For missed recoverable groups, report counts whose component is represented versus absent from the prefix.

## Predeclared interpretation boundary

The component-identity direction is considered strong enough to justify one separately frozen component-level successor only if **all** of the following hold:

1. zero frozen components contain more than one non-NEG strict shower group;
2. exact v31 HDB 2013 has at least **2** duplicate component slots at budget 11;
3. exact v31 HDB 2014 has at least **1** duplicate component slot at budget 9;
4. HDB 2013 has at least **2** recoverable-but-missed strict groups whose frozen components are absent from the top-11 prefix;
5. HDB 2014 has at least **1** recoverable-but-missed strict group whose frozen component is absent from the top-9 prefix.

The 2/1 slot requirements are fixed from #1053's previously established minimum shower-set correction cardinality, not selected from this diagnostic result.

Passing this diagnostic does not select a component representative rule or authorize hard de-duplication automatically. Any successor must be separately frozen after the result.

## Explicit non-search commitments

This diagnostic evaluates no:

- component-level score or order;
- representative family rule;
- component cap other than descriptive occupancy;
- radius/metric/edge filter;
- hop depth or component closure alternative;
- NEG removal or bridge pruning;
- component-size threshold;
- year/budget-specific selector;
- source quota;
- feature/model/k/diversity/fusion change;
- oracle identity rule;
- post-result rescue.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Truth-aware identities from #1050/#1053 may not enter component construction or any future rule.
- Candidate generation and memberships remain unchanged.
