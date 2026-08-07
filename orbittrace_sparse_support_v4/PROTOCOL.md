# OrbitTrace sparse-support v4 development protocol

## Purpose

Wavelet catalogue v3 failed because dense positive-lobe memberships percolated into only 23 giant recurrent families. This successor changes the **catalogue proposal scaffold**, not the frozen episode geometry or target boundary.

The target-free proposal scaffold is the already-frozen fixed4 persistence family set from the exposed 2022–2023 development panel. Those families are generated from compact four-event structures and therefore avoid the 128-member transitive-overlap failure of catalogue v3.

The scientific ranking signal is the already-frozen OrbitTrace multi-anchor wavelet energy v3, which uses the exact Brown-family 4° / 10%-speed geometry and the L2 energy of the four strongest positive leave-one-out anchor coefficients.

This development stage is restricted to **2022 and 2023**. Solar longitude 20°–55° remains excluded before label normalization through the exact frozen catalogue parser. **No 2024–2026 catalogue and no OrbitTrace target coordinate, activity interval, canonical member, or identity may be accessed.**

## Frozen sources

- fixed4 development scaffold: exact persistence families from workflow run `31106001133`;
- fixed4 scaffold size: **197 recurrent families**;
- fixed4 persistence baseline: 61 recovered known showers at top 100, 90 qualified matches, top-100 dominant precision 0.6809376504699393;
- multi-anchor v3 source Git blob: `2ba4835db23f8f623cdd28d0a4e6113b7954ecb2`;
- Brown comparator source Git blob: `493fcc7f2d2cc75ee35acf17e142e7ce7c1e03e8`;
- exact target-excluded catalogue parser/scientific source SHA-256: `ef3e69317af59fdac7a030edc77f742fc4772473d7f16b719b5d804cd4117f51`.

The failed wavelet catalogue-v3 result is preserved and is not rewritten.

## Candidate scaffold

Every one of the 197 frozen fixed4 recurrent families remains a proposal. No label is used to create, remove, split, merge, or modify proposals.

For each family and each development year:

1. take the frozen family centroid for that year (`sol`, sun-centered ecliptic longitude, ecliptic latitude, geocentric speed);
2. take the same target-excluded scan catalogue used by the frozen catalogue-v3 parser;
3. select events inside the frozen **10° solar-longitude activity window** centered on the family centroid;
4. calculate each event's exact frozen Brown-family 4° / 10%-speed radius from the centroid;
5. select the **128 nearest events** using stable deterministic tie handling;
6. compute the exact frozen multi-anchor-v3 episode score and the exact Brown single-peak comparator score on that same 128-event episode.

A family/year with fewer than 128 eligible window events is an integrity failure; there is no adaptive episode-size fallback.

## Source-preserving calibration

For each development year, construct the same frozen Mondrian source-preserving background factory from the target-excluded calibration catalogue.

For every supported 10° calibration bin:

- generate exactly **512** deterministic null episodes;
- score each null with frozen multi-anchor v3;
- score the same null with the frozen Brown comparator;
- require the v3-reported `brown_peak` and the independent Brown comparator score to agree within `1e-10`;
- use conservative empirical p-values `(1 + # null_score >= observed_score) / 513`.

No candidate-family score influences calibration generation or supported-bin selection.

## Frozen family rankings

Four rankings are reported. There is **no parameter search**.

### 1. Multi-anchor v3

For each family, rank by:

1. worst-year empirical v3 p-value ascending;
2. Fisher evidence `-2 * sum(log(p_year))` descending;
3. minimum year v3 score descending;
4. family ID ascending.

### 2. Brown comparator

Use the identical recurrence ranking rule with Brown empirical p-values and Brown scores.

### 3. Fixed4 persistence

Use the exact frozen fixed4 persistence order from run `31106001133`, unchanged.

### 4. Fixed equal-weight rank fusion

Use standard reciprocal-rank fusion with **k = 60**:

`RRF = 1/(60 + v3_rank) + 1/(60 + fixed4_persistence_rank)`.

Sort RRF descending, then family ID ascending. The weight and `k` are frozen before development results are computed.

## Evaluation

Labels are used only after the complete family set and all four rankings exist.

Eligibility and matching use the same frozen catalogue-v3 definitions:

- known shower has at least 8 total labeled events and at least 4 in each development year;
- family/label overlap must be at least 4 events;
- a qualified match requires family precision at least 0.5;
- recovered-at-100 is determined by the ranking position of the best-F1 qualified family for each eligible label;
- top-100 dominant precision is the mean dominant known-label fraction of the first 100 families.

Because the family set is unchanged, the eligible-label count must remain **355** and the set's total qualified-match capacity must reproduce the fixed4 scaffold's **90** qualified labels.

## Preregistered development gates

Sparse-support v4 passes development only if every gate passes:

1. exact 197-family fixed4 development scaffold and frozen baseline provenance;
2. exact 2022–2023 target-excluded catalogue and blind interval;
3. exact frozen v3 and Brown self-tests;
4. at least 30 supported calibration bins in each year;
5. exactly 512 null episodes per supported bin;
6. every family/year local episode contains exactly 128 events;
7. independent Brown score equals v3 `brown_peak` within `1e-10` for every candidate and null episode;
8. eligible labels = 355 and fixed family set retains 90 qualified labels;
9. pure v3 recovered-at-100 >= **48** (`floor(0.8 * 61)`);
10. pure v3 top-100 dominant precision >= **0.50**;
11. pure v3 recovered-at-100 >= Brown recovered-at-100 on the same scaffold;
12. fixed RRF recovered-at-100 >= **61** (the frozen fixed4 persistence baseline);
13. fixed RRF top-100 dominant precision >= **0.60**.

## Claim boundary

A pass would establish a target-free **proposal + ranking** architecture on exposed 2022–2023 development data. It would not establish prospective transfer, blind OrbitTrace rediscovery, or original discovery provenance. Any later validation must be separately frozen before new catalogue performance is opened.

A failure is preserved and does not authorize same-data retuning under the same version name.
