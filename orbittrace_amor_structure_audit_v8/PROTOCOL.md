# OrbitTrace AMOR 1990–1999 structure-only audit — frozen protocol

## Preconditions

This audit may execute only after pooled-year-centroid v8 passes its frozen GMN 2022–2023 development gate. The previously preserved full-history audit must also pass for the complete AMOR 1990–1999 pool.

Until those prerequisites pass, no AMOR annual ZIP is to be opened.

## Allowed access

The audit may access only the official IAU MDC radio-catalogue index and the ten annual AMOR ZIP archives for 1990–1999.

It may record only structural metadata:

- archive URL, byte size, SHA-256;
- ZIP member names, member byte sizes, CRCs;
- text-member byte hashes;
- non-empty line counts;
- whether a first line is a textual header and, if so, its field names;
- delimiter/token-width counts without converting any token to a number or interpreting any meteor value.

It may not parse or persist any meteor identifier, date, solar longitude, radiant, speed, orbit, shower code, or other scientific value. It may not compute any detector score, family, D-criterion, target statistic, or OrbitTrace comparison.

## Frozen panel-selection rule

After all ten archives have been audited structurally, the later external-validation panel is selected deterministically as the **two AMOR years with the largest opaque data-record counts**, ties resolved by earlier year.

This rule is frozen before first archive access. It uses exposure volume only and never scientific values. There is no alternate pair, fallback pair, or year cycling based on later method performance.

## Gates

A structure-audit pass requires:

1. the exact full-history AMOR freshness prerequisite passes;
2. all ten annual archive links 1990–1999 are present on the official IAU MDC radio page;
3. all ten archives download successfully and are valid non-empty ZIPs;
4. every archive contains at least one non-empty text-like data member;
5. structural scanning completes without numeric conversion or scientific-field interpretation;
6. exactly two years are selected by the frozen record-count rule;
7. no OrbitTrace target information is accessed.

A structural mismatch may justify a transport-only correction before scientific AMOR values are decoded, but may not change the year-selection rule or inspect scientific values.

## Claim boundary

A pass establishes only that AMOR can be transported structurally and fixes one two-year panel before scientific access. It is not method validation and does not authorize OrbitTrace reveal by itself.
