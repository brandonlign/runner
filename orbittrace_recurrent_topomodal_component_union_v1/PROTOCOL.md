# OrbitTrace recurrent-TopoModal component-union v1 — frozen protocol

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This successor is scientifically distinct from the closed overlap-consensus ordering. It does not reorder or thin that closed list. Instead it treats Recurrent-EOM clusters and independently overlap-confirmed TopoModal clusters as a bipartite cluster graph and emits one event-level union meta-cluster per Recurrent-EOM component. This is a cluster-ensemble / meta-cluster membership architecture rather than a ranking rescue.

The motivation is label-free: the closed overlap-consensus pretruth showed that every retained TopoModal mode is connected to exactly one Recurrent-EOM parent, but multiple child modes can consume many equal-budget slots. Component union collapses the entire one-parent bipartite component into one candidate while preserving the exact Recurrent-EOM parent rank and budget.

## 1. Firewall

Use only target-excluded GMN 2022+2023 sparse development panels. Inclusive solar longitude `[20.0,55.0]` remains excluded.

Forbidden:

- OrbitTrace target information or target-region events;
- SonotaCo 2013/2014 scientific access;
- ASFN/EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- truth-informed child selection, overlap thresholds, union weights, rank changes, candidate budgets, or post-result rescue.

## 2. Immutable zero-label source

Use only the sealed pretruth catalogue from the closed overlap-consensus Stage 1:

- workflow run `32072681272`;
- pretruth artifact `9302288262`;
- file `RECURRENT_TOPOMODAL_OVERLAP_CONSENSUS_V1_PRELABEL.json`;
- SHA-256 `bd0d28410d23bef0c5c8847ecd8d54e91b74e148ce62e8533407787d265e468f`.

This file was persisted before shower truth opened and contains, for all eight frozen sparse panels:

- exact Recurrent-EOM parents `P_1,...,P_K` in frozen rank order;
- all full TopoModal support modes retained by the already-frozen exact-overlap corroboration rule;
- for each retained TopoModal mode, its unique `corroborating_parent_rank`;
- exact annual event identities and equal budget `K`.

The later truth result from the closed overlap-consensus method is **not an input** to candidate construction.

## 3. Sole component-union rule

For each Recurrent-EOM parent `P_r`, let

`T_r = { S_j : corroborating_parent_rank(S_j) = r }`.

Emit exactly one successor candidate

`C_r = P_r union (union_{S in T_r} S)`.

If `T_r` is empty, `C_r = P_r` exactly.

The successor catalogue is exactly

`C_1, C_2, ..., C_K`

in the original Recurrent-EOM rank order.

There is:

- no overlap fraction/Jaccard/F1/containment threshold;
- no choice of one child over another;
- no child weighting;
- no event voting threshold;
- no TopoModal rank in the successor order;
- no support-only component;
- no recurrent orphan insertion;
- no learned model;
- no tunable coefficient.

Every overlap-confirmed TopoModal child connected to a parent is included in that parent's union component.

## 4. Mandatory zero-label pretruth authorization

Before shower truth is opened, persist `RECURRENT_TOPOMODAL_COMPONENT_UNION_V1_PRELABEL.json` with exact memberships and provenance.

All eight panels must satisfy:

1. immutable source SHA and firewall reproduce exactly;
2. exact Recurrent-EOM parent ranks are `1..K`;
3. every source TopoModal child has exactly one valid corroborating parent rank;
4. successor count is exactly `K`;
5. successor rank `r` corresponds exactly to parent rank `r`;
6. `C_r` contains the full parent `P_r`;
7. `C_r` equals exactly the set union of `P_r` and **all** source children assigned to `r`;
8. no source child is omitted or assigned twice;
9. successor candidates are pairwise disjoint;
10. every successor has support at least 4.

Report, without tuning:

- number of parents with at least one child;
- mean/max membership expansion ratio `|C_r|/|P_r|`;
- fraction of each component contributed outside its parent;
- four nested-bucket cross-scale mean-best-Jaccard values.

Require before truth:

11. successor cross-scale mean-best-Jaccard is at least Recurrent-EOM in all `4/4` nested bucket pairs;
12. aggregate successor cross-scale mean-best-Jaccard is at least Recurrent-EOM.

Only `PASS_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1_PRETRUTH` authorizes truth.

## 5. Truth semantics and reciprocal-rank metric

Use the exact established target-excluded GMN 2022/2023 sparse truth runtime and parent matching semantics:

- annual eligibility >=4 events;
- positive match requires precision >=0.5 and overlap >=4;
- exact equal candidate budget `K`;
- report qualified matches, recovered@25/@50/@100/@500, top-100 dominant precision, fragmentation, and historical conditional MRR.

Historical conditional MRR is diagnostic only.

The preregistered ranking gate is the zero-filled eligible-query MRR established before this successor outcome:

`MRR_zero = (1/|E|) * sum_q RR(q)`,

where `RR(q)=1/r_q` for a recovered eligible shower and `0` for an eligible unrecovered shower.

Aggregate by unweighted mean over the eight annual panels at each scale. Report pooled reciprocal mass per eligible query as a diagnostic.

## 6. Binding ten-gate contract

### Fine `d=1024`

1. successor qualified-total strictly greater than Recurrent-EOM;
2. successor qualified matches nonlower in at least `6/8` panels;
3. successor mean zero-filled MRR at least Recurrent-EOM;
4. successor precision mean at least Recurrent-EOM;
5. successor fragmentation mean no higher than Recurrent-EOM.

### Coarse `d=128`

6. successor qualified-total at least Recurrent-EOM;
7. successor qualified matches nonlower in at least `6/8` panels;
8. successor mean zero-filled MRR at least Recurrent-EOM;
9. successor precision mean at least Recurrent-EOM;
10. successor fragmentation mean no higher than Recurrent-EOM.

All ten gates are mandatory. Return exactly:

- `PASS_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1`, or
- `FAIL_RECURRENT_TOPOMODAL_COMPONENT_UNION_V1`.

The first technically valid truth result is binding.

## 7. Closure

A PASS authorizes only a separately frozen scale/full-GMN translation stage. It does not authorize protected target access or automatically replace the current champion.

A valid FAIL permanently closes this exact component-union architecture. Do not rescue it by omitting children, choosing one child, weighting/voting child memberships, intersection instead of union, expansion caps, overlap thresholds, alternate rank order, support-only inserts, changed K, scale-specific rules, or changed gates.

Any subsequent method must be genuinely distinct and separately frozen before truth.
