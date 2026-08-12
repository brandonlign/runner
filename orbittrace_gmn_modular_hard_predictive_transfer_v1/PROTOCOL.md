# OrbitTrace GMN modular hard predictive transfer v1

## Scientific role

This is a separately frozen target-excluded GMN successor. It is motivated only by three binding GMN development results:

1. The exact hard-family module passed in run `31560470070`: immutable hard order + exact predictive order by equal 1-based rank sum improved recovered@100 `59 -> 62`, recovered@50 `38 -> 39`, top-100 dominant precision `0.6884631112636006 -> 0.7145192896079117`, and MRR `0.046734076055452344 -> 0.04907166615045645`.
2. Global fusion across all 4,504 candidates failed in run `31561024725`.
3. Re-fusing predictability against the active #839-induced hard suborder failed in run `31561474296`.

The sole new question is therefore modular transfer: can the **already-passed hard-family ranking module from (1)** be inserted into the exact hard slots of the active #839 full-union order while every P19/P20 candidate remains fixed in its exact baseline slot?

No SonotaCo information is used. SonotaCo 2013/2014 is inaccessible. The first technically valid result is binding. No alternate module, weight, source partition, slot subset, threshold, or post-result rescue is authorized.

## Immutable inputs

Use the exact target-excluded GMN 2022/2023 candidate universe:
- hard = 226
- P19 = 1075
- P20 = 3203
- union = 4504

Use the exact active #839 full-union grouped five-fold OOF quality/diversity baseline, which must reproduce:
- recovered@25 = 22
- recovered@50 = 40
- recovered@100 = 75
- recovered@500 = 159
- qualified matches = 256
- top-100 dominant precision = 0.7645689180574315
- MRR = 0.019037817654898162

Use the exact immutable original hard order from frozen P19 prelabel payload SHA-256 `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`.

Use the exact predictive hard rule frozen before run `31560470070` (source blob `25d91e92c41f83416ad87766c2d96884c30b714c`).

## Exact passed hard module

Compute the exact predictive order over the 226 hard candidates:
`(lower worst-year predictive q90, lower worst-year predictive median, higher q90 gain, family_id)`.

Convert the immutable original hard order and predictive hard order to 1-based ranks. The module order is exactly:
`(original_hard_rank + predictive_rank, original_hard_rank, family_id)`.

This is the same hard-family ranking architecture that produced the binding PASS in run `31560470070`. It is not re-fitted to the active #839 hard suborder.

## Frozen modular insertion rule

1. Reproduce the exact active #839 full-union baseline order.
2. Record every absolute position occupied by a hard candidate; exactly 226 such slots must exist.
3. Replace the hard IDs in those positions, in slot order, with the exact passed hard-module order defined above.
4. Every P19 and P20 candidate remains in its exact original absolute baseline position.
5. No hard candidate may enter a soft slot and no soft candidate may enter a hard slot.

No additional fusion with #839 hard ranks is permitted.

## Binding PASS gate

PASS requires all five:
- recovered@100 strictly greater than 75;
- recovered@50 >= 40;
- recovered@25 >= 22;
- top-100 dominant precision >= 0.7645689180574315;
- MRR >= 0.019037817654898162.

Otherwise verdict is FAIL and this exact modular transfer is permanently closed.

## Claim boundary

PASS would be target-excluded GMN development evidence only. It would authorize at most one separately frozen SonotaCo transfer applying the same modular source-slot principle to the exact v31 parent. It would not itself establish HDBSCAN superiority.

## Firewall

- protected solar longitude 20 deg through 55 deg remains excluded;
- SonotaCo 2013/2014 access = false;
- OrbitTrace target information access = false;
- target-region events accessed = false;
- MAARSY scientific access = false;
- DMS scientific access = false.
