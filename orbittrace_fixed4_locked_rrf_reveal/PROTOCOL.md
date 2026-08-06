# Locked fixed4 RRF reveal source audit

## Purpose

Freeze the exact identifier-reveal implementation before the target-free locked-RRF catalogue scan finishes.

This stage is source-only. It does not download, open, or inspect either the blind scan artifact or the canonical OrbitTrace artifact. It computes no overlap, rank, verdict, or scientific endpoint.

## Immutable inputs expected later

The reveal runner accepts:

- one exact GitHub Actions artifact containing `orbittrace_fixed4_locked_rrf_scan.json.gz` and `locked_rrf_scan_sha256.txt`;
- the exact canonical OrbitTrace artifact already used by the earlier calibrated blind reveal;
- the exact inner scan-payload SHA-256 frozen before canonical access.

The later workflow must verify both artifact ZIP hashes before execution.

## Locked scan integrity

The scan must report:

- verdict `LOCKED_RRF_SCAN_FROZEN_AWAITING_SEPARATE_REVEAL`;
- ranking formula `0.66/(60+persistence_rank) + 0.34/(60+min_year_strength_rank)`;
- a complete `locked_rrf` ranking containing every preserved family exactly once.

## Canonical member freeze

The canonical member table is extracted only from:

`reconstruction/exact_downstream/primary/april_candidate_members.csv`

inside the checksum-pinned expert-review bundle. Only years 2022–2026 are evaluated, with exact counts:

- 2022: 10;
- 2023: 8;
- 2024: 14;
- 2025: 34;
- 2026: 29;
- total: 95.

## Frozen reveal criteria

### Full locked-RRF recovery

- rank at most 25;
- at least four represented years;
- at least 16 exact canonical members;
- at least four canonical members in at least three years.

Verdict: `FULL_LOCKED_RRF_ORBITTRACE_RECOVERY`.

### Partial locked-RRF recovery

If full recovery fails:

- rank at most 100;
- at least three represented years;
- at least 12 exact canonical members;
- at least four canonical members in at least two years.

Verdict: `PARTIAL_LOCKED_RRF_ORBITTRACE_RECOVERY`.

Otherwise:

`NO_LOCKED_RRF_ORBITTRACE_RECOVERY`.

No family merge, replacement, rescoring, reranking, alternate matching, threshold change, or sensitivity substitution is allowed.

## Output boundary

The reveal reports exact overlap IDs, overlap by year, rank, family size, precision, canonical recall, and the complete set of rule hits. It may not alter the frozen scan or use descriptive significance to replace the decision rule.
