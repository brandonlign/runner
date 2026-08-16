# OrbitTrace EOM + leaf union v2 — frozen protocol

## Scientific role

**TARGET-EXCLUDED GMN 2022+2023 DEVELOPMENT ONLY.**

This is one preregistered structural candidate-pool experiment. It tests whether OrbitTrace loses recoverable sparse showers because HDBSCAN EOM forces a parent-or-descendants partition even when both a broad recurrent parent and a fine recurrent leaf may be useful detection candidates.

## Frozen baseline

The exact full-data density-synchronous recurrent-EOM winner from run `31852836840` is the baseline:
- exact candidate count: `2094`;
- total recovered@100: `179`;
- 2022: recovered@50 `45`, recovered@100 `89`, top100 dominant precision `0.7873334043`, MRR `0.02250537317`, fragmentation median top500 `1.0`;
- 2023: recovered@50 `46`, recovered@100 `90`, top100 dominant precision `0.7898245986`, MRR `0.02203028491`, fragmentation median top500 `1.0`.

The baseline prelabel/result artifacts are immutable inputs. Their candidate memberships and order must be reproduced exactly before the successor is evaluated.

## Sole successor change

Use the same target-excluded pooled GMN 2022+2023 catalogue, GEO6 representation, HDBSCAN hierarchy, `min_cluster_size=10`, `min_samples=10`, Euclidean metric, epsilon `0`, `allow_single_cluster=False`, and density-synchronous stability objective as the frozen winner.

The successor candidate pool is:

1. every exact density-synchronous EOM baseline family; plus
2. every HDBSCAN **leaf-selected** family from the **same condensed tree**, using the same density-synchronous stability map instead of ordinary HDBSCAN stability.

Only exact-identical event-membership duplicates may be removed. If a leaf family has exactly the same membership as an EOM family, retain one copy. No overlap threshold, similarity threshold, family-size threshold beyond HDBSCAN's frozen minimum, top-k pruning, score blend, learned weight, orbital criterion, year-balance factor, perturbation score, or post-result rescue is authorized.

The complete deduplicated candidate order is fixed by the unchanged winner ranking semantics:
1. descending raw density-synchronous stability;
2. descending ordinary HDBSCAN stability;
3. descending member count;
4. deterministic family ID.

Thus the experiment changes only candidate availability across hierarchy resolution; it does not change geometry, density estimation, stability definition, or ranking objective.

## Prelabel freeze

Before any known-shower truth is indexed, persist:
- exact reconstructed condensed-tree hash;
- exact baseline EOM candidate membership/order hash and verification against the frozen winner artifact;
- selected leaf node IDs;
- leaf candidate memberships and scores;
- exact duplicate count;
- complete deduplicated union candidate memberships and final order;
- all source/input hashes and firewall state.

Known-shower truth may be opened only after this prelabel artifact is written.

## Binding development gate

Baseline total recovered@100 is `179`. The successor passes only if **all** are true:

1. total recovered@100 across 2022+2023 is at least `184` (`+5` minimum);
2. neither year regresses in recovered@50;
3. neither year regresses in recovered@100;
4. neither year regresses in top100 dominant precision;
5. neither year regresses in MRR;
6. neither year worsens in median top500 fragmentation;
7. the mechanism is active: at least one non-duplicate leaf family is added and the final order/pool differs from baseline;
8. all structural, source, provenance, and firewall assertions pass.

Otherwise the verdict is `FAIL_EOM_LEAF_UNION_V2_GMN_DEVELOPMENT` and this exact architecture is permanently rejected. No alternate leaf weighting, EOM/leaf mixture weight, leaf-size cap, overlap filter, duplicate rule, top-k leaf quota, or score rescue may be chosen after seeing the result.

## Permanent firewall

- Protected solar longitude `[20°,55°]` is removed inclusively before labels.
- OrbitTrace target information/events remain inaccessible.
- SonotaCo 2013/2014 is inaccessible.
- AMOS is inaccessible.
- ASFN and EFN are inaccessible.
- MAARSY and DMS are inaccessible scientifically.

A GMN development pass would justify a separately frozen transfer test; it does not itself establish external generalization.