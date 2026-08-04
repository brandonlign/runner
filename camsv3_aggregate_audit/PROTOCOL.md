# CAMSv3 2011–2015 aggregate-only label and uncertainty audit

Status: frozen before any CAMSv3 label token or data-column value is inspected.

## Development and confirmation boundary

- Development years: **2011–2015**.
- Reserved untouched year: **2016**.
- The structural parser-v2 gate in PR #91 inspected only archive hashes, member names, headers, row counts, and widths. No 2016 value or label token has been read.
- This workflow must not download the 2016 archive.

## Purpose

Determine whether CAMSv3 development years provide usable geometry, reported uncertainties, and a sufficiently populated, bounded label vocabulary for a later separately frozen survey-native mapping audit.

This stage is aggregate-only. It stores no event rows and computes no detector score, calibration window, p-value, AUROC, recall, catalogue endpoint, or GhostStream endpoint.

## Pinned development archives

Use the exact official 2011–2015 archive URLs, SHA-256 hashes, CSV basenames, and row counts already passed by PR #91. Select each CSV only by exact `PurePosixPath(member).name` equality.

Required fields:

- geometry: `LS`, `RA`, `DECL`, `Vg`;
- label: `sh`;
- reported uncertainty: `delta_RA`, `delta_DECL`, `delta_Vg`.

Exact aggregate-audit source SHA-256: `2331a2df893cda15d74dc2fefc3d94ed7759c18636986ce3acd37e47fca6eb63`.

## GhostStream blindness

Remove every row with solar longitude from 20.0° through 55.0° inclusive before any geometry, label, or uncertainty aggregate is formed. No GhostStream radiant, speed, orbit, membership, event list, score, or local background enters this audit.

## Permitted aggregates

The workflow may record only:

- annual and pooled row counts;
- invalid-solar and blind-interval counts;
- geometry completeness;
- completeness and median/p90/p99 of nonnegative finite `delta_RA`, `delta_DECL`, and `delta_Vg`;
- normalized `sh` token counts and top 100 tokens;
- counts of blank, numeric, bounded alphanumeric, and other tokens;
- fraction of nonblank tokens that are printable ASCII and at most 32 characters.

It may not retain or upload any event row or event identifier.

## Frozen gates

Every gate must pass:

1. exact 2011–2015 total row count;
2. zero malformed rows;
3. at least 99% valid solar longitude;
4. geometry completeness outside the blind interval at least 0.98;
5. complete nonnegative `delta_RA`, `delta_DECL`, and `delta_Vg` for at least 90% of geometry-ready rows;
6. at least 10,000 nonblank label rows;
7. at least 20 unique nonblank label tokens;
8. at least 99% of nonblank label rows use printable ASCII tokens no longer than 32 characters;
9. 2016 is absent from every input and result.

## Continuation boundary

A complete pass authorizes only a separately frozen survey-native label-mapping audit on the same 2011–2015 development years. That next audit must define one generic mapping rule before recomputing support. CAMSv3 2016 remains untouched.

A failure kills the CAMSv3 development route without changing gates, years, quality rules, or token handling. No detector benchmark, confirmation run, catalogue scan, or GhostStream application is authorized by this audit.