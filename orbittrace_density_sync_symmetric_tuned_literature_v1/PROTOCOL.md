# OrbitTrace density-synchronous recurrent-EOM — symmetric tuned challenge v1

## Scientific question

Does the already-frozen density-synchronous recurrent-EOM method outperform the tuned ordinary HDBSCAN winner from the mechanically symmetric SonotaCo benchmark when it receives the identical pooled event universe, identical cross-year development/test protocol, identical support-parameter search, and identical evaluator?

This is a one-shot successor transfer. The density-synchronous method definition predates the symmetric SonotaCo benchmark result and is not altered using that result.

## Method freeze

Use the exact density-synchronous recurrent-EOM kernel with Git blob `587a304f451e41b9503272f1783a6c6ebb295000`, originally frozen and scientifically evaluated before this benchmark. It depends on the exact recurrent-EOM parent kernel Git blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`.

For a hierarchy node C, density-synchronous recurrent-EOM integrates the pointwise minimum of the two exposure-normalized annual alive-mass curves over HDBSCAN density lambda:

`S_sync(C) = integral min(A_2013^C(lambda), A_2014^C(lambda)) d lambda`.

No harmonic/geometric/soft minimum, blend, exponent, route-specific rule, budget rule, reranker, membership repair, or post-result rescue is permitted.

## Pre-existing justification

The exact kernel passed pre-access synthetic/source audits in its original lineage and then passed its frozen target-excluded GMN 2022/2023 development gate. Its later deterministic perturbation study showed the strict recovery gain was sample-sensitive, although mean precision and MRR improved. Those results motivate this transfer but do not determine the SonotaCo outcome.

The previously considered harmonic annual-total combiner is explicitly rejected before execution because the project's frozen annual-min bottleneck diagnostic failed; it is not part of this benchmark.

## Common universe and information

Reuse the exact common SonotaCo event construction from symmetric benchmark v2:

- 2013 common event intersection: 15,988 events;
- 2014 common event intersection: 13,258 events;
- pooled common universe: 29,246 events;
- both years pooled label-free before truth for every method.

The density-synchronous candidate catalogue for every support configuration must be persisted before any truth artifact is downloaded in the execution workflow.

## Symmetric support tuning

Density-synchronous recurrent-EOM receives exactly the same finite-support grid used for recurrent-EOM in symmetric benchmark v2:

`(min_cluster_size,min_samples) = (5,5), (10,5), (10,10), (20,10), (20,20), (40,20), (40,40), (50,25), (50,50), (80,40), (80,80), (100,50), (100,100)`.

No density-synchronous-specific support values are added.

The frozen tuned-HDBSCAN and tuned-Sugar results from binding symmetric benchmark run `32220399133` are reused without alteration. Recomputing them would add no scientific information because their candidate generators, tuning grids, common rows, folds, and evaluator are unchanged.

## Cross-year tuning/test

Use the same two folds:

- tune on 2013 truth, evaluate on 2014 truth;
- tune on 2014 truth, evaluate on 2013 truth.

For density-synchronous recurrent-EOM, choose support configuration using exactly the v2 development objective:

1. maximize mean Hungarian macro-F1 over K=10,20,30,40;
2. tie-break by summed recovered showers over those budgets;
3. then K=40 macro-F1;
4. then earlier grid entry.

The opposite-year labels cannot influence configuration selection.

## Evaluator

Use the exact symmetric-v2 evaluator:

- eligible showers have at least four common-universe members;
- exact `SPORADIC` excluded;
- one-to-one Hungarian assignment maximizing shower/candidate F1;
- common candidate budgets K=10,20,30,40;
- native complete-catalogue macro-F1 also reported.

## Primary comparison and gate

The primary metric remains the two-fold mean of the K=10/20/30/40 macro-F1 curve.

A positive density-sync-over-HDBSCAN result requires BOTH:

1. density-synchronous recurrent-EOM mean test curve macro-F1 is strictly greater than frozen tuned HDBSCAN (`0.345475559012312`); and
2. density-synchronous recurrent-EOM total recovered showers at K=40 is at least frozen tuned HDBSCAN (`52`).

K=40 macro-F1 and native macro-F1 are reported but are not additional promotion gates.

If either condition fails, the verdict is negative. No method modification or second SonotaCo attempt is authorized from this result.

## Interpretation boundary

A PASS would establish that the pre-existing density-synchronous recurrence objective beats the strongest tuned ordinary-HDBSCAN comparator in this specific symmetric two-year SonotaCo benchmark. It would not establish universal state of the art or independent external generalization.

A FAIL means density-synchronous recurrent-EOM does not solve the tuned-HDBSCAN gap under this benchmark. The result must be retained as-is.
