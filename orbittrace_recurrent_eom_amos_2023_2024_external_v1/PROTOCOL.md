# Recurrent-EOM HDBSCAN v1 — frozen AMOS 2023/2024 external-validation protocol

## Status and scientific role

This protocol is frozen after:

1. recurrent-EOM HDBSCAN v1 passed its fixed target-excluded GMN 2022/2023 development gate;
2. the same frozen method beat exact v31 on all four exposed SonotaCo 2013/2014 panels in binding run `31829200215` / artifact `9230008341`;
3. the same frozen method subsequently failed the separately preregistered GMN 2020/2021 retrospective temporal-transfer gate.

The GMN 2020/2021 outcome is explicitly **not used to change any method, transform, threshold, parameter, ranking rule, evaluator, or gate below**. It is preserved as a negative retrospective result only.

AMOS 2023/2024 is fixed as the intended genuinely external survey panel before any AMOS event-level scientific values are available to this recurrent-EOM branch. A future AMOS result may count as external validation only if the complete receipt and execution obey this protocol without amendment after data receipt.

No AMOS event row, radiant, velocity, shower association, or orbit element is accessed by this freeze.

## Frozen recurrent-EOM method

Use exact promoted recurrent-EOM HDBSCAN v1 unchanged:

- promoted method implementation: `orbittrace_recurrent_eom_hdbscan_v1/recurrent_eom.py`;
- required Git blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- promoted GMN development runner Git blob: `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`;
- representation: `GEO6 = (cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72)`;
- pooled two-year HDBSCAN hierarchy;
- `min_cluster_size=10`;
- `min_samples=10`;
- metric `euclidean`;
- cluster selection `eom`;
- `cluster_selection_epsilon=0.0`;
- `allow_single_cluster=False`;
- annual EOM contributions normalized by the accessible event count in each year;
- recurrent stability = minimum of the two normalized annual EOM contributions;
- exact HDBSCAN `get_clusters` extraction on the unchanged hierarchy;
- vanilla parent ranking: ordinary EOM stability, then the inherited deterministic tie order;
- recurrent successor ranking: recurrent stability, ordinary stability, member count, deterministic family ID.

There is no model training on AMOS and no transport calibration.

## Frozen AMOS years and receipt boundary

Exactly calendar years `2023` and `2024` are allowed. No year substitution, expansion, or switching is allowed after receipt.

The provider transfer must be logically separated into three keyed layers:

1. **blinding index**, complete solved multi-station sample, exact columns
   `event_id,utc_time,solar_longitude_deg`;
2. **physical geometry**, only for IDs retained by the blind receipt, exact columns
   `event_id,ra_j2000_deg,dec_j2000_deg,vg_km_s`;
3. **shower associations**, separate mapping keyed only by `event_id`, unopened until candidate generation and complete pooled ranks are frozen.

The physical transfer must contain the complete retained solved sample, including sporadic meteors, not a shower-only subset.

No orbit elements are needed or authorized for recurrent-EOM.

## Frozen protected-region handling

The protected solar-longitude interval is inclusive `[20.0,55.0]` degrees.

For each year:

1. open only the minimal blinding index;
2. reject duplicate/blank IDs, non-finite longitude, wrong-year timestamps, or extra columns;
3. remove every ID with `20.0 <= solar_longitude_deg <= 55.0`;
4. persist a deterministic retained-ID allowlist and its hash;
5. only then may the corresponding physical rows for those retained IDs be opened.

Any physical file containing a protected or non-allowlisted ID is a technical failure/no-result.

The protected rows' radiant, speed, label, and orbit values must never be opened.

## Frozen AMOS canonical adapter

The AMOS coordinate adapter was independently frozen before recurrent-EOM AMOS access on zero-data branch `agent/orbittrace-amos-2023-2024-zero-data-acquisition-v1`.

Exact adapter source identities:

- `amos_canonical_adapter_v1/transform.py` Git blob `612ad23af6e11ac2155282258e3d1429fbe00d67`;
- `amos_canonical_adapter_v1/adapt.py` Git blob `9a0fb05f94d6a28cd95f97d864e76400056273b0`.

The adapter is fixed as:

- J2000 geocentric equatorial radiant -> ecliptic longitude/latitude using fixed obliquity `23.43928 deg`;
- `sun_lon = wrap180(ecliptic_lon_j2000 - solar_longitude_deg)`;
- `ecl_lat = transformed geocentric ecliptic latitude`;
- `vg = reported geocentric speed km/s unchanged`;
- no quality cut;
- no empirical alignment, survey calibration, offset, scale correction, velocity correction, or fit to GMN/SonotaCo/AMOS values.

