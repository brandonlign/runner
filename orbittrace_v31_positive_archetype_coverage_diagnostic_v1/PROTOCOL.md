# OrbitTrace v31 positive-reference archetype coverage diagnostic

## Role

Post-result exposed-SonotaCo diagnostic only after #1050/#1053 localized the remaining HDB failure to tiny fixed-budget shower-set selection, while v36 and v37 rejected two local-geometry explanations (distance-scale normalization and five-fold reference starvation).

This diagnostic asks one narrower question before any new successor is selected:

> Does the frozen v31 HDB top-budget set spend multiple slots on candidates supported by the same learned annual-positive reference archetype pair, while recoverable missed shower groups often point to positive-reference archetype pairs not represented in the selected set?

If so, positive-reference archetype coverage is a concrete set-selection mechanism worth separately freezing. If not, it is rejected as a development direction. This diagnostic itself must not evaluate a new candidate order, selector, literature score, fusion, cutoff, or replacement rule.

## Frozen computation

Reproduce exact v31 from the immutable #950 payload:

- 71D features and fixed family memberships;
- shared deterministic five-fold strict-whole-shower OOF groups across Sugar and HDBSCAN;
- fold-training z-score over all 71 dimensions;
- annual positive definition `F1_y > 0.5`;
- ordinary Euclidean `k=1` nearest annual-positive and nearest annual-nonpositive references;
- annual margin `d_nonpositive-d_positive`;
- annual `min`;
- exact #839 diversity (`lambda=0.8`, `scale=1.0`);
- exact equal rank-sum with frozen v19.

For every held-out family and each year, in addition to the unchanged margin, record the identity and strict group of the exact nearest annual-positive training reference. The ordered pair

`(nearest_positive_group_2013, nearest_positive_group_2014)`

is the family's **positive-reference archetype signature**. No collapsing, weighting, distance threshold, similarity threshold, label hierarchy, or alternate signature is considered.

## HDB fixed-budget summaries

For the exact v31 HDB fused order and each frozen literature budget (2013 budget 11; 2014 budget 9), report only:

1. the top-budget family IDs and their archetype signatures;
2. number of unique signatures and duplicate slots;
3. collision sets: signatures represented by more than one selected family;
4. for every strict shower group with at least one fixed candidate having annual `F1>0.5`, the earliest such candidate in exact v31 fused order;
5. among recoverable-but-missed groups, whether that representative's ordered archetype signature is absent from the current top-budget signature set;
6. counts/fractions of missed recoverable groups with novel versus already-covered signatures, plus descriptive fused-rank medians.

Truth may be used only to define annual recoverability and surfaced/missed diagnostic categories. It may not enter the archetype signature or any new ordering.

## Required controls

The run is diagnostic-valid only if exact v31 reproduces:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDBSCAN 2013 `0.14888037368183737 / 9`;
- HDBSCAN 2014 `0.15198123772301594 / 9`.

No successor is authorized by this protocol. After the diagnostic result is recorded, any successor must be separately motivated, specified, frozen, and executed once.

## Firewall

- SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`.
- Protected OrbitTrace solar longitude `20°–55°` remains inaccessible.
- No OrbitTrace target information or target-region event access.
- No MAARSY or DMS scientific access.
- No #1050/#1053 oracle-selected identity is hard-coded or used to construct the diagnostic statistic.
- No new rank, cutoff, parameter search, signature search, metric search, feature search, diversity search, fusion search, source quota, or budget-specific successor is evaluated.
