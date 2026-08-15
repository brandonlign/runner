# OrbitTrace density-synchronous recurrent-EOM — GMN train robustness CV v1

## Scientific role

**TRAIN / DEVELOPMENT ROBUSTNESS ONLY.**

This protocol characterizes whether the already-promoted density-synchronous recurrent-EOM method from PR #1263 remains superior to its exact recurrent-EOM v1 parent under deterministic perturbations of the permanent target-excluded GMN 2022+2023 training corpus.

It is not a new method, does not alter #1263, does not promote a successor, and does not access the permanent SonotaCo validation set or AMOS final-test set.

## Immutable methods

Parent:
- exact recurrent-EOM HDBSCAN v1 kernel blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- GEO6 representation;
- HDBSCAN `min_cluster_size=10`, `min_samples=10`, Euclidean, EOM, epsilon 0, `allow_single_cluster=False`;
- annual normalization and recurrent quality `min(E_2022,E_2023)` unchanged.

Champion:
- exact density-synchronous kernel blob `587a304f451e41b9503272f1783a6c6ebb295000`;
- same hierarchy and HDBSCAN settings;
- local quality `S_sync(C)=integral min(A_2022^C(lambda),A_2023^C(lambda)) d lambda`;
- same ranking semantics as #1263.

No parameter, representation, threshold, score, ranking, or evaluator modification is authorized by this robustness experiment.

## Permanent firewall

- Years are exactly GMN 2022 and 2023.
- Protected solar longitude `[20°,55°]` is removed inclusively before any shower label can be used.
- OrbitTrace target information/events remain inaccessible.
- SonotaCo 2013/2014 is inaccessible to this experiment despite being the permanent validation set.
- AMOS 2023/2024 is inaccessible and remains the permanent final test.
- ASFN/EFN/other historical panels are inaccessible.
- MAARSY and DMS are inaccessible scientifically.

## Deterministic perturbation

Each accessible event is assigned to exactly one fold by:

`fold(event_id) = int.from_bytes(SHA256(UTF8(event_id))[0:8], 'big') mod 10`.

For fold `f in {0,...,9}`, all accessible events with `fold(event_id)==f` are removed from **both** years before GEO6 construction. The remaining approximately 90% corpus is used unchanged.

This is deterministic and depends only on stable event ID. No physical coordinate, year-specific threshold, shower label, candidate identity, or result enters fold assignment.

## Per-fold execution

For each fold independently:
1. parse the same frozen target-excluded GMN 2022/2023 corpus used by #1263;
2. remove the fixed hash bucket;
3. fit exactly one pooled HDBSCAN hierarchy on the retained events;
4. compute exact recurrent-EOM parent extraction/order;
5. compute exact density-synchronous extraction/order on the same hierarchy;
6. freeze hierarchy, node qualities, memberships and complete orders before opening the already-exposed GMN training labels;
7. evaluate both methods with the exact #1263 GMN evaluator.

No fold may influence another fold and no failed fold may be rerun with a changed scientific rule.

## Frozen aggregate robustness criterion

Across the 20 year-fold panels (10 folds x 2 years), define simple paired aggregates.

Density-synchronous robustness is `PASS_DENSITY_SYNC_GMN_TRAIN_CV_V1` iff all are true:

1. total `recovered_at_50` across all 20 panels is not lower than recurrent-EOM;
2. total `recovered_at_100` across all 20 panels is **strictly higher** than recurrent-EOM;
3. mean top-100 dominant precision across all 20 panels is not lower;
4. mean MRR across all 20 panels is not lower;
5. median top-500 fragmentation across all 20 panels is not higher;
6. the density-synchronous mechanism is active in at least one fold.

Otherwise the robustness verdict is `FAIL_DENSITY_SYNC_GMN_TRAIN_CV_V1`.

This robustness verdict does **not** rewrite the binding #1263 GMN development PASS. A failure means the observed development superiority is not robust to deterministic 10% holdouts and should materially reduce confidence before final-method selection. No post-result fold weighting, fold removal, alternate hash, alternate holdout fraction, seed, bootstrap, threshold, or rescue is authorized.

## Validation/test governance

This experiment consumes only permanent TRAIN/DEVELOPMENT data. It cannot activate SonotaCo automatically and it cannot access AMOS under any outcome. Future method validation remains governed by PR #1264.
