# OrbitTrace v24 HDBSCAN graph-coherence diagnostic v1

## Role
Diagnostic only after the clean #1013 no-go. This does not define, score, select, or promote a successor ranker. The current SonotaCo line has varied regression, classification, pairwise, group-dense, and fusion objectives while retaining the same 71D v22 representation. Those objectives continue to lose the HDBSCAN panels. The 71D representation already contains four compressed label-free consensus-graph descriptors, so simply adding degree/cross-source degree would repeat existing information.

This diagnostic asks one narrower question: does the exact frozen radius-1.0 #843 candidate graph contain coherent same-shower neighborhood structure around recoverable HDBSCAN shower groups that exact v24 fails to surface within the fixed equal-budget cutoffs? A positive answer would justify a separately frozen graph/bag representation experiment; a negative answer would reject that direction before another promotion candidate is created.

## Frozen graph
The graph is exactly the v19/#843 graph already used to create the existing v22 consensus features:
- years 2013/2014 transported through the existing SonotaCo v19 implementation;
- first-year prefilters: circular solar-longitude difference <=7 degrees, ecliptic-latitude difference <=4 degrees, geocentric-speed difference <=4 km/s;
- edge distance = maximum of the exact frozen support `centroid_distance` over 2013 and 2014;
- radius exactly 1.0;
- no radius, metric, source, edge-weight, or neighborhood search.

The HDBSCAN pretruth catalogue is regenerated with the exact v22 preparation while the existing `v19.build_edges` call is passively captured. The resulting 71D features, centroids, memberships, family order, and v19 order must match the immutable #950 payload before truth is loaded.

## Exact v24 reproduction
After the pretruth graph and immutable payload identity pass, exposed SonotaCo truth may be loaded. The diagnostic reproduces exact v24 two-head strict-whole-shower OOF training, `min(pred2013,pred2014)`, exact #839 diversity 0.8/1.0, and equal rank-sum with frozen v19. The HDBSCAN 2013 and 2014 v24 panel metrics must exactly reproduce #950 before diagnostic statistics are accepted.

## Diagnostic measurements only
For each year separately, a strict shower group is `recoverable` when at least one fixed family assigned to that unchanged v22 best label has annual F1 > 0.5, using the already-frozen literature recovery criterion. A group is `surfaced` when a recoverable family from that group appears within exact v24's fixed HDBSCAN budget (11 in 2013, 9 in 2014); otherwise it is `missed`.

For surfaced and missed recoverable groups separately, report only structural graph properties:
- number of candidate families assigned to the group;
- whether at least one radius-1.0 edge connects two families assigned to that same group;
- whether at least one such same-group edge is cross-generator;
- count of same-group internal graph edges;
- size of the largest same-group graph connected component;
- fraction of graph edges incident to the group's families that remain inside the same truth group.

Also report graph-wide same-group edge purity and cross-generator same-group edge purity. These are post-result diagnostic measurements only.

## Explicit prohibitions
Do not compute a graph-propagated score, neighbor-max/mean score, graph-pooled rank, literature performance for any graph transform, graph feature subset, alternate radius, weighted edge, component consolidation, source quota, or successor model. No diagnostic output may itself be promoted as a detector/ranker. Any successor must be separately frozen after this diagnostic and before its result.

SonotaCo 2013/2014 remains exposed development-only. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar longitude 20-55 degrees remain inaccessible.
