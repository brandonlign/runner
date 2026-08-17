# OrbitTrace support-cut × bifiltration bridge v1 — zero-label structural protocol

## Scientific role
Prospective architecture combining two independently frozen mechanisms whose known failure modes are complementary:
- topomodal support-resolved cut v1 produced a pairwise-disjoint, high-recovery/high-purity candidate set with fragmentation 1.0, but its native modal-contrast ordering failed MRR;
- annual-density bifiltration v1 produced strong cross-scale structure and persistence-area ordering with high MRR/purity, but its standalone catalogue was dominated by nested redundant candidates and lost coverage.

This is **not** a post-hoc score blend or a rerun of either closed method. Candidate extraction comes only from the already-frozen support-resolved cut; annual-density bifiltration is used only as independent recurrence evidence when an **exact event-membership identity** exists between the two constructions.

## Frozen label-free inputs
1. Support-resolved cut artifact `9267530845`, binding run `31961908008`.
   - `TOPOMODAL_SUPPORT_RESOLVED_CUT_V1_PRELABEL.json` SHA-256 `4529eadd9ff93aae057f0a6fd5e0dd923f2300b7c6e01b74a0b7638e22da6de6`.
   - Scientific role `PRELABEL_TOPOMODAL_SUPPORT_RESOLVED_CUT_V1`.
   - Contains all eight disjoint successor candidate lists and recurrent-EOM budgets before truth.
2. Bifiltration prelabel artifact `9291169452`, run `32037435314`.
   - `BIFILTRATION_GMN_RANKING_V1_PRELABEL.json` SHA-256 `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`.
   - Contains the complete bifiltration candidate lists in frozen persistence-area order before truth.

Both inputs record no target information and no shower truth in candidate construction.

## One new mechanism
For each frozen GMN subset:
1. Take the complete support-resolved cut candidate set unchanged.
2. Build an exact-membership lookup over the complete bifiltration candidate set using the sorted tuple of event IDs as the key.
3. A support-cut candidate is **bridge-eligible** if and only if its event-ID set exactly equals one bifiltration candidate membership. No Jaccard/overlap tolerance, containment substitution, nearest neighbor, or approximate matching is allowed.
4. Assign an eligible support-cut candidate the already-frozen `persistence_area` of that exact bifiltration membership.
5. The prospective bridge catalogue consists only of exact-matched support-cut candidates, ordered by `persistence_area desc`, then `member_count desc`, then the support-cut `family_hash` ascending.

No modal-contrast blend or fallback is allowed. An unmatched support-cut candidate is not given an inferred bifiltration score.

## Zero-label structural gates
All must pass before any truth endpoint is allowed:
1. `exact_match_capacity_all_8`: exact-matched support-cut candidates >= recurrent-EOM budget K in all eight subsets.
2. `pairwise_disjoint_all_8`: bridge candidates preserve the support-cut pairwise-disjoint property in all eight subsets.
3. `topk_unique_event_coverage_nonzero_all_8`: the first K bridge candidates cover at least one event in every panel (sanity gate; capacity plus support floor should imply this).
4. `cross_scale_mean_not_lower_than_recurrent`: using only event memberships, mean best-Jaccard coherence between d=1024 and d=128 top-K bridge catalogues is at least recurrent-EOM's corresponding mean.
5. `cross_scale_nonlower_at_least_3_of_4`: bridge coherence is nonlower than recurrent in at least three of four buckets.

Cross-scale comparison restricts coarse candidates to the fine event universe, drops restricted supports below 4, deduplicates exact memberships, and computes the unweighted mean best Jaccard for fine top-K candidates.

## Future truth contract if structurally authorized
If and only if all five zero-label gates pass, freeze a separate target-excluded GMN truth endpoint using exactly the bridge-eligible candidate set and exact persistence-area order above. Use the same equal-budget K and the same ten recovery/MRR/precision/fragmentation gates as the prior sparse-GMN successor tests. No parameter or ordering change is permitted after this structural result.

## Stop/no-rescue rule
If exact membership does not provide K candidates in every panel, or coherence gates fail, close this bridge. Do not add approximate overlap matching, containment matching, a nearest bifiltration candidate, modal-contrast fallback, area/contrast blend, quota, weight, exponent, or relaxed gate.

## Firewall
No shower truth is permitted in this structural workflow. No OrbitTrace target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, or DMS may be accessed.