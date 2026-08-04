# SonotaCo 2023 confirmation-source repair v2

Status: frozen after PR #144 exposed an incomplete source transformation and before any SonotaCo 2023 data row is decoded or any detector score is computed.

## Failure being repaired

PR #144 correctly verified the 2023 archive, science-member hash, and header schema, but its generated confirmation wrapper changed only year/name literals. It retained the 2024 archive SHA-256, member SHA-256, parser-v2 SHA-256, and expected row count. Its claimed source-equivalence pass was therefore invalid. No candidate score or scientific endpoint was computed.

## Frozen structural action

This audit may stream the exact pinned science member as opaque bytes solely to:

1. verify its already frozen SHA-256 `3f1cfedf59553568d6471e022ad032ec5ba71ce5287a24071d30bcc1e8bac685`;
2. count LF line terminators and inspect only the final byte;
3. count quote bytes and require exactly zero, proving that no quoted embedded newline can make physical and CSV record counts differ.

No field, label, number, row, or column after the already audited header may be decoded, retained, parsed, summarized, or inspected. The exact preregistered 2023 data-row count is physical-line count minus one header line, with an adjustment only if the final byte is not LF.

## Sole authorized source transformation

Start from exact pinned 2024 parser SHA-256 `d3f9c99bb64b6458a8637bc308bc84ba9d00d83258fa1383a1d73a0865dd072b` and exact pinned confirmation source SHA-256 `94081bcc564170b7273704f94d098fd8bb2d5b0e63e53d95117b48415f1031e7`.

The generated 2023 parser may change only explicit 2024→2023 year/archive/member identity and exact archive/member hashes, as in PR #144.

The generated 2023 confirmation wrapper may change only:

- `2024` to `2023` in explicit year/function/output/verdict identity;
- `024a` to `023a` in explicit archive/member identity;
- archive SHA-256 `409bb958c6f114e542d818e7c4fcf7a58d89b2fb33090a442c8087bdcaa1540f` to the frozen 2023 archive SHA-256 `9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430`;
- member SHA-256 `0f25a0f9ea174c2b99915f48a61b35e35e3cde7f3117d82d4e05f8c4112acb00` to the frozen 2023 member SHA-256 above;
- parser-v2 SHA-256 to the exact generated 2023 parser SHA-256;
- `EXPECTED_ROWS = 38_793` to the opaque-byte-derived frozen 2023 data-row count.

No parser rule, native-label rule, blindness boundary, quality filter, model scale, geometry, episode, seed prefix, calibration size, test size, comparator, fold, alpha, scientific gate, output content, or verdict logic may change.

## Audit requirements

The audit must:

- compile and AST-parse both generated sources;
- reverse every authorized transformation and reconstruct both pinned 2024 sources byte-for-byte;
- prove the generated confirmation source contains the exact 2023 archive/member/parser hashes and derived exact row count and contains none of the corresponding 2024 literals;
- preserve the generated source and deterministic gzip/base64 payload;
- execute neither source and compute no support count, detector score, p-value, fold, AUROC, FPR, recall, or other scientific endpoint.

## Decision rule

A complete pass authorizes only one separately frozen SonotaCo 2023 replacement independent-replication execution with the generated exact source and unchanged scientific gates. Any audit failure kills this repair. The result must not be described as the originally preregistered SonotaCo 2024 confirmation.

GhostStream remains fully blinded. No SonotaCo 2024 data or result artifact is accessed.
