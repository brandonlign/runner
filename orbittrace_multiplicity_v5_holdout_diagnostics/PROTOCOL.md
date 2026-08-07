# OrbitTrace multiplicity-v5 holdout diagnostic protocol

## Purpose

Diagnose the already-completed prospective sparse-support multiplicity-v5 GMN 2020–2021 holdout without changing v5, reopening any meteor catalogue, redefining the preregistered pass rule, or accessing OrbitTrace.

Authoritative source result:

- run `31195683802`
- job `92923195880`
- artifact `9000956881`
- verdict `INCONCLUSIVE_MULTIPLICITY_V5_HOLDOUT_POWER`
- recurrent family count `92`
- qualified known-shower count `56`

The holdout was inconclusive because the preregistered minimum of 100 recurrent families was not met. With only 92 families, every top-100 endpoint contained the entire catalogue and therefore cannot diagnose ranking quality.

## Frozen diagnostic questions

Using only the existing v5 output artifact:

1. How often does multiplicity improve, worsen, or tie the rank of the same qualified known-shower family relative to Brown, total-v3, and fixed4 persistence?
2. What are the mean, median, quartile, and extreme rank changes?
3. Do the non-saturated preregistered rank metrics (MRR and median rank) agree with the direction of the per-label rank changes?
4. Is the 2020–2021 failure mode purely the absolute top-k power gate, or is there evidence of an additional integrity/ranking failure?

## Allowed outputs

- per-label rank deltas;
- counts of improved/worsened/tied qualified labels;
- mean/median/quartile rank deltas;
- largest rank improvements and degradations;
- MRR and median-rank comparisons copied from the frozen holdout result;
- family-rank correlations and catalogue size copied from the frozen result.

No new performance threshold is defined. No top-50, top-fraction, alternate cutoff, weight, p-value, or fusion rule is tested. These diagnostics are descriptive only and cannot convert the v5 holdout into a pass.

## Frozen classification

Return `DIAGNOSIS_V5_TOP100_SATURATED_BUT_RANK_SIGNAL_PRESENT` only if:

- the frozen family count is below 100;
- all four top-100 recovery counts equal the common qualified-match count;
- multiplicity MRR is greater than Brown MRR;
- multiplicity median rank is lower than Brown median rank.

Otherwise return `DIAGNOSIS_V5_TOP100_SATURATED_OR_RANK_SIGNAL_MIXED`.

This classification is descriptive and not a scientific pass gate.

## Blindness boundary

This stage must use only the frozen Actions artifact. It must not call a catalogue API, access any 2020–2026 raw meteor file, inspect solar longitude 20°–55°, or access OrbitTrace coordinates, members, identity, activity, or any target-consistency criterion.
