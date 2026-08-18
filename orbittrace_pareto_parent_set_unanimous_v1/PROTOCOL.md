# OrbitTrace Pareto parent-set unanimous v1 — frozen protocol

## Status

**FROZEN BEFORE IMPLEMENTATION, BEFORE ANY ZERO-LABEL D=64 OUTCOME, AND BEFORE ANY D=64 SHOWER-TRUTH OUTCOME FOR THIS SUCCESSOR.**

This is one new target-excluded GMN successor motivated only by already-sealed results:

1. recurrent–TopoModal Pareto-prominence v1 passed its sparse d=1024/d=128 contract 10/10;
2. exact unique-parent translation to d=64 aborted pretruth because 8 retained TopoModal candidates overlapped more than one Recurrent-EOM parent;
3. overlap-barycenter Pareto v1 repaired that correspondence structurally and passed 12/12 pretruth gates, but binding truth failed 4/5 because zero-filled MRR decreased despite much higher recovery and precision;
4. the barycenter closure explicitly identifies the remaining legitimate mechanism class: represent multi-parent correspondence without collapsing it to a single scalar, while reducing exactly to the successful unique-parent Pareto relation when correspondence is unique.

The present successor does exactly that. It introduces no threshold, weight, parent selection, membership change, candidate deletion, source quota, or label-aware decision.

## 1. Firewall

Use only target-excluded GMN 2022+2023 development data. Inclusive solar longitude `[20.0,55.0]` remains inaccessible.

Forbidden throughout this experiment:

- OrbitTrace target information or target-region events;
- SonotaCo 2013/2014 scientific access;
- ASFN/EFN event-level access;
- AMOS scientific access;
- MAARSY or DMS scientific access;
- any truth-informed threshold, parent assignment, set reduction, rank rule, candidate budget, or post-result rescue.

## 2. Immutable scientific sources

Reuse exactly the same scientific source paths and constants used by overlap-barycenter v1:

- support-resolved TopoModal cut from `agent/orbittrace-topomodal-support-resolved-cut-v1`;
- TopoModal structural runner from `agent/orbittrace-topomodal-hierarchy-scale-v1`;
- promoted Recurrent-EOM parent runner `orbittrace_recurrent_eom_hdbscan_v1/run_development.py`;
- exact positive sparse Pareto prelabel from run `32077197154`, used only to prove singleton-case identity;
- exact target-excluded GMN source/runtime hashes and denominator-64 hash partition used by the frozen barycenter translation.

No source membership, modal contrast, Recurrent rank, event universe, D=64 bucket assignment, or equal budget K may change.

## 3. Candidate correspondence

For each d=64 panel, build the exact frozen support-resolved TopoModal candidate set and exact Recurrent-EOM parent catalogue.

Retain a TopoModal candidate iff it has positive exact-event overlap with at least one Recurrent parent. Preserve its full membership unchanged.

For retained candidate `s`, define the **complete corroborating-parent rank set**

`P(s) = sorted unique { r : TopoModal(s) overlaps Recurrent parent of rank r }`.

Also preserve the exact overlap counts only as provenance. They do not enter ranking.

There is no selected parent, best parent, overlap-weighted parent, Jaccard parent, barycenter, mean, minimum-as-score, maximum-as-score, or other scalar correspondence statistic.

## 4. Intrinsic TopoModal objective

Construct the exact original Pareto-prominence modal rank `M(s)` over all retained candidates:

1. descending `modal_contrast`;
2. ascending frozen `native_support_rank`;
3. ascending `family_hash`.

`M(s)` is one-indexed and must be a permutation `1..N`.

## 5. Set-valued recurrence dominance

For two distinct retained candidates `a,b`, say that **a unanimously precedes b in Recurrent evidence** iff

`max(P(a)) <= min(P(b))`.

This means every Recurrent parent corroborating `a` is no later than every Recurrent parent corroborating `b`. If the two parent-rank sets cross or overlap ambiguously, neither candidate receives an artificial scalar recurrence advantage from that ambiguity.

Define Pareto dominance:

`a` dominates `b` iff

