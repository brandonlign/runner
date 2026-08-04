# SonotaCo 2025 label-token and parser audit

Status: frozen after the PR #56 format gate passed and before any SonotaCo label frequency, feature distribution, window, score, or scientific endpoint is inspected.

## Purpose

Establish a deterministic parser and label mapping for a later independent-survey screen of the exact PR #38 coverage-normalized Mondrian four-clique method.

This remains a data-only stage. It does not decode or execute the scorer, form windows, generate calibration samples, compute a comparator, inspect a candidate score, or evaluate power.

## Frozen inputs

### SonotaCo

- exact URL: `https://www.astro.sk/iaumdcDB/public/data/SNMv3/025a.zip`;
- archive SHA-256 fixed by PR #56: `f4eb716a4b900658fcc658a633d918eca28946f59da75935f1fd5f6bc539bf52`;
- exact member: `025a/_U2_20250101_S.csv`;
- member SHA-256: `30d8cbdf414b2e9d6e587374fec7a4b6fa94c86e76a35e9b335cd4d0cbc917f7`;
- encoding: UTF-8-SIG;
- delimiter: comma;
- published records: 36,826.

### Frozen GMN/MDC mapping

- exact runner artifact: `real-shower-meta-data-audit` from run `30855193522`;
- `audit.json` SHA-256: `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`;
- use only the already frozen shower code, IAU number, eligibility flag, and complex key from its profiles;
- no GMN score or GhostStream information enters this audit.

## Header normalization

Strip leading and trailing ASCII whitespace from every header. The required normalized fields are:

- `sol(deg)`;
- `ra(deg)`;
- `de(deg)`;
- `vg(km/s)`;
- `ra sd(deg)`;
- `de sd(deg)`;
- `vg sd(km/s)`;
- `Ncam`;
- `Er(deg)`;
- `Shower`.

No alternate column or inferred coordinate may replace a missing required field.

## GhostStream blindness

Parse solar longitude first. Rows with valid solar longitude from 20.0° through 55.0° inclusive are discarded before label tokens, feature completeness, matched showers, complex counts, or any other downstream aggregate is formed. Invalid-solar-longitude rows may be counted only as parse failures; their labels must not be read or reported.

## Frozen label rules

Normalize a label token with `strip().upper()`.

- **background token:** empty, contains no ASCII letter, or begins with `SPO`;
- **matched positive token:** exactly a code present in an eligible frozen GMN/MDC profile;
- **unmatched token:** every other non-background token; it is recorded but excluded from any later positive or background reservoir.

No token may be manually reassigned after its frequency is observed. In particular, unmatched shower-like tokens may not be folded into the background.

## Geometry-ready rule

A row is geometry-ready only if all four frozen physical inputs are finite and within:

- `0 <= sol < 360`;
- `0 <= ra < 360`;
- `-90 <= de <= 90`;
- `0 < vg < 100 km/s`.

A row is reservoir-ready only if it is geometry-ready and `Ncam >= 2`. No uncertainty or error threshold is tuned in this audit; finite uncertainty and `Er` availability are reported only as aggregate diagnostics.

## Permitted outputs

Only aggregate outputs may be preserved:

- total rows and parse failures;
- rows removed by the blind interval;
- geometry-ready and reservoir-ready counts;
- complete normalized label-token counts outside the blind interval;
- background, matched, and unmatched counts;
- matched eligible shower counts and complex counts;
- aggregate uncertainty/error completeness.

No row values, event identifiers, feature distributions, spatial/solar histograms, or GhostStream-local statistic may be uploaded.

## Frozen continuation gates

Every gate must pass:

1. exact SonotaCo archive and member hashes match;
2. exact GMN/MDC audit hash matches;
3. all required normalized fields are present and unique;
4. all 36,826 rows are structurally parsed;
5. geometry completeness outside the blind interval is at least 0.95;
6. at least 10,000 reservoir-ready background rows remain;
7. at least 20 eligible matched shower codes have at least 20 reservoir-ready rows each;
8. those supported showers span at least 10 frozen complex keys;
9. at least 90% of reservoir-ready rows have finite RA, Dec, and speed uncertainties plus finite `Er`.

## Continuation and kill rules

A complete pass authorizes only a separately frozen scientific screen that reuses the exact PR #38 score, feature scales, fixed 10° Mondrian calibration, seeds, comparators, and scientific gates where structurally applicable.

Any failed gate kills this exact SonotaCo-2025 labeled-source formulation. Do not add label aliases, redefine background, lower support counts, relax the blind interval, use unmatched labels as sporadics, or switch years after observing the result.
