# OrbitTrace M2D recursive evidence cut v1

## Objective

Replace the support-only TopoModal frontier with a single disjoint hierarchy cut chosen by the already-defined label-free M2D evidence. The goal is to remove oversized merged families without adding a size cap, target coordinate, activity window, or fitted threshold.

## Frozen method

The physical TopoModal hierarchy is unchanged:

- physical embedding: frozen OrbitTrace TopoModal embedding;
- radius: 1.0;
- minimum reportable support: 4;
- full hierarchy: every ToMATo leaf/internal node and its exact member set;
- M2D formula: `M_2D(S)=(1/|S|)*sum_{B subseteq S}|B|*A(B)` with the same frozen annual-density bifiltration evidence;
- score tie-breaks do not affect the hierarchy cut; strict floating-point `>` is used.

The recursive evidence cut is deterministic on the hierarchy compressed to reportable (support >=4) nodes:

1. a reportable node with no reportable descendant child is emitted;
2. unreportable support <4 twigs are treated as noise and skipped when forming the compressed hierarchy;
3. if a reportable node has exactly one immediate reportable descendant child, recurse into that child;
4. if it has two immediate reportable descendant children, compare the exact M2D scores of the parent and the two children:
   - if `max(M2D(child_a), M2D(child_b)) > M2D(parent)`, recurse into **both** children;
   - otherwise emit the parent.

Thus no target branch can be cherry-picked: whenever evidence forces a split, both reportable branches remain eligible. The output is one pairwise-disjoint antichain/frontier of the hierarchy. Compressing sub-support twigs is exactly the support-pruned behavior, expressed without introducing another parameter.

Final selected families are ranked by unchanged M2D descending, then family hash ascending. Exact M2D ties are therefore resolved deterministically without adding a scientific score.

## Development firewall

The first development test uses exactly the target-excluded GMN 2022/2023 sparse universes already frozen for M2D literature fairness (d=128 and d=1024; buckets 0..3). Solar longitude [20 deg,55 deg] is excluded before candidate construction and truth evaluation. Canonical OrbitTrace IDs, OrbitTrace coordinates, the PR #1378 rank-84 family, and the support-pruned replay result are prohibited from method selection.

No new continuous or discrete tuning parameter exists in this method. No threshold/radius/support sweep is authorized after truth.

## Frozen GMN promotion gates

Compared against the immutable baseline M2D catalogue on the same panel and comparator capacities:

- mean macro-F1 is not lower on the Sugar-capacity route;
- recovered F1>0.5 is not lower on the Sugar-capacity route;
- mean macro-F1 is not lower on the HDBSCAN-capacity route;
- recovered F1>0.5 is not lower on the HDBSCAN-capacity route;
- d=128 mean macro-F1 and recovery are not lower;
- d=1024 mean macro-F1 and recovery are not lower;
- the method still beats the corresponding published-config Sugar and HDBSCAN comparators under the already-frozen fairness evaluator;
- mean selected-family member count is strictly lower than baseline M2D;
- p90 selected-family member count is strictly lower than baseline M2D;
- maximum selected-family member count is strictly lower than baseline M2D;
- the evidence rule must actually split at least one parent because a child has strictly higher M2D;
- candidates are pairwise disjoint and no post-result parameter search occurs.

A failure freezes this exact method as negative. A pass permits no-tuning transfer to the exact 29,246-event SonotaCo symmetric benchmark. Only after those method-level tests may the already-revealed OrbitTrace case be characterized, and that characterization cannot be called a new blind rediscovery.