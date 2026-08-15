# Final #1263 AMOS 2023/2024 — locked scientific execution runbook

## Status

**Pre-data operational runbook only.** This document does not authorize a provider request or access to AMOS data. `EXECUTION_FREEZE.json` is authoritative if any prose here conflicts with it.

The purpose is to make the future one-shot AMOS execution mechanical rather than interpretive after data receipt.

## Preconditions — all required before any provider file is opened

1. Final protocol Git blob must equal `1ddb4bae33a1ae8a6224cbc4abcba5dda70cf993`.
2. Execution freeze Git blob must equal `84e85d69b2fcbf1dcdeeeaf0568c026c50548bd7`.
3. Final selected method remains exact #1263 binding head `182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`.
4. Recurrent kernel blob must equal `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`.
5. Density-synchronous kernel blob must equal `587a304f451e41b9503272f1783a6c6ebb295000`.
6. Pretruth generator blob must equal `b76d7c53ab238cd45f12027947f2098a770ba7b6`.
7. Postfreeze evaluator blob must equal `513a626d056a76029eb1522e19bdb99f973f8bb7`.
8. Blind receipt blob must equal `9fed803aa09f03f779610eaff5304251bbf21020`.
9. Adapter transform / adapter blobs must equal `612ad23af6e11ac2155282258e3d1429fbe00d67` / `9a0fb05f94d6a28cd95f97d864e76400056273b0`.
10. The binding zero-data pipeline, comparator-isolation, transport-reuse, and execution-freeze audits must all remain PASS by exact recorded artifact/result identities.
11. A compliant staged provider transfer must exist. If not, stop. Do not substitute another survey, year, sample, or reconstructed source.

## Stage 1 — blind receipt only

Allowed files for exactly years 2023 and 2024 contain exactly:

`event_id,utc_time,solar_longitude_deg`

Run only the exact frozen blind-receipt implementation.

For each year the receipt must:

- reject blank/duplicate IDs;
- reject wrong-year timestamps;
- reject non-finite/out-of-range solar longitude;
- reject any extra column;
- exclude inclusively every ID with `20.0 <= solar_longitude_deg <= 55.0`;
- emit the retained-ID allowlist/hash only.

Do **not** open a Stage-2, Stage-2B, or Stage-3 file before both Stage-1 allowlists are persisted and hashed.

Any protected-event radiant, speed, orbit, uncertainty, or association must remain unopened permanently.

## Stage 2 — retained physical geometry

Allowed exact header:

`event_id,ra_j2000_deg,dec_j2000_deg,vg_km_s`

Requirements:

- every row ID is in the appropriate Stage-1 retained allowlist;
- every retained ID appears exactly once;
- no other ID appears;
- fields are documented geocentric J2000 RA/Dec and geocentric speed;
- complete retained solved multi-station population, including sporadics;
- no quality-selected, shower-only, fireball-only, case-study, or hand-picked subset.

Run the exact frozen canonical adapter independently for 2023 and 2024. The resulting canonical file may contain only the adapter's historical dummy sentinels (`iau=0`, `complex_key=HIDDEN`) in addition to geometry. Any actual truth-bearing value is a technical no-result.

## Optional Stage 2B — literature comparator supplement

Allowed exact header:

`event_id,ra_sd_deg,dec_sd_deg,vg_sd_km_s,convergence_angle_deg,q_au,e`

This table is optional. It is not an input to the primary final-method generator.

Rules:

- retained IDs only;
- unknown/duplicate IDs fail closed;
- truth-bearing fields fail closed;
- blank comparator-only values are allowed and affect only the corresponding supplementary pairwise universe;
- no imputation or empirical conversion;
- no optional field changes the primary AMOS sample;
- no uncertainty, convergence angle, q, or e value enters ordinary HDBSCAN, recurrent-EOM, or density-synchronous GEO6 clustering.

If incompatible or absent, record `AMOS_LITERATURE_SUPPLEMENT_INPUT_INCOMPATIBLE_PRETRUTH` and continue only the primary one-shot test. Do not request a post-result replacement supplement.

## Pretruth generation — one and only hierarchy construction

With only Stage-2 canonical geometry available, execute exactly one call to the frozen final pretruth generator using exactly:

