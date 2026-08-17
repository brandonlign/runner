# OrbitTrace v31 within-surfaced-group representative-quality diagnostic v1

## Scientific role

Post-result exposed-SonotaCo diagnostic only. Frozen v31 reaches the full HDBSCAN-2014 recovered-shower count (9/9) while missing comparator macro-F1 by only ~0.0049, and reaches 9/10 HDBSCAN-2013 recoveries. This diagnostic asks whether those residual deficits are caused by weak family representatives inside shower groups that v31 already surfaced, versus failure to surface the required shower groups globally.

It does not define a deployable score, select a successor, alter v31, or evaluate any target-containing data.

## Immutable replay

Reconstruct exact v31 from the immutable #950/v24 71D pretruth payload, memberships, strict shared whole-shower folds, annual truth targets, fold-local z-scored Euclidean k=1 positive/nonpositive margin, annual `min`, exact #839 diversity `lambda=0.8`, `scale=1.0`, and exact v19 equal-rank-sum fusion. Exact HDBSCAN v31 controls must reproduce before any diagnostic statistic is accepted:

- 2013 macro-F1 `0.14888037368183737`, recovered `9`, budget `11`;
- 2014 macro-F1 `0.15198123772301594`, recovered `9`, budget `9`.

## Strict group and annual-quality definitions

Use the unchanged v22/v24 fixed best recurrent label for each family. A labeled family belongs to strict group `SHOWER/<best_label>`; an unlabeled family remains its unique `NEG/...` group. Annual family quality is the unchanged fixed-label annual F1. An annual-recoverable group is a strict shower group containing at least one fixed candidate family with annual F1 strictly greater than the frozen evaluator threshold 0.5.

## Group-constrained representative oracle

For HDBSCAN 2013 and 2014 separately:

1. freeze the exact v31 top-budget family list;
2. record its strict group multiset and annual F1 values;
3. for each `SHOWER/<label>` represented in those top-budget slots, replace only those slots with the same number of distinct fixed candidate families from that same strict group having the highest annual F1 for that year, stable family ID tie-break;
4. leave any `NEG/...` slot unchanged;
5. append the remaining exact v31 order after the oracle top-budget list, excluding already-used families;
6. evaluate this truth-aware diagnostic order with the unchanged equal-budget one-to-one evaluator.

The oracle may never introduce a shower group absent from the original v31 top-budget group multiset. It therefore measures only within-surfaced-group representative headroom, not global ranking headroom. If a strict group appears multiple times in the top budget, the oracle uses the corresponding number of distinct highest-F1 families from that same group.

## Required diagnostics

For each year report:

- exact v31 metric and recovery count;
- group-constrained oracle macro-F1 and recovery count;
- comparator macro-F1 and recovery count;
- top-budget number of unique strict shower groups and NEG slots;
- number of annual-recoverable strict groups present anywhere in the fixed HDB candidate universe;
- number of those annual-recoverable groups surfaced in the exact v31 top budget;
- for every top-budget shower-group slot: selected family ID/F1, oracle same-group family ID/F1, and F1 gain;
- median and maximum same-group representative F1 gain.

## Interpretation boundary

- If the group-constrained oracle crosses the comparator macro-F1/recovery gate while introducing no new shower group, then within-group representative selection has sufficient headroom and may motivate a separately frozen representative-selection successor.
- If the oracle remains below comparator despite best same-group representatives, then representative choice alone is insufficient.
- If the v31 top budget contains fewer annual-recoverable groups than required by the comparator recovery count, that shortfall is necessarily a global group-surfacing problem and cannot be repaired by same-group representative selection.

No oracle order is promotable. No representative rule, feature, model, membership, threshold, group definition, fusion, or parameter is selected here. Any successor must be separately named and frozen after this result.

SonotaCo 2013/2014 remains exposed development-only. No MAARSY, DMS, OrbitTrace target information, target-region events, or protected solar-longitude 20°–55° content may be accessed.