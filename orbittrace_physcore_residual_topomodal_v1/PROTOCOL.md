# OrbitTrace PhysCore-Residual TopoModal v1 — frozen protocol

## Scientific motivation

PhysCore-HDBSCAN v1 proved that a fixed meteor-physics membership regularizer improves the exact published 2025 catalogue-HDBSCAN method in both exposed SonotaCo years without losing any recovered shower. Its separate matched Sugar/D_SH characterization then exposed a different limitation: the published-HDBSCAN parent naturally proposes only about 10–12 families on those row universes, while Sugar/D_SH naturally propose 34–47. The deficit is therefore proposal capacity, not a reason to retune the successful PhysCore rule.

This successor combines only mechanisms that were independently frozen before this protocol:

1. exact published catalogue-HDBSCAN as the high-confidence proposal stage;
2. exact frozen PhysCore-HDBSCAN v1 membership regularization;
3. exact frozen fixed-scale TopoModal hierarchy as a residual sparse-stream proposal stage.

No existing method is retuned.

## Exact candidate construction

For each annual/pairwise row universe:

1. Start from the exact published-HDBSCAN parent output for that same row universe.
2. Apply the exact frozen PhysCore-HDBSCAN v1 rule. The PhysCore family count and family order remain exactly the parent HDBSCAN family count/order, with one refined family per parent family.
3. Let `A` be the union of all events retained by the refined PhysCore families.
4. Define the residual event universe `R = U \ A`, where `U` is the complete pairwise row universe.
5. Run the exact frozen TopoModal implementation from Git blob `752df8212ce601227f6e9170b0fe994ba06b515d`, unchanged, on `R` only. Adapt only field names: `lon = sun_lon`, `lat = ecl_lat`.
6. Final candidate order is deterministic concatenation:
   - all PhysCore families first, in exact frozen PhysCore/HDBSCAN order;
   - then every residual TopoModal family in the exact order returned by the frozen TopoModal source.
7. No candidate is removed, reranked, blended, thresholded, or deduplicated after this concatenation. Because residual TopoModal sees only `R`, its memberships are event-disjoint from all PhysCore memberships by construction.

There is no overlap threshold, fusion weight, quota, per-channel score normalization, cross-channel tie rule, or result-informed candidate selection.

## Frozen source identities

- PhysCore-HDBSCAN v1 direct PASS workflow: `31988198562`.
- PhysCore direct result artifact: `9274439445`.
- PhysCore matched-literature transfer/pretruth workflow: `31988628399`.
- PhysCore matched-literature pretruth artifact: `9274576168`.
- Frozen TopoModal source Git blob: `752df8212ce601227f6e9170b0fe994ba06b515d`.
- Exact published catalogue-HDBSCAN source SHA-256: `a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2`.

## Label-free activation gates

Before any new shower truth is opened:

- every source/output/row/comparator hash is frozen;
- the first `N_HDB` successor candidates on the original HDBSCAN row universe are exactly membership-identical and order-identical to the already-binding PhysCore direct candidates, where `N_HDB` is 11 (2013) and 9 (2014);
- every residual TopoModal family is a subset of `R` and therefore disjoint from the PhysCore accepted-event union;
- protected solar longitude `[20,55]` is absent;
- no truth-bearing field enters candidate generation;
- the natural successor candidate count is at least the frozen literature comparator budget in each Sugar/D_SH panel: 34/46/41/47 respectively.

If any capacity gate fails, the successor is a label-free structural failure and the truth stage is blocked. No threshold/order rescue is authorized.

## Binding literature-facing evaluation

### Published HDBSCAN

The already-binding direct PhysCore-HDBSCAN result transfers to this successor at the exact published-HDBSCAN natural reporting budget if and only if the pretruth prefix-equivalence gate passes, because the successor's first 11/9 candidates are then exactly the previously evaluated PhysCore candidates.

Those inherited exact direct results are:
- 2013: `0.1756351130` vs published HDBSCAN `0.1681717489`, recovered `10 vs 10`;
- 2014: `0.1688317479` vs `0.1568959558`, recovered `9 vs 9`.

No HDBSCAN truth is reopened to obtain those inherited panels.

### Sugar and D_SH

For each Sugar/D_SH year panel, let `B` be that literature comparator's already-frozen natural family count. Evaluate exactly the first `B` successor candidates against all `B` literature candidates using the exact established SonotaCo mapping and Hungarian one-to-one F1 semantics:

- eligible known showers have native mapped support >= 4;
- primary metric: macro-F1 over eligible known showers;
- secondary noninferiority condition: recovered known showers with assigned F1 > 0.5.

A panel is a WIN only if successor macro-F1 is strictly greater than the literature comparator and successor recovered count is at least the literature comparator count.

`PASS_PHYSCORE_RESIDUAL_TOPOMODAL_V1` requires:
- exact inherited published-HDBSCAN wins in both years via pretruth prefix equivalence; and
- four new Sugar/D_SH panel wins.

Anything else is `FAIL_PHYSCORE_RESIDUAL_TOPOMODAL_V1`.

## Closure rule

The first technically valid outcome is binding. A failure does not authorize changing the residual definition, TopoModal physical scale/radius/support/density/hierarchy/order, PhysCore rule, HDBSCAN settings, concatenation order, comparator budget, metrics, truth mapping, panel set, or pass criterion.

## Scientific role and firewall

SonotaCo 2013/2014 is `EXPOSED DEVELOPMENT ONLY`; this is not pristine external validation. Protected `[20°,55°]`, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.
