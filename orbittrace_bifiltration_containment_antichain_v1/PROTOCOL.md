# OrbitTrace bifiltration containment-antichain v1 — zero-label structural protocol

## Scientific role
Prospective zero-label structural successor to annual-density bifiltration v1. This experiment is motivated by the binding GMN persistence-area ranking failure: persistence area produced high purity/MRR but severe nested fragmentation and poor shower coverage. No successor truth result has been viewed when this protocol is frozen.

## Frozen inputs
- Immutable bifiltration GMN prelabel artifact: `9291169452` from run `32037435314`.
- `BIFILTRATION_GMN_RANKING_V1_PRELABEL.json` SHA-256: `95f8a57718a30b2c7e85016d505276d72cccb9e4ac1d6eb29f13067efc73dd0c`.
- That prelabel contains the eight target-excluded GMN 2022/2023 subset universes, the complete recurrent-EOM comparator lists/budgets, and the complete bifiltration candidate lists in the already-frozen order `(persistence_area desc, member_count desc, family_hash asc)`.
- It contains no shower labels and records `shower_truth_used=false`.

## One new mechanism
Treat the frozen bifiltration candidates in each subset as a finite poset under **strict event-set containment**. Traverse candidates in the already-frozen persistence-area order. Accept a candidate if and only if it is incomparable by strict containment with every previously accepted candidate; otherwise reject it.

Equivalently, for candidate event set `A` and each already-selected set `B`, reject if `A ⊂ B` or `B ⊂ A`. Exact equality cannot occur because memberships were already deduplicated.

This defines a deterministic **persistence-priority containment antichain**. It introduces:
- no overlap/Jaccard threshold;
- no new score or fitted weight;
- no label-derived parameter;
- no change to candidate membership, bifiltration construction, support floor, radius, annual-density coordinates, persistence area, or tie breaks.

If later authorized for truth evaluation, its catalogue order is exactly the acceptance order above. No re-ranking is permitted.

## Zero-label diagnostics
For each of the eight frozen subsets (`d ∈ {128,1024}`, bucket `0..3`):
1. Verify source SHA, schemas, firewalls, candidate membership hashes/order, and recurrent budget `K`.
2. Construct the containment antichain over the complete bifiltration candidate list.
3. Require the selected list to be pairwise incomparable by strict containment.
4. Compare the first `K` antichain candidates with the first `K` raw persistence-area candidates using only event IDs:
   - selected candidate capacity;
   - strict-containment pair count;
   - number/fraction of unique subset events covered by the top `K` candidates.
5. For each bucket, compare coarse (`d=128`) and fine (`d=1024`) top-`K` catalogues. Restrict each coarse candidate to the fine event universe, drop supports below 4, deduplicate memberships, then compute for every fine candidate the best Jaccard against the restricted coarse list. Record the unweighted mean best Jaccard for the antichain and for recurrent-EOM.

## Frozen structural gates
All must pass:
1. `capacity_all_8`: antichain candidate count is at least recurrent budget `K` in all eight subsets.
2. `zero_nested_topk_all_8`: the first `K` antichain candidates contain zero strict-containment pairs in all eight subsets.
3. `topk_event_coverage_nonlower_all_8`: top-`K` antichain unique-event coverage is not lower than raw persistence-area top-`K` coverage in every subset.
4. `topk_event_coverage_strict_pooled`: pooled top-`K` unique-event coverage across the eight panels is strictly greater than raw persistence-area ordering.
5. `cross_scale_mean_not_lower_than_recurrent`: mean of the four bucketwise antichain cross-scale Jaccards is at least the corresponding recurrent-EOM mean.
6. `cross_scale_nonlower_at_least_3_of_4`: antichain cross-scale Jaccard is at least recurrent-EOM in at least three of four buckets.

The gates are intentionally label-free and target the exact failure mode—nested redundancy—without allowing the previous truth result to choose an overlap threshold or a new ranking score.

## Stop rule
If any structural gate fails, close containment-antichain v1. Do not change containment to a Jaccard/overlap threshold, quota, lineage definition, persistence-area exponent, support multiplier, or alternative greedy order.

If all structural gates pass, freeze a separate target-excluded GMN truth endpoint before opening labels. That endpoint must use the exact antichain order and the same recovery/MRR/precision/fragmentation promotion contract used by the previous sparse GMN ranking tests.

## Firewall
No shower labels are permitted in this workflow. No OrbitTrace target-region events/information, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, or DMS are permitted. The inclusive protected solar-longitude interval `[20°,55°]` remains excluded by the inherited prelabel.