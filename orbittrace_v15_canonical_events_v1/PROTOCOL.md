# OrbitTrace canonical event interface v1 — transport-only freeze

## Purpose

Freeze one survey-independent event representation so the same frozen OrbitTrace scientific implementation can consume GMN, SonotaCo, and MAARSY without survey-specific detector code.

This is a **format/transport refactor only**. It does not change v15 scoring, proposal construction, recurrence, ranking, nested cardinalities, thresholds, evaluation gates, dataset roles, or any scientific result. It reads no survey file and performs no network access.

## Canonical method-facing record

Every event presented to the common detector has exactly these fields:

- `id`: stable nonempty string;
- `year`: explicit integer year; downstream code must never infer year from the ID;
- `sol`: geocentric solar longitude in degrees, normalized to `[0, 360)`;
- `sun_lon`: Sun-centered geocentric ecliptic radiant longitude in degrees, represented in `[-180, 180]`;
- `ecl_lat`: geocentric ecliptic radiant latitude in degrees, `[-90, 90]`;
- `vg`: geocentric speed in km/s, finite and positive;
- `iau`: constant `0` placeholder in the pre-truth detector interface;
- `complex_key`: constant `HIDDEN` placeholder in the pre-truth detector interface.

No shower label, truth mapping, comparator result, orbit, target identity, or target-region information is part of this method-facing record.

Survey-specific quality cuts remain where they were already frozen. The canonical contract must not invent a new cross-survey quality threshold merely to make row counts look similar.

## GMN adapter

GMN already reaches the frozen detector as event dictionaries containing the canonical geometry names `sol`, `sun_lon`, `ecl_lat`, and `vg`. The GMN adapter therefore performs validation/field projection only. It must not recompute coordinates, rescale speed, choose years, alter event order, or modify detector inputs.

The caller supplies the already-governed allowed GMN year set. This module does not select a new GMN train/test/validation year.

## SonotaCo adapter

The frozen SonotaCo normalizer already emits the same method-facing geometry:

`id, year, sol, sun_lon, ecl_lat, vg, iau=0, complex_key=HIDDEN`.

Its existing conversion remains authoritative: decode solar longitude first, remove closed solar-longitude interval 20°–55° before other scientific geometry, convert RA/Dec with the frozen ecliptic helper, and set `sun_lon = wrap180(lambda_ecl - sol)`.

The canonical SonotaCo adapter only validates/projects the output of that frozen normalizer. It does not parse the raw SonotaCo archive and does not alter the frozen SonotaCo cuts.

## MAARSY adapter

Use the already-frozen public schema mapping unchanged:

- native `sun_lon` -> canonical `sol`;
- native `slon` -> canonical `sun_lon` after `wrap180`;
- native `slat` -> canonical `ecl_lat`;
- native `vels` -> canonical `vg = ||vels||` in km/s.

Stable final-pipeline identity is `MAARSY|YEAR|ARCHIVE_MEMBER|ROW_INDEX_0BASED`.

For the fixed final external route, only year 2021 is the unlabeled recurrence-support scan and year 2022 is the scored validation scan. The adapter itself never opens truth. The scientific runner must read/normalize `sun_lon` first and remove every row with `20 <= sol <= 55` before reading/passing `slon`, `slat`, or `vels` for that row. The adapter rejects any blinded row that nevertheless reaches it.

No proxy radiant, learned transform, unit inference, orbit substitution, or pseudo-year is permitted.

## Shared-detector rule

After canonicalization, **survey identity may not branch the scientific detector**. GMN, SonotaCo, and MAARSY canonical rows must enter the same frozen detector functions and the same v15 ranking/scoring implementation. Any future source that contains `if survey == ...` (or equivalent) inside proposal, family, scoring, multiplicity, consensus-rank, or evaluation science is a protocol violation.

Differences in sampling density are handled only by the already-frozen method semantics; they are not repaired by format-specific scientific code.

## Equivalence / firewall gates

Before any new scientific execution, all must hold:

1. canonical records contain exactly the eight fields above;
2. GMN and SonotaCo projection preserves their existing geometry values exactly as floats;
3. MAARSY mapping exactly reproduces the frozen `sun_lon/slon/slat/vels` transform;
4. year is explicit and never inferred from event IDs;
5. target interval 20°–55° cannot enter the MAARSY geometry adapter;
6. truth-bearing keys are rejected before projection;
7. the adapter package has no network, HDF5/archive, catalogue-download, or known-shower loader;
8. no DMS route, replacement dataset, new year selection, or scientific threshold is introduced;
9. no scientific execution marker is included in this source-only freeze.

Passing these gates establishes only a common data interface. It is not a development PASS, literature PASS, external-validation PASS, or authorization to reveal OrbitTrace.
