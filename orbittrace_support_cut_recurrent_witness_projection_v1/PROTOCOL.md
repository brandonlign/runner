# OrbitTrace support-cut recurrent-witness projection v1 — zero-label structural protocol

## Scientific status
This is a prospective **catalogue-architecture** successor defined after two relevant truth results are already known: support-resolved TopoModal and internal-2D-mass TopoModal both materially improve recovery/purity over recurrent-EOM but fail their MRR promotion gates. Those constituent results motivate the architecture, but **no truth evaluation of the witness-projection catalogue has been performed or inspected when this protocol is frozen**.

The mechanism is intentionally not a new scalar score, weighted rank fusion, source-slot rule, candidate union, or overlap-threshold search. The catalogue contains only the already-frozen pairwise-disjoint support-resolved candidates. Recurrent-EOM contributes only a deterministic ordering witness.

## Frozen label-free inputs
1. TopoModal support-resolved-cut v1 prelabel:
   - binding run `31961908008`
   - artifact `9267530845`
   - `TOPOMODAL_SUPPORT_RESOLVED_CUT_V1_PRELABEL.json` SHA-256 `4529eadd9ff93aae057f0a6fd5e0dd923f2300b7c6e01b74a0b7638e22da6de6`
   - contains all eight support-cut candidate lists and recurrent-EOM comparator lists/budgets before shower truth.
2. Annual-density bifiltration GMN ranking prelabel, used **only for the immutable full subset event universes needed by the cross-scale structural diagnostic**:
   - run `32037435314`
   - artifact `9291169452`
   - `BIFILTRATION_GMN_RANKING_V1_PRELABEL.json` SHA-256 `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`

Both artifacts record `shower_truth_used=false`, no OrbitTrace target access, no SonotaCo access, and no protected external access.

## Candidate universe — unchanged
For every deterministic sparse GMN panel, use the **complete support-resolved-cut candidate set unchanged**. No member is added, removed, merged, split, or reassigned. This preserves its pairwise-disjoint candidate memberships and candidate capacity.

The recurrent-EOM candidate set is not part of the output catalogue.

## Sole new mechanism: recurrent witness projection
Let recurrent candidates be `P_1, P_2, ...` in their already-frozen recurrent-EOM order. Let support-cut candidates be `S_1, S_2, ...` in their already-frozen native support-cut order.

Traverse recurrent candidates in order. For each recurrent candidate `P_r`:

1. Compute the exact event intersection count `|P_r ∩ S|` with every support-cut candidate `S`.
2. If all counts are zero, `P_r` has no witness and emits nothing.
3. Otherwise choose the unique witness target by:
   - maximum exact intersection count;
   - if tied, lexicographically smaller support-cut `family_hash`.
4. If that support candidate has not already been emitted, emit it immediately; if it was emitted by an earlier recurrent candidate, emit nothing.

After the recurrent list is exhausted, append every still-unemitted support-cut candidate in its **original frozen support-cut order**.

This final acceptance sequence is the complete successor catalogue order.

### Important consequences
- There is no Jaccard/F1/containment threshold.
- There is no nearest-distance parameter.
- There is no score or rank averaging.
- Recurrent candidates never occupy output slots and never coexist with support-cut candidates.
- Multiple recurrent families may witness the same disjoint support candidate; duplicate witnesses collapse naturally and free earlier catalogue positions for later/support-only candidates.
- For every emitted witnessed support candidate, its successor rank must be no greater than the rank of its earliest recurrent witness. This rank-nonexpansion property is an integrity invariant of the architecture.

No alternate intersection normalization, reciprocal-overlap rule, majority requirement, minimum overlap, global matching optimization, or secondary witness score is authorized.

## Deterministic panels and budgets
Use exactly the eight frozen target-excluded panels:
- d=128, buckets 0..3, K=`29,35,38,33`;
- d=1024, buckets 0..3, K=`8,5,6,9`.

K is the exact stored recurrent-EOM candidate count/budget in each panel.

## Stage 1 — zero-label structural gate
No shower labels may be loaded. For each panel, construct and serialize the complete witness-projection order and audit:

1. `candidate_capacity_all_8`: projected catalogue count >= K in all eight panels.
2. `pairwise_disjoint_all_8`: output memberships retain the support-cut pairwise-disjoint property.
3. `topk_parent_witnessable_all_8`: every recurrent candidate in the first K positions has positive intersection with at least one support-cut candidate. This is required because the architecture is intended to structurally protect the parent catalogue's early evidence, not merely append a recovery reservoir.
4. `witness_rank_nonexpansion_all`: every support candidate emitted by a recurrent witness appears at successor rank <= its earliest recurrent witness rank.
5. `cross_scale_mean_not_lower_than_recurrent`: across the four deterministic buckets, mean top-K fine-to-coarse membership coherence is >= recurrent-EOM's mean.
6. `cross_scale_nonlower_4_of_4`: projected top-K coherence is >= recurrent-EOM in all four buckets.
7. `immutable_membership_budget_order_audit`: input memberships, recurrent order, native support order, subset universes, and K values reproduce the frozen artifacts exactly.

Cross-scale coherence is label-free: restrict each d=128 top-K membership to the corresponding d=1024 event universe, drop restricted supports below 4, deduplicate exact memberships, and compute each fine top-K candidate's best Jaccard to the restricted coarse list; bucket score is the unweighted mean.

## Stage 2 — conditional first truth endpoint
If and only if all Stage-1 gates pass, freeze a separate evaluator against the exact serialized witness-projection prelabel before opening labels. Use the same equal-budget K and the same ten recovery/MRR/precision/fragmentation promotion gates as the support-cut sparse-GMN successors:

Fine d=1024:
1. qualified total strictly greater than recurrent-EOM;
2. qualified nonlower in >=6/8 annual panels;
3. mean MRR not lower;
4. mean top-100 dominant precision not lower;
5. mean fragmentation not higher.

Coarse d=128:
6. qualified total not lower;
7. qualified nonlower in >=6/8 annual panels;
8. mean MRR not lower;
9. mean top-100 dominant precision not lower;
10. mean fragmentation not higher.

All ten must pass. The first technically valid truth result is binding.

## No-rescue rule
A Stage-1 failure closes recurrent-witness projection v1 without truth. A valid Stage-2 failure closes the architecture. No normalized-overlap variant, Jaccard/F1 witness, reciprocal assignment, global bipartite matching, overlap threshold, witness quota, rank fusion, slot preservation, internal-mass/modal-contrast blend, alternative append order, K change, or gate change is authorized from the outcome.

## Firewall
The inherited inclusive solar-longitude exclusion `[20°,55°]` remains in force. Stage 1 may access no shower labels. OrbitTrace target information/events, SonotaCo 2013/2014, ASFN/EFN event-level data, AMOS, MAARSY, and DMS remain inaccessible. A conditional Stage 2 may access only target-excluded GMN 2022/2023 development truth.