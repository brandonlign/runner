# Recurrent-EOM HDBSCAN v1 — frozen European Fireball Network 2017/2018 external-validation protocol

## Status and scientific role

This protocol is frozen before the first OrbitTrace access to any event-level value from the European Fireball Network (EFN) 2017–2018 catalog `J/A+A/667/A157`.

The panel was identified only from public catalogue/paper metadata after recurrent-EOM HDBSCAN v1 was already promoted on target-excluded GMN 2022/2023 and had already completed the exposed SonotaCo 2013/2014 v31 benchmark. Repository searches performed before this freeze found no indexed scientific use of the EFN 2017/2018 catalog, its CDS identifier `J/A+A/667/A157`, or the Borovička et al. 824-fireball cohort in prior OrbitTrace work.

The later negative GMN 2020/2021 retrospective result is **not** used to alter any method, field, threshold, ranking rule, evaluator, or gate below.

If the access boundary below is followed exactly, EFN 2017/2018 is intended as an independent external-survey validation panel for the already-frozen recurrent-EOM method. It is not development data and may not be used to tune a successor.

No EFN event row, solar longitude, radiant, velocity, orbit, or shower association was accessed while freezing this protocol.

## Frozen published survey cohort

Use exactly the final published CDS catalogue:

- CDS/VizieR catalogue: `J/A+A/667/A157`;
- paper: Borovička et al., A&A 667, A157 (2022), “Data on 824 fireballs observed by the digital cameras of the European Fireball Network in 2017–2018. I.”;
- fixed final catalogue size in the public metadata: 824 fireballs;
- calendar years: exactly 2017 and 2018.

The authors report that their underlying digital-camera database contained more multi-station meteors and that the final 824 were the already-published reliable trajectory/orbit cohort. That survey-side selection predates OrbitTrace and is treated as the immutable native EFN data product. Use **all 824 published catalogue records** before the protected-region exclusion. Do not apply any new OrbitTrace quality cut, camera-count cut, uncertainty cut, magnitude cut, range cut, shower cut, or reliability threshold.

If the fetched catalogue is not exactly the documented fixed 824-record release, the run fails closed pending a metadata-only adjudication; do not silently substitute a later/different EFN release.

## Frozen recurrent-EOM method

Use exact promoted recurrent-EOM HDBSCAN v1 unchanged:

- method implementation Git blob: `30ac3fa3bc47910370df5282258e3d1429fbe00d67`;
- promoted development runner Git blob: `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`;
- representation: `GEO6 = (cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72)`;
- pooled two-year HDBSCAN hierarchy;
- `min_cluster_size=10`;
- `min_samples=10`;
- metric `euclidean`;
- cluster selection method `eom`;
- `cluster_selection_epsilon=0.0`;
- `allow_single_cluster=False`;
- annual EOM contributions normalized by the accessible event count in each year;
- recurrent stability = minimum of the two normalized annual EOM contributions;
- exact HDBSCAN `get_clusters` extraction on the unchanged hierarchy;
- vanilla-parent ordering by ordinary EOM stability with the inherited deterministic tie rule;
- recurrent-successor ordering by recurrent stability, ordinary stability, member count, deterministic family ID.

There is no EFN training, calibration, parameter selection, reranking, or fusion.

## Frozen native EFN field mapping

The published CDS ReadMe documents the following native catalogue fields:

- `Code`: fireball code / event identifier;
- `Obs.date`: observation date;
- `Obs.time`: observation time;
- `Lsun`: Solar Longitude J2000, degrees;
- `Lgeo-Lsun`: ecliptical longitude of the geocentric radiant minus Solar Longitude, degrees;
- `Bgeo`: ecliptical latitude of the geocentric radiant, degrees;
- `Vgeo`: geocentric velocity, km/s;
- `Shower`: possible meteor shower, IAU code.

No astronomical coordinate conversion and no velocity conversion are permitted. The canonical recurrent-EOM row is exactly:

- `id = trimmed Code`;
- `year = calendar year parsed from Obs.date`;
- `sol = Lsun`;
- `lon = Lgeo-Lsun`;
- `lat = Bgeo`;
- `vg = Vgeo`.

