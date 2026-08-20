# M2D SACV Pareto pair catalogue v1

## Purpose

Test whether the limitation is caused by selecting one annual SACV hypothesis too early rather than by the SACV hypothesis space itself.

This is a catalogue reorganization, not a new detector. The candidate universe is frozen before target truth and consists only of validated SACV annual hypothesis pairs.

## Candidate construction

For each immutable M2D parent:

1. Enumerate all admissible 2022 SACV hypotheses.
2. Enumerate all admissible 2023 SACV hypotheses.
3. Keep only exact reciprocal cross-year validated pairs.
4. Represent each pair by the union of its two SACV hypothesis memberships.

No target labels, OrbitTrace membership, SonotaCo truth, or post-result tuning may enter.

## Ranking

Do not collapse objectives into a hand-designed scalar. Rank candidates through nondominated Pareto layers using:

1. original M2D parent rank (lower is better);
2. original SACV 2022 hypothesis rank (lower is better);
3. original SACV 2023 hypothesis rank (lower is better).

Within a Pareto layer, preserve the frozen SACV native ordering only as a deterministic tie-break.

## Evaluation

The catalogue receives the same budget as the existing SACV/M2D parent catalogue. Extra generated candidates cannot increase benchmark exposure.

Primary question:

Does preserving multiple independently validated ancestral explanations improve blind recovery quality without target-aware selection?

If not, close this direction rather than adding additional ranking objectives.
