# Majority-conditioned recurrence: frozen full Stage-0

Status: frozen before any full-stage candidate score, threshold, FWER, recovery value, or continuation decision is computed.

## Authorization and exact candidate

PR #86 passed all six reduced-screen gates and authorized one independently seeded larger simulation benchmark. This full stage uses the exact audited candidate without changing its annual median, subtraction, truncation, recurrence order, grid, template bank, null generators, injections, or comparators.

Pinned provenance:

- source-audit commit: `b8748f3e641e52dfe3b1500d6c7356bd9732f54a`;
- exact worst-family base source SHA-256: `4384dd0352174e57ca1f93a2c3bd070002f026cef8acace035ba4ec05e577dac`;
- exact majority-conditioned candidate SHA-256: `3d60e3622d7ec406bb03cd4ab43faec84be1eff4d0dd70afa6ed79b8fd777281`;
- exact observed-subset MD5: `f57a2ac71832ceca9227441c00b8cd58`.

## Frozen full-stage design

- independent seed: `20260806`;
- 100 calibration catalogs per null family;
- 100 fresh ideal-null catalogs;
- 100 fresh shared-structure-null catalogs;
- 100 recurrent and 100 transient injections per strength;
- unchanged strengths 4, 6, 8, and 12 per active year;
- unchanged five active years of fifteen;
- unchanged third-strongest adjusted annual evidence;
- unchanged catalog alpha `0.10`;
- unchanged worst-family threshold: maximum of independent ideal-null and shared-structure complete-search thresholds.

## Fixed comparators

- pooled virtual year;
- pooled plus annual confirmation;
- hard third-year recurrence;
- worst-family soft recurrence product.

## Frozen full-stage gates

Every gate must pass:

1. ideal-null FWER at most `0.15`;
2. shared-structure-null FWER at most `0.15`;
3. weak one-year-artifact detection at most `0.20`;
4. weak recurrent recovery no more than `0.05` below the strongest comparator;
5. weak recurrence-margin gain at least `0.05` over the strongest comparator;
6. strong recurrent recovery no more than `0.05` below the strongest comparator.

The 0.15 FWER ceilings are prospectively stricter than the reduced screen's 0.20 kill thresholds. The exact source's embedded reduced gates are not sufficient for this stage; the workflow independently enforces these full-stage gates from the preserved metrics.

Any failure kills this exact formulation. No median rule, coefficient, recurrence order, active-year count, histogram grid, template width, null family, distortion, calibration mechanism, seed, trial count, alpha, comparator, threshold, or gate may change after seeing the result.

A complete pass authorizes only a separately frozen real-survey structural and label-support feasibility gate. It does not authorize confirmation, a catalogue scan, or GhostStream application.