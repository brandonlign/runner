# Legacy conditional-MRR geometry audit

## Scope

This is a **sealed-result-only mathematical audit** of binding run `32086031907`, result SHA-256 `dfa395e969a260ef82a25cd7296c841f525e8c090c9eea05b1b234b155bf6b6d`.

It opens no new shower truth, recomputes no candidates, trains no model, changes no order, changes no metric gate, and cannot reclassify the binding `FAIL_TOPOMODAL_REPRESENTATIVE_SHARE_OOF_V1` verdict.

## Upper bound

In one annual panel with `q > 0` distinct recovered shower labels, the inherited evaluator assigns each recovered label a distinct positive integer first rank. Therefore, irrespective of the ranking method, the largest possible historical conditional MRR at that fixed recovered-label count is obtained when the `q` first ranks are exactly `1,2,...,q`:

`MRR_conditional_max(q) = H_q / q`,

where `H_q = sum_{r=1}^q 1/r`.

This is a combinatorial upper bound. It does not depend on any shower identity or candidate score.

## Binding representative-share result versus its fixed-count upper bound

### Fine scale (`d=1024`)

Binding successor recovered counts across the eight bucket-year panels are:

`[4,4,3,3,5,3,3,6]`.

Mean historical conditional MRR actually achieved:

`0.5399553571428571`.

Mean of the panelwise theoretical maxima `H_q/q` at those exact recovered counts:

`0.5438888888888889`.

Therefore the binding order achieves:

`0.5399553571428571 / 0.5438888888888889 = 0.9927677659419233`

or **99.28% of the maximum conditional MRR mathematically possible at its actual recovered counts**.

The Recurrent-EOM conditional-MRR comparator is `0.6959325396825397`, which is above the successor's fixed-count theoretical ceiling. No reordering of the same recovered set can pass the historical fine MRR gate.

Panelwise, representative-share reaches the exact `H_q/q` ceiling in four of eight panels and is at least 96% of the ceiling in every fine panel.

### Coarse scale (`d=128`)

Binding successor recovered counts across the eight bucket-year panels are:

`[16,19,14,20,15,19,16,19]`.

Mean historical conditional MRR actually achieved:

`0.18492944432304148`.

Mean of the panelwise theoretical maxima `H_q/q` at those exact recovered counts:

`0.20201465558404824`.

Therefore the binding order achieves:

`0.18492944432304148 / 0.20201465558404824 = 0.915425882287543`

or **91.54% of the maximum conditional MRR mathematically possible at its actual recovered counts**.

The Recurrent-EOM conditional-MRR comparator is `0.23584530975502274`, again above the successor's fixed-count theoretical ceiling. No reordering of the same recovered set can pass the historical coarse MRR gate.

## Reciprocal-rank mass check

The zero-filled eligible-query MRR uses the same reciprocal-rank numerator but retains unrecovered eligible showers in the denominator with reciprocal rank zero.

Binding run `32086031907` increased that metric at both scales:

- fine: `0.3308496315192744 -> 0.40583723072562355`;
- coarse: `0.06440922700317128 -> 0.07557745653492765`.

Thus the successor increased total reciprocal-rank mass relative to the fixed eligible-query population while the conditional average fell. The direction reversal is produced by conditioning the historical mean on the larger recovered set, not by a loss of total reciprocal-rank retrieval utility.

## Consequence

For the binding representative-share candidate set, the remaining historical conditional-MRR deficit is **not primarily reorderable ranking headroom**. Fine ordering is already essentially combinatorially saturated; coarse ordering has some headroom but not enough to reach Recurrent-EOM without changing which labels are recovered.

A future method could technically raise historical conditional MRR only by changing the recovered-label distribution itself—for example by concentrating recovery into fewer/easier panels or failing to recover some later true showers. Because the existing promotion gates require only 6/8 panelwise nonloss, such behavior can in principle game the conditional average while reducing useful coverage elsewhere.

Accordingly, do not treat historical conditional MRR alone as evidence that representative-share ranks are globally worse. This audit does **not** change any historical verdict. For future separately preregistered work, early-retrieval quality should be measured against a fixed eligible-query denominator (zero-filled reciprocal rank or another independently frozen query-level ranking measure) rather than optimized by intentionally suppressing legitimate recoveries.