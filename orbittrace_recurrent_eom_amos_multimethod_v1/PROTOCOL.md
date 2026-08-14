# Recurrent-EOM HDBSCAN v1 — AMOS 2023/2024 multi-method external benchmark freeze

## Status and role

This is a **pre-data protocol freeze** for a supplementary AMOS 2023/2024 literature-comparison benchmark. It is created before any AMOS event-level scientific value, shower association, orbit element, uncertainty, or comparator-quality field is available to this branch.

It does **not** alter the already-frozen primary AMOS external-validation protocol in `orbittrace_recurrent_eom_amos_2023_2024_external_v1/PROTOCOL.md`. That primary protocol remains the binding test of recurrent-EOM versus ordinary HDBSCAN EOM on the complete retained AMOS geometry sample.

This supplementary protocol asks a different question: **on AMOS, does the already-promoted recurrent-EOM method beat the same serious literature comparator classes used in the exposed SonotaCo benchmark when each comparison is run on an identical pretruth structural universe?**

The protected OrbitTrace solar-longitude interval `[20.0,55.0]`, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.

## Frozen candidate method

Recurrent-EOM is unchanged from the promoted method:

- implementation Git blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- GEO6 representation `(cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72)`;
- pooled two-year HDBSCAN hierarchy;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- EOM condensed hierarchy;
- `cluster_selection_epsilon=0.0`;
- `allow_single_cluster=False`;
- annual EOM contribution normalized by the accessible event count in that year;
- recurrent stability = minimum of the two normalized annual EOM contributions;
- exact HDBSCAN `get_clusters` extraction on the unchanged hierarchy;
- candidate order = recurrent stability descending, ordinary stability descending, member count descending, deterministic family ID.

No AMOS value may change a method constant, score, ranking rule, representation dimension, speed scale, or extraction rule.

## Frozen AMOS adapter and protected-data boundary

Use the exact AMOS canonical adapter already frozen before data:

- `transform.py` Git blob `612ad23af6e11ac2155282258e3d1429fbe00d67`;
- `adapt.py` Git blob `9a0fb05f94d6a28cd95f97d864e76400056273b0`.

Exactly calendar years 2023 and 2024 are allowed. The blind receipt must first open only `event_id,utc_time,solar_longitude_deg`, exclude `[20.0,55.0]` inclusively, and persist the retained-ID allowlist. No comparator-only physical field may be opened for an ID outside that allowlist.

## Frozen comparator set

Exactly two literature comparator classes are eligible for the primary supplementary benchmark because they have already-audited implementations in the OrbitTrace repository and were used in the established SonotaCo literature comparison.

### 1. Sugar-style DBSCAN recurrence comparator

Use the already-audited comparator adapter Git blob:

`00578445ed0957fb3708bb84fda1df6ef7b5b004`

It in turn requires the already-audited Sugar core source SHA-256:

`5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb`

Frozen constants remain exactly:

- min samples `5`;
- epsilon percentile `23`;
- clone iterations `1000`;
- overlap threshold `0.5`;
- minimum recurrence `100`;
- strong recurrence `500`;
- seed root `20170209`.

For AMOS, the deterministic pre-data seed namespace is fixed now as:

- corpus namespace `amos-2023-2024-label-free-sugar-v1`;
- comparator-pair identifier `ORBITTRACE_VS_SUGAR_AMOS`.

No seed string may change after AMOS receipt.

Sugar pairwise structural eligibility is frozen exactly as in the established comparator contract after protected exclusion and finite base geometry:

- finite nonnegative `ra_sd_deg`, `dec_sd_deg`, `vg_sd_km_s`;
- strict `convergence_angle_deg > 15.0`;
- `vg_sd_km_s <= 0.10 * vg_km_s + 1.0`.

Zero uncertainty is allowed. Negative uncertainty is rejected.

### 2. Catalogue-HDBSCAN literature comparator

Use the same already-audited comparator adapter Git blob:

`00578445ed0957fb3708bb84fda1df6ef7b5b004`

with already-audited catalogue-HDBSCAN source SHA-256:

`a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2`.

Frozen comparator requirements remain:

- HDBSCAN version `0.8.44`;
- min cluster size `100`;
- all non-noise native labels are catalogue families.

HDBSCAN pairwise structural eligibility is frozen as:

- finite `convergence_angle_deg`, `vg_sd_km_s`, `q_au`, `e`;
- `convergence_angle_deg >= 15.0`;
- `vg_sd_km_s / vg_km_s <= 0.10`;
- `0 <= e <= 1.0`;
- `0 < q_au <= 1.0`.

The comparator-only `q_au` and `e` fields are never inputs to recurrent-EOM.

## Supplemental AMOS fields required for fair comparator execution

The existing recurrent-EOM AMOS geometry transfer remains sufficient for the primary external-validation test but is not sufficient for these literature comparators. A separate retained-ID-only supplemental transfer is therefore frozen now with exact columns:

`event_id,ra_sd_deg,dec_sd_deg,vg_sd_km_s,convergence_angle_deg,q_au,e`

