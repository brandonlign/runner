# Worst-family calibrated recurrence: frozen Stage-0 protocol

**Frozen before authoritative execution: 2026-08-04.**

## Scientific question

Can the leave-one-year-out recurrence product preserve its demonstrated power advantage when catalog-level thresholds are calibrated to control each predeclared null family separately rather than only their average mixture?

PR #65 is an authoritative no-go. It improved recurrence power and rejected every one-year artifact, but a pooled 50/50 calibration quantile allowed shared-structure FWER of 0.24. This is a new calibration formulation and does not relabel PR #65.

## Candidate statistic

Reuse the exact PR #65 recurrence score:

- compute one-sided annual Poisson excess p-values at every template;
- convert to annual `-log10(p)` evidence;
- discard the single strongest year;
- sum the second- and third-strongest annual evidence values.

All SonotaCo data, coordinate transforms, ESV mask, annual channels, grids, template widths, recurrent injections, one-year artifacts, and comparators remain unchanged.

## Worst-family catalog calibration

For every detector independently:

1. generate 80 ideal independent-year null catalogs and record the maximum over the complete adaptive template bank;
2. generate 80 null catalogs with the fixed smooth shared annual distortion and record the complete-search maximum;
3. estimate the conservative 90th-percentile threshold separately within each null family;
4. use the larger of those two thresholds for every later decision.

This controls against the worst predeclared family rather than an average mixture. The rule is applied equally to pooled, pooled-plus-confirmation, original ReplicaStream, and the candidate.

## Evaluation

Use:

- 60 fresh ideal-null catalogs;
- 60 fresh shared-structure-null catalogs;
- 60 injection trials for every strength;
- recurrent injections active in five years at 4, 6, 8, or 12 meteors per active year;
- equal-total-mass one-year artifacts;
- catalog alpha 0.10.

Weak recurrence averages 4 and 6 meteors per active year; strong recurrence averages 8 and 12. The recurrence margin is weak recurrent recovery minus weak one-year-artifact recovery.

The strongest baseline is selected separately for each endpoint among pooled, pooled-plus-confirmation, and original ReplicaStream, all under the same worst-family calibration.

## Frozen continuation gates

Every gate must pass:

1. candidate ideal-null FWER at most 0.15;
2. candidate shared-structure-null FWER at most 0.15;
3. weak recurrent recovery no more than 0.05 below the strongest baseline;
4. weak one-year-artifact detection at most 0.20;
5. recurrence-margin gain over the strongest baseline at least 0.05;
6. strong recurrent recovery no more than 0.05 below the strongest baseline.

Numerical comparisons use a fixed `1e-12` tolerance only to prevent binary floating-point representation of an exact decimal boundary from changing a gate. This tolerance is frozen before execution and does not alter any scientific threshold.

Any failed gate gives `KILL_WORST_FAMILY_RECURRENCE`. No score, family, distortion, trial count, quantile, threshold, comparator, injection, or gate may change afterward.

A pass authorizes only a separately frozen real known-shower and held-out-year benchmark. It does not establish novelty and does not authorize applying the method to GhostStream.
