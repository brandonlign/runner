# OrbitTrace exact fanout v3 — record-slice execution freeze

Infrastructure-only performance successor to fanout v2. This is not a scientific detector variant and cannot be selected by scientific outcome.

## Motivation observed from target-excluded execution

Fanout v2 balanced exact work by proposal count per solar-longitude center. The completed pre-exact manifests showed that exact-rescore cost is dominated more closely by `proposal_count × local_window_event_count`, because every proposal performs full-window geometry passes.

On the already-blinded 2022/2023 pre-exact manifests:

- 2022 center 260°: 17,429 proposals × 26,715 events = 465,615,735 proposal-event pairs;
- 2023 center 260°: 23,948 proposals × 41,292 events = 988,860,816 proposal-event pairs;
- 2023 center 140°: 21,089 proposals × 35,590 events = 750,557,510 proposal-event pairs.

Proposal-count-only six-way scheduling had estimated actual geometry-work max:min ratios of about 1.61× for 2022 and 1.72× for 2023. The 2023 shard containing center 260° became the final straggler after the other eleven exact shards completed.

## Frozen execution-only change

Fanout v3 keeps the exact same pre-exact captured center records, event windows, repaired v6 source, dependencies, floating-point functions, exact-rescore function, scientific ordering, thresholds, proposal caps, family semantics, ranking, gates, and blind boundary.

The only change is execution partitioning:

1. estimate each center's work as `len(records) * len(window_event_ids)`;
2. define ideal six-way work as total estimated work / 6;
3. split a center into the minimum number of **contiguous proposal-record slices** needed so no unsplit center is forced to exceed the ideal work share;
4. assign slices by deterministic longest-processing-time scheduling using the same estimated cost;
5. each slice calls the immutable original exact-rescore function on its exact contiguous proposal subsequence and exact full event window;
6. serialize every slice with center, record-start/stop, exact input-record hash, and exact output order;
7. before scientific replay, require complete nonoverlapping contiguous coverage of every original center record list and reconstruct the full exact output in original proposal order;
8. replay those full outputs through the immutable year scan and unchanged repaired main.

No score or scientific output may influence partitioning.

## Projected balance on already-blinded manifests

With six execution shards/year and the fixed rule above:

- 2022 projected estimated-work max:min ratio: about 1.001×;
- 2023 projected estimated-work max:min ratio: about 1.001×.

This compares with approximately 1.61× and 1.72× respectively under proposal-count center scheduling.

## Equivalence requirement

Before fanout v3 may replace v2 for a scientific execution, a source/target-excluded equivalence audit must prove:

- exact pre-exact input SHA identity;
- every center/proposal appears exactly once across slices;
- every slice preserves the original proposal order;
- reassembled center outputs have the exact original proposal-anchor sequence;
- a bounded exact-rescore comparison is byte-identical to the already-proven scalar/contiguous multiprocessing path;
- replay through the unchanged year scan yields identical anchors/components on the audit input;
- no labels, OrbitTrace target information, or excluded 20°–55° events enter the audit.

A failed equivalence audit rejects fanout v3; it cannot justify changing detector science.