Rules:

1. the file may contain only IDs already retained by the Stage-1 blind receipt;
2. every supplied value must refer to the same solved multi-station solution as the base AMOS geometry row;
3. missing values are represented as blank/null and make that event ineligible only for the comparator requiring the missing field;
4. no shower association, shower code, sporadic flag, target-region row, or additional orbit element is allowed in this supplemental file;
5. recurrent-EOM code must not receive `ra_sd_deg`, `dec_sd_deg`, `vg_sd_km_s`, `convergence_angle_deg`, `q_au`, or `e` as feature inputs.

If AMOS cannot supply these fields with documented meanings compatible with the frozen comparator assumptions, the affected comparator is recorded as `NOT_EVALUABLE_INPUT_INCOMPATIBLE_PRETRUTH`; it is neither a scientific win nor loss and no proxy, fit, derived replacement, threshold relaxation, or alternative comparator implementation may be chosen after receipt.

## Pairwise same-information fairness

Each literature comparison has its own exact **pairwise structural universe**, defined pretruth as the retained AMOS IDs satisfying that comparator's frozen structural predicate.

For a given comparator:

- the literature comparator receives exactly that pairwise universe;
- recurrent-EOM is independently rerun from scratch on exactly the same pairwise universe, pooling 2023+2024 exactly as usual;
- recurrent-EOM may ignore comparator-only fields but may not receive extra rows unavailable to the comparator;
- no event may be removed because of shower identity, method score, candidate rank, or posttruth performance.

The primary complete-sample AMOS recurrent-EOM-vs-vanilla-EOM result remains separate and must not be replaced by these pairwise restricted analyses.

## Pretruth freeze

Before any AMOS shower-association mapping is opened, for each evaluable comparator pair the workflow must freeze and SHA-256 bind:

- retained pairwise event IDs by year;
- exact canonical geometry input hash;
- comparator source/blob identities and all constants;
- recurrent-EOM source/blob identities and all constants;
- complete recurrent-EOM candidate memberships and deterministic pooled order;
- complete comparator family memberships for each year;
- comparator family count for each year;
- all deterministic Sugar seeds or seed-generating identities sufficient to reproduce them;
- proof that comparator-only fields never entered recurrent-EOM features;
- mechanism/eligibility status.

No truth-bearing field may enter either method before this freeze.

## Frozen evaluation

After all method outputs above are frozen, open only the separate shower-association mapping for retained IDs.

For each comparator and each year independently:

1. eligible known showers have at least 4 events in that comparator's exact pairwise universe;
2. build the shower-by-family F1 matrix for the literature comparator;
3. build the shower-by-candidate F1 matrix for recurrent-EOM using the same truth IDs;
4. let `B` equal the number of non-noise catalogue families produced by that literature comparator in that year, fixed before truth;
5. evaluate the literature comparator on all its `B` families;
6. evaluate recurrent-EOM on the first `min(B, number_of_recurrent_candidates)` candidates in its pretruth pooled order after restricting memberships to that year;
7. apply the same maximum-F1 one-to-one Hungarian assignment to both methods;
8. report macro-F1 and assigned-shower count with F1 `> 0.5`;
9. also report recurrent candidate capacity if fewer than `B` candidates exist; there is no budget backfill, alternate cutoff, or truth-informed adjustment.

The comparator-derived budget is a pretruth structural quantity, not a truth-derived parameter.

## Frozen superiority gate

A comparator/year panel is a recurrent-EOM **WIN** only if both:

- recurrent-EOM macro-F1 is strictly greater than the literature comparator macro-F1; and
- recurrent-EOM recovered F1>0.5 count is at least the literature comparator count.

`PASS_RECURRENT_EOM_AMOS_MULTIMETHOD_SUPERIORITY_V1` requires WIN on all four evaluable primary panels:

- Sugar 2023;
- Sugar 2024;
- catalogue-HDBSCAN 2023;
- catalogue-HDBSCAN 2024.

If one comparator is pretruth input-incompatible, no reduced-panel PASS token may be substituted. Report `INCOMPLETE_RECURRENT_EOM_AMOS_MULTIMETHOD_SUPERIORITY_V1_INPUT_INCOMPATIBLE` and preserve any evaluable panel results descriptively.

A technically valid all-panel failure is binding. No comparator-specific rescue, alternate budget, threshold, field proxy, subset, seed namespace, quality cut, recurrent-EOM alteration, or post-result parameter search is authorized.

## Scientific interpretation

This supplementary benchmark can establish that recurrent-EOM's superiority over established methods transfers to a genuinely external survey. It cannot replace the primary complete-sample AMOS external-validation gate, and a supplementary PASS alone does not authorize protected OrbitTrace target access.

## Firewall declarations

Every artifact must assert:

- `scientific_role='PRISTINE_EXTERNAL_AMOS_MULTIMETHOD_SUPPLEMENT'`;
- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `orbittrace_target_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `amos_truth_access_before_pretruth=false`;
- `comparator_only_fields_entered_recurrent_eom=false`;
- `post_result_parameter_search=false`.
