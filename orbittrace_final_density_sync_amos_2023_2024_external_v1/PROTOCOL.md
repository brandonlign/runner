# OrbitTrace final-selected density-synchronous recurrent-EOM — AMOS 2023/2024 one-shot protocol

## Status and authority

**Frozen before any AMOS 2023/2024 event-level scientific access.**

This is the single final external-test protocol authorized by method-selection closure PR #1267. The selected method is exactly density-synchronous recurrent-EOM HDBSCAN v1 from PR #1263, binding execution head:

`182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`

This protocol supersedes the unexecuted recurrent-EOM-specific AMOS endpoint in PR #1244 as the sole AMOS scientific endpoint. PR #1244 remains preserved as historical provenance and audited infrastructure. The old endpoint and this endpoint must not both be executed sequentially.

No AMOS request is sent and no AMOS scientific row is opened by this freeze.

## 1. Immutable selected method

Use exact #1263 unchanged:

- representation: `GEO6 = (cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72)`;
- pooled two-year HDBSCAN hierarchy;
- `min_cluster_size=10`;
- `min_samples=10`;
- metric `euclidean`;
- cluster selection `eom`;
- `cluster_selection_epsilon=0.0`;
- `allow_single_cluster=False`;
- `prediction_data=False`;
- exact recurrent-EOM kernel blob `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`;
- exact density-synchronous kernel blob `587a304f451e41b9503272f1783a6c6ebb295000`;
- exact #1263 scientific GMN runner blob `157813ca331165180a6d20aa71bfc78d5984396f` as implementation provenance;
- density-synchronous node quality `S_sync(C)=integral min(A_2023^C(lambda),A_2024^C(lambda)) d lambda`, with annual alive mass normalized by accessible event count in each AMOS year;
- exact HDBSCAN/FOSC EOM extraction on that scalar quality;
- rank by descending density-synchronous quality, then descending ordinary HDBSCAN stability, descending member count, ascending deterministic family ID.

The two AMOS years replace GMN year labels only in the already-defined two-year annual-normalization calculation. There is no AMOS training, fit, calibration, thresholding, weight selection, score blend, or survey-specific adjustment.

No later robustness result, comparator outcome, or external observation may change this method.

## 2. Permanent final-test panel

Exactly AMOS calendar years `2023` and `2024` are allowed.

No alternate AMOS year, selected event subset, spectral/fireball-only sample, case-study sample, reconstructed catalogue, other external survey, or replacement survey is allowed if this panel is unavailable or negative.

AMOS remains one shot.

## 3. Protected-region receipt firewall

The provider transfer must preserve the already-audited three-layer design from PR #1244.

### Stage 1 — blind index only

Complete solved multi-station population for 2023/2024 with exactly:

`event_id, utc_time, solar_longitude_deg`

For each year:

1. reject duplicate or blank IDs, wrong-year timestamps, non-finite longitude, or extra columns;
2. remove inclusively every ID with `20.0 <= solar_longitude_deg <= 55.0`;
3. persist a deterministic retained-ID allowlist and hash;
4. only retained IDs may proceed to physical geometry.

Protected-row radiant, speed, orbit, uncertainty, and shower association must never be opened.

### Stage 2 — retained physical geometry only

For retained IDs only, exact primary-method fields:

`event_id, ra_j2000_deg, dec_j2000_deg, vg_km_s`

The sample must be the complete retained solved multi-station population, including sporadics, not a shower-only or quality-selected subset.

### Stage 3 — shower associations only after pretruth freeze

Separate retained-ID keyed mapping:

`event_id, shower_association`

The label mapping remains inaccessible until all three candidate orders described below are persisted and hash-frozen.

## 4. Immutable AMOS canonical adapter

Reuse only the already-audited zero-data adapter from PR #1244 by exact source identity:

- `transform.py` blob `612ad23af6e11ac2155282258e3d1429fbe00d67`;
- `adapt.py` blob `9a0fb05f94d6a28cd95f97d864e76400056273b0`.

The transform remains:

- geocentric J2000 RA/Dec -> geocentric ecliptic longitude/latitude using fixed obliquity `23.43928 deg`;
- `sun_lon = wrap180(ecliptic_lon_j2000 - solar_longitude_deg)`;
- `ecl_lat = geocentric ecliptic latitude`;
- `vg = provider geocentric speed km/s` unchanged;
- no empirical alignment, quality cut, offset, scale correction, velocity correction, or survey calibration.

