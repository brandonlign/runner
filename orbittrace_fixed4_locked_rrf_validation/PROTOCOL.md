# Fixed4 locked reciprocal-rank fusion: one-shot temporal validation

## Purpose

Test the already locked conservative reciprocal-rank fusion on previously unused known-shower labels from 2019–2021. This stage is a validation test, not ranking development and not an OrbitTrace application.

## Immutable detector and wrapper core

The workflow verifies the exact v2 source and preserves all reusable detector and geometry helpers. The fixed-4° distance, 128-window Mondrian calibration, 64-neighbor shortlist, 128-neighbor audit, anchored four-clique construction, maximum-pairwise-distance score, component requirements, family-link radius 1.5, and strength definitions remain unchanged.

Only the year set, locked ranking implementation, three-year label-eligibility rule, validation verdict, and output orchestration differ from v2.

## Locked formula

`RRF = 0.66/(60 + persistence_rank) + 0.34/(60 + min_year_strength_rank)`

The formula was selected from the target-excluded 2022–2025 artifact in PR #196. It cannot change after this workflow starts.

## One-shot test corpus

- complete official GMN months for 2019, 2020, and 2021;
- solar longitude 20°–55° removed before shower-label normalization or endpoint access;
- all geometrically valid events outside the exclusion enter the target-free scan;
- only events labelled `SPORADIC` after exclusion enter Mondrian calibration.

An eligible known shower must contain at least eight labelled events total and at least four events in at least two of the three test years. Family matching remains fixed at at least four exact events and precision at least 0.5.

## Frozen validation rule

The locked RRF passes only if, relative to persistence on 2019–2021:

- qualified recovery at rank 100 does not decline;
- qualified recovery at rank 500 does not decline;
- mean reciprocal rank strictly improves;
- mean dominant-label precision among the top 100 declines by no more than 0.05.

Verdicts:

- `PASS_LOCKED_RRF_TEMPORAL_VALIDATION`;
- `FAIL_LOCKED_RRF_TEMPORAL_VALIDATION`.

A pass authorizes one separately frozen target-free OrbitTrace catalogue application using this exact formula. A failure permanently rejects this formula. Neither result alters the historical HDBSCAN discovery chronology.