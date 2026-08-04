# SonotaCo 2023 confirmation-wrapper hash repair audit

Status: source-only; frozen before any SonotaCo 2023 data row or detector score is accessed.

## Motivation

PR #144 passed the 2023 archive/member/header/parser audit, but post-artifact source inspection found that its generated confirmation wrapper retained three 2024 transport constants:

- archive SHA-256;
- science-member SHA-256;
- parser-source SHA-256.

The wrapper was never executed. The only authorized repair is to replace those three one-occurrence constants with values already frozen by PR #144. No method code or scientific configuration may change.

## Exact immutable input

Download artifact `sonotaco-2023-schema-source-audit` from workflow run `30920089789`.

Required input hashes:

- generated 2023 parser: `9619dfc0b339b39d287833778769f12a643e2b0157fdcd6115cd9c40be528322`;
- unrepaired generated 2023 confirmation source: `1c119e0dfc154f34da06097da6c4a4cb2f7c6b11b7a1e6a9a9330baf25f1567e`;
- unrepaired payload: `6057e584ad23409996cd04ff595222c76cddff1d05f2da4a3e8c10bed973ca67`.

## Exact substitutions

Each old constant must occur exactly once and each new constant zero times before repair:

1. archive:
   - old `409bb958c6f114e542d818e7c4fcf7a58d89b2fb33090a442c8087bdcaa1540f`
   - new `9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430`
2. member:
   - old `0f25a0f9ea174c2b99915f48a61b35e35e3cde7f3117d82d4e05f8c4112acb00`
   - new `3f1cfedf59553568d6471e022ad032ec5ba71ce5287a24071d30bcc1e8bac685`
3. parser source:
   - old `d3f9c99bb64b6458a8637bc308bc84ba9d00d83258fa1383a1d73a0865dd072b`
   - new `9619dfc0b339b39d287833778769f12a643e2b0157fdcd6115cd9c40be528322`.

## Frozen output hashes

The repaired confirmation source must be exactly:

- bytes: `30395`;
- SHA-256: `32d199a652a9469c10ac3b2d9496177c11bb12901ccf2c3c9b24bbfd86ff4cb7`;
- deterministic gzip/base64 payload SHA-256: `c6fc5283a55e6b496748dd327607fd9a0cfed0d303fbf96b1f6e4b368feaeee4`.

## Audit gates

The workflow must prove:

- all exact input and output hashes;
- exactly the three authorized substitutions;
- repaired source compiles and AST-parses;
- repaired constants point to SonotaCo 2023 archive/member/parser;
- reversing the three hashes, `023a` to `024a`, and `2023` to `2024` reproduces exact pinned 2024 confirmation source SHA-256 `94081bcc564170b7273704f94d098fd8bb2d5b0e63e53d95117b48415f1031e7`;
- reversing the 2023 parser substitutions reproduces exact pinned 2024 parser SHA-256 `d3f9c99bb64b6458a8637bc308bc84ba9d00d83258fa1383a1d73a0865dd072b`;
- all thresholds, seeds, calibration sizes, folds, score functions, blind interval, and scientific gates remain byte-equivalent under reversal;
- no archive, mapping file, meteor row, detector score, or endpoint is opened or computed.

A pass authorizes only a separately preregistered one-shot SonotaCo 2023 replacement independent replication using the exact repaired artifact. SonotaCo 2024 and GhostStream may not be accessed.
