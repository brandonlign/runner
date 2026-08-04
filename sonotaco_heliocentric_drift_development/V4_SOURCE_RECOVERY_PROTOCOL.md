# SonotaCo heliocentric drift v4 source recovery

Status: frozen after PRs #119 and #121 failed before source decoding.

## Purpose

The exact v1 heliocentric-drift source was previously verified and compiled at SHA-256 `9a3873758b87aff129603fa6e375fa55c5eb4d22b2cf7231d0ffad359c2eae4e`. PR #117 then stopped before scoring because its synthetic three-event self-test reached a shape validator written for production 128-event episodes. The separately frozen v2 repair authorized only generalizing that assertion to `N × 3`, with `N` equal to the input event count.

The manually transported v2 payload in PRs #119 and #121 was corrupted before decompression. No scientific result was produced. This source-only recovery therefore decodes the already verified v1 payload directly and preserves its exact text plus the shape-validation interface needed to reproduce the authorized repair without guessing compressed bytes.

## Frozen actions

1. Verify the committed v1 payload file SHA-256 `0667645c0fe3cbe279fd44e01e0e46f991a738561397c40b03c088ce8d812fef`.
2. Decode it and require exact source SHA-256 `9a3873758b87aff129603fa6e375fa55c5eb4d22b2cf7231d0ffad359c2eae4e`.
3. Compile the source.
4. Preserve the exact decoded source, all source lines containing shape validation, and an AST inventory of comparisons involving `.shape`.
5. Do not install scientific dependencies, request a mapping artifact, open any meteor archive, construct an episode, or execute a detector score.

## Decision rule

Pass if the payload and decoded-source hashes are exact, compilation succeeds, and at least one shape comparison is exposed. A pass authorizes only a separately frozen execution workflow that applies the already authorized single shape-generalization edit and requires the preregistered v2 source SHA-256 `10e87a4ada2eaceb5a8852642f786ce3e8e3978ac490844104c346532e41508c` before any data access.

SonotaCo 2024 and GhostStream remain untouched.
