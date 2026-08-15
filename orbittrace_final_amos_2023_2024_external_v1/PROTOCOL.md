# OrbitTrace final method — AMOS 2023/2024 one-shot external-validation protocol v1

## Status and scientific role

This protocol is frozen **after OrbitTrace method selection is closed in PR #1267 and before any AMOS 2023/2024 event-level scientific value is accessed**.

The primary method is fixed as exact density-synchronous recurrent-EOM HDBSCAN v1 from PR #1263, binding execution head:

`182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`

The primary scientific question is deliberately narrow:

> On a genuinely external AMOS 2023/2024 survey, does the already-selected density-synchronous extraction retain its preregistered advantage over its exact recurrent-EOM parent without sacrificing the parent's recovery, precision, reciprocal-rank quality, or fragmentation?

AMOS is the **single final external test**. A technically valid primary failure is binding and closes the external-generalization claim. No alternate final method, threshold, subset, survey, or post-result rescue is allowed.

No AMOS event row, radiant, velocity, shower association, orbit element, uncertainty, or comparator-quality field is accessed by this freeze.

---

## 1. Supersession of older unexecuted AMOS endpoints

PR #1244 froze an earlier AMOS endpoint for recurrent-EOM v1. PR #1248 froze a supplementary recurrent-EOM-vs-literature AMOS benchmark. Both were scientifically careful **pre-data** protocols, and both remain permanent provenance records.

Neither old endpoint has been scientifically executed and no AMOS event-level data have been opened.

Because methodology selection subsequently promoted #1263 and is now explicitly closed before AMOS access, this protocol **supersedes #1244 and #1248 as the only scientific AMOS execution endpoint**. Their audited transfer, adapter, comparator, and fail-closed engineering definitions may be inherited where unchanged, but their old recurrent-EOM primary hypothesis must not be executed as a separate chance before or after this endpoint.

There is exactly one AMOS truth opening and one final primary decision.

---

## 2. Frozen primary method — exact density-synchronous recurrent-EOM #1263

Use the exact selected method unchanged.

### Representation and hierarchy

- `GEO6 = (cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72)`;
- pooled two-year HDBSCAN hierarchy on the complete retained AMOS 2023+2024 canonical geometry;
- `min_cluster_size=10`;
- `min_samples=10`;
- metric `euclidean`;
- ordinary HDBSCAN hierarchy construction unchanged;
- `cluster_selection_epsilon=0.0`;
- `allow_single_cluster=False`.

### Exact density-synchronous extraction

For every condensed-tree node `C`, split its normalized alive-mass persistence by AMOS calendar year to obtain `A_2023^C(lambda)` and `A_2024^C(lambda)` using the exact #1263 algorithm with annual normalization by the accessible retained event count of each year.

The local node quality is:

`S_sync(C) = integral min(A_2023^C(lambda), A_2024^C(lambda)) d lambda`.

Use exact #1263 density-synchronous kernel blob:

`587a304f451e41b9503272f1783a6c6ebb295000`

with exact recurrent-EOM/FOSC support kernel blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`.

Selection uses the same unchanged FOSC/EOM bottom-up extraction. Candidate ranking is exactly:

1. density-synchronous stability descending;
2. ordinary EOM stability descending;
3. member count descending;
4. deterministic family ID.

No AMOS-specific model training, smoothing, density-lambda alignment, lag, weighted minimum, annual weighting, blend with recurrent-EOM, calibration, reranking, or threshold exists.

---

## 3. Locked primary comparator — exact recurrent-EOM parent

The primary comparator is exact promoted recurrent-EOM HDBSCAN v1, not a refit or altered method.

On the **identical retained AMOS events and identical pooled HDBSCAN hierarchy**, define annual normalized EOM contributions `E_2023(C)` and `E_2024(C)` and parent node quality:

`R(C) = min(E_2023(C), E_2024(C))`.

Use exact recurrent-EOM implementation blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`.

Parent ranking remains recurrent stability, ordinary stability, member count, deterministic family ID.

The primary external test therefore isolates the selected #1263 scientific change: **pointwise density-synchronous overlap versus minimum of separately integrated annual EOM totals on one identical hierarchy**.

The recurrent-EOM comparator is not an alternate final method. If it beats #1263 externally, #1263 fails the final selected-method test; the project does not switch methods after seeing AMOS.

---

