# OrbitTrace GMN v31 measurement-uncertainty schema gate v1

## Scientific role

This is a **target-excluded, truth-free feasibility gate only**. It asks whether the exact GMN 2022+2023 event universe already used by the passed v31-principle development route can be joined, by event ID, to the reported marginal geocentric radiant/speed uncertainties in the official GMN monthly trajectory summaries.

It does not create, score, rank, perturb, clone, refit, or evaluate any v31 successor. A PASS only establishes that a later, separately frozen measurement-error method could technically use the information.

## Why this gate is scientifically distinct

The active v31 parser was already audited and exposes only `id,year,sol,sun_lon,ecl_lat,vg` plus hidden-label placeholders; it drops measurement uncertainties. Earlier uncertainty-inflated quartet experiments (#57/#61) changed the quartet detector score and are permanently closed. The failed v31 margin-confidence experiment changed only post-hoc fusion of the existing fixed margin and is also closed. This gate changes neither mechanism. It only audits whether **new raw measurement-error information** exists for the immutable v31 events.

No result from #57, #61, the v31 near-passes, or SonotaCo is used to choose an uncertainty multiplier, clone count, covariance rule, statistic, transform, threshold, seed, fusion rule, or scientific endpoint here.

## Frozen source panel

- Years: **2022 and 2023 only**.
- Months: all twelve official GMN monthly trajectory summaries in each year.
- URL template: `https://globalmeteornetwork.org/data/traj_summary_data/monthly/traj_summary_monthly_{year}{month:02d}.txt`.
- Raw delimiter/encoding and fixed field locations are inherited from the already-established `real_shower_meta_stage0` parser:
  - event ID: field 0
  - solar longitude: field 5
  - RA sigma: field 8
  - Dec sigma: field 10
  - geocentric-speed sigma: field 16
- No shower/code/orbit/quality field is used by this gate.

The target v31 event universe is reconstructed with the exact pinned label-free v8/active-parser source chain already used by the passed GMN v31-principle route. The audit must first reproduce the exact 2022/2023 target-excluded scan universe and then compare its event IDs with the raw uncertainty map.

## Firewall order

For each raw record the implementation may inspect only event ID and solar longitude first. Solar longitude is normalized to `[0,360)`. If it lies in the inclusive protected interval **20.0°–55.0°**, the record is discarded immediately and no uncertainty field from that record may be indexed, interpreted, retained, summarized, or emitted.

Only outside the protected interval may fields 8, 10, and 16 be parsed. Shower labels, shower codes, orbital elements, RA/Dec/Vg point estimates, and target information are never interpreted by this audit.

No per-event uncertainty value is written to the artifact. Only aggregate counts/fractions and distribution summaries over already-retained target-excluded events may be emitted.

## Frozen feasibility gates

All must pass:

1. All 24 fixed monthly sources are retrieved successfully and recorded by SHA-256.
2. The reconstructed active scan has exactly years 2022 and 2023 and contains no event in 20°–55°.
3. Every active-scan event ID is unique within its year.
4. At least **95%** of active-scan events in each year join to a raw record with finite, nonnegative RA, Dec, and Vg marginal uncertainties. The 95% completeness floor is inherited from the project's earlier real-shower uncertainty feasibility gate; it is not chosen from this result.
5. No protected-interval uncertainty field is accessed by the implementation's explicit control flow.
6. No shower truth, SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY, or DMS is accessed.

Strictly-positive uncertainty fractions and aggregate median/p90/p99 values may be reported as diagnostics only. They have **no hidden continuation threshold** and cannot be used to tune a later method.

## Decision

- PASS: `PASS_GMN_V31_MEASUREMENT_UNCERTAINTY_SCHEMA_V1`. This authorizes only a separately frozen scientific proposal selected from external physical/statistical motivation before its first outcome.
- FAIL: `FAIL_GMN_V31_MEASUREMENT_UNCERTAINTY_SCHEMA_V1`. The exact raw-uncertainty transport route is closed; no year substitution, completeness relaxation, alternate uncertainty field, imputation, or parser rescue selected from the outcome.

Regardless of verdict, no SonotaCo benchmark is authorized by this gate.