The canonical AMOS row entering recurrent-EOM is exactly:

`id, year, sol, sun_lon, ecl_lat, vg`

with any label field kept opaque/unopened until pretruth freeze.

If AMOS cannot supply a documented geocentric J2000 radiant and geocentric speed matching these fields, this protocol defers the panel rather than changing the method.

## Pretruth freeze requirement

Before any AMOS shower association is opened, the execution must persist and hash-freeze, for both vanilla EOM and recurrent-EOM:

- exact retained event counts by year;
- exact canonical GEO6 input hash;
- complete condensed-tree identity sufficient to reproduce the selection;
- selected node IDs;
- every candidate membership/event-ID list;
- every candidate score used in ordering;
- the complete deterministic pooled candidate order;
- mechanism-active flag;
- all method/adapter/input source hashes.

No truth-bearing field may enter HDBSCAN fitting, stability calculation, node selection, membership construction, or ranking.

## Frozen external evaluator

After the complete pretruth candidate payload is frozen, open only the separate AMOS shower-association mapping for retained IDs.

For each year independently:

- an eligible known shower has at least 4 accessible retained events in that year;
- a candidate is positive for a shower only if overlap >= 4 and precision >= 0.5;
- each eligible shower contributes only its first qualifying rank to recovered-at-k and MRR;
- report recovered @25, @50, @100, @500;
- report top-100 dominant precision;
- report mean reciprocal rank across represented eligible showers under the inherited evaluator semantics;
- report median top-500 fragmentation;
- report qualified/represented shower count.

The comparison parent is vanilla HDBSCAN EOM on **the identical retained AMOS events, identical GEO6 representation, and identical hierarchy**. The only scientific difference is ordinary-EOM versus recurrent-EOM stability used in selection/ranking.

## Frozen external-validation gate

The gate is copied unchanged from the promoted GMN 2022/2023 recurrent-EOM protocol and is not modified in response to the GMN 2020/2021 retrospective result.

For **each** of 2023 and 2024, recurrent-EOM must satisfy all of:

1. recovered@50 >= vanilla EOM;
2. recovered@100 >= vanilla EOM;
3. top-100 dominant precision >= vanilla EOM;
4. MRR >= vanilla EOM;
5. median top-500 fragmentation <= vanilla EOM.

Across the two years:

6. recovered@100 must be strictly higher than vanilla EOM in at least one year;
7. recurrent-EOM must select a different HDBSCAN node set from vanilla EOM.

Pass token:

`PASS_RECURRENT_EOM_HDBSCAN_V1_AMOS_2023_2024_EXTERNAL_VALIDATION`

Otherwise:

`FAIL_RECURRENT_EOM_HDBSCAN_V1_AMOS_2023_2024_EXTERNAL_VALIDATION`

A technically valid failure is binding and authorizes no AMOS-specific rescue. A pass is external-survey validation evidence for the already-frozen recurrent-EOM method; it does not authorize access to the OrbitTrace protected target.

## Technical no-result conditions

The run is a technical failure/no-result if any of the following occurs before a valid endpoint:

- source/blob pin mismatch;
- adapter pin mismatch;
- unexpected AMOS header or year;
- duplicate event ID;
- protected-region survivor;
- geometry row outside the retained-ID allowlist;
- missing retained geometry row;
- non-finite/invalid geometry;
- label access before pretruth freeze;
- vanilla custom extraction fails exact partition identity against vanilla HDBSCAN;
- selected-node/compact-label mapping fails;
- execution cannot prove exactly years 2023 and 2024 were used.

Engineering-only repairs to file paths/runtime plumbing may be made only if they cannot alter scientific bytes or expose an AMOS scientific endpoint before the repair is frozen.

## No-rescue rule

After the first technically valid AMOS endpoint, do not change or search:

- HDBSCAN parameters;
- recurrent-stability formula or annual combiner;
- year weights;
- GEO6 dimensions or speed scale;
- coordinate transform or obliquity;
- quality filters;
- ranking tie breakers;
- truth threshold/overlap rule;
- metric;
- budgets;
- evaluator;
- fusion or reranking;
- survey-specific calibration.

Any future method after a failure must be a separately motivated and independently frozen successor, not an AMOS-result-informed repair of recurrent-EOM v1.

## Firewall declarations

Every pretruth and result artifact must assert:

- `scientific_role='PRISTINE_EXTERNAL_AMOS_2023_2024_VALIDATION_ONLY'`;
- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `orbittrace_target_access=false`;
- `sonotaco_used_for_tuning=false`;
- `amos_post_result_parameter_search=false`.
