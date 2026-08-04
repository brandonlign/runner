# SonotaCo radiant-drift source-interface audit

Status: frozen before any source is decoded on this branch.

## Purpose

PR #112 showed that the exact original phase-weighted quartet and the fixed 10° phase-gated radiant-speed quartet are complementary, well calibrated, and stronger than all fixed comparators, but the fused detector remained one k=4 recovery short of the frozen alpha-0.05 gate. The next distinct physical hypothesis is local radiant drift across activity phase: a real shower may trace a short phase-ordered radiant-speed manifold rather than a phase-independent compact ball.

Before defining that detector, this audit may inspect only the exact source interfaces inherited from PR #109 and PR #112. It must not open a meteor archive or compute any score.

## Frozen actions

1. Decode the exact PR #109 phase-gated source from `sonotaco_phase_gated_3d/source_parts/part00.b64` and require SHA-256 `fb93ab74edf4c79b00bca6f5c1e6c1a4be33904204bbd2aed296cf2b01dd10b2`.
2. Decode the exact PR #112 high-resolution fusion source from `sonotaco_hires_multiview_fusion/source_parts_v2/part00.b64` through `part07.b64` and require SHA-256 `7ab556184e0965ce066d24a75f2067b9256465d1899c805afa0061f717d34382`.
3. Compile both sources and emit their exact decoded text plus an AST inventory of constants, function signatures, imported names, and attribute access rooted at `episode`, `event`, and `base`.
4. Assert that neither source audit workflow nor decoded source is executed against data.

## Decision rule

Pass only if both exact hashes and compilation checks succeed and the inventory exposes enough information to define a separately frozen drift-aware score without modifying the parser, labels, reservoirs, windows, seeds, folds, endpoints, or existing controls.

A pass authorizes only a separately preregistered SonotaCo 2025 drift-development experiment. SonotaCo 2024 and GhostStream remain untouched.
