# OrbitTrace balanced-recovery order-stage diagnostic v1

## Purpose

Diagnose the already-failed PR #997 balanced-recovery architecture without defining or evaluating another promotion candidate.

PR #997 cleanly reproduced the fixed v22/v25 pretruth payloads and then failed the all-panel literature gate 2/4. This diagnostic asks only **where the rare balanced-recovery shower groups are lost** between the frozen OOF classifier score and the final order:

1. raw balanced-recovery OOF probability;
2. exact #839 geometric diversity (`lambda=0.8`, `scale=1.0`);
3. exact parameter-free equal rank-sum with frozen v19.

No new model, target, feature, membership, class weight, probability calibration, diversity value, fusion weight, source quota, or literature promotion candidate is authorized.

## Frozen reconstruction

Reconstruct exactly PR #997 using:

- exact v22 71D pretruth payloads for Sugar and HDBSCAN routes;
- exact fixed v19-expanded memberships, centroids, v19 orders, and tie ranks;
- exact immutable SonotaCo exposed truth only after pretruth identity;
- exact #997 binary target `F1_2013 > 0.5 AND F1_2014 > 0.5` for the unchanged v22/v25 best recurrent label;
- exact strict whole-shower groups shared across routes;
- exact deterministic five-fold assignment;
- exact #839 inverse-group weights;
- exact #997 `ExtraTreesClassifier` parameters;
- exact #839 diversity and exact v19 equal rank-sum.

The diagnostic must reproduce the #997 OOF-probability and final-order hashes if a frozen #997 reference result is supplied.

## Frozen diagnostic measurements

For each route, report:

- family-level OOF ROC AUC and average precision for the fixed balanced-recovery target;
- strict-group-level OOF ROC AUC and average precision, where a shower group's score is the maximum family probability in that group and the group is positive iff any family in it satisfies the fixed target;
- for each of four already-existing orders — `raw_probability`, `probability_plus_diversity`, `v19_control`, and `final_v19_rank_sum` — the first-rank distribution of distinct positive shower groups;
- at the two already-frozen comparator budgets for that route, the number of distinct balanced-recovery-positive shower groups surfaced and the number of target-positive families surfaced;
- total distinct positive shower groups, median first rank, q75 first rank, q90 first rank, and best/worst first rank.

These are target-retrieval diagnostics only. Do **not** compute new literature superiority pass/fail results for raw probability or diversity-only orders. The only literature result remains PR #997's already-failed fused order.

## Interpretation boundary

The diagnostic may distinguish:

- score-separability failure: raw OOF probability itself fails to surface positive shower groups;
- diversification loss: raw probability surfaces them but geometric diversity pushes them out;
- fusion loss: diversity order surfaces them but v19 rank-sum pushes them out.

It may not select an alternate order, fusion weight, threshold, class weight, calibration, feature subset, tree capacity, source route, or successor method. Any successor must be separately named and frozen after this diagnostic is complete.

## Firewall

- SonotaCo role: exposed development only.
- Candidate/membership changes: false.
- Scientific ranker training beyond exact #997 replay: false.
- New literature promotion evaluation: false.
- Parameter/feature/target/fusion/diversity search: false.
- MAARSY scientific access: false.
- DMS scientific access: false.
- OrbitTrace target-information access: false.
- Protected 20°–55° target-region access: false.
