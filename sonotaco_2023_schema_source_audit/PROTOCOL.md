# SonotaCo 2023 replacement schema and source-equivalence audit

Status: frozen before any SonotaCo 2023 data row, label, support count, score, p-value, fold, or endpoint is decoded or computed.

## Authorization

PR #141 established that the official SonotaCo 2023 archive is available, structurally valid, and absent from all 140 pre-existing runner refs and commit messages. It recorded archive SHA-256 `9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430` and main member `023a/_U2_20230101_S.csv` without opening any member.

This audit may perform the minimum additional work required to preregister a one-shot replacement confirmation:

1. stream the exact main member once to compute its SHA-256;
2. retain and decode only bytes through the first line ending;
3. inspect only the CSV header schema;
4. fetch the exact pinned SonotaCo 2024 structural parser source and exact fixed4 confirmation source;
5. generate SonotaCo 2023 source candidates by year/archive/member/hash substitutions only;
6. prove each generated candidate reverses byte-for-byte to its exact pinned 2024 source;
7. compile and AST-parse generated sources without executing them.

## Forbidden actions

The audit may not retain, decode, parse, count, summarize, label, or score any data row after the header. It may not compute solar longitude, shower support, event quality, calibration windows, detector scores, p-values, folds, AUROC, false-positive rates, recall, or any scientific endpoint. It may not access SonotaCo 2024 archive bytes or any GhostStream value.

## Exact pinned sources

- 2024 structural parser commit: `60bbe701981256b89aaa1c9361efef2bbb2dd57e`.
- 2024 parser source SHA-256: `d3f9c99bb64b6458a8637bc308bc84ba9d00d83258fa1383a1d73a0865dd072b`.
- 2024 fixed4 confirmation commit: `8ac287c377ef3b140691217dd30285b723dd2cdf`.
- confirmation payload SHA-256: `c558141ce984f3b9d5ee5eecf7e80d3df54ce7ac0e0ac1e46ca5d84a7b7017d2`.
- decoded confirmation source SHA-256: `94081bcc564170b7273704f94d098fd8bb2d5b0e63e53d95117b48415f1031e7`.
- frozen standalone final-model source SHA-256: `747b2b1471f3ba193d68a39dd82ad3ac8506be63b651d45f84ffabb8d1acd301`.

## Header compatibility gates

The effective 2023 header must:

- decode under the exact frozen encoding candidates and delimiter set;
- contain at least 40 unique non-empty normalized fields;
- reconcile at most the documented trailing blank field;
- contain exact unit-bearing geometry/label fields `Sol(deg)`, `Ra(deg)`, `De(deg)`, `Vg(km/s)`, and `shower` after normalization;
- contain uncertainty fields `Ra_sd(deg)`, `De_sd(deg)`, and `Vg_sd(km/s)` after normalization;
- contain match diagnostics `dr`, `dv`, and `dd` after normalization.

## Source-equivalence gates

The generated 2023 parser and confirmation sources must:

- compile and AST-parse;
- contain the exact 2023 URL, archive hash, member name, and computed member hash;
- reverse byte-for-byte to the exact pinned 2024 sources under the recorded substitutions;
- leave all method functions, thresholds, calibration sizes, seeds, folds, gates, and score definitions unchanged;
- contain no SonotaCo 2024 archive access;
- contain no GhostStream values.

A pass authorizes only a separate final source audit and preregistered one-shot SonotaCo 2023 replacement confirmation. It does not authorize scoring in this audit.
