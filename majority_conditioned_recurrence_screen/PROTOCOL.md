# Majority-conditioned recurrence: frozen reduced kill screen

Status: frozen before any candidate score, null threshold, recovery value, FWER, or continuation decision is computed.

## Candidate and provenance

This screen executes the exact source derived and statically audited in PR #84:

- pinned source-audit commit: `b8748f3e641e52dfe3b1500d6c7356bd9732f54a`;
- exact worst-family base source SHA-256: `4384dd0352174e57ca1f93a2c3bd070002f026cef8acace035ba4ec05e577dac`;
- exact majority-conditioned candidate SHA-256: `3d60e3622d7ec406bb03cd4ab43faec84be1eff4d0dd70afa6ed79b8fd777281`;
- exact observed-subset MD5: `f57a2ac71832ceca9227441c00b8cd58`.

At each template width and grid location, the candidate subtracts the pointwise median annual evidence across all fifteen years from every year's evidence, truncates below zero, then takes the unchanged third-strongest adjusted annual evidence. It maximizes over the unchanged template bank.

No quantile, coefficient, recurrence order, template width, grid, null family, injection, comparator, or threshold is selected in this screen.

## Frozen reduced design

- independent seed: `20260805`;
- 30 calibration catalogs per null family;
- 30 fresh ideal-null catalogs;
- 30 fresh shared-structure-null catalogs;
- 40 recurrent injections and 40 one-year artifacts per strength;
- strengths: unchanged 4, 6, 8, and 12 meteors per active year;
- active years: unchanged 5 of 15;
- recurrence requirement: unchanged third-strongest year;
- catalog alpha: `0.10`;
- thresholds: unchanged worst-family calibration, the maximum of separately estimated ideal-null and shared-structure complete-search thresholds.

This is a reduced kill screen. It does not validate the method.

## Fixed comparators

- pooled virtual year;
- pooled plus annual confirmation;
- original hard third-strongest recurrence;
- worst-family soft recurrence product.

## Frozen continuation gates

Every gate encoded in the exact candidate source must pass:

1. ideal-null FWER at most `0.20`;
2. shared-structure-null FWER at most `0.20`;
3. weak recurrent recovery no more than `0.05` below the strongest comparator;
4. weak one-year-artifact detection at most `0.20`;
5. weak recurrence-margin gain at least `0.05` over the strongest comparator;
6. strong recurrent recovery no more than `0.05` below the strongest comparator.

Any failed gate kills this exact candidate. Do not change the annual median, truncation, recurrence order, active-year count, grid, template bank, null model, distortion, seed, trial counts, alpha, threshold construction, comparator, or gate after seeing the result.

A complete pass authorizes only a separately frozen independently seeded full Stage-0. It does not authorize real-shower testing, confirmation, a catalogue scan, or GhostStream application.