# OrbitTrace Recurrence-Bottleneck TopoModal (RBT) v1 — frozen protocol

## Scientific question

Can the giant-family failure of pooled-density TopoModal be reduced by defining the mode field from **simultaneous annual support** rather than pooled support, without introducing a fitted scale or threshold?

The motivating structural fact is that the post-promotion support-pruned OrbitTrace replay still placed all 18 canonical 2022/2023 members inside a 1,708-event ToMATo **leaf**. Another parent/child hierarchy cut therefore cannot fix the failure. Annual-density bifiltration showed that keeping the 2022 and 2023 density fields separate produces very pure recurrent fragments, but its 2D threshold catalogue over-fragmented repeated structures. RBT v1 collapses those two annual density coordinates *before* topology is constructed, using their pointwise bottleneck (minimum) as one scalar recurrence field.

No OrbitTrace protected-region events/canonical IDs or coordinates enter RBT construction or parameter choice.

## Frozen construction

Use the exact target-excluded GMN 2022/2023 sparse universes already frozen for support-pruned M2D v1: denominators 128 and 1024, buckets 0..3, protected inclusive solar-longitude interval `[20°,55°]` removed before all candidate construction.

Inherited unchanged:
- six-dimensional physical embedding from fixed-scale TopoModal;
- Euclidean radius `1.0`;
- minimum support `4`;
- exact event universes and candidate budgets;
- exact annual-density bifiltration components used by M2D;
- exact M2D formula and annual Hungarian evaluator.

For one sparse panel containing `n22` 2022 events and `n23` 2023 events:
1. Build the exact radius-1 graph used by fixed-scale TopoModal.
2. For every event x, count radius-neighborhood events from each year (including x itself in its own year exactly as in the frozen annual-density bifiltration construction): `d22(x)` and `d23(x)`.
3. Define normalized annual densities
   - `rho22(x)=d22(x)/n22`
   - `rho23(x)=d23(x)/n23`.
4. Define the recurrence-bottleneck scalar field
   - `rho_RBT(x)=min(rho22(x), rho23(x))`.

This is a fixed logical-AND recurrence operator: density is limited by the less-supported year. There is no mixing coefficient, exponent, floor, pseudocount, smoothing constant, or fitted threshold.

5. Run `gudhi.clustering.tomato.Tomato(graph_type="manual", density_type="manual")` on the unchanged radius graph with `rho_RBT` as weights.
6. Reconstruct the exact ToMATo hierarchy and apply the already-promoted support-pruned terminal rule unchanged:
   - recurse if both immediate children have support >=4;
   - if exactly one child has support >=4, discard the sub-support child as noise and recurse into the reportable child;
   - if both children are sub-support but their parent has support >=4, retain the parent;
   - terminal sub-support pieces are noise.
7. The resulting selected candidates are pairwise disjoint. No parent and descendant coexist.

Zero-valued bottleneck densities are allowed and are not removed or offset. They represent events with no radius-neighborhood support from at least one year and remain part of the same fixed graph; no additional zero-density cutoff is introduced.

## Frozen score and ranking

Every RBT candidate C receives the unchanged exact M2D score from the frozen annual-density bifiltration components:

`M2D(C) = (1/|C|) * sum_{B subseteq C} |B| * A(B)`.

Final deterministic ranking:
1. exact M2D descending;
2. RBT modal contrast descending;
3. membership hash ascending.

No size bonus/penalty, overlap suppression, quota, score blend, route-specific rule, or target-informed tie break is allowed.

## No fitted parameters

RBT v1 introduces no new radius, support threshold, density threshold, annual mixing coefficient, exponent, persistence cutoff, member-size cutoff, score coefficient, recursion search, or candidate-budget change. The annual bottleneck is exactly `min`.

## Pretruth structural gate

The complete RBT ranking is sealed before GMN shower labels are opened. Before truth, compare its frozen top-budget size profile with promoted support-pruned v1 on the same eight panels.

Truth may be opened only if all are true:
1. RBT differs structurally from support-pruned v1 on at least one panel;
2. top-budget size-biased member burden is strictly lower than support-pruned v1;
3. top-budget p90 member count is not higher;
4. top-budget maximum member count is strictly lower.

If any structural gate fails, freeze exact RBT v1 as a zero-label no-go and do not open GMN shower truth.

## Binding GMN quality gates

If structural gates pass, use exact PR #1377 comparator-capacity semantics:
- for each published comparator panel, `k = len(published comparator clusters)`;
- evaluate RBT as `RBT[:k]`;
- evaluate support-pruned v1 as `support_pruned[:k]`;
- shortfall is allowed and scored naturally; never pad or reject.

RBT promotes only if all are true:
1. Sugar-route mean macro-F1 >= support-pruned v1;
2. Sugar-route recovered F1>0.5 >= support-pruned v1;
3. HDBSCAN-route mean macro-F1 >= support-pruned v1;
4. HDBSCAN-route recovered F1>0.5 >= support-pruned v1;
5. d=128 mean macro-F1 and recovered F1>0.5 are both nonlower;
6. d=1024 mean macro-F1 and recovered F1>0.5 are both nonlower;
7. RBT still beats the published-config Sugar comparator in mean macro-F1 with nonlower recovered F1>0.5;
8. RBT still beats the published-config HDBSCAN comparator in mean macro-F1 with nonlower recovered F1>0.5.

PASS: `PASS_RECURRENCE_BOTTLENECK_TOPOMODAL_V1_GMN_DEVELOPMENT`.
Otherwise: `FAIL_RECURRENCE_BOTTLENECK_TOPOMODAL_V1_GMN_DEVELOPMENT`.

A valid failure freezes exact RBT v1. No replacement of `min` by harmonic/geometric mean, annual weights, pseudocount, density floor, radius/support sweep, or post-truth score tuning is authorized as a rescue.

## Post-promotion sequence

Only after GMN PASS:
1. run the frozen method on the already-defined SonotaCo transfer benchmark without retuning;
2. evaluate against the fair symmetric tuned-HDBSCAN benchmark where technically applicable; a published-config-only win is insufficient for the user's algorithm-superiority goal;
3. only after acceptable transfer may a full 2022+2023 GMN SPORADIC target-free protocol replay be run;
4. OrbitTrace exact-ID reveal remains separate and occurs only after the full ranking is sealed.

Because prior OrbitTrace reveals are already historically known, any later replay is post-development target-free protocol evidence, not a pristine new blind-discovery claim.

## Firewall

Forbidden before the RBT pretruth is sealed:
- GMN shower labels;
- protected `[20°,55°]` events;
- OrbitTrace canonical IDs, target coordinates, or revealed family membership;
- SonotaCo 2013/2014 truth;
- ASFN/EFN event-level data;
- AMOS, MAARSY, or DMS scientific data;
- post-result parameter search.
