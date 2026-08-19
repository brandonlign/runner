# OrbitTrace M2D cross-year recurrence core v1

## Scientific question

Can the already-promoted support-resolved TopoModal + exact annual-density M2D catalogue retain its broad, high-recall discovery envelopes while attaching a deterministic cross-year recurrence core that removes nonrecurrent background without sacrificing generic known-shower recovery?

This is a new extraction architecture, not a retune of M2D. The parent envelope membership, M2D score, rank, physical embedding, target-excluded development universes, comparator capacities, and literature evaluator remain immutable.

## Frozen parent

The parent is the exact support-resolved M2D catalogue used by PR #1377 on target-excluded GMN 2022/2023. Exact fair-pretruth SHA-256:

`8b0f4629659c1bfd750747303ad04ff67355adf66d4dbe474ce7fba788f5bae5`

The parent already passed the same-universe published-configuration Sugar/HDBSCAN fairness benchmark. This experiment cannot change that discovery claim or ranking.

## Exact physical metric

All recurrence calculations use the exact existing TopoModal physical embedding from `orbittrace_topomodal_hierarchy_scale_v1/run_diagnostic.py`:

- solar-longitude chord divided by `2 sin(5 deg / 2)`;
- radiant-direction chord divided by `2 sin(4 deg / 2)`;
- log-speed divided by `log(1.1)`.

No new physical scale or feature is introduced.

## Cross-year recurrence core

For each immutable M2D envelope independently:

1. Split its members into 2022 and 2023.
2. For each event in each year, compute its within-year reference radius as the distance to its `min(4, n_year - 1)`-th nearest *other* member of that same envelope/year. The inherited support constant 4 is the only neighbor count; for a smaller annual slice all available same-year neighbors are used.
3. Find that event's single nearest member from the opposite year in the same envelope.
4. Add an undirected cross-year edge when that nearest opposite-year distance is no larger than the source event's within-year reference radius. A qualifying directed nearest-neighbor relation is sufficient to create the undirected edge; no reciprocal-neighbor requirement or fitted distance cutoff is added.
5. Compute connected components of this cross-year-edge graph.
6. A recurrent component is retained iff it contains at least two 2022 members and at least two 2023 members. This is the minimal two-observation-per-year recurrence requirement and automatically preserves the inherited total support floor of four.
7. The envelope's extraction core is the union of **all** retained recurrent components. There is no component selection, weighting, target-aware choice, or fallback to the envelope when the core is empty.

Thus the output is dual-view:

- discovery envelope: exact parent M2D membership and exact rank;
- extraction core: deterministic subset produced only by cross-year recurrence geometry.

The extraction core cannot create a family, change candidate capacity, alter rank, recruit an event outside its envelope, or merge envelopes.

## Development firewall

Development uses only the exact PR #1377 target-excluded GMN 2022/2023 universes. Solar longitude `[20 deg, 55 deg]` is already absent before this method receives geometry. OrbitTrace target coordinates, canonical IDs, revealed rank-84/rank-82 families, full target-region events, SonotaCo truth, and external-survey truth are prohibited from construction and pretruth.

The complete envelope-to-core mapping and all core memberships must be hash-frozen before known-shower truth is opened.

## Frozen evaluation

Candidate budgets are unchanged and equal to each exact published comparator's complete cluster count, as in PR #1377. For every panel, both the envelope catalogue and the core catalogue use the identical parent candidate order and capacity.

Two evaluations are binding.

### A. Full-catalogue core utility

Using the same annual Hungarian one-to-one F1 evaluator, compare core memberships with exact parent envelope memberships.

For **each comparator route separately** (Sugar and HDBSCAN), all must hold across its 16 panels:

- mean macro precision is strictly higher for cores;
- mean macro F1 is not lower for cores;
- total `F1 > 0.5` recoveries are not lower for cores.

For **each comparator x denominator scale** (`Sugar/HDBSCAN x 128/1024`), both must hold across the eight corresponding panels:

- mean macro F1 is not lower for cores;
- total `F1 > 0.5` recoveries are not lower for cores.

### B. Same-discovery paired utility

First perform the unchanged envelope Hungarian assignment. For every envelope assignment with parent `F1 > 0.5`, score that exact same candidate's core against that same shower with no rematching.

For Sugar and HDBSCAN routes separately:

- at least one recovered parent assignment must exist;
- mean paired precision must be strictly higher for the core;
- mean paired F1 must be not lower for the core.

All gates are conjunctive. This prevents the core from appearing useful merely by rematching to different showers or by deleting difficult families.

## Outcome boundary

A PASS authorizes an exact frozen no-retuning SonotaCo transfer of this dual-view architecture before any OrbitTrace target characterization. A FAIL freezes this exact recurrence rule as a negative result. No k-neighbor sweep, reciprocal-neighbor variant, radius multiplier, component-size threshold search, year weighting, score blend, fallback rule, or target-informed rescue is authorized from the same development truth.