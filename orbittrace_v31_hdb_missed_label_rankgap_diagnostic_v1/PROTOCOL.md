# OrbitTrace v31 HDB recoverable-label rank-gap diagnostic v1

## Role
Post-result diagnostic only after #1040/#1043 showed that perfect representative choice within v31's already surfaced HDB shower labels cannot close the HDBSCAN gap, and #1044 showed that naive arithmetic-mean group prototypes destroy performance. This diagnostic defines no successor ranker.

## Frozen v31 reproduction
Use the immutable #950 v22 71D payload and exact v31 scientific rule unchanged: strict whole-shower five-fold OOF; fold-training mean/population-standard-deviation scaling over all 71 features; k=1 Euclidean nearest annual-positive/nonpositive family margin; annual `min`; exact #839 diversity lambda 0.8 / scale 1.0; one equal rank-sum with immutable v19. Exact v31 HDB metrics must reproduce before interpretation: 2013 macro-F1 0.14888037368183737 / recovered 9 / budget 11; 2014 0.15198123772301594 / recovered 9 / budget 9.

## Diagnostic universe
For each HDB year, use every eligible recurrent truth shower under the unchanged evaluator (>=4 truth events). For every such label, inspect all fixed HDB-route candidate families in the immutable #950 universe and compute annual F1 to that label. Record the best fixed candidate F1 and its original fixed-universe rank.

A label is `candidate_recoverable` iff at least one fixed candidate has annual F1 > 0.5. A label is `v31_surfaced_recoverable` iff at least one annual-F1>0.5 candidate for that label lies inside the exact v31 top-budget active set used by the evaluator. Otherwise, if a recoverable candidate exists, it is `recoverable_but_missed`.

For each candidate-recoverable label, report the best-F1 candidate and its rank in four already-fixed orders: raw v31 local-margin order before diversity, v31 diversity order, immutable v19 order, and final v31 fused order. Also report whether any recoverable candidate for the label lies within top 2x and top 5x the fixed HDB budget. No alternative cutoff is evaluated as a success criterion; these are descriptive rank-gap diagnostics only.

## Questions answered
1. How many eligible HDB truth showers have no recoverable fixed candidate at all (proposal/membership ceiling)?
2. Among showers with recoverable candidates, how many are already surfaced by v31 versus missed purely by ranking?
3. Are missed recoverable showers generally just below the budget or far down the order?
4. At which already-existing v31 stage (raw local geometry, diversity, v19, final fusion) do their best recoverable candidates lose rank?

## Prohibitions
No new ranking, cutoff, candidate, membership, representative selector, score transform, group prototype, graph transform, feature/model/metric/k/threshold/diversity/fusion/source-quota search, or literature promotion result is authorized. No diagnostic rank threshold may itself become a successor rule without a separately frozen protocol. SonotaCo remains exposed development-only. MAARSY, DMS, OrbitTrace target information, target-region events, and protected solar longitude 20-55 degrees remain inaccessible.
