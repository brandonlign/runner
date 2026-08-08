# OrbitTrace family-year representation source-only audit

## Purpose

This audit addresses the sole unresolved post-v11 methodology question without evaluating known-shower labels: whether v8's pooled family-year centroid can move away from the constituent same-year component modes that generated the connected family.

It is diagnosis only. It does not define, score, select, or evaluate a successor detector.

## Fixed scientific scope

- Parent: exact promoted v8 commit `c9d6c44704013ba0c9430100e98a29a56b453304`.
- GMN 2022/2023 only.
- Solar longitude 20°–55° is removed by the already-audited frozen parser before any label normalization or method access.
- Exact v6/v8 fixed4 proposal generation, component construction, 1.5 connected-family topology, and 226-family universe.
- No target coordinates, target members, prior target family/rank, Stage A/B outputs, external-survey values, or target-region events.

## Label boundary

`parse_catalogue` returns the inherited hidden-label handle, but this audit may not index, iterate, count, normalize, compare, serialize, or otherwise inspect it. No ranking or known-shower evaluation is performed.

## Frozen diagnostics

For every family-year:

1. count constituent v8 components;
2. for duplicate family-years, recompute the exact v8 pooled centroid from the union of unique constituent events;
3. measure frozen centroid-distance from that pooled centroid to the nearest and farthest constituent component centroid;
4. measure the maximum pairwise centroid-distance among constituent components;
5. descriptively count duplicate family-years whose pooled centroid is farther than the already-frozen 1.5 family-link radius from every constituent component centroid.

The 1.5 comparison is descriptive only and cannot become a successor threshold.

The audit also records the exact inherited 128-event episode centering semantics from the frozen multiplicity source: `family.centroids[year]` supplies the solar-longitude window center and full radiant-speed anchor; the episode is the exact 128 smallest frozen wavelet-r2 events.

## Decision boundary

The artifact may motivate one separately frozen label-free successor architecture. It may not compare candidate successor rules, inspect shower outcomes, tune a threshold/weight, or authorize target access.
