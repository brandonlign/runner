# Significance-witness macro-F1 v1 — dormant current-paper validation contingency

## Status

**FROZEN BEFORE THE FIRST TECHNICALLY VALID GMN MACRO-F1 OUTCOME. DORMANT UNLESS GMN PASSES.**

Activation requires exact `PASS_SIGNIFICANCE_WITNESS_MACROF1_V1_GMN` under the scientific method/prospective GMN evaluator frozen on PR #1370 at head `06c2005afd118203fcb407e0dbe4f5746d307761`.

A GMN FAIL closes this contingency without SonotaCo scientific execution.

## Frozen method identity

- protocol blob `2bf554e9d1798e119433e385a3858847b681f6fa`;
- prelabel-builder blob `7a81aa882960aa87d1d0a06c65f699bdb941cf81`;
- GMN macro-F1 evaluator blob `f27d74f239c43bdb97f2f6cfd46333b91b540e38`;
- source significance-pruned prelabel SHA-256 `bb5f071e19a39297170730985c65181a05ca92dbe7b366f1a84e77d99e074a9a`;
- recurrent witness ordering by exact recurrent-EOM candidate rank;
- significance witness chosen by maximum exact event-count overlap, ties by frozen significance `family_hash`;
- exact recurrent candidate retained iff overlap is zero with every significance-pruned component;
- remaining significance components appended in frozen significance order;
- no overlap fraction/threshold, fitted weight, prefix, route rule, year rule, or budget-aware construction.

No validation-specific method change is authorized.

## Exact benchmark currently used in the paper

The sole primary SonotaCo validation is the current equal-temporal paper benchmark with frozen result Git blob `1ac067658d7a1d99b1a276099ca6d3fee83a6c0b` and verdict `PASS_TEMPORAL_FAIR_LITERATURE_4_OF_4`.

Panels and comparator-complete budgets:

1. Sugar 2013 — `B=40`;
2. Sugar 2014 — `B=43`;
3. published-configuration HDBSCAN 2013 — `B=14`;
4. published-configuration HDBSCAN 2014 — `B=14`.

For each route, the validation implementation must construct the complete significance-witness catalogue using pooled 2013+2014 **label-free** events and freeze/hash that complete catalogue before any shower truth is loaded. The physical significance-pruned candidate source must transfer mechanically from the frozen method definition: support-4 empirical density rank, exact 5°/4°/10% physical radius graph, GUDHI manual ToMATo hierarchy, 199 fixed graph-permutation nulls, FWER alpha 0.05 max-prominence threshold, statistically simplified flat partition, and frozen significance ranking. Recurrent-EOM witnesses must use the exact current paper recurrent-EOM implementation on the same route universe.

After pretruth freeze only:

- use the current paper eligible-shower rule (>=4 events in the evaluated year);
- use the exact same one-to-one Hungarian F1 evaluator;
- compute macro-F1 over all eligible showers with zero for unmatched truth showers;
- report recovered assigned showers at `F1>0.5`;
- evaluate only the frozen comparator-complete budget for that panel.

## Validation gate

Significance-witness macro-F1 v1 can replace current recurrent-EOM in the paper only if:

1. strict macro-F1 superiority over the corresponding literature comparator on all 4/4 panels;
2. recovered `F1>0.5` count at least equal to literature on all 4/4 panels;
3. macro-F1 no lower than current recurrent-EOM on all 4/4 panels;
4. recovered count no lower than current recurrent-EOM on all 4/4 panels;
5. strict macro-F1 improvement over current recurrent-EOM on at least one panel;
6. mean macro-F1 across all four panels strictly higher than current recurrent-EOM.

A valid SonotaCo FAIL is binding. No support/significance change, overlap rule change, orphan rule change, ranking change, route exception, budget exception, or second SonotaCo attempt is authorized.

The later symmetric tuned-HDBSCAN benchmark remains optional harder secondary characterization only after a current-paper validation PASS; it cannot redefine or rescue this endpoint.