Only finite native values are valid. If any retained published row lacks a finite `Lsun`, `Lgeo-Lsun`, `Bgeo`, or positive finite `Vgeo`, the first execution is a technical no-result. Do not drop that row or impute a value after access.

No error/uncertainty column, orbit element, brightness, physical class, camera count, or other catalogue field enters the detector.

## VizieR/TAP access boundary

The CDS/VizieR service supports SQL/ADQL-style table access and server-side column projection/filtering. This protocol requires staged projection so the protected rows’ physical geometry and shower labels are never returned to OrbitTrace.

The exact internal TAP table identifier may be discovered after this protocol only through `TAP_SCHEMA`/catalogue metadata. That metadata lookup is engineering-only and must not return an EFN event record. The resolved table identifier and column metadata must be frozen before the first event query.

### Stage 1 — minimal blind index

The first event-level query may return **only**:

`Code, Obs.date, Obs.time, Lsun`

for the complete fixed 824-row catalogue.

No other column may be selected, downloaded, logged, cached, or inspected at Stage 1.

The blind receipt must:

1. require exactly 824 rows;
2. require unique, nonblank `Code` values;
3. require every `Obs.date` year to be 2017 or 2018 and both years to be nonempty;
4. require finite `Lsun` in `[0,360)`;
5. exclude every event with inclusive `20.0 <= Lsun <= 55.0`;
6. persist sorted retained IDs by year and their SHA-256 hashes;
7. emit no radiant, velocity, label, orbit, or target value.

### Stage 2 — retained native geometry only

Only after Stage-1 retained-ID hashes are frozen may a second server-side query return physical fields.

The server-side query must itself restrict rows to `Lsun < 20.0 OR Lsun > 55.0` and return only:

`Code, Obs.date, Lsun, Lgeo-Lsun, Bgeo, Vgeo`

No protected-row physical value may be returned by the server.

The Stage-2 program must require that the returned `Code` set equals the Stage-1 retained-ID set exactly. Any missing, extra, duplicate, or protected ID is a technical failure/no-result.

### Stage 3 — shower associations only after pretruth freeze

Before any `Shower` value is queried, persist and SHA-256 freeze the complete recurrent-EOM and vanilla-EOM pretruth payload described below.

Only then may a server-side query, again restricted to `Lsun < 20.0 OR Lsun > 55.0`, return:

`Code, Shower`

for the retained records.

The returned IDs must equal the retained-ID allowlist exactly.

Label canonicalization is fixed before access:

- trim surrounding whitespace;
- blank or `---` means `SPORADIC`;
- otherwise use the exact trimmed IAU shower code as the opaque label;
- do not merge aliases, parent complexes, branches, related objects, or shower names after access.

`Object` and all orbit/physical columns remain unopened in Stage 3.

## Pretruth freeze requirement

Before Stage 3, persist and hash-freeze:

- Stage-1 input/index provenance and retained-ID hashes;
- exact retained event counts by year;
- exact canonical GEO6 input hash;
- complete condensed-tree identity sufficient to reproduce selection;
- vanilla selected node IDs;
- recurrent selected node IDs;
- every vanilla candidate membership/event-ID list;
- every recurrent candidate membership/event-ID list;
- every candidate score used in ordering;
- complete deterministic vanilla order;
- complete deterministic recurrent order;
- mechanism-active flag;
- catalogue/metadata identities;
- exact recurrent-EOM source identities;
- exact access/query-plan identities.

No `Shower`, `Object`, orbital element, or other truth-bearing catalogue field may enter candidate generation, HDBSCAN fitting, stability calculation, node selection, membership construction, or ranking.

## Frozen external evaluator

After the complete pretruth payload is frozen, use the Stage-3 `Shower` mapping only as evaluation truth.

For each year independently:

- an eligible known shower has at least 4 accessible retained events in that year;
- a candidate is positive for a shower only if overlap >= 4 and precision >= 0.5;
- each eligible shower contributes only its first qualifying rank to recovery and MRR;
- report recovered @25, @50, @100, @500;
- report top-100 dominant precision;
- report mean reciprocal rank across represented eligible showers under the promoted evaluator semantics;
- report median top-500 fragmentation;
- report qualified/represented shower count.

