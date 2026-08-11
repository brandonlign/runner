# OrbitTrace v31 dual-disagreement enrichment diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only after binding v41 failed 0/4. The global component-ordering line is closed by v40/v41. Two independently frozen diagnostics remain positive and point to a more local failure mode:

- #1072: 7/9 recoverable-but-missed HDB groups in each year have a frozen cross-route connected component containing strictly better normalized v31 evidence than the group's own HDB representative.
- #1086: recoverable-but-missed HDB groups are selectively suppressed by exact v31 relative to the immutable pre-SonotaCo #839/#853 quality order in both years.

This diagnostic asks whether these two independent disagreement signs co-occur on the same missed recoverable groups. It does not define or evaluate a new rank, score, selector, replacement rule, promotion position, or successor.

## Immutable inputs

Use only:

1. immutable #950 HDB pretruth payload artifact `9074742322` (zip SHA-256 `d940fa255804866f14bc34b1d72467d17adddcfb7d82c954ed5a8d1668aa307a`) for the exact manifest `quality_order`; and
2. authoritative #1072 component-closure diagnostic run `31455141716`, artifact `9087743465`, whose pretruth component SHA is `c1b80484502907ad19e0d51d8d48d364f3bf7a27e17576e073fe86ae44f499cd` and graph SHA is `2f25aa7d9af1df0a350c034b2280a790c3869a7775bf6d7063d0d1e4cc802b25`.

Require 229 HDB families and the exact #1072 v31 HDB controls:

- 2013 `0.14888037368183737 / 9`, budget 11;
- 2014 `0.15198123772301594 / 9`, budget 9.

No raw protected target data, MAARSY, DMS, or new SonotaCo event access is authorized.

## Fixed group representative

Preserve #1072's exact annual recoverable-group rows and representative convention unchanged. For each year, #1072 already records the annual-recoverable HDB candidate with the smallest exact v31 fused rank for each strict shower group and labels it `surfaced_hdb` or missed at the frozen HDB budget.

No new representative is chosen.

## Two frozen disagreement signs

For an exact #1072 group representative `i`:

### 1. Quality suppression sign

Let `rank_quality(i)` be the candidate's one-indexed position in the immutable #950 `quality_order`, and `rank_v31(i)` its exact #1072 HDB representative rank.

Define

`quality_suppressed(i) := rank_quality(i) < rank_v31(i)`.

This is exactly the positive-sign condition of #1086's frozen statistic. There is no magnitude threshold.

### 2. Cross-route component support sign

Use #1072's already-frozen values:

- `representative_hdb_percentile`; and
- `best_component_normalized_v31_percentile`.

Define

`component_supported(i) := best_component_normalized_v31_percentile < representative_hdb_percentile`.

This is exactly #1072's strict component-closure opportunity condition. There is no distance, size, rank-window, or magnitude threshold.

### Joint sign

Define

`dual_disagreement(i) := quality_suppressed(i) AND component_supported(i)`.

No OR variant, weighted combination, score product, sum, rank fusion, or alternative Boolean rule is tested.

## Descriptive annual comparison

For each year separately, preserve #1072's 9 surfaced and 9 missed recoverable groups. Report for each class:

- group count;
- quality-suppressed count/fraction;
- component-supported count/fraction;
- dual-disagreement count/fraction;
- exact representative audit rows.

## Predeclared interpretation gate

The joint direction is supported only if in **both 2013 and 2014**:

1. at least one missed recoverable group has `dual_disagreement=true`; and
2. the dual-disagreement fraction among missed recoverable groups is strictly greater than the fraction among surfaced recoverable groups.

No minimum enrichment ratio or effect-size threshold is selected.

A PASS does not authorize a deployable correction rule. It only establishes that the intersection of the two independently diagnosed disagreement mechanisms is more selective than either mechanism alone. Any successor must be separately frozen before evaluation and may not use truth-aware group identities or #1071 oracle cardinalities.

A FAIL closes this exact AND-intersection mechanism; no OR rule, softened sign, quality-suppression magnitude cutoff, component-gain cutoff, top-k, rank window, or post-result alternative Boolean search is authorized within this diagnostic.

## Non-search commitments

No new rank/score/selector; no quality fusion; no component rerank; no threshold; no top-k; no rank window; no route/year/budget-specific successor; no candidate/membership/feature/model change; no source quota; no post-result second rule.

## Firewall

- SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region events may be accessed.
- No MAARSY or DMS scientific access is authorized.
- Truth-aware identities from #1050/#1053/#1071 cannot define this diagnostic or any future ranking rule.
