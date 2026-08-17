# OrbitTrace v31 cross-route corroboration diagnostic

## Scientific role

Post-result exposed-SonotaCo diagnostic only after:

- #1050 proved the fixed 229-family HDB candidate universe can beat both exact HDB literature gates;
- #1053 localized the v31 failure to tiny-budget shower-set selection;
- v36 rejected density-normalized local geometry;
- v37 rejected five-fold reference-starvation as the cause;
- #1058 found positive-reference archetype collisions, but v38 then proved those collisions are not valid shower-group redundancy surrogates.

The next question is whether the already-strong Sugar route supplies an independent truth-free corroboration signal for HDB candidate groups. Sugar and HDB fixed candidates are generated from the same exposed matched event rows, but their candidate families/rankings are distinct. Cross-route event agreement therefore can provide evidence that an HDB candidate is supported by another generator without using the HDB candidate's truth label.

This diagnostic evaluates no new candidate order, selector, fusion, thresholded ranker, or literature successor.

## Exact parent reproduction

Reproduce exact v31 using the immutable #950 payload:

- fixed Sugar/HDB family memberships and 71D features;
- exact shared strict-whole-shower five folds;
- fold-training z-score over all 71 dimensions;
- annual positive `F1_y > 0.5`;
- Euclidean `k=1` annual positive-vs-nonpositive margin;
- annual `min`;
- exact #839 diversity `lambda=0.8`, `scale=1.0`;
- exact equal rank-sum with frozen v19.

Required exact controls:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDBSCAN 2013 `0.14888037368183737 / 9`;
- HDBSCAN 2014 `0.15198123772301594 / 9`.

Any mismatch is a technical/provenance failure.

## Frozen cross-route match

For every fixed HDB family `H` and every fixed Sugar family `S`, compute event-membership Jaccard

`J(H,S) = |members(H) ∩ members(S)| / |members(H) ∪ members(S)|`.

For each HDB family choose exactly one Sugar corroborator by the lexicographic rule:

1. larger Jaccard;
2. larger raw shared-event count;
3. smaller exact Sugar v31 fused rank;
4. lexicographically smaller Sugar family ID.

If all Sugar families have zero shared events, the HDB family is recorded as having no cross-route corroborator rather than inventing a geometric match.

For the chosen corroborator record only predeclared truth-free quantities:

- maximum Jaccard;
- shared-event count;
- exact-membership equality flag;
- Sugar v31 fused rank;
- Sugar v31 rank percentile.

No alternate overlap metric, centroid match, radius, event weighting, source weighting, membership expansion, or match search is authorized.

## Truth-aware diagnostic categories only

Truth may be used only after all HDB-to-Sugar matches are frozen, to summarize already-existing recoverability categories.

For each HDB year at its exact literature budget:

1. enumerate every strict HDB shower group with at least one fixed candidate having annual `F1 > 0.5`;
2. define its representative as its earliest recoverable HDB candidate in exact v31 fused order;
3. split representatives into surfaced versus missed by the exact HDB literature budget;
4. report distributions of maximum Jaccard and matched Sugar rank for surfaced and missed groups;
5. report the predeclared **strong cross-route corroboration** count, defined as both:
   - maximum Jaccard `>= 0.5`; and
   - matched Sugar v31 fused rank within that year's exact frozen Sugar literature budget (`34` in 2013, `46` in 2014).

Also report the same corroboration descriptors for every HDB top-budget candidate, separated descriptively by whether that candidate itself has annual `F1 > 0.5`.

The `0.5` Jaccard threshold is frozen as majority union overlap and is diagnostic only; it is not authorized as a successor threshold. The Sugar budgets are pre-existing literature evaluation budgets, not selected from this result.

## Interpretation boundary

A useful result would be evidence that recoverable-but-missed HDB groups are frequently corroborated by strongly overlapping, high-ranked Sugar families while some current HDB budget slots are not. Such a result may motivate one separately frozen cross-route ranking successor.

A null/negative result closes this simple cross-route membership-corroboration direction. No successor is authorized by this diagnostic itself.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access.
- No truth-aware identity from #1050/#1053 may be hard-coded or used to construct the match.
- No new rank, fusion, selector, overlap threshold search, metric search, feature search, source quota, route-specific rescue, or post-result second search is evaluated.
