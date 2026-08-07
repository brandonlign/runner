# OrbitTrace SonotaCo 2015/2017 parser transport protocol

## Purpose

Construct deterministic SonotaCo 2015 and 2017 parser sources from the exact validated SonotaCo-2023 fixed4-confirmation parser source **without accessing either 2015 or 2017 meteor archive**.

This is an implementation/source-transport stage only. It computes no detector score and reads no shower-label data.

## Preconditions

The transport may run only after:

1. the corrected full-repository freshness audit has verdict `PASS_CORRECTED_SONOTACO_2015_2017_REPO_FRESHNESS_AUDIT` and identifies 2015/2017 as having no actual prior SonotaCo data access in repository history while detecting spent 2016 as the positive control;
2. the exact validated 2023 parser source has SHA-256 `bc2636005cc25da33e8accb6bdb70beea6ab900862cd1e6342a481395ac8f3e6`;
3. the source-only 2023 parser audit has passed and confirms no meteor archive or target access.

## Frozen scientific parser behavior

The following behavior must remain unchanged from the validated 2023 parser:

- UTF-8-SIG CSV parsing;
- ZIP path safety and CRC checks;
- raw/effective header widths `46 / 45`;
- exact required normalized header set, including `soldeg`, `shower`, `radeg`, `dedeg`, `vgkms`, and `ncam`;
- finite-value parsing;
- solar longitude modulo 360°;
- **closed 20°–55° solar-longitude exclusion before the shower field is read**;
- shower/background token normalization and the exact GMN-MDC mapping source;
- geometry/quality cuts `0 <= RA < 360`, `-90 <= Dec <= 90`, `0 < Vg < 100`, `ncam >= 2`;
- equatorial-to-ecliptic transformation and Sun-relative ecliptic longitude;
- ESV exclusion from the background reservoir;
- native-label syntax and mapping diagnostics;
- parser gates requiring native syntax fraction >=0.90, mapped non-background fraction >=0.90, at least 30 supported native codes, at least 10,000 post-ESV sporadics, and at least 30 distinct labeled showers.

The exact mapping-audit SHA-256 remains:

`f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`.

## Allowed year transport changes

For target year `Y` in `{2015, 2017}`, the transport may change only:

- `YEAR: 2023 -> Y`;
- corpus/result/function/event-id strings containing `2023 -> Y`;
- annual member path `023a/_U2_20230101_S.csv -> 0YYa/_U2_Y0101_S.csv`;
- the three values that cannot exist before first archive access:
  - `ARCHIVE_SHA256` becomes `None`;
  - `MEMBER_SHA256` becomes `None`;
  - `EXPECTED_ROWS` becomes `None`;
- corresponding integrity gates change from comparison against those unknowable constants to:
  - archive SHA is computed and is a 64-character digest;
  - annual-member SHA is computed and is a 64-character digest;
  - record count is positive and malformed-row count is zero.

No other parser gate, geometric cut, label rule, header rule, mapping rule, or blindness rule may change.

## Frozen member convention

Before archive access the exact expected annual members are fixed by the established SonotaCo annual-file convention:

- 2015: `015a/_U2_20150101_S.csv`
- 2017: `017a/_U2_20170101_S.csv`

If either archive does not contain exactly that member, the future validation is an integrity failure/inconclusive transport result. The protocol must not search for an alternate scientific member after seeing archive contents.

## Source-only transport gates

For both generated sources:

1. the 2023 ancestor hash is exact;
2. the corrected freshness artifact is exact and passes;
3. the source-only 2023 parser audit artifact is exact and passes;
4. generated source compiles;
5. static AST/text audit confirms the frozen 20°–55° exclusion occurs before the first access to `row[index["shower"]]`;
6. all frozen parser constants/rules above are present;
7. the expected annual member is exact;
8. the 2023 archive hash, member hash, and row-count literal do not survive in the generated source;
9. no 2015/2017 archive is downloaded or opened;
10. no scientific score, shower-label row, excluded interval, or OrbitTrace target information is accessed.

A source-only pass freezes the generated parser SHA-256 values. It does **not** authorize archive access by itself. The external multiplicity-validation protocol must be committed and frozen separately before the first 2015/2017 archive download.
