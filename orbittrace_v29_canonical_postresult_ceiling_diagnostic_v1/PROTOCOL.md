# OrbitTrace v29 canonical SonotaCo post-result ceiling diagnostic v1

## Purpose

Diagnose the authoritative 0/4 exposed-development failure of PR #973 without defining, tuning, or evaluating a successor ranking rule.

The only question is whether the exact already-frozen canonical v29 catalogue contains enough fixed-membership families to beat each literature comparator at its frozen budget, or whether proposal/membership quality is already the binding ceiling.

## Immutable inputs

- PR #973 authoritative run `31437739544` and its pretruth catalogue `V29_CANONICAL_PRETRUTH_CATALOGUE.json`;
- exact pretruth catalogue SHA-256 `dd751abd4330f58b4056eb8da473ee4d19ae756211f0538c41b252ffc9fb352b`;
- exact PR #973 scientific verdict `FAIL_V29_CANONICAL_SONOTACO_ALL_PANEL_LITERATURE_SUPERIORITY_DEVELOPMENT`;
- immutable exposed truth/comparator package from run `31405109267`;
- exact frozen comparator budgets and Hungarian F1 semantics already used by PR #973.

No candidate generation, membership expansion, model inference, ranking, threshold, source quota, or parameter is recomputed or changed.

## Diagnostics

For each Sugar/HDBSCAN x 2013/2014 panel:

1. reproduce the PR #973 candidate result exactly;
2. report source composition of the actual top-budget catalogue prefix;
3. count prefix families whose best attainable fixed-membership F1 against any eligible shower exceeds 0.5;
4. over the complete fixed 334-family catalogue, compute the maximum-total-F1 one-to-one family/shower assignment using at most the frozen comparator budget;
5. separately compute the maximum number of one-to-one assignments with F1 > 0.5 at the same budget;
6. report only aggregate oracle source composition and selected-rank summary (minimum/median/maximum), not an oracle family order.

The oracle is truth-aware and diagnostic only. It is explicitly ineligible as a deployable ranking, target, feature, quota, training-example selection rule, or successor definition.

## Interpretation

`RANK_PLACEMENT_HEADROOM_REMAINS` requires, in every panel, both:

- diagnostic maximum-total-F1 macro-F1 strictly exceeds the literature comparator macro-F1; and
- diagnostic maximum recoveries with F1 > 0.5 are at least the literature recovery count.

Otherwise the conclusion is `FIXED_CATALOGUE_CEILING_LIMITS_SUPERIORITY`.

Even if rank headroom remains, this diagnostic does not authorize source quotas, oracle imitation, SonotaCo-specific weights, rank cutoffs, or any post-result parameter search. A later successor, if any, must be separately motivated and frozen.

## Firewall

SonotaCo 2013/2014 is already exposed development-only. No MAARSY, DMS, OrbitTrace target information, protected 20°–55° target-region events, or protected validation data may be accessed.
