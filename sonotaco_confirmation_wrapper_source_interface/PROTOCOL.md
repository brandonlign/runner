# SonotaCo confirmation-wrapper source-interface audit

Status: frozen after SonotaCo 2023 replacement feasibility passed and before any 2023 ZIP member is opened.

## Purpose

The exact fixed-4° detector is frozen by PR #136. A replacement one-shot confirmation on SonotaCo 2023 must preserve the existing confirmation parser, native-label rules, geometry, episode construction, calibration, comparators, folds, thresholds, and gates while changing only explicit year/archive identity and provenance.

The existing confirmation wrapper was committed before the procedurally premature 2024 run. Its source can be audited independently of any 2024 data or endpoint. This audit decodes and inventories that source only so a separately frozen 2023 wrapper can be constructed without guessing or altering detector logic.

## Frozen actions

1. Verify `sonotaco_fixed4_confirmation/source_parts/part00.b64` file SHA-256 `c558141ce984f3b9d5ee5eecf7e80d3df54ce7ac0e0ac1e46ca5d84a7b7017d2`.
2. Decode the payload and require source SHA-256 `94081bcc564170b7273704f94d098fd8bb2d5b0e63e53d95117b48415f1031e7`.
3. Compile and parse the source with Python 3.12.
4. Preserve the exact decoded source plus an AST inventory of constants, function signatures, seed literals, parser requirements, source hashes, archive/member literals, and scientific gate names.
5. Do not install scientific dependencies, download any archive, open any ZIP member, load a mapping artifact, construct an episode, or execute the source.

## Decision rule

Pass only if both hashes and compilation are exact, the source contains the fixed 4° candidate and complete confirmation gates, and the inventory exposes all year-specific literals required for a separately frozen 2023 transformation.

A pass authorizes only a source-only 2023 transformation/equivalence audit. It does not authorize opening the 2023 science CSV.

No 2024 artifact or endpoint is read or used. GhostStream remains untouched.
