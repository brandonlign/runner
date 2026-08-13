# OrbitTrace GMN v31 hard-family measurement package v1

## Role
Truth-free target-excluded input packaging only. This is downstream of the binding PASS `PASS_GMN_V31_MEASUREMENT_UNCERTAINTY_SCHEMA_V1` and upstream of any measurement-error successor. It computes no labels, margins, rankings, recoveries, or promotion metrics.

## Immutable family universe
Use the exact P19 prelabel payload SHA-256 `276129ef8f9f31a1f8e7b1570c15f5e67ed1a7274f293f5da65bab60f86e32b8`, exactly **226** hard families and their existing event IDs. No candidate generation, family repair, deletion, deduplication, or membership change.

## Raw panel and firewall
Use only GMN 2022 and 2023 monthly trajectory summaries. For each raw row, inspect event ID and solar longitude first. Inclusive solar longitude 20°–55° is discarded before RA, Dec, Vg or uncertainty fields are indexed. Shower labels/codes, orbit elements, quality metadata and target information are never interpreted.

For retained rows needed by at least one immutable hard family, package exactly:
`id, year, sol, ra, dec, vg, ra_sigma, dec_sigma, vg_sigma`.
No other raw field is emitted.

## Required integrity gates
1. P19 payload identity and 226-family universe reproduce exactly.
2. Every unique immutable hard-family member has exactly one retained raw record and all six point-estimate/uncertainty values are finite; uncertainties are nonnegative and Vg is positive. **100% member coverage is mandatory.** No missing-member deletion or imputation.
3. Raw point estimates reproduce the active canonical parent geometry using fixed J2000 obliquity 23.43928° and `wrap180(ecliptic_longitude - solar_longitude)`. Circular solar-longitude and Sun-centered-longitude differences, ecliptic-latitude difference and Vg difference must each be <= `1e-9` in their native units for every packaged member.
4. No event in 20°–55° is packaged.
5. No shower truth, SonotaCo 2013/2014, OrbitTrace target information/events, MAARSY or DMS is accessed.

## Output
A deterministic JSONL package sorted by `(year,id)`, a manifest with SHA-256, counts and maximum geometry-equivalence errors, and no labels. A PASS is `PASS_GMN_V31_MEASUREMENT_UNCERTAINTY_PACKAGE_V1`.

A FAIL closes this exact package route. No tolerance relaxation, missing-member deletion, imputation, alternate raw field, year substitution or geometry transform may be selected from the outcome.