The canonical row entering all primary hierarchy methods is exactly:

`id, year, sol, sun_lon, ecl_lat, vg`

If AMOS cannot supply documented geocentric J2000 radiant and geocentric speed consistent with this contract, the final test remains acquisition-blocked rather than changing the transform.

## 5. Three locked primary hierarchy methods

Fit exactly one pooled HDBSCAN hierarchy to the retained 2023+2024 GEO6 events.

On this identical hierarchy freeze three complete candidate outputs before truth:

### A. Ordinary HDBSCAN EOM baseline

Use ordinary HDBSCAN stability and standard EOM extraction/ranking.

Scientific role: primary external baseline.

### B. Recurrent-EOM predecessor comparator

Use exact recurrent-EOM quality:

`R(C)=min(E_2023(C),E_2024(C))`.

Scientific role: locked immediate predecessor comparator only. It cannot become the final method after AMOS.

### C. Final selected density-synchronous method

Use exact #1263 quality:

`S_sync(C)=integral min(A_2023^C(lambda),A_2024^C(lambda)) d lambda`.

Scientific role: sole final method under test.

All three outputs must share the identical retained events, GEO6 matrix, core distances, mutual reachability graph, MST, condensed hierarchy, HDBSCAN parameters, and evaluator.

## 6. Mandatory pretruth freeze

Before any AMOS shower association is opened, persist and hash-freeze:

- exact retained IDs and counts by year;
- canonical geometry hash and GEO6 matrix hash;
- condensed-tree hash;
- ordinary-stability map hash;
- recurrent annual-EOM maps and recurrent scalar-quality hash;
- density-synchronous annual reconstruction and scalar-quality hash;
- selected node IDs for ordinary, recurrent, and density-synchronous methods;
- every candidate membership/event-ID list for all three methods;
- every ordering score and complete deterministic pooled order for all three methods;
- mechanism-activity flags ordinary vs recurrent, recurrent vs density-synchronous, and ordinary vs density-synchronous;
- all source/blob/environment identities;
- declarations that no truth-bearing field has been accessed.

Candidate generation, membership construction, node selection, and ranking must be impossible to recompute after labels are opened except for byte-for-byte verification.

## 7. External evaluator

After the complete pretruth freeze, open only the retained-ID shower-association map.

For each year independently:

- eligible known shower: at least 4 retained labeled events in that year;
- candidate qualifies for a shower only if overlap >= 4 and precision >= 0.5;
- each eligible shower contributes only its first qualifying rank;
- report recovered @25/@50/@100/@500;
- report full-catalogue qualified/represented showers;
- report top-100 dominant precision;
- report mean reciprocal rank under the exact inherited evaluator semantics;
- report median top-500 fragmentation.

The evaluator and truth semantics must be byte-equivalent to the frozen recurrent-EOM/#1263 GMN evaluator except for AMOS input transport.

## 8. Primary one-shot external-validation gate

The final selected density-synchronous method passes AMOS external validation only if **all** conditions below hold.

### Versus ordinary HDBSCAN EOM, each year separately

For both 2023 and 2024:

1. recovered@50 is not lower;
2. recovered@100 is not lower;
3. top-100 dominant precision is not lower;
4. MRR is not lower;
5. median top-500 fragmentation is not higher.

Across the two years:

6. recovered@100 is strictly higher than ordinary HDBSCAN in at least one year;
7. density-synchronous extraction/order differs from ordinary HDBSCAN, proving the selected method is active.

### Versus recurrent-EOM predecessor, each year separately

For both 2023 and 2024:

8. recovered@50 is not lower;
9. recovered@100 is not lower;
10. top-100 dominant precision is not lower;
11. MRR is not lower;
12. median top-500 fragmentation is not higher.

A strict recovered@100 improvement over recurrent-EOM is **not** required for the primary external-validation PASS. It is recorded separately as incremental evidence because #1265 already established that the full-GMN +1 recall gain was perturbation-sensitive.

Primary PASS token:

`PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION`

Otherwise:

`FAIL_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION`

A technically valid FAIL means external generalization of the selected final method was not established under the prespecified AMOS test. No method switch or replacement external panel is authorized.

## 9. Predeclared incremental density-synchrony result

Separately report whether density-synchronous extraction shows incremental external advantage over recurrent-EOM.

Incremental PASS requires:

- all recurrent-EOM no-regression conditions 8–12 above; and
- recovered@100 strictly exceeds recurrent-EOM in at least one AMOS year; and
- density-synchronous selected nodes or complete order differs from recurrent-EOM.