## 4. Locked contextual comparator — ordinary HDBSCAN EOM

Also reconstruct exact ordinary HDBSCAN EOM on the identical complete retained AMOS geometry and hierarchy.

Ordinary-EOM performance is reported to show how both recurrence-aware extraction criteria compare with their standard HDBSCAN parent on the new survey.

Ordinary HDBSCAN is **contextual, not part of the primary #1263-vs-recurrent gate**, and cannot become a replacement final OrbitTrace method after AMOS.

Before truth opening, the execution must verify that the custom ordinary extraction exactly reproduces the standard HDBSCAN partition/selected nodes under the pinned runtime, or the run is a technical no-result.

---

## 5. Frozen AMOS years and complete-sample boundary

Exactly calendar years `2023` and `2024` are allowed.

No year substitution, extension, truncation, alternative seasonal window, or post-receipt sample switch is allowed.

The requested population is the **complete solved multi-station AMOS sample** for those two calendar years, including sporadic meteors. It may not be a shower-only, high-confidence-shower-only, spectral-only, fireball-only, manually curated, quality-selected, or publication-selected subset.

The final method applies no new AMOS quality cut beyond validity requirements in the frozen schema/adapter.

---

## 6. Frozen staged blind transfer

The transfer remains logically separated so protected rows and truth are inaccessible to clustering/ranking.

### Stage 1 — minimal blinding index

For each year, open only exact columns:

`event_id,utc_time,solar_longitude_deg`

Before any geometry is opened:

1. require unique nonblank IDs across the requested population;
2. require ISO-8601 UTC timestamps in the stated calendar year;
3. require finite solar longitude in `[0,360)`;
4. exclude **inclusively** every ID satisfying `20.0 <= solar_longitude_deg <= 55.0`;
5. freeze and hash deterministic retained-ID allowlists for 2023 and 2024.

No protected-row radiant, speed, label, orbit, uncertainty, convergence-angle, or other physical value may ever be opened.

### Stage 2 — retained geometry only

Only after Stage 1, open exact base geometry columns for exactly the retained IDs:

`event_id,ra_j2000_deg,dec_j2000_deg,vg_km_s`

Any protected/non-allowlisted ID in a geometry file is a technical failure/no-result.

### Stage 2B — optional comparator supplement

Only after Stage 1, a retained-ID-only supplementary table may be opened for the pre-frozen literature benchmarks:

`event_id,ra_sd_deg,dec_sd_deg,vg_sd_km_s,convergence_angle_deg,q_au,e`

These fields are structurally barred from the primary method, recurrent-EOM parent, and ordinary-EOM feature matrices. Missing compatible Stage-2B fields may make the **supplementary literature benchmark** input-incompatible; they do not invalidate the complete-sample primary external test.

### Stage 3 — shower associations

Shower labels remain in a separate retained-ID-only mapping and must remain unopened until **all complete-sample and all evaluable supplementary method outputs are frozen and SHA-bound**.

Exact columns:

`event_id,shower_code`

Every retained ID must have exactly one row. Unassigned events use literal `SPORADIC`. Shower codes are opaque identifiers to the evaluator.

---

## 7. Frozen AMOS canonical coordinate adapter

Reuse the independently frozen pre-data AMOS canonical adapter from #1244:

- `transform.py` Git blob `612ad23af6e11ac2155282258e3d1429fbe00d67`;
- `adapt.py` Git blob `9a0fb05f94d6a28cd95f97d864e76400056273b0`.

Mapping remains exactly:

- geocentric J2000 equatorial radiant -> ecliptic longitude/latitude with fixed obliquity `23.43928 deg`;
- `sun_lon = wrap180(ecliptic_lon_j2000 - solar_longitude_deg)`;
- `ecl_lat = transformed geocentric ecliptic latitude`;
- `vg = reported geocentric speed km/s` unchanged.

Canonical method input row:

`id, year, sol, sun_lon, ecl_lat, vg`.

No empirical AMOS-to-GMN alignment, offset, scale correction, velocity correction, survey calibration, or fit is authorized.

If AMOS cannot provide documented geocentric J2000 radiant and geocentric speed matching this frozen interpretation, the final panel is input-incompatible rather than adapted post hoc.

---

## 8. Complete pretruth freeze

Before any Stage-3 shower association is opened, freeze and SHA-256 bind the complete proposal for **all three complete-sample methods**: ordinary EOM, recurrent-EOM, and #1263 density-synchronous recurrent-EOM.

