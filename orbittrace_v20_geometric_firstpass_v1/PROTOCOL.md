# OrbitTrace v20 — geometric first-pass diversification

## Motivation

The exposed SonotaCo v19 result preserved the same scientific picture as the pre-v19
oracle diagnosis: the hard/P19/P20 family universe contains enough high-quality families
to beat the catalogue-HDBSCAN panels, but the tiny 9/11-candidate budgets are spent
inefficiently. v19 rank-sum improved HDBSCAN 2013 substantially but still lost HDBSCAN
2013/2014.

This successor changes neither candidate generation nor the membership estimator. It asks
one narrower question: can the existing label-free geometric redundancy graph keep direct
fragment neighbors from consuming the very first catalogue slots?

## Frozen input method

v20 inherits exactly:

- v17 hard + P19 + P20 pair-portable proposal universe;
- v15 adaptive hard-family density consensus;
- #839/#853 quality/diversity ranker;
- #843 pre-suppression cross-generator consensus score at radius `1.0` and source-quality
  weight `2.0`;
- v19 parameter-free equal-weight **rank-sum** fusion;
- v16/v17 fixed joint-conformal membership expansion.

The complete candidate universe is preserved.

## Fixed geometric first-pass rule

Direct family adjacency is exactly the already-used #843 pair metric and radius `1.0`.
No radius, activity window, speed scale, source weight, cutoff, or budget is searched.

Starting from the exact v19 rank-sum order, scan families once:

1. accept a family into the first pass if it has no direct conflicting edge to a family
   already accepted;
2. otherwise defer it;
3. after the first pass, append every deferred family in its original v19 rank-sum order.

Thus no family is deleted. The rule is independent of the comparator budget and only
changes early catalogue ordering.

Exactly two mechanism variants are frozen:

- `cross_source_firstpass`: only direct radius-1.0 edges joining different generator
  sources (`hard`, `p19`, `p20`) create a first-pass conflict;
- `all_source_firstpass`: every direct radius-1.0 edge creates a first-pass conflict.

`rank_sum_control` is the unchanged v19 winner and must reproduce exact v19 family
identities and all four v19 metrics.

These are structural sensitivity variants, not a radius/weight grid. There is no second
search or interpolation after results.

## Exposed-development evaluation

For Sugar and HDBSCAN matched row routes, all three candidate outputs are produced and
SHA-256 frozen before the already-exposed immutable truth/comparator artifact is loaded.
Evaluation then uses exact #854-compatible equal-budget one-to-one maximum-total-F1
assignment.

The successor is selected by the same robust four-panel lexicographic key used in v19:
pair wins, worst macro-F1 ratio, worst recovery ratio, mean macro-F1 ratio, mean recovery
ratio, then the predeclared conservative preference `cross_source_firstpass` over
`all_source_firstpass`.

An all-panel development PASS requires the selected variant to beat the literature
macro-F1 and tie/beat recovered-F1>0.5 count in all four comparator/year panels.

## Firewall and interpretation

SonotaCo 2013/2014 is exposed development only. This experiment cannot constitute
external validation. No MAARSY, DMS, OrbitTrace target information, target-region event,
or solar-longitude 20°–55° target content is authorized.

A failure is preserved as v20 failure. A pass freezes the selected v20 architecture for
a later candidate-specific protected-validation protocol; it does not authorize opening
protected data by itself.
