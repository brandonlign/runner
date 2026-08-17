# OrbitTrace recurrent-TopoModal support mask v1 — frozen protocol

## Status

**FROZEN BEFORE IMPLEMENTATION AND BEFORE ANY SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This successor is a distinct membership architecture motivated by the already-closed recurrent-orphan completion result. It does not rerank TopoModal, tune an overlap threshold, modify Recurrent-EOM geometry, or rescue the closed orphan-completion catalogue.

The scientific question is narrower:

> Can the exact Recurrent-EOM early ordering be retained while TopoModal acts only as an independent event-level support mask that removes parent halo unsupported by any support-cut mode?

The architecture preserves exactly one candidate slot per Recurrent-EOM parent and preserves the exact Recurrent-EOM rank of that slot. The only scientific change is candidate membership.

## 1. Firewall

Use only target-excluded GMN 2022+2023 development panels already serialized before truth in the recurrent-orphan completion Stage-1 artifact.

Inclusive solar longitude `[20.0,55.0]` remains excluded.

Forbidden:

- OrbitTrace target information or target-region events;
- SonotaCo 2013/2014 scientific access;
- ASFN/EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- any truth-informed membership threshold, rank change, score blend, source quota, candidate budget change, or post-result rescue.

## 2. Immutable source

Use only the Stage-1 zero-label orphan-completion prelabel:

- workflow run `32043362123`;
- artifact `9292356070`;
- `SUPPORT_CUT_RECURRENT_ORPHAN_COMPLETION_V1_PRELABEL.json`;
- SHA-256 `278d659542668e52033a5369f9afdf685e010a2c14c7ff5211b0b60dd73f2d4a`.

That file was sealed before shower truth was opened and contains, for all eight frozen sparse panels:

- exact Recurrent-EOM candidate memberships and ranks;
- the complete support-resolved TopoModal cut represented exactly once as `support_projection` plus `support_append` rows;
- exact panel event identities and equal candidate budget `K`.

The later orphan-completion truth result is **not an input** to candidate construction.

## 3. Exact support-mask membership rule

For one frozen panel let:

- `P_r` be the Recurrent-EOM candidate at original rank `r`;
- `S_1,...,S_m` be every support-cut candidate recovered from the immutable Stage-1 prelabel, i.e. every successor row whose `catalogue_source` is `support_projection` or `support_append`;
- `U_S = union_j S_j` be the event set represented anywhere in the support-cut catalogue.

For every Recurrent-EOM parent independently compute

`M_r = P_r intersect U_S`.

Use exactly the already-frozen support-4 reporting floor:

- if `|M_r| >= 4`, emit `M_r` as the successor candidate at rank `r`;
- otherwise emit the original `P_r` unchanged at rank `r`.

There is no overlap fraction, Jaccard/F1 threshold, witness winner, TopoModal rank, density score, persistence score, source quota, learned model, annual label, or tuned parameter.

The rule uses **all** TopoModal support children touching a Recurrent-EOM parent. It never chooses one child over another.

## 4. Ranking and budget — immutable Recurrent-EOM backbone

The successor candidate count is exactly the Recurrent-EOM candidate count in every panel.

The successor rank is exactly the original Recurrent-EOM rank:

`rank_successor(r) = rank_recurrent(r)`.

No candidate may move earlier or later. No support-only candidate is inserted as an additional slot. Equal-budget truth evaluation therefore uses the complete successor list and complete Recurrent-EOM list at the same `K`.

This isolates membership from ranking: any MRR change must arise from a different event representation at the same parent rank, not from candidate reordering.

## 5. Mandatory zero-label pretruth audit

Before shower truth is opened, persist `RECURRENT_TOPOMODAL_SUPPORT_MASK_V1_PRELABEL.json` containing every exact successor membership and audit field.

Require all eight frozen panels to satisfy:

1. exact original panel/event universe restored;
2. exact original Recurrent-EOM order restored;
3. successor candidate count exactly `K`;
4. successor ranks exactly `1..K` and identical to parent ranks;
5. every successor has support at least 4;
6. every successor membership is a subset of its corresponding parent membership;
7. every `support_mask` row equals exactly `P_r intersect U_S`;
8. every fallback occurs iff the exact mask has support below 4;
9. successor candidates are globally pairwise disjoint;
10. the mechanism is active in every panel (at least one parent is genuinely masked).

Also report, as non-gating structural diagnostics only:

- masked/fallback counts;
- retention fractions;
- the exact parent and successor cross-scale mean-best-Jaccard values on the four already-frozen nested bucket pairs.

No structural diagnostic may be used to alter the membership rule.

Only a technically valid pretruth audit authorizes the binding truth endpoint.

## 6. Binding truth endpoint

Use the exact same target-excluded GMN 2022/2023 sparse truth runtime, annual eligibility semantics, match definition, equal budgets, and ten gates used by #1284 and the closed orphan-completion endpoint.

There are sixteen annual panels: four buckets x two years at each of two scales.

### Fine scale `d=1024`

1. successor qualified-total is **strictly greater** than Recurrent-EOM;
2. successor qualified matches are nonlower in at least `6/8` annual panels;
3. successor mean MRR is at least Recurrent-EOM;
4. successor mean top-100 dominant precision is at least Recurrent-EOM;
5. successor mean median top-500 fragmentation is no higher than Recurrent-EOM.

### Coarse scale `d=128`

6. successor qualified-total is at least Recurrent-EOM;
7. successor qualified matches are nonlower in at least `6/8` annual panels;
8. successor mean MRR is at least Recurrent-EOM;
9. successor mean top-100 dominant precision is at least Recurrent-EOM;
10. successor mean median top-500 fragmentation is no higher than Recurrent-EOM.

All ten gates are mandatory.

Return exactly one binding verdict:

- `PASS_RECURRENT_TOPOMODAL_SUPPORT_MASK_V1`, or
- `FAIL_RECURRENT_TOPOMODAL_SUPPORT_MASK_V1`.

## 7. Interpretation and closure

A PASS would show that TopoModal is useful as an independent consensus membership estimator while Recurrent-EOM remains the ranking backbone. It would authorize only a separately frozen scalability/portability stage; it would not authorize protected target access.

A valid FAIL permanently closes this exact global support-mask membership rule. Do not rescue it by:

- changing support 4;
- requiring an overlap fraction;
- using Jaccard/F1/containment thresholds;
- choosing only some TopoModal children;
- weighting children;
- blending parent and mask events;
- changing fallback behavior;
- reranking candidates;
- inserting support-only candidates;
- changing K;
- tuning per scale/bucket/year;
- relaxing MRR or any other gate.

Any future architecture must be scientifically distinct and separately frozen before truth.
