# SonotaCo 2024 untouched-confirmation feasibility gate

Status: frozen before downloading the 2024 archive or inspecting any 2024 row count, label token, feature value, shower support, score, comparator, or scientific endpoint.

## Purpose

Determine whether the official SonotaCo Network SNMv3 2024 annual archive is structurally usable as a future untouched external-survey confirmation panel.

SonotaCo 2025 has already been consumed for a label-syntax audit and may be used only for survey-native development. SonotaCo 2024 remains reserved. This gate is data-only and cannot compute a detector score.

## Frozen source

- official IAU MDC SonotaCo archive URL: `https://www.astro.sk/iaumdcDB/public/data/SNMv3/024a.zip`;
- required annual member basename: `_U2_20240101_S.csv`;
- archive and selected member SHA-256 values will be recorded after download;
- no fallback URL, mirror, alternate year, or manual attachment is permitted.

## Permitted inspection

The workflow may inspect only:

- HTTP/download success and nonzero bytes;
- ZIP CRC and safe member paths;
- member names and byte sizes;
- text encoding and delimiter;
- CSV header names and uniqueness;
- total row count and malformed-row count.

It must not retain, print, aggregate, or inspect any data-column value, shower-label frequency, solar-longitude distribution, uncertainty distribution, geometry distribution, or score.

## Frozen gates

Every gate must pass:

1. the official archive downloads and is nonempty;
2. all ZIP paths are safe and CRC validation passes;
3. exactly one CSV member has basename `_U2_20240101_S.csv`;
4. the selected member contains at least 30,000 and at most 50,000 nonempty records;
5. the member decodes using the frozen encoding order `utf-8-sig`, `cp932`, `shift_jis`, `latin-1`;
6. the delimiter is one of comma, semicolon, tab, or pipe;
7. the header contains at least 40 unique nonempty fields;
8. zero malformed-width records are present;
9. normalized headers include fields for solar longitude, radiant right ascension, radiant declination, geocentric speed, shower label, and at least one reported uncertainty/error quantity.

Header normalization lowercases text and removes all non-alphanumeric characters. Required semantic alternatives are frozen in the parser before execution.

## Continuation boundary

A pass authorizes only:

1. a separately frozen SonotaCo 2025 survey-native development screen using one generic label-prefix rule for every token; and
2. if that development screen passes, a separately frozen one-shot application of the exact resulting formulation to this reserved 2024 archive.

A feasibility pass does not authorize reading 2024 labels, fitting mappings from 2024, changing thresholds, or applying any method to GhostStream.

Any failed gate kills 2024 as the planned confirmation source. No row-count bound, header rule, source URL, member name, encoding, or required field may be changed after execution.