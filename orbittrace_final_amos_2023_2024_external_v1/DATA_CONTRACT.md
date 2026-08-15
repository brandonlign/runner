# OrbitTrace final AMOS 2023/2024 staged data contract v1

This is a transport/schema contract for the one-shot final AMOS protocol in `PROTOCOL.md`. It is frozen before any AMOS event-level scientific access and does not alter the selected #1263 method, comparators, evaluator, or gate.

## Stage 1 — blinding index only

Request one complete file per calendar year:

- `AMOS_2023_INDEX.csv`
- `AMOS_2024_INDEX.csv`

Exact header, no extra columns:

```text
event_id,utc_time,solar_longitude_deg
```

Requirements:

- stable nonblank `event_id`;
- IDs unique within and across the requested 2023/2024 population;
- ISO-8601 UTC timestamp whose calendar year matches the file;
- finite `solar_longitude_deg` in `[0,360)`;
- complete solved multi-station sample, including sporadics;
- no radiant, speed, orbit, uncertainty, quality, shower, or target information.

Only Stage 1 may be opened initially.

The frozen blind receipt removes every ID with inclusive `20.0 <= solar_longitude_deg <= 55.0` and emits deterministic retained-ID allowlists/hashes.

Protected IDs never proceed to later stages.

## Stage 2 — retained base geometry only

Only after the Stage-1 allowlist is frozen, request one geometry file per year for **exactly the retained IDs and no others**:

- `AMOS_2023_GEOMETRY_RETAINED.csv`
- `AMOS_2024_GEOMETRY_RETAINED.csv`

Exact header:

```text
event_id,ra_j2000_deg,dec_j2000_deg,vg_km_s
```

Provider definitions must be compatible with:

- `ra_j2000_deg`: geocentric radiant right ascension, J2000, degrees in `[0,360)`;
- `dec_j2000_deg`: geocentric radiant declination, J2000, degrees in `[-90,90]`;
- `vg_km_s`: positive geocentric speed in km/s from the same solved multi-station solution.

Requirements:

- exactly one row for every retained ID;
- no protected/non-allowlisted ID;
- no shower association/code/flag;
- no extra quality/orbit/uncertainty columns;
- all required base geometry finite and physically valid.

These rows are the only physical inputs allowed to ordinary EOM, recurrent-EOM, and #1263 density-synchronous recurrent-EOM.

## Stage 2B — optional retained comparator supplement

This layer is optional for the primary final test and exists only to execute the already-frozen Sugar-style and catalogue-HDBSCAN literature comparisons fairly.

If available, request one retained-ID-only file per year:

- `AMOS_2023_COMPARATOR_SUPPLEMENT_RETAINED.csv`
- `AMOS_2024_COMPARATOR_SUPPLEMENT_RETAINED.csv`

Exact header:

```text
event_id,ra_sd_deg,dec_sd_deg,vg_sd_km_s,convergence_angle_deg,q_au,e
```

Definitions must refer to the same solved multi-station solution as Stage 2:

- `ra_sd_deg`: reported uncertainty/standard deviation for geocentric RA, degrees;
- `dec_sd_deg`: reported uncertainty/standard deviation for geocentric Dec, degrees;
- `vg_sd_km_s`: reported geocentric-speed uncertainty, km/s;
- `convergence_angle_deg`: documented multi-station convergence angle, degrees;
- `q_au`: perihelion distance, AU;
- `e`: eccentricity.

Rules:

1. only Stage-1 retained IDs may appear;
2. no shower association or truth-bearing field may appear;
3. blank/null values are allowed only as explicit missing comparator metadata and make that event structurally ineligible for whichever frozen comparator requires the field;
4. supplied numeric values must be finite where present;
5. negative uncertainties are invalid;
6. no other orbit element or quality field is authorized;
7. Stage-2B fields must never enter the feature matrix, hierarchy, scoring, extraction, or ranking of ordinary EOM, recurrent-EOM, or #1263.

If Stage 2B is unavailable or semantically incompatible, the affected supplementary literature comparator is `NOT_EVALUABLE_INPUT_INCOMPATIBLE_PRETRUTH`. The primary complete-sample AMOS test remains valid if Stages 1, 2, and 3 satisfy their contracts.

## Pretruth execution boundary

After Stage 2 (and Stage 2B if available), the pretruth process must freeze complete outputs for:

- ordinary HDBSCAN EOM;
- exact recurrent-EOM;
- exact #1263 density-synchronous recurrent-EOM;
- every evaluable Sugar-style pairwise universe/output;
- every evaluable catalogue-HDBSCAN pairwise universe/output.

The pretruth artifact and SHA-256 must be persisted before Stage 3 is opened.

The pretruth generator must have **no label-file argument** and must fail if any truth-bearing field is present in its input schema.

## Stage 3 — retained shower associations only

Only after the complete pretruth hash is frozen may one label file per year be opened:

- `AMOS_2023_LABELS_RETAINED.csv`
- `AMOS_2024_LABELS_RETAINED.csv`

Exact header:

```text
event_id,shower_code
```

Requirements:

- exactly one row per retained event ID and no other IDs;
- nonblank `shower_code`;
- unassigned meteors use literal `SPORADIC`;
- shower codes are treated as opaque identifiers;
- no radiant, speed, orbit, quality, uncertainty, target, or other physical field.

The evaluator must require the exact pretruth SHA-256 and must not be able to recompute candidates, hierarchy, pairwise eligibility, family budgets, or ranking.

## Complete-sample primary method input

After the frozen adapter, the only canonical row entering all three complete-sample HDBSCAN methods is exactly:

```text
id,year,sol,sun_lon,ecl_lat,vg
```

No Stage-2B field may survive into that object.

## Fail-closed conditions

Before a technically valid primary endpoint, any of the following produces an engineering no-result rather than a scientific PASS/FAIL:

- unexpected/extra column in Stages 1, 2, or 3;
- duplicate/blank ID;
- wrong-year Stage-1 timestamp;
- invalid/nonfinite Stage-1 solar longitude;
- Stage-2 or Stage-3 ID not in the retained allowlist;
- missing Stage-2 row for a retained ID;
- protected ID in any later layer;
- invalid required Stage-2 geometry;
- Stage-3 truth opened before exact pretruth freeze;
- pretruth hash mismatch;
- truth-bearing field reaching the pretruth process.

Stage-2B-only incompatibility affects only supplementary literature comparators and must not be converted into a primary no-result or used to alter the primary sample.

## Data minimization and firewall

No request or file in this contract authorizes:

- OrbitTrace protected target information/events;
- physical values for `[20°,55°]` protected rows;
- MAARSY or DMS scientific data;
- a different AMOS year;
- a selected shower-only AMOS sample;
- AMOS fields for survey-specific calibration/tuning;
- any post-result new field request intended to rescue performance.

No AMOS scientific data existed or was accessed when this contract was frozen.
