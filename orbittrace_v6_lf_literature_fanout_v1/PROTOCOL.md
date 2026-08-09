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

## Frozen production fanout

After the bounded real-data equivalence gate passes, full matched-literature execution uses exactly **8 deterministic exact shards per panel-year** and up to **4 contiguous exact-rescore workers per shard**. The four panel-year universes remain independent, giving 32 exact shard jobs in total. This is an execution partition only; shard count and worker count never enter a score or scientific gate.

The shard scheduler is fixed before the v6-LF development verdict. It may not be changed from observed HDBSCAN/Sugar scientific outcomes. A technical resource failure may be retried with the exact same partition; changing the partition would require a separately source-audited execution-equivalence protocol and cannot change scientific values.

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

Before the complete v6-LF family/ranking freeze, detector jobs may access only exact matched event IDs/geometry, immutable all-event calibration, the source-audited ID manifest, and the two hash-pinned SonotaCo archives. They may not have the raw HDBSCAN/Sugar assignment files or IAU truth mapping available on disk.

The one input-preparation job is allowed to read the already-frozen comparator assignment artifacts solely through the source-audited ID-manifest builder that extracts the exact common event-ID universes. It then deletes every assignment directory before creating the reusable pretruth bundle. The uploaded pretruth bundle contains only the pinned runtime, ID-only manifest, and SonotaCo archives; filenames containing assignments/mapping/audit truth are rejected before upload.

The four panel-year replay jobs produce pretruth checkpoints. The evaluation job downloads only those checkpoints and the ID-only bundle, constructs both recurrent v6-LF rankings, writes and SHA-256 freezes the complete pretruth ranking JSON, and asserts the raw comparator-assignment directories and truth mapping do not exist. Only after that freeze does it download the four comparator assignment artifacts and known-shower truth metadata.

Native-background IDs in the manifest are checked only as a subset/count integrity field and are never used to select calibration events. Solar longitude 20°–55° remains excluded from every pretruth stage.

## Activation

The bounded real equivalence gate requires a genuine exact v6-LF development PASS. It uses only HDBSCAN-2023 pretruth geometry and the cheapest real center that genuinely splits at 512 records, comparing complete-center scalar exact output against the production split/parallel path byte-for-byte. It opens no truth mapping and computes no literature endpoint.

Full matched-literature fanout requires a three-line one-file child marker containing:

1. `EXECUTE_V6_LF_MATCHED_LITERATURE_AFTER_REAL_EQUIVALENCE`;
2. the exact v6-LF development PASS run ID;
3. the successful bounded real-equivalence run ID.

Authorization accepts exactly one valid v6-LF development-result artifact lineage: the original frozen fanout result or the pre-frozen strict-semantic recovery result, never both. It verifies all v6-LF development gates true and verifies the real-equivalence artifact before any matched panel is materialized.

The final evaluation reuses the already-frozen `combine_pretruth.py` and `evaluate_frozen.py`, exact HDBSCAN/Sugar denominators, and unchanged `BROAD_CATALOGUE_SUPERIORITY` / `SPARSE_STREAM_SUPERIORITY` / `NO_LITERATURE_SUPERIORITY` classification rules. No alternative comparator, year, denominator, stratum, or superiority threshold may be selected from the result.

A v6-LF development no-go permanently leaves this infrastructure dormant. A technical failure does not authorize changing any fanout or scientific rule.
