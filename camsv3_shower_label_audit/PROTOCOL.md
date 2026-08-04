# CAMSv3 survey-native shower-label interface audit

Status: frozen before reading any CAMSv3 data-column value.

## Purpose

Determine whether the official CAMSv3 `sh` field provides enough survey-native labeled showers and same-survey sporadic background to support a development screen of the unchanged PR #38 coverage-normalized 10-degree Mondrian four-clique method.

This is an aggregate-only label-interface audit. It computes no detector score, no calibration window, no injection, no AUROC, no p-value, and no GhostStream endpoint.

## Frozen source boundary

- Development-interface audit: pinned CAMSv3 2011–2015 archives only.
- Reserved untouched external confirmation panel: pinned CAMSv3 2016 archive. Parser-v2 inspected only its archive structure and header; this audit must not download, open, or read the 2016 archive.
- SonotaCo 2024 remains untouched.

The 2011–2015 archive SHA-256 hashes, member basenames, delimiters, and row counts are unchanged from structural parser v2.

## Authoritative field semantics

The official IAU Meteor Data Center parameter documentation defines `Sh` as the **shower number**. The frozen documentation snapshot is:

- URL: `https://ceres.ta3.sk/iaumdcdb/public/docs/document.pdf`
- bytes: `211571`
- SHA-256: `de8965b63389479c1dce39a36057ba2d0dd8742c45c67a60af4a330de14d324b`

The CAMSv3 header exposes this field as exact lowercase `sh`.

## Frozen native-label rule

After a row passes the phase boundary below, normalize `sh` only by Unicode/ASCII whitespace stripping.

- background: blank, or an exact numeric representation of zero matching `^\+?0+(?:\.0+)?$`;
- labeled shower: an exact positive integral numeric representation matching `^\+?[0-9]+(?:\.0+)?$` whose numeric value is greater than zero; map it to that integer IAU shower number;
- unsupported: every other nonblank representation.

No aliases, shower names, three-letter codes, fuzzy matching, suffix handling, manual exceptions, or value-specific repairs are allowed.

## GhostStream blindness and row boundary

For each 2011–2015 archive:

1. verify the pinned archive SHA-256 and exact safe member basename;
2. parse only exact fields `LS` and `sh` from the semicolon CSV;
3. require finite `LS` in `[0, 360)`;
4. remove solar longitude **20 degrees through 55 degrees inclusive** before any label category, count, support table, year table, or gate is formed.

Invalid-phase rows and blind-interval rows may be counted only as pre-boundary exclusions. No `sh` value from either group may be parsed or classified.

## Frozen aggregate outputs

The authoritative artifact may contain only:

- archive/row provenance by year;
- counts of valid-phase rows, blind-interval exclusions, invalid-phase exclusions;
- counts and fractions for background, labeled, and unsupported syntax;
- total number of distinct positive shower numbers;
- number of shower numbers meeting each support threshold, without listing their identities;
- number of shower-year cells meeting each support threshold;
- number of years represented per supported shower, summarized as a histogram;
- the frozen gates and verdict.

It must not emit individual rows, shower-number identities, top tokens, token frequencies by identity, geometry values, or any 2016 value.

## Frozen support definitions

- `supported_k8_shower_year`: at least 8 labeled members for one shower number in one development year;
- `supported_k12_shower_year`: at least 12 labeled members for one shower number in one development year;
- `multi_year_supported_shower`: at least 16 total labeled members and at least 4 members in each of at least two development years;
- `independent_complex_proxy_unit`: one positive IAU shower number for this interface gate only. This is not yet the final complex-disjoint unit; a later scientific protocol must map numbers to exact IAU codes and the frozen PR #14 complex map before evaluation.

## Frozen continuation gates

Every gate must pass:

1. all five pinned 2011–2015 archives pass source and parser checks;
2. the 2016 archive is neither requested nor opened;
3. no row from solar longitude 20–55 inclusive reaches label parsing;
4. unsupported syntax is at most 1% of post-boundary rows;
5. at least 90% of nonblank/nonzero label-like values map through the single positive-integer rule;
6. at least 50,000 post-boundary background events;
7. at least 30 distinct positive shower numbers;
8. at least 25 supported-k8 shower-year cells;
9. at least 20 supported-k12 shower-year cells;
10. at least 20 multi-year-supported shower numbers.

A pass authorizes only a separately frozen CAMSv3 2011–2015 scientific development screen. Before that screen reads geometry or score values, it must freeze the exact IAU shower-list snapshot and number-to-code mapping, PR #14 complex map, quality filters, year handling, phase bins, window construction, calibration counts, seeds, folds, comparators, thresholds, and scientific gates. CAMSv3 2016 remains untouched unless that complete development screen passes every frozen gate.

A failure kills this exact CAMSv3 native-label interface. No syntax rule, threshold, archive set, or support gate may be changed after execution.
