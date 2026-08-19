# OrbitTrace geometric joint EOM v1 — frozen protocol

## Status

**FROZEN BEFORE THE FIRST TECHNICALLY VALID GMN OUTCOME.**

This is a scientifically distinct successor after RC-EOM and DCRR showed that ordinary density persistence contains useful information but that replacing recurrent selection or exposing both cuts as separate fixed-budget hypotheses is harmful. The permanent split remains unchanged: GMN 2022/2023 target-excluded is development; SonotaCo 2013/2014 is the fixed validation / current-paper benchmark; no SonotaCo execution is authorized unless this version first passes GMN.

## Method

Fit exactly one pooled target-excluded HDBSCAN hierarchy in the existing GEO6 representation using the inherited fixed settings:

- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- EOM;
- cluster-selection epsilon 0;
- no single root cluster.

For every condensed-tree node `C`, compute:

- ordinary HDBSCAN excess-of-mass stability `S_ord(C)`;
- exact current recurrent-EOM stability `S_rec(C)=min(E_2022(C),E_2023(C))` using frozen kernel blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`.

Define one parameter-free joint node quality

`S_geo(C) = sqrt(S_ord(C) * S_rec(C))`.

Run the normal EOM dynamic program once on `S_geo`. The resulting selected nodes are a single non-overlapping partition, not a union catalogue.

Rank selected candidates by:

1. descending `S_geo`;
2. descending `S_rec`;
3. descending `S_ord`;
4. descending member count;
5. deterministic family ID.

There is no blend coefficient, exponent search, normalization parameter, route rule, budget rule, threshold, top-K exception, ordinary/recurrent union, or post-result fallback. Global positive rescaling of either `S_ord` or `S_rec` multiplies all `S_geo` by one common factor and therefore cannot alter selection or ranking.

## Why this differs from closed consensus-EOM

Consensus-EOM v1 required the two annual EOM components of a parent to dominate the summed child vector componentwise. Geometric joint EOM instead combines **ordinary pooled density persistence** and the already-aggregated recurrent stability into a scalar geometric joint quality and applies standard EOM. It neither reopens annual-combiner variants nor rescues consensus-EOM.

## Pre-GMN technical gates

Before accessing GMN labels, the binding execution must prove:

- exact parent recurrent kernel identity;
- exact density-synchronous champion kernel identity;
- `S_geo >= 0` and finite for every node;
- year-swap invariance;
- positive separate rescaling invariance of ordinary/recurrent axes;
- if the two stability maps are proportional, geometric joint EOM selects the same nodes as either map;
- hierarchy is not modified;
- complete successor selected nodes, memberships, order, and stability maps are persisted before truth scoring.

## GMN development benchmark

Use the permanent target-excluded GMN 2022+2023 development panel and the existing known-shower evaluator. Protected solar longitude `[20°,55°]` inclusive remains excluded before candidate construction or truth use.

The comparison parent is the current **density-synchronous recurrent-EOM GMN champion** from PR #1263, not the older recurrent-EOM method.

Frozen champion metrics:

### 2022
- recovered@50 `45`;
- recovered@100 `89`;
- top-100 dominant precision `0.7873334042799703`;
- MRR `0.022505373166085363`;
- median top-500 fragmentation `1.0`.

### 2023
- recovered@50 `46`;
- recovered@100 `90`;
- top-100 dominant precision `0.7898245986099988`;
- MRR `0.02203028490649908`;
- median top-500 fragmentation `1.0`.

### Promotion gate

Geometric joint EOM passes GMN only if:

1. mechanism is active;
2. recovered@50 is no lower than density-sync in both years;
3. recovered@100 is no lower in both years;
4. top-100 dominant precision is no lower in both years;
5. MRR is no lower in both years;
6. median top-500 fragmentation is no worse in both years;
7. at least one year has strict recovered@100 improvement over density-sync.

A valid FAIL permanently closes exact geometric joint EOM v1. No weight/exponent/normalization/rerank/support-setting rescue is authorized.

## SonotaCo / current-paper validation

Only after a GMN PASS may exactly one validation be frozen and run using the **same benchmark currently used in the paper**:

- Sugar 2013 B=40;
- Sugar 2014 B=43;
- published-configuration HDBSCAN 2013 B=14;
- published-configuration HDBSCAN 2014 B=14;
- identical pooled 2013+2014 label-free temporal information;
- identical eligible-shower definition and Hungarian one-to-one F1 scoring.

The later symmetric tuned-HDBSCAN benchmark is secondary characterization only and cannot replace or rescue the current-paper validation.
