# OrbitTrace v31 quality-suppression diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only. Exact v31 remains the strongest genuine all-route method at 2/4, while v40 showed that broad component-level promotion can improve HDB 2013 but damages HDB 2014. The truth-aware joint nested oracle #1071 established only a structural fact: one deployable nested HDB order extremely close to v31 can clear both HDB panels, so the remaining correction is sparse. Oracle-selected family/group identities are non-promotable and do not enter this diagnostic.

This diagnostic tests one distinct hypothesis: some recoverable HDB shower groups missed by v31 may be **selectively suppressed by the SonotaCo-trained v31 local-geometry/fusion order relative to the already-frozen pre-SonotaCo #839/#853 quality order**. The #839 quality order is not itself proposed as a successor: v17 already showed that its global HDB top ordering is insufficient, and v34 rejected complete-order fusion as a solution. It is used here only as an independent frozen quality prior for disagreement diagnosis.

No new score, rerank, fusion, selector, replacement, threshold, component rule, or successor is evaluated.

## Immutable inputs

Use the immutable #950 HDB pretruth payload only. Before exposed truth is interpreted, require:

- 229 HDB families;
- `truth_accessed=false` in the feature and membership manifests;
- exact 71D feature and centroid hashes from the manifest;
- the exact manifest `quality_order`, containing every HDB family exactly once;
- the exact manifest `v19_order` and all other v31 inputs unchanged.

The pretruth `quality_order` is the fixed #839/#853 quality/diversity order inherited through v17. It must not be recomputed, retuned, or replaced.

Only after immutable pretruth identity is verified may the already-exposed SonotaCo truth be loaded and exact v31 reproduced.

## Exact v31 reproduction

Reproduce the frozen v31 HDB order using the unchanged 71D strict-whole-shower five-fold OOF local geometry:

- fold-training z-score across all 71 dimensions;
- ordinary Euclidean `k=1` annual positive/nonpositive references;
- annual positive iff fixed-label annual `F1 > 0.5`;
- margin `d_nonpositive-d_positive`;
- annual `min`;
- exact #839 diversity `lambda=0.8`, `scale=1.0`;
- one equal rank-sum with exact frozen v19.

Required HDB parent controls:

- 2013: macro-F1 `0.14888037368183737`, recovered `9`, budget `11`;
- 2014: macro-F1 `0.15198123772301594`, recovered `9`, budget `9`.

Any mismatch is an engineering/provenance failure and yields no diagnostic result.

## Frozen disagreement statistic

For each HDB family `i`, with `N=229`, define:

- `p_v31(i) = (rank_v31(i)-1)/(N-1)`;
- `p_quality(i) = (rank_quality(i)-1)/(N-1)`;
- `suppression(i) = p_v31(i) - p_quality(i)`.

Positive suppression means the fixed pre-SonotaCo quality prior ranks that same candidate better than v31 does.

There is exactly one statistic. No absolute value, ratio, log, clipping, coefficient, percentile threshold, rank window, component aggregation, v19/consensus alternative, or search is authorized.

## Truth-aware descriptive grouping

For each year separately, use exposed truth only after the two rank orders are fixed.

A strict HDB shower group is annual-recoverable if at least one fixed HDB candidate in that group has annual `F1 > 0.5`. For each such group, define its diagnostic representative as the annual-recoverable candidate with the smallest exact v31 fused rank, tie family ID. This is the same rank-based representative convention used to determine whether a recoverable group is surfaced by the frozen v31 budget; it is not a new representative selector.

Classify the group as:

- `surfaced` if that representative rank is within the frozen HDB literature budget for that year;
- `missed` otherwise.

Report for surfaced and missed groups: count, linked candidate identities for audit, median/Q25/Q75 suppression, positive-suppression count/fraction, median v31 rank, and median quality rank. Also report the exact current top-budget candidates descriptively, but do not select removals or replacements.

## Predeclared interpretation gate

The quality-suppression direction is considered supported only if, in **both 2013 and 2014**:

1. the median suppression of missed recoverable groups is strictly positive; and
2. the median suppression of missed recoverable groups is strictly greater than the median suppression of surfaced recoverable groups.

No minimum effect size is selected. Failure of either condition in either year closes this specific quality-suppression hypothesis.

A PASS does **not** authorize direct #839-quality promotion, equal/weighted fusion, a suppression cutoff, top-k correction, oracle-cardinality correction, or any deployable ranking. Any successor would require a separate freeze after this result and must preserve the sparse-correction lesson from #1071 without using oracle identities.

## Non-search commitments

No feature/model/target change; no quality-order recomputation; no consensus/v19 alternative statistic; no fusion; no threshold; no rank-window or top-k search; no component rule; no source quota; no candidate/membership change; no budget-specific successor; no post-result second statistic.

## Firewall

- SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Truth-aware identities from #1050/#1053/#1071 cannot define the statistic, gate, or any successor.
