# Dominant-Core Regrowth (DCR) v1

## Motivation and development status

BWM v1 established that the frozen persistence-weighted co-witness graph can sharply decontaminate support-pruned TopoModal families, but hard replacement fragmented true showers and collapsed recall. CMR v1 regrew every BWM seed by a strict weighted-majority rule and recovered some recall, but still underperformed the promoted support-pruned baseline. FOCR v1 then refined only extreme-size parents; it preserved more quality, but still lost too much recall. The frozen FOCR result therefore identifies **replacement of a multi-core parent**—not simply the number or size of refined parents—as the remaining failure mode.

DCR v1 uses a label-free distinction between a **core-plus-residual** decomposition and a genuinely multi-core decomposition. A support-pruned parent is eligible for refinement only when exactly one already-frozen BWM seed contains a strict majority of the parent's members. In that case DCR emits the already-frozen CMR v1 regrowth attached to that dominant seed. If no BWM seed has a strict majority, DCR retains the promoted support-pruned parent unchanged.

This method is designed after BWM/CMR/FOCR target-excluded GMN development results were observed. GMN 2022/2023 is therefore development evidence, not untouched validation. OrbitTrace protected `[20°,55°]` events/canonical IDs/coordinates, the previously revealed OrbitTrace family, SonotaCo truth, and external-survey truth remain prohibited from construction.

## Frozen selector

For each promoted support-pruned parent `P` inside each of the eight exact target-excluded GMN sparse panels:

1. Use the already-frozen BWM v1 seed communities assigned to `P`.
2. A seed `C` is dominant iff `2 * |C| > |P|`.
3. At most one disjoint BWM seed can satisfy this strict-majority rule.
4. If a dominant seed exists, emit the exact already-frozen CMR v1 regrowth associated with that seed.
5. Otherwise emit `P` unchanged.
6. Emit exactly one candidate per promoted support-pruned parent.
7. Recompute the unchanged exact M₂D score for the emitted membership and rank by exact M₂D descending, then membership hash.

The factor one-half is the logical strict-majority boundary; it is not fitted to labels, target size, OrbitTrace overlap, or a benchmark score. DCR introduces no new geometric scale, modularity search, affinity threshold, size cutoff, growth depth, score blend, or rescue parameter.

## Structural gate before GMN truth

The exact candidate catalogue is sealed before the evaluator opens GMN shower truth. It must:

- refine at least one parent;
- strictly reduce mean top-budget family size versus promoted support-pruned v1;
- strictly reduce p90 top-budget family size;
- strictly reduce maximum top-budget family size; and
- strictly reduce size-biased top-budget member burden.

If any structural gate fails, GMN truth is not opened.

## Binding GMN development evaluation

If the structural gate passes, reuse the exact byte-frozen BWM/PR #1377 evaluator and capacity semantics without modification:

- `k = len(published comparator clusters)` per panel/year/comparator;
- DCR uses the first `k` frozen DCR candidates;
- no padding;
- one-to-one Hungarian macro-F1 and `F1 > 0.5` recovery are unchanged.

All ten inherited quality gates remain binding: nonlower support-pruned macro-F1 and recovery on Sugar, HDBSCAN, d=128, and d=1024, plus preservation of the established published-configuration Sugar and HDBSCAN wins.

A GMN pass is only a development qualification. The exact frozen DCR method must transfer to a non-GMN endpoint before any generalization claim or full-GMN OrbitTrace characterization. No post-result majority alteration, seed-size rule, CMR change, M₂D change, or rescue sweep is authorized within DCR v1.
