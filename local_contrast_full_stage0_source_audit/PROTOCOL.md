# Local-contrast full Stage-0 source interface audit

This auxiliary runner-only workflow reconstructs the exact worst-family source and derives the exact local-contrast candidate used in the reduced screen. It records the decoded candidate source SHA-256, compilation status, command-line arguments/defaults, top-level constants, and function signatures.

It performs no catalog generation, null simulation, injection, calibration, threshold estimation, detector score, or endpoint computation. It accesses no real-shower labels, confirmation panel, catalogue scan, or GhostStream data.

The sole purpose is to freeze an independently seeded larger Stage-0 command without guessing whether the existing source exposes a seed argument. Any subsequent full Stage-0 must preserve the local-contrast statistic, kernel, recurrence rule, null families, injections, comparators, and written scientific gates.