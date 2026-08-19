# OrbitTrace greedy M2D antichain v1

## Objective

Remove broad TopoModal ancestors when a more internally coherent descendant exists, without a size cap, target coordinate, activity interval, or fitted threshold.

## Frozen method

Use the unchanged radius=1.0 TopoModal hierarchy, minimum reportable support=4, annual-density bifiltration, and exact M2D score `M_2D(S)=(1/|S|)*sum_{B subseteq S}|B|*A(B)`.

For every hierarchy node with support >=4:

1. compute exact label-free M2D;
2. sort all nodes by M2D descending, then family hash ascending;
3. scan in that order and accept a node iff its event set is disjoint from every already accepted node;
4. reject every overlapping node (ancestor or descendant) after a higher-ranked node has been accepted.

Because a TopoModal hierarchy is laminar, the accepted set is a pairwise-disjoint antichain. A broad ancestor survives only if it outranks every overlapping descendant by M2D. No extra threshold or tunable parameter is introduced.

Final catalogue order is the same M2D-descending order used for packing.

## Development firewall

First test: exact frozen target-excluded GMN 2022/2023 sparse universes (d=128,1024; buckets 0..3), with solar longitude [20 deg,55 deg] removed before candidate construction and truth evaluation. OrbitTrace canonical IDs/coordinates/reveal outputs and SonotaCo are prohibited from method selection.

## Frozen promotion gates

Against immutable baseline M2D under the established PR #1377 comparator-capacity evaluator:

- Sugar-capacity mean macro-F1 and F1>0.5 recovery are not lower;
- HDBSCAN-capacity mean macro-F1 and recovery are not lower;
- d=128 and d=1024 mean macro-F1 and recovery are each not lower;
- still beats the frozen published-config Sugar and HDBSCAN comparators;
- mean, p90, and maximum selected-family member counts are all strictly lower than baseline M2D;
- at least one broad hierarchy node is rejected because of overlap with a higher-M2D accepted node;
- output candidates are pairwise disjoint;
- no post-result parameter search occurs.

If any structural gate fails before truth, truth remains unopened and v1 is frozen negative. If all structural gates pass, the sealed pretruth may be evaluated once against GMN truth. A GMN pass permits no-tuning transfer to the exact 29,246-event SonotaCo symmetric benchmark. OrbitTrace is characterized only after method-level promotion and is not used for tuning.