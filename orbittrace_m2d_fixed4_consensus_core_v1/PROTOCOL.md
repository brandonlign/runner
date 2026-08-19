# OrbitTrace M2D x fixed4 consensus core v1

## Scientific question

Can the already-promoted support-resolved TopoModal + exact M2D discovery catalogue preserve its broad, high-recall envelopes while attaching a compact **independent-detector consensus core** defined only by the already-frozen fixed-4-degree anchored-quartet geometry?

This is deliberately not another TopoModal hierarchy cut, recurrence-radius variant, M2D retune, or ranking change. The parent M2D envelope membership and complete order remain immutable. fixed4 is used only as a second, independently motivated geometry/support view inside each already-existing M2D envelope.

## Frozen parent discovery layer

Exact target-excluded GMN fairness pretruth from PR #1377:

`8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5`

All parent candidate existence, memberships, M2D scores, ranks, comparator capacities and primary literature claims remain unchanged. The consensus core cannot create, merge, delete or rerank a discovery envelope.

## Frozen fixed4 corroboration layer

For each parent M2D envelope and each year separately:

1. Sort that envelope/year's event IDs lexicographically. If fewer than four events exist, the annual core is empty.
2. Treat each event once as an anchor.
3. Compute the exact frozen fixed4 anchor distance from that anchor to **every other event in the same M2D envelope/year**, using the immutable coverage-normalized fixed-4-degree geometry (`exact_anchor_distances`).
4. Select the three nearest other events by ascending exact distance with the sorted event-ID order providing the stable tie order.
5. Canonicalize the anchor + three neighbors as a four-ID set.
6. Count how many distinct anchors independently select each identical quartet.
7. A quartet is corroborated iff it is selected by at least **two anchors**, exactly the inherited fixed4 catalogue anchor-multiplicity floor.
8. The annual consensus core is the union of all events belonging to any corroborated quartet. The two annual cores are then unioned into the candidate's reportable consensus core.

No fixed4 calibration threshold, shower label, p-value, score cutoff, distance threshold, top-k search, family link, target coordinate, target ID or post-result parameter enters this rule. The exact fixed4 distance is used only to identify each anchor's nearest three neighbors; the only support requirement is the already-established two-anchor multiplicity.

The all-other-event exact search is an implementation strengthening of the frozen fixed4 nearest-neighbor operation: it removes shortlist approximation rather than changing the metric or neighbor count. No event outside the immutable M2D envelope is eligible for the core.

## Dual-output semantics

- **Primary discovery output:** exact parent M2D envelope and exact parent rank.
- **Consensus characterization output:** fixed4-corroborated subset of that envelope.

The primary discovery/literature benchmark is therefore mathematically unchanged by construction. The scientific question here is whether the secondary core is a useful high-purity representation of the same discoveries.

## Firewall

Development uses only the exact PR #1377 target-excluded GMN 2022/2023 sparse universes. Solar longitude `[20 deg,55 deg]` is absent before either geometry enters this method.

The complete consensus-core membership for every envelope in every sparse panel must be hash-frozen before known-shower truth is reconstructed. OrbitTrace canonical IDs, revealed M2D rank-84/rank-82 families, target-region rows, SonotaCo truth and external-survey truth are prohibited from construction or selection.

## Frozen utility evaluation

Use the unchanged annual Hungarian parent-envelope assignment from PR #1377 at each exact comparator capacity. The core is evaluated **only against the same shower assigned to the same parent envelope**; no core rematching is allowed for the primary utility gate.

For each comparator route separately (Sugar and HDBSCAN), collect every parent assignment with parent F1 > 0.5 across all available panels. The following are all required:

1. at least 20 parent-recovered assignments exist (nonvacuity);
2. at least 75% of those assignments have a nonempty consensus core in the scored year;
3. mean consensus-core precision is at least 0.80;
4. mean consensus-core precision is strictly higher than mean parent-envelope precision;
5. mean consensus-core F1 is at least 75% of the mean parent-envelope F1;
6. among assignments with nonempty cores, at least half have core precision no lower than parent precision.

The same summaries are also reported by denominator scale and year, but no post-result scale-specific exception is allowed.

A secondary rematched core catalogue evaluation is reported diagnostically only; it cannot rescue a failed same-discovery utility gate because the core is intended to characterize the parent discovery, not switch identities.

## Outcome boundary

A PASS authorizes exactly one frozen no-retuning SonotaCo transfer of the same dual-output architecture. Only if that transfer independently satisfies the same paired-utility logic may the exact frozen consensus rule be applied to the already-blind baseline M2D OrbitTrace candidate for exact-ID characterization.

A FAIL permanently closes this exact consensus rule. It does not authorize changing anchor multiplicity, using one-anchor quartets, adding a fixed4 score/calibration threshold, expanding outside the envelope, selecting only a best quartet/component, changing the nearest-neighbor count, or any target-informed rescue.