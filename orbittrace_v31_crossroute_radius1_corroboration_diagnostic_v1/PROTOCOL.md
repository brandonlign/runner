# OrbitTrace v31 cross-route radius-1 corroboration diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only. Exact v31 remains the strongest genuine HDB near-miss. #1050 proved the fixed HDB universe can beat both HDB literature panels at exact budgets; #1053 showed the remaining correction is only one shower-group substitution in 2014 and two in 2013. #1049 showed the inherited radius-1 **within-HDB** graph is 100% strict-shower pure but cannot surface missed groups because those groups are missed together. #1058 found repeated positive-reference archetypes, but binding v38 (#1060) proved that archetype identity is not candidate-group identity and closed the archetype de-duplication line.

This diagnostic asks a distinct question: whether the other already-fixed SonotaCo candidate route, **Sugar**, supplies independent label-free radius-1 corroboration for HDB recoverable shower groups that exact v31 misses. If HDB and Sugar rank the same physical structure differently, cross-route agreement could provide set-selection information unavailable to within-HDB propagation.

No cross-route score, rerank, fusion, selector, replacement rule, cutoff, or successor is evaluated here.

## Frozen pre-truth cross-route graph

Before exposed truth is loaded, use the immutable #950 pretruth centroids and exactly the already-frozen #1049 radius-1 geometry.

For one annual 4-vector `(sol, lon, lat, log_vg)`, define the #1049 distance using:

- wrapped solar-longitude difference divided by 4;
- wrapped longitude difference multiplied by `cos(mean latitude)` and divided by 2;
- latitude difference divided by 2;
- difference of `exp(log_vg)` divided by 2;
- Euclidean norm of those four scaled differences.

For one Sugar candidate and one HDB candidate, define cross-route distance as the maximum of the 2013 and 2014 annual distances. Add a cross-route edge iff this exact distance is `<= 1.0`.

The radius, metric, annual maximum, centroid representation, and candidate universes are inherited exactly. No radius/metric/year-combiner/feature search is authorized.

The pre-truth graph file must contain only immutable family identities, edge indices/distances, and adjacency. It must state `truth_accessed=false` and is written before the truth artifact is loaded.

## Exact v31 replay after graph freeze

After the pre-truth graph identity is fixed, load the immutable exposed SonotaCo truth and reproduce exact v31 for both routes using:

- immutable #950 71D features and memberships;
- shared deterministic strict-whole-shower five-fold assignment;
- fold-training mean/population-standard-deviation z-scoring;
- annual positive definition `F1_y > 0.5` for the fixed best recurrent label;
- ordinary Euclidean `k=1` annual margin `d_nonpositive - d_positive`;
- annual `min`;
- exact #839 diversity `lambda=0.8`, `scale=1.0`;
- one equal rank-sum with frozen v19.

Required controls:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDB 2013 `0.14888037368183737 / 9`;
- HDB 2014 `0.15198123772301594 / 9`.

Any mismatch invalidates the diagnostic.

## Diagnostic statistics

First report global truth-aware cross-route edge purity after the graph is already frozen: same strict shower group, different strict shower groups, or involving a NEG family.

Then, independently for 2013 and 2014:

1. Define each annual-recoverable HDB strict shower group as a group containing at least one fixed HDB candidate with annual `F1 > 0.5`.
2. Mark the group surfaced iff its best-ranked annual-recoverable HDB candidate is inside the exact v31 HDB literature budget (11 in 2013, 9 in 2014).
3. For every annual-recoverable HDB candidate in the group, inspect only its already-frozen pre-truth Sugar cross-route neighbors.
4. Report the smallest exact Sugar v31 fused rank among those neighbors, with stable family-ID tie handling. Also report whether that best Sugar neighbor lies inside the exact Sugar literature budget for that year and whether it lies inside a Sugar prefix equal in size to the HDB budget.
5. Summarize these quantities separately for surfaced and missed HDB groups.

Truth is used only to define diagnostic shower groups/recoverability and to measure edge purity. It does not alter the graph, v31 orders, radius, metric, or any rank.

## Interpretation boundary

- If missed HDB recoverable groups commonly have same-shower cross-route edges to high-ranked Sugar candidates, while surfaced groups show comparable or stronger purity, then a separately frozen cross-route corroboration successor may be justified.
- If missed groups generally have no cross-route edge or only low-ranked/impure Sugar neighbors, cross-route radius-1 corroboration is closed as a useful surfacing mechanism at this inherited geometry.
- The diagnostic cannot select a propagation formula, fusion weight, cutoff, budget rule, source quota, or replacement identity.

No truth-derived identity from #1050/#1053 may be hard-coded or converted directly into a successor rule.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Candidate generation and memberships remain unchanged.
- No cross-route score/rerank is evaluated.
- No radius, metric, aggregation, fusion, feature, source-quota, or post-result parameter search is authorized.
