# OrbitTrace GMN v31 Qc availability v1

Truth-free, target-excluded feasibility only. This gate asks whether the official GMN 2022+2023 monthly trajectory summaries provide native maximum convergence angle `Qc (deg)` for the exact immutable P19 hard-family member universe.

Official GMN schema defines `Qc (deg)` as the **maximum convergence angle between all stations that observed the meteor**. The exact 24 monthly files are fixed. Field locations inherited from the established project parser: event ID field 0, solar longitude field 5, Qc field 80.

For every raw row, inspect only event ID and solar longitude first. Inclusive solar longitude 20.0–55.0 is discarded before field 80 is indexed. Qc is read only for retained rows whose event IDs belong to the immutable P19 set.

Immutable controls: P19 prelabel SHA `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`; 226 hard families; 8,794 unique members; 4,726 in 2022 and 4,068 in 2023. No deletion, substitution or imputation.

PASS requires all 24 sources and at least 95% of immutable members in each year with exactly one finite Qc in [0,180]. Only aggregate completeness and a diagnostic Qc histogram/quantiles may be emitted. Those diagnostics cannot alter the separately frozen >15-degree feature.

No shower truth, other geometry, scientific ranking, SonotaCo scientific value, target information/events, MAARSY or DMS is accessed.

PASS: `PASS_GMN_V31_QC15_AVAILABILITY_V1`; FAIL: `FAIL_GMN_V31_QC15_AVAILABILITY_V1`.

A FAIL closes this transport. No tolerance/completeness relaxation, alternate quality field, member deletion/imputation, threshold change or year substitution may be selected from the result.