# OrbitTrace v31 HDB fixed-budget label-set substitution diagnostic v1

## Scientific role

Post-result exposed-SonotaCo oracle diagnostic only. Exact v31 remains the strongest HDBSCAN-2014 near miss. #1040/#1043 show that same-label representative choice alone cannot beat HDBSCAN; #1046 shows that each year contains multiple recoverable shower labels outside the tiny fixed budget; #1049 shows direct radius-1 graph propagation has no surfacing headroom. This diagnostic asks how many **shower-label substitutions** in v31's frozen top-budget set are sufficient in principle to cross the HDBSCAN gate while memberships remain fixed.

It does not define a deployable rank, score, selector, successor, cutoff, or parameter.

## Immutable v31 replay

Reconstruct exact v31 from the immutable #950/v24 71D pretruth payload and exact exposed truth: shared strict whole-shower five-fold assignment across Sugar/HDBSCAN, fold-local arithmetic mean and population standard deviation, Euclidean k=1 nearest annual-positive (`F1_y>0.5`) and annual-nonpositive margin, annual `min`, exact #839 diversity `lambda=0.8, scale=1.0`, and exact v19 equal-rank-sum fusion.

Exact HDBSCAN controls must reproduce before any oracle result is accepted:

- 2013 macro-F1 `0.14888037368183737`, recovery `9`, budget `11`;
- 2014 macro-F1 `0.15198123772301594`, recovery `9`, budget `9`.

## Fixed truth-group definitions

Use the unchanged v22/v24 best recurrent label for each fixed family. A strict shower group is `SHOWER/<best_label>`. For each year, annual family quality is the unchanged fixed-label annual F1. A strict shower group is annual-recoverable iff it contains at least one fixed HDB family with annual F1 strictly greater than the frozen evaluator threshold 0.5.

For each annual-recoverable strict shower group, define its **oracle incoming representative** once as the fixed family with highest annual F1 for that year, stable family ID tie-break. This is truth-aware diagnostic information and is never promotable.

## Frozen substitution search

For each year independently:

1. Freeze the exact v31 top-budget family list and its strict group set.
2. Define the incoming label pool as every annual-recoverable strict shower group **absent from the exact v31 top-budget group set**.
3. For each incoming group, use only its single oracle incoming representative defined above.
4. Evaluate exhaustively every **one-for-one** substitution: remove exactly one exact-v31 top-budget family and insert exactly one incoming representative.
5. Independently evaluate exhaustively every **two-for-two** substitution: remove exactly two distinct exact-v31 top-budget families and insert oracle representatives from exactly two distinct incoming groups.
6. No three-or-more substitution search is authorized.

For evaluation, the substituted families occupy the removed top-budget slots in stable slot order; all non-top exact-v31 families follow in their original order with already-used families removed. Because the evaluator truncates to the same fixed budget before Hungarian assignment, no extra family enters the diagnostic set.

The exact candidate memberships and evaluator are unchanged.

## Required outputs

For each year report:

- exact v31 and HDBSCAN comparator metrics;
- exact top-budget family IDs/groups;
- incoming missed-recoverable group pool and each group's oracle representative/F1;
- number of one-substitution and two-substitution configurations evaluated;
- whether **any** one-substitution configuration crosses the literature gate;
- whether **any** two-substitution configuration crosses the literature gate;
- the minimum substitution count in `{1,2}` that can cross the gate, or `NONE_WITHIN_TWO`;
- best one-substitution macro-F1/recovery and stable substitution identity;
- best two-substitution macro-F1/recovery and stable substitution identity;
- number of gate-passing configurations at each substitution count.

A configuration passes only if candidate macro-F1 is strictly greater than the HDBSCAN comparator and recovered `F1>0.5` count is at least the comparator count.

Within each substitution count, the descriptive `best` configuration is chosen deterministically by: gate-pass first, macro-F1 descending, recovery descending, then lexicographically by removed-family tuple and incoming-group tuple. This is diagnostic reporting only.

## Interpretation boundary

- If one substitution can cross a panel, that panel requires only a very small label-set correction in principle.
- If one fails but two can cross, the necessary correction is still small but not single-label.
- If neither one nor two can cross, the remaining ranking error is broader than a two-label correction under the fixed candidate universe and exact v31 budget.

This result cannot select which label to promote in a deployable method. No truth-derived substitution, oracle representative, or result-bearing configuration may be used directly in protected validation or target search. Any successor must use label-free information and be separately named/frozen.

No feature/model/metric/k/threshold/diversity/fusion/member/radius/graph/weight search is performed here. SonotaCo 2013/2014 remains exposed development-only. No MAARSY, DMS, OrbitTrace target information, target-region events, or protected solar-longitude 20°–55° content may be accessed.