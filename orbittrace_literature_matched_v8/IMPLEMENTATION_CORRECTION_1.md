# Implementation correction 1 — native 2025 parser interface

Workflow run `31225912469` passed every source/protocol/comparator freeze guard and verified both exact SonotaCo archive hashes. It then failed during the 2025 parse, before any v8 yearly scan, family construction, pooled centroid, score, ranking, or label-dependent scientific endpoint existed.

The failure was:

`RuntimeError: unexpected raw header structure: 43, ['ctime']`

Cause: the source-only 2023→2025 parser transport preserved the validated 2023 trailing-empty-column / 46-field header assumption, while the already-known native SonotaCo 2025 file uses the older 43-field header.

This is an interface error, not a scientific result. The failed run and artifact remain preserved.

## Frozen correction

The retry may change only the 2025 parser plumbing:

- stop transporting the 2023 parser to 2025;
- decode and hash-check the exact native 2025 adapter already used by the frozen SonotaCo 2025 literature benchmark (`SHA-256 5e6d7a6545d83902362cc06c2fae5d285ae92eb2e8e1d7d42fd9769862ebf518`);
- expose that adapter through the benchmark's `parse_sonotaco_2025_events` interface without changing its parser body.

No v8 constant, source, family rule, centroid rule, score, ranking rule, benchmark metric, decision gate, competitor record, year, archive, label mapping, or blindness rule may change.
