# OrbitTrace Local Renormalized Basin v1 — frozen protocol

## Scientific question

Can a second, strictly local density normalization split internally heterogeneous TopoModal terminal basins without using labels, target information, a new geometric scale, or a size threshold, while preserving the target-excluded GMN quality of promoted support-pruned M2D v1?

This test exists because the promoted support-pruned cut already recurses through every hierarchy node for which both children have support >=4. Therefore any remaining oversized selected *leaf* cannot be repaired by another parent-vs-child hierarchy cut. LRB v1 tests one new mechanism only: recompute density inside each already-selected terminal basin and perform one additional ToMATo pass at the inherited radius/support.

## Frozen method

Parent method: promoted M2D support-pruned cut v1.

Inherited constants, unchanged:
- physical embedding: exact frozen TopoModal embedding;
- Euclidean radius: 1.0;
- minimum support: 4 events;
- annual-density bifiltration and exact M2D formula unchanged;
- sparse GMN universes and candidate budgets unchanged;
- ranking primary key: exact M2D descending.

For each terminal basin S selected by support-pruned v1:
1. Restrict to the events in S.
2. Rebuild the radius-1 graph on S only.
3. Define local density rho_S(x)=deg_S(x)/|S|.
4. Run the same manual-graph ToMATo hierarchy and the exact promoted support-pruned terminal rule once on S.
5. If the local pass yields fewer than two reportable selected basins, retain S unchanged.
6. If it yields at least two reportable selected basins, replace S by those basins; local sub-support terminal pieces remain noise.
7. Do not recurse a second time. There is exactly one local refinement pass.

No parent and its local children coexist in the final catalogue.

For a locally refined child C of parent S in a panel of N events, its local modal contrast is converted back to the parent panel's density units by multiplying by |S|/N. This is an algebraic unit conversion because rho_S uses denominator |S| whereas the global density uses denominator N. Unrefined candidates retain their original global modal contrast.

Final deterministic ranking:
1. exact M2D descending;
2. globally-scaled modal contrast descending;
3. family hash ascending.

## No new fitted parameters

LRB v1 introduces no new radius, support threshold, candidate-size threshold, score weight, penalty coefficient, recursion depth search, route-specific rule, or target-informed cutoff. The local pass count is structurally fixed at exactly one.

## Development firewall

The method is constructed and ranked only on the same target-excluded GMN 2022/2023 sparse universes used by support-pruned v1. The protected solar-longitude interval [20 deg, 55 deg] is removed before candidate generation. OrbitTrace canonical IDs, the previously revealed rank-84/rank-82 families, their coordinates, their member counts, and exact target overlap are prohibited from method selection/evaluation.

The full candidate ranking must be sealed before GMN shower truth is opened. SonotaCo 2013/2014 truth is not used in GMN development.

## Binding GMN promotion gates

All gates are evaluated against the exact frozen support-pruned v1 ranking under PR #1377 comparator-capacity semantics (method[:k], capacity shortfall scored rather than padded or rejected).

LRB v1 promotes only if all are true:
1. mechanism active before truth: at least one support-pruned terminal basin is replaced by >=2 local reportable basins;
2. Sugar-route mean Hungarian macro-F1 >= support-pruned v1;
3. Sugar-route recovered F1>0.5 >= support-pruned v1;
4. HDBSCAN-route mean Hungarian macro-F1 >= support-pruned v1;
5. HDBSCAN-route recovered F1>0.5 >= support-pruned v1;
6. d=128 mean macro-F1 and recovery are both nonlower than support-pruned v1;
7. d=1024 mean macro-F1 and recovery are both nonlower than support-pruned v1;
8. the published-config Sugar superiority gate remains passed;
9. the published-config HDBSCAN superiority gate remains passed;
10. top-budget size-biased member burden sum(n_i^2)/sum(n_i) is strictly lower than support-pruned v1;
11. top-budget p90 member count is not higher than support-pruned v1;
12. top-budget maximum member count is strictly lower than support-pruned v1.

A valid failure freezes this exact LRB v1. No local-pass recursion, alternate radius/support, size gate, M2D weight, contrast weight, or threshold sweep is authorized as a rescue.

## Post-promotion sequence

Only if GMN passes:
1. evaluate the frozen method on the already-defined SonotaCo benchmark without retuning;
2. only if that transfer is scientifically acceptable, perform a post-promotion target-free protocol replay of the full 2022+2023 GMN SPORADIC catalogue;
3. any OrbitTrace exact-ID reveal remains separate and occurs only after the full ranking is sealed.

Because prior OrbitTrace reveals are already known historically, any later full-catalogue run is described as a post-development target-free protocol replay, not a pristine new blind discovery.
