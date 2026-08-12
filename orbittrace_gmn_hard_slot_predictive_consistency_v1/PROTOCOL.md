# OrbitTrace GMN hard-slot predictive-consistency successor v1

## Scientific role

This is a separately frozen target-excluded GMN successor motivated by two binding GMN development results:

1. Hard-family candidate-internal predictive consistency passed on the exact 226-family hard universe in run `31560470070`: recovered@100 `59 -> 62`, recovered@50 `38 -> 39`, top-100 dominant precision `0.6884631112636006 -> 0.7145192896079117`, MRR `0.046734076055452344 -> 0.04907166615045645`.
2. Global transfer across all 4,504 hard/P19/P20 candidates failed in run `31561024725`: recovered@100 `75 -> 69` and top-100 dominant precision `0.7645689180574315 -> 0.6779311511322345`.

The discrepancy motivates one minimal architecture: preserve the active full-union baseline's source-class placement exactly and allow the GMN-authorized predictive signal to reorder **only hard candidates inside slots already occupied by hard candidates**. P19 and P20 candidates never move, never exchange slots with hard candidates, and retain their exact baseline order and positions.

This is GMN development, not SonotaCo. SonotaCo 2013/2014 remains inaccessible during this experiment. The first technically valid result is binding. No alternative slot rule, source partition, rank weight, threshold, route, candidate deletion, or post-result rescue is authorized.

## Immutable universe and baseline

Use the exact active GMN 2022/2023 candidate universe:

- hard: 226
- P19: 1075
- P20: 3203
- union: 4504

Use the exact active #839 34-feature grouped five-fold OOF quality/diversity baseline with diversity lambda `0.8`, scale `1.0`, and its exact tie rule. It must reproduce:

- recovered@25 = 22
- recovered@50 = 40
- recovered@100 = 75
- recovered@500 = 159
- qualified matches = 256
- top-100 dominant precision = 0.7645689180574315
- MRR = 0.019037817654898162

No baseline model, candidate, membership, source identity, diversity rule, feature, fold, or label definition changes.

## Exact predictive rule

Use the exact hard-family predictive implementation already frozen before run `31560470070` (source blob `25d91e92c41f83416ad87766c2d96884c30b714c`). For each hard candidate only:

- annual leave-one-out OLS when n>=4 with design `[1, signed_delta_sol / 10 deg]` and response `[radiant unit-vector x,y,z, log(vg)]`;
- held-out residual `hypot(radiant_angle / 3 deg, abs(delta_log_vg) / log(1.08))`;
- annual n<4 uses static centroid residual with learned fraction 0;
- candidate order is `(lower worst-year predictive q90, lower worst-year predictive median, higher q90 gain, family_id)`.

No predictive score is computed for purposes of reordering P19 or P20 candidates.

## Frozen hard-slot rule

Given the exact active #839 full-union baseline order:

1. Record all zero-based positions whose candidate source is `hard`. This position vector is immutable.
2. Extract the hard candidates in their baseline relative order; this is the `baseline_hard_order`.
3. Compute the exact predictive hard order over the same 226 hard candidates.
4. Convert `baseline_hard_order` and `predictive_hard_order` to 1-based ranks. The sole hard candidate order is sorted by:
   `(baseline_hard_rank + predictive_rank, baseline_hard_rank, family_id)`.
5. Replace only the hard IDs occupying the recorded hard slots with this fused hard order.
6. Every P19/P20 ID remains in its exact baseline position. Their relative order and absolute slot indices are unchanged.

No hard candidate may enter a soft slot and no soft candidate may enter a hard slot.

## Binding PASS gate

PASS requires all five:

- recovered@100 strictly greater than 75;
- recovered@50 >= 40;
- recovered@25 >= 22;
- top-100 dominant precision >= 0.7645689180574315;
- MRR >= 0.019037817654898162.

Otherwise verdict is FAIL and this exact hard-slot architecture is permanently closed.

## Claim boundary

A PASS is target-excluded GMN development evidence only. It does not establish HDBSCAN literature superiority. Only after a PASS may one separately freeze a SonotaCo transfer that applies the same source-slot preservation principle to the exact v31 parent. No SonotaCo benchmark may be viewed before that transfer is fully frozen.

## Firewall

- protected solar longitude 20 deg through 55 deg remains excluded;
- SonotaCo 2013/2014 access = false;
- OrbitTrace target information access = false;
- target-region events accessed = false;
- MAARSY scientific access = false;
- DMS scientific access = false.
