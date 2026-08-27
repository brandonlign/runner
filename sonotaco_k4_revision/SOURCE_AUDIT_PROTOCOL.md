# SonotaCo k=4 revision source audit

Status: frozen before any new SonotaCo data access or detector execution.

## Purpose

Recover the exact decoded SonotaCo 2025 adapter and PR #38 Mondrian scorer sources used in PR #69 so that the four-member near-miss can be diagnosed from the real implementation rather than guessed from aggregate metrics.

## Boundaries

- Use only repository bytes already committed on PR #69.
- Decode and hash-check source files; compile them, but do not download any meteor archive or prior result artifact.
- Do not execute a detector, construct a window, read a meteor row, or compute a score.
- SonotaCo 2024 remains untouched.
- No GhostStream value, member, radiant, orbit, score, or local region may be accessed.

## Frozen expected hashes

- SonotaCo adapter source SHA-256: `5e6d7a6545d83902362cc06c2fae5d285ae92eb2e8e1d7d42fd9769862ebf518`.
- PR #38 Mondrian scorer source SHA-256: `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`.
- Baseline payload decoded source SHA-256: `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`.

A pass authorizes only implementation inspection and a separately frozen diagnostic design. It does not authorize a method revision, confirmation run, catalogue scan, or GhostStream application.
