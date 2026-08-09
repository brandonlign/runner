# OrbitTrace v6-LF final blind Stage-A protocol

## Eligibility

This Stage-A protocol is dormant unless **all three** pre-result method-selection gates have already passed:

1. v6-LF has passed all frozen target-excluded GMN 2022/2023 development gates;
2. the no-retuning exact-row SonotaCo comparison is classified `BROAD_CATALOGUE_SUPERIORITY` or `SPARSE_STREAM_SUPERIORITY` against the frozen Sugar/HDBSCAN panels;
3. the prospectively frozen, event-value-unexposed MAARSY 2018/2019 cross-survey validation has returned exact `PASS_V6_LF_MAARSY_2018_2019_EXTERNAL_VALIDATION` under PR #589's frozen integrity, power and scientific generalization gates.

Development PASS alone, literature superiority alone, any MAARSY power-inconclusive result, or a scientific MAARSY FAIL cannot authorize Stage A. No target-region deployment may occur before all three artifacts are durably available and verified.

The earlier GMN 2024/2025 temporal-holdout proposal is explicitly **not** an authorization artifact: repository history showed that target-excluded 2024/2025 scientific values, known-shower labels and F1 endpoints had already been consumed in PR #453 / run `31235104333`. That panel cannot be relabeled as prospective external evidence.

No development, comparator, external-validation, or final-search parameter may be changed after those results.

## Frozen method

Stage A uses the exact promoted v6-LF architecture:

- exact repaired v3-primary catalogue-v6 detector source;
- v3 primary catalogue channel and frozen fixed4 rescue machinery unchanged;
- all-event Mondrian null calibration, with every geometrically valid scan row copied into the calibration reservoir;
- no catalogue shower-label selection, null trimming, density masking, iterative cleaning, or retuning;
- exact proposal budgets, empirical p-value rules, exact rescoring, components, cross-year recurrence and primary ranking from the promoted v6-LF method;
- rescue families are diagnostic only and cannot satisfy final OrbitTrace recovery.

## Discovery corpus

The discovery corpus is fixed to complete GMN **2022 and 2023** geometry.

Unlike target-excluded development, Stage A does **not** remove solar longitude 20°–55°: the purpose of the final application is to open the previously withheld region after method selection is complete.

This is the only scientific difference between development input construction and deployment input construction: the blind-region exclusion is removed because the method is now frozen and authorized for final discovery. Geometry validity, stable-ID deduplication, sun-centered coordinate construction and all-event calibration remain exact.

## Hard Stage-A firewall

Before any family ranking is durably frozen, Stage A may read only:

- stable event ID;
- solar longitude;
- ecliptic longitude;
- ecliptic latitude;
- geocentric speed;
- raw-input provenance/hash fields.

It must not read or normalize the catalogue shower-label **values**.

It must not have access to:

- the withheld OrbitTrace reference artifact;
- OrbitTrace event IDs;
- target coordinates/radiants/velocity/orbit/activity profile;
- target identity/name;
- any historical target rank from prior methods;
- any post-reveal matching result.

The label column name may be discovered as part of generic schema validation, but its values must remain unread.

## Exact geometry semantics

For each monthly file:

- parse numeric `sol`, `lam`, `bet`, `vg` with coercion;
- require 0 <= sol <= 360;
- require 0 <= lam <= 360;
- require -90 <= bet <= 90;
- require 5 <= vg <= 75 km/s;
- do **not** apply the development 20°–55° exclusion;
- deduplicate stable IDs in deterministic monthly order;
- set `sun_lon = wrap180(lam - sol)` using the exact frozen base helper;
- set `iau=0`, `complex_key="HIDDEN"` for scan rows;
- copy every scan row into calibration with only `complex_key="SPORADIC"` changed.

No label-dependent field may affect scan or calibration membership.

## Stage-A output

After scanning both years, exact rescoring, component construction, two-year recurrence and primary ranking, Stage A must serialize an artifact with schema:

`orbittrace-final-stage-a-ranked-families-v2`

Required top-level fields:

- `schema`;
- `method_id` = exact frozen v6-LF method identity;
- `years` = `[2022, 2023]`;
- `target_reference_accessed` = `false`;
- `catalogue_shower_labels_used` = `false`;
- exact source/input provenance and hashes;
- complete `primary_families` in contiguous rank order.

Each primary-family entry contains **only**:

- `family_id`;
- `rank`;
- `years`;
- `event_ids_by_year` with exact stable IDs for 2022 and 2023.

The entire Stage-A artifact must be SHA-256 frozen before any Stage-B target-reference access.

## Execution infrastructure

Fanout/checkpointing is implementation-only and may be used exactly as in the audited v6-LF development executor:

1. independent pre-exact capture for 2022 and 2023;
2. deterministic proposal-count-balanced exact-rescore shards;
3. each shard delegates to the immutable scalar exact-rescore function and preserves proposal order;
4. input-hashed year replay;
5. final two-year family construction and Stage-A serialization.

Infrastructure may be repaired only for technical correctness/equivalence and must never inspect target-reference data or alter scientific output.

Any execution workflow must verify the exact development PASS artifact, exact matched-literature superiority artifact, and exact `PASS_V6_LF_MAARSY_2018_2019_EXTERNAL_VALIDATION` artifact **before** the first full-region GMN row is requested. It must also reject the invalidated GMN 2024/2025 holdout lineage as an external authorization source. Marker text alone is insufficient authorization.

## Transition to reveal

After Stage A is complete, its artifact is immutable. The separate `orbittrace_final_exact_id_firewall_v2` Stage-B evaluator may then receive a scrubbed withheld payload containing exact target event IDs and years only.

No Stage-A rerun, ranking alteration, family merge, member expansion, coordinate search or threshold change is allowed after Stage B begins.