- canonical 2023 file;
- canonical 2024 file;
- empty/new output directory.

The generator must:

1. verify exact years and protected exclusion;
2. build GEO6;
3. fit exactly one pooled HDBSCAN hierarchy;
4. reproduce vanilla HDBSCAN partition through the custom EOM path;
5. compute ordinary EOM output;
6. compute exact recurrent-EOM on the same hierarchy;
7. compute exact density-synchronous #1263 quality on the same hierarchy;
8. verify annual-EOM reconstruction within the frozen `1e-12` tolerance;
9. freeze selected nodes, memberships, complete candidate orders, score/map/tree/input hashes, and mechanism flags for all three methods;
10. emit `FINAL_DENSITY_SYNC_AMOS_2023_2024_PRETRUTH.json` and `PRETRUTH_SHA256.txt` before any Stage-3 association is opened.

If this run fails technically before a valid pretruth freeze, only non-scientific transport/runtime repair consistent with the protocol may be frozen before another attempt. No method, data, feature, parameter, gate, score, ranking, or subset change is permitted.

## Mandatory checkpoint before labels

Before opening Stage 3, independently verify:

- pretruth file exists and its SHA-256 equals `PRETRUTH_SHA256.txt`;
- role is `PRISTINE_FINAL_EXTERNAL_AMOS_2023_2024_TEST_ONLY`;
- phase is `PRETRUTH_FROZEN`;
- selected final method is #1263;
- years are `[2023, 2024]`;
- blind exclusion is `[20.0,55.0]`;
- all truth/firewall access flags are false;
- the ordinary/recurrent/density-sync outputs share the same condensed-tree hash;
- source pins equal `EXECUTION_FREEZE.json`;
- no Stage-3 file has yet been opened by the scientific runtime.

Persist the exact pretruth hash externally to the evaluator invocation record.

## Stage 3 — retained shower associations only

Allowed exact header:

`event_id,shower_association`

Requirements:

- only retained IDs;
- every retained ID exactly once;
- exact coverage of both retained yearly sets;
- no blank values;
- use explicit `SPORADIC` for no assigned shower;
- no extra columns.

Only after the mandatory checkpoint may these files be supplied to the frozen evaluator.

## One-shot postfreeze evaluation

Run the exact frozen evaluator once with:

- exact pretruth JSON;
- exact pretruth SHA-256 string;
- Stage-3 2023 associations;
- Stage-3 2024 associations;
- empty/new output directory.

The evaluator must not receive geometry and cannot refit HDBSCAN or recompute candidates/ranks.

The first technically valid result file

`FINAL_DENSITY_SYNC_AMOS_2023_2024_EXTERNAL_RESULT.json`

is binding.

## Binding interpretation

Primary PASS token:

`PASS_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION`

Primary FAIL token:

`FAIL_DENSITY_SYNCHRONOUS_RECURRENT_EOM_V1_AMOS_2023_2024_FINAL_EXTERNAL_VALIDATION`

Separately report incremental density-synchrony token:

- `PASS_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS`, or
- `NO_DEMONSTRATED_DENSITY_SYNCHRONY_INCREMENT_OVER_RECURRENT_EOM_AMOS`.

A primary FAIL means the selected final method did not establish external generalization under the prespecified AMOS test. It does **not** authorize switching to recurrent-EOM/ordinary HDBSCAN/literature comparators, changing thresholds or budgets, rerunning AMOS, or seeking another external survey.

A primary PASS is external-validation evidence for the already-selected method; it does not authorize OrbitTrace protected-target access.

## Permanent stop rules

After the first technically valid AMOS endpoint, stop scientific execution. Do not:

- rerun with altered code or environment for a different scientific answer;
- change final method;
- change HDBSCAN settings;
- change annual normalization or density-synchronous/recurrent formula;
- change coordinate mapping or speed scale;
- add/remove quality filters;
- change truth thresholds, metrics, budgets, or evaluator;
- select a different year/sample;
- calibrate to AMOS;
- combine/fuse/rerank based on outcome;
- open another external survey as a replacement chance.

Preserve PASS or FAIL exactly and proceed only to reporting/interpretation.