# SonotaCo phase-span selector source-only audit

Status: frozen before any SonotaCo archive or detector score is opened.

This audit decodes and SHA-256 verifies the exact phase-span-conditioned selector candidate, compiles it, and checks the preregistered structural contract:

- exactly three thresholds: 2.5°, 5.0°, and 7.5°;
- 128 original-calibration, 512 component-reference, and 512 selector-calibration episodes per supported bin;
- original view selected only when the phase-gated quartet span is at or below the chosen threshold, otherwise the phase-gated 3D view;
- complex-held-out threshold selection and deterministic pseudo-fold assignment;
- no SonotaCo 2024 resource, GhostStream value, or network/data access in the audit.

A pass authorizes only a separate frozen SonotaCo 2025 development PR. It does not authorize SonotaCo 2024.

Frozen candidate source SHA-256: `aab855db949bd520aa142a51a140c6e181918be0428bdee082b427fd1240a569`.
