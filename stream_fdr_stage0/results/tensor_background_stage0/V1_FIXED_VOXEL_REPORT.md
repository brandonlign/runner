# Robust background decomposition v1 — fixed-voxel no-go

Authoritative runner workflow: `30845895975`

Artifact: `tensor-background-stage0` (`8868669374`)

Artifact digest: `sha256:b160374112df6bac4eacdcf465b00dbac808c39d00c61b28b38459ab45e73490`

## Verdict

**KILL_OR_REDESIGN_ROBUST_BACKGROUND_DECOMPOSITION**

The primary method applied column-group-sparse robust decomposition to a seven-year by 768-cell Anscombe-transformed phase-space count matrix. GhostStream was excluded.

## Null control

- primary FPR: **0.039**;
- Wilson 95% interval: **[0.017, 0.088]**.

## Fatal power failure

All frozen recurring-stream conditions had zero localized recovery. This was not solely a coarse-localization artifact:

- primary acceptance of strong recurring injections: **0.104**;
- pooled-count acceptance of strong recurring injections: **0.344**;
- primary acceptance of recurring-moderate injections: **0.031**;
- pooled-count acceptance of recurring-moderate injections: **0.125**;
- primary acceptance of recurring-sparse injections: **0.021**.

The primary also marginally failed the one-year-artifact ceiling at **0.104**.

## What worked

The robust decomposition strongly suppressed a broad recurring ridge: primary acceptance **0.010** versus pooled-count acceptance **0.250**. This supports the background-removal premise but not the fixed-voxel implementation.

## External control

M2026-A1 was not accepted. Primary score **0.314** versus threshold **2.131**, with coarse-cell localization distance **9.071** standardized units.

## Interpretation

The fixed grid dilutes compact streams across coarse cells and neighborhoods, while the nuclear/group-sparse decomposition can absorb the remaining recurring signal. The protocol permits one representation redesign: calculate the annual local-density field at observed event centers rather than fixed voxels, then apply the same low-rank/background separation logic. This removes quantization and gives every injected or real meteor a candidate center.

No tuning of the v1 grid, lambda, score threshold, or continuation gates is allowed. If the event-centered redesign fails, the robust-background direction is closed.
