# OrbitTrace support-cut recurrent-orphan completion v1 — zero-label structural protocol

## Scientific role
Prospective catalogue-architecture successor after support-resolved TopoModal and internal-2D-mass TopoModal showed substantially higher recovery/purity but lower MRR than recurrent-EOM, and recurrent-witness projection v1 passed every zero-label structural gate except complete parent witnessability.

No truth result for this orphan-completion catalogue has been accessed when this protocol is frozen.

This is not generic union, hard-slot fusion, or joint-slot permutation. A recurrent candidate can enter the output only when the entire support-resolved catalogue has **zero shared events** with it, meaning support-cut literally has no event-level representation of that recurrent family.

## Frozen label-free inputs
- support-resolved-cut prelabel: run `31961908008`, artifact `9267530845`, SHA-256 `4529eadd9ff93aae057f0a6fd5e0dd923f2300b7c6e01b74a0b7638e22da6de6`.
- target-excluded subset-universe prelabel: run `32037435314`, artifact `9291169452`, SHA-256 `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`.

Both inputs were frozen before their truth evaluations and record no target-region, SonotaCo, or protected-external access.

## Frozen catalogue rule
For each panel, let recurrent candidates `P_r` be in exact recurrent-EOM rank order and support-cut candidates `S_j` in exact native support-cut order.

Traverse recurrent candidates in order:
1. Compute exact event-intersection counts `|P_r ∩ S_j|` for all support candidates.
2. If the maximum count is positive, choose the support witness with maximum count; tie by smaller support `family_hash`. If that support row is not already emitted, emit it. If already emitted, the recurrent row is considered represented by that earlier output and emits nothing.
3. If **all** intersection counts are zero, emit `P_r` itself as a `recurrent_orphan`.
4. After every recurrent row has been processed, append every still-unemitted support candidate in its original native support-cut order.

Output source types are therefore only:
- `support_projection`: unchanged support-resolved candidate memberships;
- `recurrent_orphan`: unchanged recurrent-EOM membership with exactly zero overlap against every support-resolved candidate;
- appended unchanged support candidates.

No recurrent candidate with positive support overlap may survive as a recurrent row.

## Structural invariants
- support candidates are pairwise disjoint by the frozen support-resolved cut;
- recurrent-EOM candidates are required to reproduce pairwise disjointness;
- every recurrent orphan is required to have zero overlap with every support candidate;
- therefore the complete mixed catalogue must be pairwise disjoint.
- each recurrent input row must have a representation in the output at rank no greater than its own recurrent rank: an earlier/current support projection or its exact orphan row.

There is no Jaccard/F1 threshold, normalized overlap, distance, weight, score blend, quota, slot fraction, or fitted parameter.

## Panels / equal budgets
Exact frozen K values:
- d=128 buckets 0..3: `29,35,38,33`;
- d=1024 buckets 0..3: `8,5,6,9`.

## Stage 1 zero-label gate
No shower truth may be loaded. Serialize the complete output order before any later evaluation. All gates must pass:
1. `candidate_capacity_all_8`: output count >= K in all eight panels.
2. `global_pairwise_disjoint_all_8`: every pair of output memberships is disjoint.
3. `complete_parent_representation_all`: every recurrent candidate is mapped either to a support projection with positive exact overlap or to an exact zero-overlap orphan.
4. `topk_parent_rank_nonexpansion_all`: each of the first K recurrent rows has representation rank <= its recurrent rank.
5. `orphan_zero_support_overlap_all`: every retained recurrent orphan has intersection count zero with every support candidate.
6. `cross_scale_mean_not_lower_than_recurrent`: mean top-K fine→coarse membership coherence >= recurrent-EOM.
7. `cross_scale_nonlower_4_of_4`: top-K coherence >= recurrent-EOM in all four buckets.
8. `immutable_membership_budget_order_audit`.

Cross-scale coherence uses exact event memberships only: restrict coarse top-K memberships to the corresponding fine event universe, drop restricted supports below 4, deduplicate exact memberships, then mean each fine top-K candidate's best Jaccard to the restricted coarse list.

## Conditional Stage 2 truth endpoint
Only if all eight structural gates pass, freeze a separate evaluator against the exact serialized order before opening labels. Use the established ten-gate sparse-GMN promotion contract.

Fine d=1024: strict qualified-total gain; >=6/8 annual panels nonlower; MRR nonlower; precision nonlower; fragmentation nonhigher.

Coarse d=128: qualified total nonlower; >=6/8 annual panels nonlower; MRR nonlower; precision nonlower; fragmentation nonhigher.

All ten must pass. First technically valid result is binding.

## No-rescue rule
Structural failure closes this mechanism without truth. Valid truth failure closes it permanently. Forbidden follow-ups include overlap thresholds, normalized intersection, Jaccard/F1 witnesses, orphan quotas, partial orphan retention, rank fusion, source slots, global matching, alternate support-winner rules, internal-mass tie-breaks, changed append order, K changes, or relaxed gates.

## Firewall
Inclusive solar longitude `[20°,55°]` remains excluded upstream. Stage 1 accesses no shower truth. OrbitTrace target information/events, SonotaCo 2013/2014, ASFN/EFN event rows, AMOS, MAARSY, and DMS remain inaccessible. A conditional Stage 2 may access only target-excluded GMN 2022/2023 development truth.