Persist at minimum:

- exact retained event IDs and counts by year;
- Stage-1 allowlist hashes;
- canonical geometry hash and GEO6 matrix hash;
- adapter source identities;
- HDBSCAN version and all fixed settings;
- condensed-tree identity/hash;
- ordinary stability map;
- recurrent annual EOM maps and recurrent node-quality map;
- density-synchronous annual alive-mass reconstruction and synchronous node-quality map;
- selected node IDs for all three methods;
- every complete candidate membership/event-ID list;
- every candidate score used for ordering;
- complete deterministic candidate orders;
- mechanism-active flags for recurrent-EOM vs ordinary EOM and #1263 vs recurrent-EOM;
- exact source/blob identities for every scientific implementation;
- firewall declarations.

The primary #1263 and recurrent-EOM methods must be reconstructed from the **same exact pooled hierarchy**, not independent HDBSCAN fits.

No truth-bearing field may enter hierarchy construction, node scoring, FOSC extraction, membership construction, or rank ordering.

---

## 9. Frozen complete-sample evaluator

Only after the pretruth freeze is persisted and hashed may Stage-3 shower associations be opened.

For each AMOS year independently, using only retained IDs from that year:

- an eligible known shower has at least 4 retained accessible events;
- a candidate qualifies for a shower only if overlap >= 4 and candidate precision >= 0.5;
- each eligible shower contributes only its first qualifying candidate rank to recovered-at-k and MRR;
- report recovered @25, @50, @100, @500;
- report top-100 dominant precision;
- report MRR over represented eligible showers under the inherited evaluator semantics;
- report median top-500 fragmentation;
- report qualified/represented shower count;
- report complete candidate count.

Apply **exactly the same evaluator** to ordinary EOM, recurrent-EOM, and density-synchronous recurrent-EOM.

No AMOS label is used to choose a rank budget, family count, threshold, field cut, method parameter, or subset for the primary comparison.

---

## 10. Binding primary external-validation gate

The primary gate copies the exact structural logic used to promote #1263 over recurrent-EOM on GMN, now applied to AMOS 2023/2024.

For **each** AMOS year, density-synchronous recurrent-EOM must satisfy all of:

1. recovered@50 >= recurrent-EOM;
2. recovered@100 >= recurrent-EOM;
3. top-100 dominant precision >= recurrent-EOM;
4. MRR >= recurrent-EOM;
5. median top-500 fragmentation <= recurrent-EOM.

Across the two AMOS years:

6. recovered@100 must be **strictly higher in at least one year**;
7. the density-synchronous mechanism must be active: its selected-node set / complete proposal cannot be identical to recurrent-EOM.

Recovered@25, recovered@500, qualified-shower count, and candidate count are reporting-only and cannot rescue a failed binding gate.

Primary pass token:

`PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_EXTERNAL_VALIDATION`

Otherwise, for a technically valid endpoint:

`FAIL_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_EXTERNAL_VALIDATION`

### Binding interpretation

A PASS is external-survey validation that the **incremental density-synchronous extraction improvement over recurrent-EOM** generalized to untouched AMOS under the same frozen decision rule.

A FAIL means external generalization of the selected #1263 improvement was **not established**. It remains a valid negative result even if #1263 beats ordinary HDBSCAN, Sugar, or catalogue-HDBSCAN on some secondary comparison.

No secondary result can override the primary token.

---

## 11. Ordinary-EOM contextual analysis

Report all complete-sample metrics for exact ordinary HDBSCAN EOM alongside recurrent-EOM and #1263.

This permits scientifically useful questions such as whether recurrence-aware extraction in either form helps relative to standard HDBSCAN on AMOS.

However:

- ordinary-EOM performance does not alter the #1263-vs-recurrent primary pass gate;
- recurrent-EOM performance against ordinary EOM does not create a second external-validation chance;
- if recurrent-EOM beats ordinary EOM while #1263 fails recurrent-EOM, the final selected #1263 method still records a primary FAIL.

---

## 12. Frozen supplementary literature-comparator benchmark

The supplementary benchmark inherits the already-frozen comparator implementations and structural-eligibility contracts from #1248, but substitutes exact #1263 as the fixed OrbitTrace method being compared.

Exactly two literature comparator classes are eligible.

### 12.1 Sugar-style DBSCAN recurrence comparator

