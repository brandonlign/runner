# SonotaCo phase-span selector source-only audit v2

Status: frozen before any meteor archive or score is opened.

PR #125 was invalidated because its candidate used reference prefix `mondrian-span-selector-reference` instead of the exact PR #112 prefix `mondrian-multiview-hires-reference`. This audit permits exactly one repair:

- replace that single literal once;
- preserve every other source byte and all selector thresholds, calibration sizes, selection rules, gates, and outputs.

The workflow decodes both v1 and v2 source payloads, proves `v2 == v1.replace(old, new, 1)`, verifies the new SHA-256, compiles the source, and repeats the structural selector audit. It opens no data.

A pass authorizes only a separate corrected SonotaCo 2025 development rerun. SonotaCo 2024 remains untouched.

Corrected source SHA-256: `1fc071aeb742b70cadbf19be9bac719e79d57ca7a74ab0ce1cb960a827df4f2a`.
