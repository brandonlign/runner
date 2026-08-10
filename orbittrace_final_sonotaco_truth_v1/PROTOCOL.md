# Final SonotaCo 2013/2014 post-output truth boundary — v1

## Purpose

This layer is the only allowed transition from the label-free final-test phase to known-shower evaluation. It is frozen before any SonotaCo 2013/2014 scientific row or native shower value is opened.

The truth reader cannot run or alter a detector. For one `comparator × year` panel it may read the SonotaCo `shower` field **only after** the exact pairwise event-ID universe, final #839 primary output, comparator primary output, and their source manifests have been frozen and hashed.

## Frozen mapping provenance

Known-shower mapping reuses the exact pre-existing GMN/MDC metadata audit previously used for SonotaCo label interpretation:

- workflow run: `30855193522`;
- artifact: `real-shower-meta-data-audit`;
- exact `audit.json` SHA-256: `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`.

The truth stage may not modify that mapping or learn a new mapping from 2013/2014.

For each eligible audit profile, every unambiguous three-character native code is mapped to the pre-existing `complex_key`. Ambiguous code mappings fail closed.

## Native SonotaCo syntax

The exact historical source convention is retained:

- trim and uppercase the `shower` token;
- native background if the token is empty, contains no ASCII letter, or begins with `SPO`;
- an eligible labeled token must match `^([A-Z0-9]{3})_JA$`;
- the captured three-character code is looked up in the frozen mapping audit.

Rows with invalid native syntax or an otherwise valid but unmapped code are **never mapped to another known shower**. Relative to the frozen eligible known-shower reference they are treated as reference background (`SPORADIC`) and counted separately in the audit. This reproduces the historical final-panel behavior where only recognized eligible mappings create positive known-shower labels and all other panel IDs default to the reference background.

## Output-freeze prerequisites

Before a truth read, the caller must provide a pretruth freeze manifest containing:

- exact year (2013 or 2014);
- exact comparator (`Sugar` or `catalogue HDBSCAN`);
- `pretruth_outputs_frozen=true`;
- `truth_accessed_before_freeze=false`;
- `target_information_access=false`;
- `target_region_access=false`;
- SHA-256 of the exact pairwise event-ID list;
- SHA-256 of the frozen #839 primary output;
- SHA-256 of the frozen comparator primary output;
- SHA-256 of the #839 source manifest;
- SHA-256 of the comparator source manifest.

The truth reader recomputes the canonical event-ID-list hash before reading labels. Any mismatch fails closed.

## Stable row identity

The truth stage uses the same physical-row identity as the final shared normalizer: `SNT<year>:<physical CSV row>`, where the header is physical row 1 and the first data row is row 2.

Only requested frozen pairwise row IDs are inspected. The reader rechecks solar longitude for each requested row and rejects any row inside the sealed closed interval 20°–55° before reading/accepting its native truth classification.

The final output event-ID set must equal the frozen requested pairwise set exactly.

## Truth timing

For each comparator/year:

1. shared pairwise rows are frozen;
2. #839 primary catalogue is frozen and hashed;
3. comparator primary catalogue is frozen and hashed;
4. source/configuration manifests are frozen and hashed;
5. pretruth freeze manifest is written;
6. only then may this truth reader inspect `soldeg` and `shower` for those exact row IDs;
7. the already-frozen #854 evaluator consumes the frozen catalogues plus the resulting truth map.

No detector rerun, membership alteration, family filtering, rank change, candidate-budget change, or comparator postprocessing may occur after truth opens.

## Firewall

This layer accepts no OrbitTrace target reference. It performs no nearest-neighbor search, no target matching, no family construction, and no scientific method selection.

Truth access remains limited to target-excluded SonotaCo 2013/2014. MAARSY and OrbitTrace target access remain unauthorized.