Use already-audited comparator adapter Git blob:

`00578445ed0957fb3708bb84fda1df6ef7b5b004`

and Sugar core source SHA-256:

`5b7699a2cf07b9b9ac6dee006c66a9b509af73ee3763093fa333d13e1deca0cb`.

Frozen constants remain:

- min samples `5`;
- epsilon percentile `23`;
- clone iterations `1000`;
- overlap threshold `0.5`;
- minimum recurrence `100`;
- strong recurrence `500`;
- seed root `20170209`.

Freeze AMOS seed namespace unchanged from the pre-data #1248 contract:

- corpus namespace `amos-2023-2024-label-free-sugar-v1`;
- comparator-pair identifier `ORBITTRACE_VS_SUGAR_AMOS`.

Structural eligibility remains:

- finite nonnegative `ra_sd_deg`, `dec_sd_deg`, `vg_sd_km_s`;
- strict `convergence_angle_deg > 15.0`;
- `vg_sd_km_s <= 0.10 * vg_km_s + 1.0`.

### 12.2 Catalogue-HDBSCAN literature comparator

Use comparator adapter blob:

`00578445ed0957fb3708bb84fda1df6ef7b5b004`

and catalogue-HDBSCAN source SHA-256:

`a8b638f56dad2597973178523e8ad15e177a4f57e7fe6159fedc84d754afd3d2`.

Frozen requirements remain:

- HDBSCAN version `0.8.44`;
- minimum cluster size `100`;
- all non-noise native labels are catalogue families.

Structural eligibility remains:

- finite `convergence_angle_deg`, `vg_sd_km_s`, `q_au`, `e`;
- `convergence_angle_deg >= 15.0`;
- `vg_sd_km_s / vg_km_s <= 0.10`;
- `0 <= e <= 1.0`;
- `0 < q_au <= 1.0`.

Comparator-only uncertainty/convergence/q/e fields may never enter #1263 features.

---

## 13. Pairwise fairness for literature comparisons

For each literature comparator separately, freeze its exact retained structural universe **before truth**.

On that same pairwise universe:

- run the literature comparator exactly as frozen;
- independently run exact #1263 from scratch on only those same rows, still pooling 2023+2024 and using unchanged density-synchronous extraction;
- do not give #1263 additional rows unavailable to the comparator;
- do not give #1263 comparator-only fields;
- do not remove rows because of labels, scores, candidate ranks, or posttruth behavior.

These restricted pairwise runs are supplementary and cannot replace the complete-sample primary endpoint.

If required comparator fields are unavailable/incompatible, record:

`NOT_EVALUABLE_INPUT_INCOMPATIBLE_PRETRUTH`

for that comparator. Do not derive proxy fields, relax thresholds, substitute a different literature method, or reduce the primary AMOS endpoint.

---

## 14. Supplementary literature evaluator and gate

For each evaluable comparator/year panel:

1. eligible known showers have at least 4 events in that comparator's frozen pairwise universe;
2. build the shower-by-family F1 matrix for the literature comparator;
3. build the shower-by-candidate F1 matrix for #1263 on the same truth IDs;
4. let `B` be the number of non-noise families produced by the literature comparator in that year, frozen before truth;
5. evaluate the comparator on all `B` families;
6. evaluate #1263 on its first `min(B, number_of_candidates)` candidates in its pretruth pooled order, restricted to that year;
7. apply the same maximum-F1 one-to-one Hungarian assignment to both;
8. report macro-F1 and assigned-shower count with F1 `> 0.5`.

A comparator/year panel is a #1263 **WIN** only if both:

- #1263 macro-F1 is strictly greater than the literature comparator macro-F1; and
- #1263 recovered F1>0.5 count is at least the comparator count.

Supplementary all-panel pass token:

`PASS_DENSITY_SYNC_AMOS_MULTIMETHOD_SUPERIORITY_V1`

requires WIN on all four evaluable panels:

- Sugar 2023;
- Sugar 2024;
- catalogue-HDBSCAN 2023;
- catalogue-HDBSCAN 2024.

If a comparator is pretruth input-incompatible, no reduced-panel PASS is allowed; report:

`INCOMPLETE_DENSITY_SYNC_AMOS_MULTIMETHOD_SUPERIORITY_V1_INPUT_INCOMPATIBLE`.

This supplementary token is **descriptive support only**. It cannot rescue a primary AMOS external-validation FAIL.

