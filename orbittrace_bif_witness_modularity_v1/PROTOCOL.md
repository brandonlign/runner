# OrbitTrace Bifiltration Witness Modularity (BWM) v1 — frozen truth protocol

## Scientific question

Can the already-frozen annual-density bifiltration evidence be converted from a highly pure but redundant fragment catalogue into a **single disjoint representation inside each promoted support-pruned basin**, preserving known-shower recovery while sharply reducing broad-family contamination?

This is a separately preregistered representation/consolidation successor motivated by the binding annual-density bifiltration v1 result. That result is closed and is not being reranked or rescued: its frozen interpretation was that raw bifiltration fragments were very pure/early but repeatedly represented the same structures, so the remaining bottleneck was representation/consolidation. BWM v1 changes the representation architecture rather than changing the frozen fragment ranking.

## Development-status disclosure

BWM v1 was designed using **target-excluded, label-free GMN structural artifacts** only. Before this protocol was frozen, a label-free implementation prototype was used to verify that the construction is active and materially reduces top-budget family size on those development panels. Therefore those size reductions are **design-stage development evidence, not an independent validation endpoint**.

No GMN shower labels, OrbitTrace protected-region events/canonical IDs, SonotaCo truth, or external-survey truth were used to choose the rule below. The first scientific quality test after this freeze is the hidden GMN shower-label evaluation defined here.

## Frozen inputs

Parent representation:
- promoted support-pruned M2D v1 pretruth SHA-256 `57a6fd0fa680fb56b3d6a8a984682213e0235baadf14b27f241927b2dbb4b50f`;
- radius 1.0, support 4, target-excluded GMN 2022/2023 sparse universes and candidate budgets unchanged.

Internal witness evidence:
- frozen annual-density bifiltration GMN endpoint prelabel SHA-256 `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`;
- this binds the original zero-label bifiltration candidate freeze SHA-256 `63519bbd8a95b0bd5db0d0f5fdccbdb67b3f1dac0158529bb808f4c798170b0b`;
- each witness B has immutable event membership and positive persistence area A(B).

The protected inclusive solar-longitude interval `[20°,55°]` was removed before both frozen inputs were constructed.

## Frozen BWM construction

For each promoted support-pruned parent basin S independently:

1. Collect every frozen bifiltration witness B whose event set is a subset of S.
2. Let U be the union of those witness event sets.
3. If `|U| < 4` or no witness exists, retain S unchanged.
4. Otherwise construct a weighted undirected co-witness graph on U. For every witness B of size m and persistence area A(B), add

   `A(B) / (m - 1)`

   to every unordered pair of distinct events inside B.

   This normalization is fixed, not fitted. Each event in B receives total graph strength A(B) from that witness, and the witness contributes total degree mass `m*A(B)`, exactly the numerator used by the M2D internal-mass score.
5. Partition this weighted graph once using deterministic Clauset-Newman-Moore greedy modularity at the standard modularity resolution `gamma=1` (`networkx.algorithms.community.greedy_modularity_communities`, NetworkX 3.6.1). No resolution search, seed, requested cluster count, or target-informed threshold is allowed.
6. Communities with fewer than the inherited minimum support of 4 events are noise.
7. If no reportable community remains, retain S unchanged. Otherwise replace S by all reportable communities. The parent and its witness communities never coexist in the final catalogue. Events in S that never enter a frozen witness, plus discarded sub-support communities, are noise for this representation.
8. BWM is applied exactly once. There is no recursive modularity pass.

Because promoted support-pruned parents are pairwise disjoint, the final BWM communities are pairwise disjoint by construction.

## Frozen candidate score and ranking

For every final BWM candidate C, recompute the **unchanged exact M2D internal mass** from the same frozen bifiltration witnesses:

`M2D(C) = (1 / |C|) * sum_{B subseteq C} |B| * A(B)`.

No fragment outside C contributes.

Final deterministic order:
1. exact M2D descending;
2. membership SHA-256 ascending.

No member-count bonus/penalty, exponent, score blend, quota, overlap suppression, or route-specific rule is permitted.

## No new fitted parameters

BWM v1 introduces no fitted geometric scale, density threshold, persistence cutoff, candidate-size cutoff, score coefficient, exponent, modularity-resolution search, cluster-count target, or recursion-depth search. The only inherited support threshold is 4. Modularity uses its standard resolution 1 exactly once.

## Hidden GMN quality evaluation

Use the exact target-excluded GMN 2022/2023 universes and the exact frozen published-configuration Sugar/HDBSCAN comparator pretruth already used by PR #1377 and support-pruned v1.

Capacity semantics are exactly PR #1377:
- for each published comparator panel, `k = len(published comparator clusters)`;
- evaluate BWM as `BWM[:k]`;
- evaluate support-pruned v1 as `support_pruned[:k]`;
- candidate shortfall is allowed and scored naturally; never pad, reject, or alter k.

Use the exact existing annual Hungarian macro-F1 / precision / recall / recovered-F1>0.5 evaluator.

## Binding GMN promotion gates

BWM v1 promotes to frozen transfer testing only if **all** are true:
1. Sugar-route mean macro-F1 >= promoted support-pruned v1;
2. Sugar-route recovered F1>0.5 >= promoted support-pruned v1;
3. HDBSCAN-route mean macro-F1 >= promoted support-pruned v1;
4. HDBSCAN-route recovered F1>0.5 >= promoted support-pruned v1;
5. d=128 mean macro-F1 >= support-pruned v1;
6. d=128 recovered F1>0.5 >= support-pruned v1;
7. d=1024 mean macro-F1 >= support-pruned v1;
8. d=1024 recovered F1>0.5 >= support-pruned v1;
9. BWM still beats the published-config Sugar comparator in mean macro-F1 with nonlower recovered F1>0.5;
10. BWM still beats the published-config HDBSCAN comparator in mean macro-F1 with nonlower recovered F1>0.5.

The label-free design-stage size profile is recorded but cannot compensate for a failed quality gate.

PASS verdict:
`PASS_BIF_WITNESS_MODULARITY_V1_GMN_DEVELOPMENT`

Otherwise:
`FAIL_BIF_WITNESS_MODULARITY_V1_GMN_DEVELOPMENT`

A valid FAIL freezes exact BWM v1. Do not tune modularity resolution, pair-weight exponent, witness-area transform, support, fragment filter, member-size cutoff, or score blend after truth.

## Post-GMN sequence

Only after a GMN PASS:
1. run the exact frozen BWM method on the already-defined SonotaCo transfer benchmark without retuning;
2. compare against the fair tuned-HDBSCAN benchmark where technically applicable; do not substitute a published-config-only win for tuned-family superiority;
3. only after acceptable transfer may a full 2022+2023 GMN SPORADIC target-free protocol replay be run;
4. any OrbitTrace exact-ID reveal remains separate and occurs only after the full ranking is sealed.

Because OrbitTrace's prior rank-84/rank-82 reveals and the giant-leaf diagnosis are historically known, a later OrbitTrace replay is post-development target-free protocol evidence, **not** a pristine independent discovery claim.

## Firewall

Forbidden during BWM construction and pretruth:
- GMN shower labels;
- protected `[20°,55°]` events;
- OrbitTrace canonical IDs, coordinates, or revealed family membership;
- SonotaCo 2013/2014 truth;
- ASFN/EFN event-level data;
- AMOS, MAARSY, or DMS scientific data;
- post-result parameter search.
