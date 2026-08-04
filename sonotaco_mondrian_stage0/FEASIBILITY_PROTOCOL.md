# SonotaCo 2025 external-survey feasibility gate

Status: frozen before downloading or inspecting the target archive.

## Purpose

Determine whether the official SonotaCo Network 2025 annual orbit archive can support a later independent-survey validation of the exact coverage-normalized 10-degree Mondrian four-clique formulation that passed PR #38.

This stage is data-format and availability only. It does not decode or execute the PR #38 scorer, classify showers, inspect score distributions, form positive or negative windows, inspect any GhostStream-region event, or compute a scientific endpoint.

## Frozen source

- provider: IAU Meteor Data Center mirror of SonotaCo Network SNMv3;
- exact archive: `https://www.astro.sk/iaumdcDB/public/data/SNMv3/025a.zip`;
- published dataset name: `_U2_20250101_S.csv`;
- published year: 2025;
- published orbit count: 36,826;
- archive listing publication date: 7 April 2026.

No alternate mirror, year, combined archive, high-accuracy subset, or replacement survey may be substituted after the result is observed.

## Data-only inspection

The runner may inspect only:

- HTTP/download success and byte count;
- archive SHA-256 and ZIP integrity;
- member names, compressed sizes, and uncompressed sizes;
- CSV encoding and delimiter needed for deterministic parsing;
- the header field names;
- aggregate CSV record count.

The runner must not report or use row values, shower-code frequencies, solar-longitude coverage, radiant distributions, speed distributions, orbit distributions, candidate scores, or any GhostStream-local statistic in this stage.

## Frozen gates

Every gate must pass:

1. the exact URL downloads a nonempty ZIP archive;
2. every ZIP member path is safe and the archive passes CRC validation;
3. at least one nonempty CSV member exists;
4. exactly one CSV member has 36,826 data records;
5. that member's basename is `_U2_20250101_S.csv`;
6. its header contains at least ten nonempty, unique fields;
7. the CSV can be parsed deterministically with one recorded encoding and delimiter;
8. no malformed row changes the field count.

## Continuation rule

A complete pass authorizes only a parser-adaptation branch and a separately frozen external-survey scientific protocol. The PR #38 source, score, 10-degree strata, calibration logic, feature scales, thresholds, comparators, and GhostStream blind interval remain unchanged and unexecuted here.

Any failed gate kills this exact SonotaCo-2025 source formulation. Do not substitute another year, loosen the published-count check, merge multiple CSV members, drop malformed rows, or inspect scientific distributions to rescue it.
