# SonotaCo 2023 replacement-panel header and parser audit

Status: frozen after PR #141 and before any SonotaCo 2023 meteor row, label, support count, score, p-value, fold, or scientific endpoint is read or computed.

## Purpose

PR #136 froze the final method as the exact fixed-4° coverage-normalized Mondrian anchored four-clique detector. PR #134 irreversibly consumed SonotaCo 2024 before the required 2025 final-development sequence was complete, so 2024 cannot honestly serve as the reserved confirmation panel. PR #141 selected SonotaCo 2023 deterministically as the most recent earlier annual panel, established no prior runner exposure, and inspected only archive central-directory metadata.

This audit may determine only whether the frozen 2024 parser interface is structurally transportable to the 2023 main CSV. It is not a detector run.

## Permitted access

The workflow may:

1. download only the exact official archive `023a.zip` and verify SHA-256 `9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430`;
2. verify the exact main member name `023a/_U2_20230101_S.csv` from the central directory;
3. open that member and read only its first physical line, bounded at 65,536 bytes;
4. decode and normalize only that header using the exact frozen parser encoding/delimiter candidates;
5. verify the required geometry, native-label, uncertainty, and match-diagnostic fields;
6. verify the exact frozen parser source SHA-256 `d3f9c99bb64b6458a8637bc308bc84ba9d00d83258fa1383a1d73a0865dd072b` and final-model source SHA-256 `747b2b1471f3ba193d68a39dd82ad3ac8506be63b651d45f84ffabb8d1acd301`.

The workflow may not read a second physical line, extract any member, hash the full uncompressed member, count records, inspect values, execute labels or mappings, construct episodes, or run the detector.

## Pass rule

Pass only if the archive and source hashes are exact; there is exactly one required main member; the first line terminates within the fixed bound; the header has a documented reconciled trailing blank if present; at least 40 unique nonempty effective normalized fields; and every frozen required field is present exactly once.

A pass authorizes only a separately frozen one-shot SonotaCo 2023 replacement-panel execution using the already frozen final method and unchanged scientific gates. Because 2023 was selected after the 2024 protocol breach, any later result must be described as a replacement independent replication panel, not as the originally preregistered untouched 2024 confirmation.

SonotaCo 2024 is not accessed by this audit. GhostStream remains blinded.
