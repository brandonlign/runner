# Locked fixed4 RRF: conditional OrbitTrace catalogue application

## Authorization condition

This protocol was committed before the one-shot 2019–2021 validation outcome was available. Execution is authorized only if the exact PR #198 artifact reports `PASS_LOCKED_RRF_TEMPORAL_VALIDATION`. A failed validation permanently blocks this application.

## Immutable method

The application uses the exact calibrated fixed-4° catalogue scanner and changes only family ranking. Detector distance, 4° solar-longitude scale, 128-window Mondrian calibration, shortlist sizes and audit, anchored quartet construction, score, retention rules, components, and 1.5 family-link radius remain unchanged.

Locked ranking:

`RRF = 0.66/(60 + persistence_rank) + 0.34/(60 + min_year_strength_rank)`

Minimum-year strength is constructed exactly as in the target-excluded v2 development source. No coefficient, constant, tie rule, or family definition may change.

## Target-free application corpus

- complete official GMN months for 2022–2025;
- January–July 2026;
- quality-controlled residual events labelled `SPORADIC`;
- no canonical OrbitTrace artifact, identifier, coordinate, activity interval, HDBSCAN assignment, prior family identity, or previous reveal output is accessible during scanning and ranking.

The workflow must freeze and hash the complete locked-RRF family ranking before retrieving the canonical member table.

## Frozen reveal criteria

The exact identifier reveal uses the same criteria as the calibrated blind deployment:

### Full blind recovery

- locked-RRF rank at most 25;
- at least four represented years;
- at least 16 exact canonical members total;
- at least four exact canonical members in at least three individual years.

Verdict: `FULL_LOCKED_RRF_ORBITTRACE_RECOVERY`.

### Partial blind recovery

If the full rule fails:

- locked-RRF rank at most 100;
- at least three represented years;
- at least 12 exact canonical members total;
- at least four exact canonical members in at least two individual years.

Verdict: `PARTIAL_LOCKED_RRF_ORBITTRACE_RECOVERY`.

Otherwise: `NO_LOCKED_RRF_ORBITTRACE_RECOVERY`.

No family merging, rescoring, alternate matching, threshold change, or sensitivity substitution is allowed after reveal.

## Claim boundary

A full result would support describing the validated final pipeline as independently recovering OrbitTrace in a target-free catalogue ranking, with HDBSCAN as the historical exploratory discovery path. It would not rewrite chronology or establish formal shower status. A partial result supports only partial blind recovery. A negative result freezes the locked-RRF transfer as unsuccessful.