The comparison parent is vanilla HDBSCAN EOM on the **identical retained EFN events, identical native GEO6 inputs, and identical hierarchy**. The only scientific difference is ordinary-EOM versus recurrent-EOM stability used in selection/ranking.

If fewer than one eligible labeled shower exists in either year, the endpoint is a technically valid **power-inconclusive external result**, not a method pass and not authorization to change the label threshold. Otherwise apply the frozen gate exactly.

## Frozen external-validation gate

Copy the promoted GMN 2022/2023 recurrent-EOM no-regression gate unchanged.

For **each** of 2017 and 2018, recurrent-EOM must satisfy all of:

1. recovered@50 >= vanilla EOM;
2. recovered@100 >= vanilla EOM;
3. top-100 dominant precision >= vanilla EOM;
4. MRR >= vanilla EOM;
5. median top-500 fragmentation <= vanilla EOM.

Across the two years:

6. recovered@100 must be strictly higher than vanilla EOM in at least one year;
7. recurrent-EOM must select a different HDBSCAN node set from vanilla EOM.

Pass token:

`PASS_RECURRENT_EOM_HDBSCAN_V1_EFN_2017_2018_EXTERNAL_VALIDATION`

Otherwise:

`FAIL_RECURRENT_EOM_HDBSCAN_V1_EFN_2017_2018_EXTERNAL_VALIDATION`

Power-inconclusive token if the fixed truth interface contains zero eligible labeled showers in either year:

`INCONCLUSIVE_RECURRENT_EOM_HDBSCAN_V1_EFN_2017_2018_EXTERNAL_VALIDATION_LABEL_POWER`

A technically valid FAIL is binding and authorizes no EFN-specific rescue. An INCONCLUSIVE result also authorizes no threshold lowering or alternate label source after inspection.

## Technical no-result conditions

The run is a technical failure/no-result if any of the following occurs before a valid endpoint:

- repository/source pin mismatch;
- VizieR catalogue provenance is not the fixed published 824-record `J/A+A/667/A157` release;
- Stage 1 returns anything except the four allowed blind-index fields;
- Stage 1 does not contain exactly 824 unique records in years 2017/2018;
- protected rows survive the blind receipt;
- Stage 2 returns a protected/non-retained ID or any column beyond the six allowed native geometry fields;
- any retained geometry row is missing/duplicated/nonfinite/invalid;
- any coordinate or velocity conversion is introduced;
- Stage 3 is queried before pretruth freeze;
- Stage 3 IDs differ from the retained allowlist;
- a truth-bearing field enters pretruth generation;
- vanilla custom EOM extraction fails exact partition identity against vanilla HDBSCAN;
- selected-node/compact-label mapping fails;
- exact years 2017/2018 cannot be proven.

Engineering-only repairs to access syntax/runtime plumbing may be made only if they cannot alter scientific bytes or expose an EFN scientific endpoint before the repair is frozen.

## No-rescue rule

After the first technically valid EFN endpoint, do not change or search:

- HDBSCAN parameters;
- recurrent-stability formula or annual combiner;
- year weights;
- GEO6 dimensions or speed scale;
- native field mapping;
- quality filters;
- label canonicalization;
- label eligibility/overlap thresholds;
- ranking/tie breakers;
- metric;
- budgets;
- evaluator;
- fusion/reranking;
- survey calibration;
- alternate EFN cohort/release.

Any future method after failure must be a separately motivated and independently frozen successor, not an EFN-result-informed repair of recurrent-EOM v1.

## Firewall declarations

Every pretruth and result artifact must assert:

- `scientific_role='PRISTINE_EXTERNAL_EFN_2017_2018_VALIDATION_ONLY'`;
- `catalogue='J/A+A/667/A157'`;
- `catalogue_rows_expected=824`;
- `years=[2017,2018]`;
- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `orbittrace_target_access=false`;
- `sonotaco_used_for_tuning=false`;
- `efn_post_result_parameter_search=false`.
