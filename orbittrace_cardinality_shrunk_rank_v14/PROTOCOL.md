# OrbitTrace cardinality-shrunk rank v14 — target-excluded successor protocol

## Purpose

v14 is a new successor to failed density-capped multiplicity v13. It addresses one target-excluded development failure mode only: low-cardinality episodes can preserve family recovery and precision while perturbing multiplicity rank quality.

v14 does **not** alter frozen #839/v8 or rescue v13. SonotaCo 2013/2014 remains scientifically exposed and unavailable for successor development. MAARSY and OrbitTrace target information/region remain inaccessible.

## Frozen inputs

Use only the already-completed, target-excluded v13 r3 artifacts from workflow run `31356056453`:

- `orbittrace-v13-cap-32`
- `orbittrace-v13-cap-64`
- `orbittrace-v13-cap-96`
- `orbittrace-v13-cap-128`
- `orbittrace-v13-direct-v5-reference`

Those artifacts were generated from target-excluded GMN 2020/2021 with labels entering only after rankings. No new catalogue download is required for v14 development.

## Single successor rule

For each stress condition and each recurrent family:

1. take the frozen v13 multiplicity rank `r_M`, zero-based with smaller rank better;
2. take the frozen v5 fixed4-persistence rank `r_F`, zero-based with smaller rank better;
3. obtain the already-frozen local episode size in each scored year;
4. define the family reliability fraction

   `q = min(year episode sizes) / 128`, clipped to `[0,1]`;

5. define the cardinality-shrunk rank

   `R14 = q * r_M + (1-q) * r_F`;

6. rank ascending by `R14`, then ascending `r_M`, then ascending `r_F`, then stable family ID.

No coefficient is fitted. There is no intercept, learned shrinkage strength, label-dependent weighting, per-cap selection, or performance-derived threshold.

### Required endpoint identities

- if `q = 1`, `R14 = r_M`; therefore cap 128 must reproduce the exact frozen multiplicity order;
- if `q = 0`, `R14 = r_F` algebraically;
- for `0 < q < 1`, `R14` must lie between `r_M` and `r_F` for every family.

## Why this is the only change

v13 established that reduced episode cardinality leaves the recurrent-family universe and top-100 recovery/precision intact but can destabilize within-universe ordering. Fixed4 persistence is an already-frozen label-free ranking of the same family universe and does not depend on the multiplicity episode amplitude. v14 therefore uses fixed4 only as a low-information ordinal anchor, with its influence determined solely by the fraction of the validated 128-event episode actually available.

## Firewall and timing

The v14 ranker may read only:

- family IDs;
- multiplicity ranking;
- fixed4-persistence ranking;
- already-frozen episode sizes / family-score metadata.

It must freeze all four v14 rankings before any known-shower evaluation payload is read.

Evaluation may then reuse the frozen target-excluded v5/v13 known-shower mapping/evaluation machinery solely to compute development metrics for the already-frozen v14 orders.

Forbidden throughout v14 development:

- SonotaCo 2013/2014 scientific rows, labels, families, scores, or comparator results;
- MAARSY scientific data;
- OrbitTrace target identity, coordinates, region, or members;
- changing the family universe;
- changing proposal generation, fixed4 persistence, multiplicity scores, local windows, or episode membership;
- selecting a cap or shrinkage function after results.

## Stress conditions

Evaluate the exact same frozen cardinality stresses as v13:

- cap 128 — identity control;
- cap 96;
- cap 64;
- cap 32.

All conditions are mandatory. No cap is a selectable model.

## Integrity gates

All must pass:

1. family universe is identical across all four input artifacts and contains 92 families;
2. cap-128 v14 order exactly equals the frozen direct-v5 multiplicity order;
3. cap-128 v14 metrics exactly equal direct-v5 multiplicity metrics;
4. every family satisfies `0 <= q <= 1`;
5. every family satisfies `min(r_M,r_F) <= R14 <= max(r_M,r_F)` within numerical tolerance;
6. `q=1` rows reproduce multiplicity rank exactly;
7. v14 rankings are frozen before labels/evaluation are opened;
8. no SonotaCo 2013/2014, MAARSY, target-region, or OrbitTrace target access occurs.

## Scientific robustness gates

Use cap 128 as the frozen reference. For **each** of caps 96, 64, and 32:

1. recovered@100 >= `ceil(0.90 * cap128 recovered@100)`;
2. MRR >= `0.90 * cap128 MRR`;
3. top-100 dominant precision >= `0.50`;
4. top-100 dominant precision loss from cap 128 <= `0.05` absolute;
5. qualified-known-shower count equals cap 128.

These are exactly the cardinality-robustness thresholds used for v13. They are not relaxed after the v13 failure.

## Decision rule

- all integrity and all lower-cap robustness gates pass:
  `PASS_CARDINALITY_SHRUNK_RANK_V14_TARGET_EXCLUDED_DEVELOPMENT`
- otherwise:
  `FAIL_CARDINALITY_SHRUNK_RANK_V14_TARGET_EXCLUDED_DEVELOPMENT`

A pass freezes v14 for later independent validation only. It does not authorize SonotaCo reuse, MAARSY access, target access, or any claim of literature superiority.
