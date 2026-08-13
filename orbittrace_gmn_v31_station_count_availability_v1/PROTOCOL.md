# OrbitTrace GMN v31 station-count availability v1

## Role

Truth-free, target-excluded feasibility only. This gate asks whether the official GMN observing-station participation table can provide an observation-count value for the exact immutable P19 hard-family member universe used by the passed GMN v31-principle parent.

It computes no family feature, v31 margin, candidate order, recovery metric, or literature result. A PASS only authorizes the separately frozen station-confirmation successor. No SonotaCo scientific outcome is accessed here.

## Immutable event universe

- Exact P19 prelabel payload SHA-256: `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`.
- Exactly 226 hard families.
- Exactly 8,794 unique immutable hard-family member event IDs; no member may be added, removed, replaced, or imputed.
- Years 2022 and 2023 only.
- These members come from the already target-excluded frozen P19 route. The audit does not query meteor geometry or shower labels.

## Frozen source and transport

Official GMN public data store only: `participating_station` table in the Global Meteor Network Data Explorer.

The table semantics are one row per participating observing station for a meteor, keyed by `meteor_unique_trajectory_identifier` and `station_code`. For each immutable event ID, the sole extracted value is:

`n_station = COUNT(*)` over its participating-station rows.

No station code is emitted or used scientifically. No meteor table, shower field, radiant, speed, orbit, uncertainty, target information, or station geography is queried.

Queries may batch event IDs for engineering efficiency, but batching cannot alter the count. Any transport retry/chunk-size change is engineering-only and must preserve the exact SQL aggregation and event universe.

## Frozen feasibility gate

All must pass:

1. P19 SHA, 226-family count, 8,794 unique-event count, and 2022/2023 year counts reproduce exactly.
2. At least 95% of immutable unique members in **each year** receive exactly one finite integer station count >=2. The 95% completeness floor is fixed before querying project station counts and is the project's established schema-completeness feasibility standard.
3. Returned event IDs are a subset of the immutable requested set; duplicates after aggregation are forbidden.
4. No station identity, station geography, shower truth, geometry, target information, SonotaCo scientific value, MAARSY or DMS is accessed.

Only aggregate per-year requested/matched/completeness counts and an overall station-count histogram may be emitted. The histogram is diagnostic only and cannot select or change a later threshold/statistic.

## Decision

PASS: `PASS_GMN_V31_STATION_COUNT_AVAILABILITY_V1`.
FAIL: `FAIL_GMN_V31_STATION_COUNT_AVAILABILITY_V1`.

A FAIL closes this exact GMN station-count transport for v31; no completeness relaxation, member deletion, station-table substitute, raw-field substitute, or year substitution may be chosen from the result.