1. `max(P(a)) <= min(P(b))`;
2. `M(a) <= M(b)`;
3. at least one of `max(P(a)) < min(P(b))` or `M(a) < M(b)` is strict.

Assign ordinary iterative nondominated layers exactly as in Pareto-prominence v1.

### Singleton identity

If every retained candidate has exactly one corroborating parent, `P(s)={R(s)}` and the dominance rule becomes exactly

`R(a)<=R(b) and M(a)<=M(b)` with at least one strict inequality,

which is the scientific relation of the successful sparse Pareto-prominence v1.

Therefore all eight frozen d=1024/d=128 positive sparse orders must reproduce exactly before d=64 truth may open.

## 6. Final deterministic order

Order all retained candidates by:

1. ascending Pareto layer `L(s)`;
2. ascending modal-prominence rank `M(s)`;
3. lexicographic ascending full tuple `P(s)`;
4. ascending frozen `native_support_rank`;
5. ascending `family_hash`.

No scalar parent summary is used even as a tie key. For singleton `P(s)=(R(s),)`, this final order reduces exactly to the successful sparse Pareto final order.

All retained candidates remain exactly once. Membership remains unchanged. The first K candidates form the equal-budget successor catalogue, where K is exactly the Recurrent comparator catalogue size in that panel.

## 7. Zero-label authorization gates

Before shower truth is opened, freeze and SHA-seal the complete d=64 prelabel. All gates are mandatory:

1. exact firewall, source hashes, denominator 64, four buckets, and 738,682-event target-excluded universe reproduce;
2. support-resolved TopoModal candidates are pairwise disjoint;
3. Recurrent parents are pairwise disjoint and ranked `1..K`;
4. every positive-overlap TopoModal candidate is retained and every zero-overlap candidate is discarded;
5. every retained membership is unchanged byte-for-byte;
6. every `P(s)` is sorted, unique, nonempty, and exactly matches all positive Recurrent overlaps; overlap counts are positive and aligned;
7. modal-prominence rank is a permutation `1..N`;
8. set-valued Pareto layers satisfy the frozen unanimous-dominance relation;
9. final order is a deterministic permutation and contains no scalar parent correspondence field used by ranking;
10. candidate capacity is at least K in all four d=64 panels;
11. genuine multi-parent correspondence is present and the set-valued order differs from the frozen barycenter order in at least one d=64 panel;
12. all eight frozen sparse d=1024/d=128 Pareto-prominence orders reproduce exactly.

Only `PASS_PARETO_PARENT_SET_UNANIMOUS_V1_PRETRUTH` authorizes shower truth.

A pretruth failure closes this exact rule without truth access.

## 8. Truth semantics and binding promotion contract

Use exactly the same target-excluded d=64 truth runtime, annual eligibility, positive-match semantics, equal budgets, and metric definitions as overlap-barycenter v1.

Historical conditional MRR is diagnostic only. The binding retrieval metric is zero-filled eligible-query MRR.

Across the same eight annual bucket-year panels, aggregate exactly as barycenter v1. All five gates are mandatory:

1. total qualified recovery is not lower than Recurrent-EOM;
2. qualified recovery is nonlower in at least 6/8 annual panels;
3. mean zero-filled eligible-query MRR is not lower than Recurrent-EOM;
4. mean top-100 dominant precision is not lower than Recurrent-EOM;
5. mean median top-500 fragmentation is not higher than Recurrent-EOM.

Return exactly one binding verdict:

- `PASS_PARETO_PARENT_SET_UNANIMOUS_V1`, or
- `FAIL_PARETO_PARENT_SET_UNANIMOUS_V1`.

The first technically valid truth execution is binding.

## 9. Closure

A PASS authorizes only a separately frozen denser/full-GMN translation and, only after an internal promotion, a separately frozen SonotaCo comparison. It does not authorize protected-target or pristine-external access.

A valid FAIL permanently closes this exact unanimous parent-set dominance architecture. No rescue by best/worst parent selection, parent-set quantiles, interval midpoint/width, overlap weighting, Jaccard, set-size penalties, epsilon/relaxed dominance, alternative set order, crowding distance, within-layer reversal, budget/rank windows, thresholds, or post-result transforms is authorized.
