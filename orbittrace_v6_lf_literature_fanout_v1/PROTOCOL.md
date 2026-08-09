# OrbitTrace v6-LF matched-literature record-slice fanout v1

## Status

Infrastructure-only performance freeze created before the current v6-LF development verdict and before any v6-LF matched-literature result. It accesses no benchmark truth, competitor cluster labels, target-region event, or OrbitTrace target information.

It is dormant unless exact frozen v6-LF first passes development. It does not change the matched HDBSCAN/Sugar universes, the all-event target-excluded calibration rule, the detector, the ranking, or the broad/sparse superiority bars.

## Execution boundary

For each independently frozen `(HDBSCAN|Sugar) × (2023|2025)` panel:

1. materialize only the exact ID-manifest row universe and geometry;
2. construct v6-LF calibration from **every exact matched scan row**, ignoring native-background membership except for integrity counts;
3. run immutable v6 proposal/calibration/dedup control flow while replacing only `exact_rescore_window_v6` with an input-capture function;
4. freeze ordered exact inputs per center: complete proposal dictionaries and complete ordered center-window event IDs;
5. deterministically split already-frozen proposal records into contiguous slices using estimated scalar work `proposal_records × window_events` and greedy least-loaded scheduling;
6. each slice reconstructs the **complete original center window** and calls the unchanged exact scorer through the already-audited contiguous multiprocessing wrapper;
7. reassemble exact outputs in original proposal-anchor order;
8. replay immutable v6 control flow using those exact outputs;
9. serialize the standard v6-LF pretruth panel-year checkpoint consumed by the existing pretruth combiner/evaluator.

No slice may alter the full center event window. No slice output may seed another slice. No score, distance, threshold, calibration event, proposal event, member, component, recurrence, family, or rank is recomputed by the combiner.

## Strict replay identity

Exact byte equality of the captured proposal dictionaries is the fast path. If the deterministic non-exact replay differs in serialization, the fallback is frozen now to the same strict semantic standard used by the canonical development recovery:

- dictionary key sets identical;
- sequence types, lengths, and order identical;
- booleans/integers/strings/IDs and all other discrete values identical;
- proposal-anchor order identical;
- complete ordered center-window event IDs identical;
- floating values only may differ, with both relative and absolute tolerance `1e-12`.

Any structural/member/ID/order/discrete-value difference or float drift above tolerance is fatal. This is an execution-equivalence rule, not a scientific tolerance or detector parameter.

## Firewall

Before the complete v6-LF family/ranking freeze, the fanout may access only exact matched event IDs/geometry, immutable all-event calibration, and the source-audited ID manifest. It may not open the IAU truth mapping or use competitor cluster assignments. Native-background IDs in the manifest are checked only as a subset/count integrity field and are never used to select calibration events.

Solar longitude 20°–55° remains excluded from every pretruth stage.

## Activation

This fanout may be benchmarked for real execution equivalence only after exact v6-LF development PASS, using one bounded pretruth panel/center and no truth mapping. Full matched-literature execution is allowed only after that real equivalence audit passes.

A v6-LF development no-go permanently leaves this infrastructure dormant. A technical failure does not authorize changing any fanout or scientific rule.
