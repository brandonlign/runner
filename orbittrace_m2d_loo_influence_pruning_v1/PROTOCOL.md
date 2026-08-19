# M₂D Leave-One-Out Influence Pruning (LOIP) v1

## Motivation and development status

The post-promotion extraction experiments establish two constraints on any successor to support-pruned TopoModal + M₂D:

1. BWM/CMR/FOCR/DCR/PADCR show that hard community/core substitution removes too many true shower members.
2. ECT v1 shows that the frozen co-witness structure contains genuine purity information, but its selected nested cores are still too aggressive: precision rises strongly while paired recall/F1 falls. A simple strict-majority retention guard was checked once on exposed GMN development and still did not recover the frozen F1 gate, so no retention-threshold sweep is authorized.

Repository history also contains an older dual-output core/halo lineage; current governance requires one final primary member set. LOIP therefore returns to a **single membership per detected support-pruned family** and changes only event-level membership, not the TopoModal hierarchy or discovery order.

LOIP is designed after target-excluded GMN 2022/2023 development results through ECT v1 were observed. GMN is exposed development evidence. OrbitTrace protected `[20°,55°]` events/canonical IDs/coordinates, the revealed target family, SonotaCo truth, and external-survey truth remain prohibited from construction.

## Frozen event rule

For a promoted support-pruned parent `P`, let its exact frozen M₂D witness set be the bifiltration components `B ⊆ P` used by the promoted score. Define

`A(P) = Σ_B |B| * persistence_area(B)`

so the unchanged flagship score is

`M₂D(P) = A(P) / |P|`.

For each event `v ∈ P`, define its exact witness-participation mass

`R(v;P) = Σ_{B ⊆ P, v ∈ B} |B| * persistence_area(B)`.

Deleting `v` alone gives

`M₂D(P \ {v}) = (A(P) - R(v;P)) / (|P|-1)`.

Therefore, algebraically and without a fitted cutoff,

`M₂D(P \ {v}) > M₂D(P)` iff `R(v;P) < M₂D(P)`.

LOIP v1 uses that identity directly:

1. Compute the exact parent M₂D witness catalogue and `M₂D(P)`.
2. Accumulate `R(v;P)` for every event from the same frozen witnesses.
3. Mark `v` as negative-influence iff `R(v;P) < M₂D(P)` using the frozen float accumulation order and a strict comparison.
4. Remove **all** negative-influence events simultaneously in one shot.
5. Do not recompute influence after removal. No removed or retained event can trigger a second pass.
6. Recompute the exact child M₂D only as a sealed structural diagnostic.
7. The output must retain inherited support `>=4`; otherwise pretruth fails closed rather than rescuing or padding the family.
8. Preserve the exact promoted support-pruned parent ordering and parent M₂D discovery score. Child M₂D cannot rerank families.

This is not a new heuristic score: it is the exact leave-one-out local-improvement condition implied by the already-promoted M₂D objective, expressed in one-pass form. There is no fitted affinity threshold, retention fraction, geometric scale, modularity search, hierarchy cut, size cap, score blend, growth depth, or target-derived parameter.

## Pretruth structural gate

The exact LOIP catalogue seals before hidden GMN shower truth. It must satisfy all of the following:

- mechanism active on at least one support-pruned parent;
- every output remains support `>=4`;
- every changed output has strictly larger recomputed child M₂D than its original parent after the simultaneous one-shot removals;
- mean top-budget family size strictly lower than support-pruned v1;
- p90 top-budget family size strictly lower;
- maximum top-budget family size strictly lower;
- size-biased top-budget member burden strictly lower.

Failure of any structural gate keeps shower truth closed.

## Binding target-excluded GMN development test

If pretruth passes, reuse the exact byte-frozen BWM/PR #1377 evaluator and comparator-capacity semantics:

- comparator capacity `k = len(published comparator clusters)` for each panel/year/comparator;
- evaluate the first `k` frozen LOIP candidates with no padding;
- same one-to-one Hungarian macro-F1 and `F1 > 0.5` recovery definitions;
- unchanged Sugar 2017, HDBSCAN 2025, d=128, and d=1024 routes.

Promotion requires all ten inherited support-pruned quality/literature gates:

- nonlower macro-F1 and `F1 > 0.5` recoveries on Sugar and HDBSCAN;
- nonlower macro-F1 and recoveries at d=128 and d=1024;
- preservation of the established published-configuration Sugar and HDBSCAN wins.

Because the remaining scientific objective is extraction purity, LOIP also requires **strictly higher macro precision than support-pruned v1 on both Sugar and HDBSCAN routes**. These are strict direction tests, not fitted numerical margins.

## Interpretation boundary

A GMN pass is development qualification only. The exact frozen LOIP method must transfer without retuning to the permanently designated SonotaCo validation/generalization stage before any full-GMN OrbitTrace characterization. Full-GMN OrbitTrace cannot tune LOIP and cannot retroactively become a new blind test because the target IDs were historically revealed.

A failure freezes exact LOIP v1. No epsilon, removal fraction, iterative deletion, top-N deletion, per-family rescue, child reranking, or influence-threshold sweep is authorized under this version.
