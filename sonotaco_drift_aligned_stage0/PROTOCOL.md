# SonotaCo drift-aligned coherence source audit

Status: frozen before any meteor archive is downloaded or any detector score is computed.

## Motivation

PR #112 established that the original phase-weighted clique and the phase-gated raw radiant-speed clique are complementary, but their high-resolution split-conformal fusion missed the k=4 alpha-0.05 gate by one recovery. The next scientifically distinct hypothesis is that raw radiant coordinates still blur a real sparse shower because meteor-shower radiants and speed can drift with solar longitude across the activity interval.

Before defining that candidate, this source-only audit decodes and inspects the exact PR #109 phase-gated scorer so the next implementation uses verified data structures and interfaces rather than inferred ones.

## Frozen audit

The workflow shall:

1. concatenate only `sonotaco_phase_gated_3d/source_parts/part00.b64` inherited from PR #112;
2. base64-decode and gzip-decompress it;
3. require SHA-256 `fb93ab74edf4c79b00bca6f5c1e6c1a4be33904204bbd2aed296cf2b01dd10b2`;
4. compile and AST-parse the exact source;
5. preserve the decoded source, function/class signatures, module constants, and source excerpts for functions touching episode scoring, quartet geometry, and metrics.

No SonotaCo archive, GMN artifact, mapping audit, meteor row, label, score, fold, endpoint, or GhostStream information may be opened or computed.

## Continuation rule

A complete source-audit pass authorizes only a separately frozen drift-aligned development candidate. The candidate must be motivated by verified source anatomy and must preserve the 20°–55° inclusive blind exclusion before all labels, reservoirs, windows, scores, folds, and endpoints. SonotaCo 2024 remains untouched.
