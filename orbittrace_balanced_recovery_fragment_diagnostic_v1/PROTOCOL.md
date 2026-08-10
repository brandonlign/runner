# OrbitTrace balanced-recovery fragment-vs-group diagnostic v1

## Purpose

Refine the completed PR #999 diagnosis without defining another promotion candidate.

PR #999 established that the failed #997 balanced-recovery architecture loses HDBSCAN recoverable showers primarily in the raw supervised score, not in geometric diversity or v19 fusion. This diagnostic distinguishes two upstream failure modes:

1. **group-recognition failure** — no family from a genuinely recoverable shower group appears early;
2. **within-group fragment-selection failure** — some family from the recoverable shower group appears early, but the actually balanced-recoverable family is ranked behind a weaker fragment/near-miss from the same shower.

No model, target, feature, candidate membership, class weight, probability calibration, order, diversity value, fusion rule, source quota, or literature promotion candidate is changed or selected.

## Frozen replay

Replay exactly PR #997 using its already-frozen artifact:

- exact v22 71D pretruth Sugar/HDBSCAN route payloads;
- exact fixed v19-expanded memberships, centroids, v19 orders, and tie ranks;
- exact immutable exposed SonotaCo truth package;
- exact #997 target `F1_2013 > 0.5 AND F1_2014 > 0.5` for the unchanged v22/v25 best recurrent label;
- exact strict whole-shower five-fold groups;
- exact #839 inverse-group weights;
- exact #997 ExtraTreesClassifier parameters;
- exact #839 diversity `0.8/1.0`;
- exact equal v19 rank-sum.

The replay must reproduce the exact #997 classifier-diversity order hash and final fused-order hash for each route. Raw floating probability SHA is recorded but nonbinding for the already-documented cross-host parallel-tree reason from #999.

## Diagnostic unit

A **positive shower group** is a strict `SHOWER/<label>` group containing at least one family with the fixed #997 balanced-recovery target equal to 1.

For each already-existing order — `raw_probability`, `probability_plus_diversity`, `v19_control`, and `final_v19_rank_sum` — and for each positive shower group, compute:

- first rank of **any** family belonging to that shower group;
- first rank of a **target-positive** family belonging to that shower group;
- selection gap = first target-positive rank minus first any-family rank;
- whether the first-ranked family from the group is itself target-positive.

For each route/order, summarize:

- number of positive shower groups;
- fraction/count whose first-ranked group member is target-positive;
- median, q75, q90, and maximum selection gap;
- at each already-frozen comparator budget, number of positive shower groups with **any member** surfaced;
- at the same budget, number with a **target-positive member** surfaced;
- `fragment_only_groups = any_member_groups - target_positive_groups`.

No new literature macro-F1 or superiority result is computed for any alternate order.

## Interpretation boundary

- If `any_member_groups` is substantially larger than `target_positive_groups` at HDBSCAN budgets, the next methodology problem is within-shower family-quality selection.
- If both are similarly low, the dominant problem is group-level representation/discrimination: the model does not recognize the recoverable shower group at all.
- If behavior differs strongly between raw/diversity/fusion, that may diagnose order-stage effects, but this diagnostic may not select an alternate order.

Any successor must be separately named and frozen after this diagnostic result.

## Firewall

- SonotaCo role: exposed development only.
- New scientific ranker: false.
- New literature promotion evaluation: false.
- Candidate/membership changes: false.
- Feature/target/model/class-weight/calibration/diversity/fusion/parameter search: false.
- MAARSY scientific access: false.
- DMS scientific access: false.
- OrbitTrace target-information access: false.
- Protected 20°–55° target-region access: false.