Token:

`PASS_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS`

otherwise:

`NO_DEMONSTRATED_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS`

The second token does not by itself rewrite the primary external-validation result; it narrows the claim about the incremental synchrony penalty.

## 10. Locked literature-comparator supplement

If and only if AMOS directly supplies the optional retained-ID-only fields already frozen in PR #1248, the same single AMOS receipt may also execute the pre-data literature benchmark.

Required optional fields are limited to those already frozen for the Sugar-style and catalogue-HDBSCAN implementations, including directly supplied uncertainties/convergence angle and `q,e` where required. They may not enter the OrbitTrace GEO6 methods.

Reuse exact previously frozen comparator implementation identities from PR #1248:

- literature adapter blob `00578445ed0957fb3708bb84fda1df6ef7b5b004`;
- Sugar core SHA-256 `5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb`;
- catalogue-HDBSCAN SHA-256 `a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2` with its frozen HDBSCAN 0.8.44 / min-cluster-size 100 configuration.

For each comparator-specific pretruth eligible universe, rerun exact #1263 density-synchronous method on the identical rows and evaluate at the comparator's frozen family-count budget using the already-established one-to-one Hungarian F1 semantics.

Supplementary all-panel literature superiority requires #1263 to have strictly higher macro-F1 and at least equal recovered `F1>0.5` families on all four panels:

- Sugar 2023;
- Sugar 2024;
- catalogue-HDBSCAN 2023;
- catalogue-HDBSCAN 2024.

PASS token:

`PASS_FINAL_DENSITY_SYNC_AMOS_ALL_PANEL_LITERATURE_SUPERIORITY`

If the optional provider fields are absent/incompatible before truth, return:

`AMOS_LITERATURE_SUPPLEMENT_INPUT_INCOMPATIBLE_PRETRUTH`

That status does not alter the primary AMOS external-validation gate and does not authorize proxy reconstruction, alternate formulas, or a second data request after seeing primary scientific outcomes.

## 11. Technical no-result conditions

Classify as technical no-result before any valid scientific endpoint if any occurs:

- source/blob pin mismatch;
- wrong AMOS year;
- duplicate/blank ID;
- protected-region survivor;
- extra or truth-bearing column in a pretruth stage;
- geometry row outside retained allowlist;
- missing retained primary geometry row;
- non-finite/invalid primary geometry;
- label access before all three primary candidate orders freeze;
- adapter identity mismatch;
- ordinary custom extraction fails exact identity against vanilla HDBSCAN;
- recurrent or density-synchronous annual reconstruction fails its frozen mathematical audit;
- selected-node/compact-label mapping fails;
- the three primary methods do not share one exact hierarchy;
- execution cannot prove exact 2023/2024 use.

Engineering-only transport/runtime repairs are allowed only if they cannot alter scientific bytes and are frozen before the next attempt. They do not authorize a scientific rule change.

## 12. Permanent no-rescue rule

After the first technically valid AMOS endpoint, do not change or search:

- final method;
- HDBSCAN parameters;
- annual normalization;
- recurrent or density-synchronous formula;
- coordinate transform;
- speed scale;
- quality filters;
- ranking/tie rules;
- truth threshold or overlap rule;
- metric;
- budgets;
- evaluator;
- comparator implementation;
- year subset;
- survey subset;
- calibration/alignment;
- fusion/reranking;
- external dataset.

Do not switch to recurrent-EOM, ordinary HDBSCAN, or a literature method based on AMOS outcomes.

## 13. Firewall declarations

Every pretruth/result artifact must assert:

- `scientific_role='PRISTINE_FINAL_EXTERNAL_AMOS_2023_2024_TEST_ONLY'`;
- `selected_final_method='density_synchronous_recurrent_eom_hdbscan_v1_pr1263'`;
- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `orbittrace_target_access=false`;
- `sonotaco_access=false`;
- `asfn_access=false`;
- `efn_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `amos_post_result_parameter_search=false`;
- `new_external_survey_hunt=false`.

## 14. Authorization boundary

This protocol authorizes **pre-data implementation and zero-data audits only**.

It does not authorize:

- sending the AMOS provider request;
- opening AMOS event-level scientific data;
- accessing protected-region values;
- running a scientific AMOS endpoint.

Those remain blocked until a compliant transfer exists and the complete final-selected-method pipeline has passed zero-data source/receipt audits under a separately frozen execution record.
