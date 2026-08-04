# Leave-one-year-out recurrence product: frozen Stage-0 protocol

**Frozen before authoritative execution: 2026-08-04.**

## Scientific question

Can a meteor-stream scan preserve the one-year-artifact immunity of partial-conjunction testing while recovering the annual evidence discarded by ReplicaStream's hard third-strongest-year statistic?

This is a runner-only development gate. It is separate from GhostStream and cannot be applied to GhostStream unless every continuation gate passes and later real-shower and held-out-year benchmarks also pass.

## Exact data and search

- Reuse the exact SonotaCo 2009–2023 subset, MD5 `f57a2ac71832ceca9227441c00b8cd58`, and the exact coordinate transform, ESV mask, histogram grid, template widths, injections, and neighborhoods from ReplicaStream PR #8.
- Preserve 15 observing years as separate evidence channels.
- Recurrent injections are active in five randomly selected years with 4, 6, 8, or 12 meteors per active year.
- One-year artifacts contain the same total injected mass concentrated in one year.
- Compare pooled virtual-year scanning, pooled scanning plus support in at least three years, the original third-strongest ReplicaStream statistic, and the new candidate.

## Candidate statistic

For every location and template width:

1. compute the one-sided Poisson excess p-value independently in each year;
2. convert to annual evidence `E_y = -log10(p_y)`;
3. identify the three strongest annual evidence values;
4. discard the single strongest value entirely;
5. score the sum of the second- and third-strongest evidence values.

Equivalently, the candidate is `-log10(p_(2) * p_(3))` after ordering annual p-values from smallest to largest and omitting `p_(1)`.

A single exceptional year contributes exactly zero to this score. A recurrent signal can accumulate strength from the next two supported years instead of being reduced to only the third-strongest year. This is a calibrated domain statistic, not a claim of new partial-conjunction theory.

## Robust catalog-level calibration

Each detector receives its own threshold from the maximum over its complete frozen template bank. Calibration maxima are pooled prospectively from equal numbers of:

- independent-year null catalogs drawn from the fitted annual backgrounds;
- catalogs with an independently drawn smooth multiplicative structure shared across all years.

The shared field uses the unchanged PR #8 stress model and `log_sigma = 0.35`. This robust calibration family is fixed before execution and is applied equally to every candidate and baseline.

Use:

- 60 paired calibration trials, producing 120 full null maxima per detector;
- 50 independent ideal-null tests;
- 50 independent shared-structure-null tests;
- 50 injection trials at every strength;
- catalog-level alpha `0.10`.

## Frozen endpoints

Weak recurrence is the mean recovery at 4 and 6 meteors per active year. Strong recurrence is the mean recovery at 8 and 12. The recurrence margin is weak recurrent recovery minus weak one-year-artifact detection.

The strongest baseline for each endpoint is selected among pooled, pooled-plus-confirmation, and the original ReplicaStream statistic.

## Frozen continuation gates

Every gate must pass:

1. candidate ideal-null catalog FWER at most `0.15`;
2. candidate shared-structure-null catalog FWER at most `0.20`;
3. weak recurrent recovery no more than `0.05` below the strongest baseline;
4. weak one-year-artifact detection at most `0.20`;
5. recurrence-margin gain over the strongest baseline at least `0.05`;
6. strong recurrent recovery no more than `0.05` below the strongest baseline.

Any failed gate gives `KILL_SOFT_RECURRENCE_PRODUCT`. No statistic, null mixture, distortion amplitude, trial count, threshold, injection, template, comparator, or gate may change after results are observed.

A pass authorizes only a separately frozen benchmark on real known weak showers with complex-disjoint and held-out-year testing. It does not establish novelty and does not authorize GhostStream application.