---

## 15. Technical no-result conditions

The final endpoint is a technical no-result, not a scientific PASS/FAIL, if a valid primary comparison cannot be reached because of issues such as:

- scientific source/blob pin mismatch;
- adapter pin mismatch;
- unexpected AMOS schema or wrong year;
- duplicate/blank event IDs;
- protected-region survivor;
- physical row outside the Stage-1 retained allowlist;
- missing retained geometry row;
- invalid/nonfinite required base geometry;
- label access before complete pretruth freeze;
- failure to prove #1263 and recurrent-EOM share one identical pooled hierarchy;
- failure of ordinary custom extraction to reproduce standard HDBSCAN;
- selected-node/compact-label mapping failure;
- failure to prove exactly calendar years 2023 and 2024;
- inability to verify the exact pretruth artifact hash before Stage-3 evaluation.

Engineering-only repairs are allowed only when the scientific method bytes, data contract, evaluator, gate, and unopened truth remain unchanged, and the repair is itself frozen before retry.

Input incompatibility limited to optional Stage-2B literature fields does **not** invalidate the complete-sample primary endpoint.

---

## 16. Permanent no-rescue rule

After the first technically valid primary AMOS endpoint, do not change or search:

- HDBSCAN parameters;
- density-synchronous formula;
- recurrent-EOM formula;
- annual weights/normalization;
- GEO6 dimensions or `vg/72` scale;
- coordinate adapter or obliquity;
- quality filters;
- ranking tie-breakers;
- truth overlap/precision thresholds;
- recovered-at-k budgets;
- evaluator semantics;
- comparator budget;
- literature thresholds or seeds;
- subset/year definition;
- survey calibration;
- fusion/reranking;
- final-method identity.

If #1263 fails, do **not**:

- switch the final method to recurrent-EOM because it looked better on AMOS;
- switch to ordinary HDBSCAN or a literature comparator;
- rerun AMOS under an altered criterion;
- search a different external dataset for another chance;
- use the AMOS result to design a new OrbitTrace successor and call it independently validated.

The negative external result is the result.

---

## 17. Required interpretation matrix

The final report must distinguish outcomes rather than compress them into one marketing statement.

### Primary PASS + literature PASS

Strongest outcome: the #1263 incremental improvement generalizes over recurrent-EOM on AMOS and also beats both frozen literature comparator classes on their fair pairwise universes.

### Primary PASS + literature incomplete/fail

External generalization of #1263 over recurrent-EOM is established under the primary gate, but broad literature superiority on AMOS is not established.

### Primary FAIL + literature PASS

The final selected improvement does **not** pass its parent-generalization test. Literature superiority may be reported descriptively, but it does not convert the primary result to a validation success.

### Primary FAIL + literature fail/incomplete

External generalization/superiority is not established on AMOS.

No cell authorizes protected target access automatically.

---

## 18. Paper claim discipline before result

Until AMOS is actually executed, the paper may state only:

- #1263 passed its frozen full-GMN development gate;
- its strict @100 gain was sample-sensitive under the frozen robustness diagnostic;
- precision/MRR improvements were more stable under that diagnostic;
- AMOS is the prespecified untouched final external test and remains pending.

Do not describe #1263 as externally validated before a primary AMOS PASS.

---

## 19. Firewall declarations

Every AMOS pretruth/result artifact must assert at minimum:

- `scientific_role='PRISTINE_FINAL_EXTERNAL_AMOS_2023_2024_VALIDATION_ONLY'`;
- `primary_method='density_synchronous_recurrent_eom_v1'`;
- `primary_method_head='182f07ade6bb5d4be2c80b88df9216bb2d6eee2d'`;
- `blind_exclusion=[20.0,55.0]`;
- `target_information_access=false`;
- `target_region_events_accessed=false`;
- `orbittrace_target_access=false`;
- `maarsy_scientific_access=false`;
- `dms_scientific_access=false`;
- `sonotaco_accessed_for_final_selection=false`;
- `amos_truth_access_before_pretruth=false`;
- `comparator_only_fields_entered_primary_method=false`;
- `amos_post_result_parameter_search=false`;
- `alternate_final_method_selection_after_amos=false`;
- `new_external_survey_rescue_authorized=false`.

This protocol authorizes **pre-data engineering preparation only**. It does not authorize sending the AMOS request or opening AMOS scientific data.
