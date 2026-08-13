# OrbitTrace GMN v31 observer-count file availability v1

## Role

Truth-free, target-excluded feasibility only. This gate asks whether the official GMN 2022+2023 monthly trajectory summaries provide the native `Num (stat)` field for the exact immutable P19 hard-family member universe.

The current official GMN data-schema documentation defines `Num (stat)` / `num_stat` as **the number of stations which observed the meteor**. This official-file route is separate from the earlier Data Explorer REST route, which produced no project data because TLS validation failed on its public preflight request.

No family feature, margin, ranking, recovery metric, SonotaCo scientific value, target information, MAARSY, or DMS is accessed by this gate.

## Immutable event universe

- P19 prelabel SHA-256 `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`.
- exactly 226 hard families;
- exactly 8,794 unique member IDs;
- year counts exactly 4,726 in 2022 and 4,068 in 2023;
- no member replacement/deletion/imputation.

## Frozen raw source

Exactly the 24 official GMN monthly trajectory-summary files:
`https://globalmeteornetwork.org/data/traj_summary_data/monthly/traj_summary_monthly_{year}{month:02d}.txt`, years 2022 and 2023, months 01..12.

Field locations are inherited from the already-established project parser and official schema:
- event ID: field 0;
- solar longitude: field 5;
- `Num (stat)`: field 84.

For each raw row, inspect only event ID and solar longitude first. Rows with inclusive solar longitude **20.0°–55.0°** are discarded before field 84 is indexed or interpreted. For retained rows, field 84 is read only if the event ID belongs to the immutable P19 member set.

No shower label/code, radiant, velocity, orbit, uncertainty, fit-error, convergence-angle, station identity/geography, brightness, height, or other field is interpreted.

## Frozen feasibility gate

All must pass:
1. all 24 monthly sources retrieve and are SHA-256 recorded;
2. exact P19 family/member/year controls reproduce;
3. at least **95%** of immutable members in each year have exactly one finite integer `Num (stat) >= 2`;
4. no protected-interval observer count is indexed;
5. no shower truth, geometry, SonotaCo scientific value, target information, MAARSY, or DMS is accessed.

Only aggregate per-year requested/matched/completeness counts and an overall observer-count histogram may be emitted. The histogram is diagnostic only. The scientific >=4 threshold and weaker-year fraction candidate were already frozen independently of these distributions.

PASS: `PASS_GMN_V31_OBSERVER_COUNT_FILE_AVAILABILITY_V1`.
FAIL: `FAIL_GMN_V31_OBSERVER_COUNT_FILE_AVAILABILITY_V1`.

A FAIL closes this exact official-file transport. No field substitution, completeness relaxation, member deletion/imputation, or year substitution may be selected from the result.