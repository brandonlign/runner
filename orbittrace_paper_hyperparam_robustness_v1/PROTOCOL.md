# OrbitTrace paper hyperparameter robustness v1 — frozen protocol

## Purpose

This is a post-discovery sensitivity analysis for the OrbitTrace manuscript. It addresses one question only: is the late-April OrbitTrace concentration present only at the stated ACRF/HDBSCAN scaling and support settings, or does the same concentration remain visible under reasonable perturbations of the parameters that define the clustering geometry?

This analysis does **not** select a new discovery method, change the 95-member canonical sample, reopen method development, or tune parameters after observing OrbitTrace recovery.

## Fixed data

Use the public GMN April 2025 and April 2026 monthly trajectory files. Apply the manuscript quality rules before clustering:

- finite geocentric radiant, solar longitude and speed;
- 5 <= Vg <= 75 km/s;
- at least two stations;
- median trajectory-fit error <= 180 arcsec;
- retain only trajectories labelled sporadic by GMN;
- for duplicate beginning times, keep the lowest-fit-error solution, breaking ties by larger station count.

The diagnostic clustering set is then fixed to trajectories within +/-12.5 degrees of lambda_sun = 36.901963 degrees. This 25-degree diagnostic band is deliberately wider than one 10-degree ACRF local window and is fixed before any sweep result is observed.

## Representation

Use the manuscript six-component periodic representation:

- sine/cosine pair for Sun-centred geocentric ecliptic longitude;
- ecliptic latitude;
- geocentric speed;
- sine/cosine pair for solar longitude.

For an angular scale s, the sine/cosine coordinates are divided by radians(s), so a small angular displacement of s degrees has approximately unit Euclidean length. Latitude is divided by its degree scale and speed by its km/s scale.

HDBSCAN uses `cluster_selection_method='leaf'`. This isolates the sensitivity of the underlying density structure; no candidate score or downstream validation threshold is changed across settings.

## Baseline

The manuscript baseline is:

- Sun-centred longitude scale: 3.5 deg
- ecliptic-latitude scale: 3.0 deg
- geocentric-speed scale: 2.5 km/s
- solar-longitude scale: 2.5 deg
- `min_cluster_size = 8`
- `min_samples = 4`

## Frozen parameter sweep

### One-factor-at-a-time sweeps

Holding all other values at baseline, evaluate:

- Sun-centred longitude scale: 2.5, 3.0, 3.5, 4.0, 4.5 deg
- ecliptic-latitude scale: 2.0, 2.5, 3.0, 3.5, 4.0 deg
- geocentric-speed scale: 1.5, 2.0, 2.5, 3.0, 3.5 km/s
- solar-longitude scale: 1.5, 2.0, 2.5, 3.0, 3.5 deg
- `min_cluster_size`: 6, 8, 10, 12, 15
- `min_samples`: 2, 3, 4, 5, 6

After deduplicating the common baseline this gives 25 settings.

### Joint corner stress

In addition, evaluate all 16 combinations of the low/high endpoints for the four parameters most directly challenged by the referee criticism:

- Sun-centred longitude scale: 2.5 or 4.5 deg
- geocentric-speed scale: 1.5 or 3.5 km/s
- `min_cluster_size`: 6 or 12
- `min_samples`: 2 or 6

The latitude and solar-longitude scales remain at their baseline values in these joint corners. Total frozen settings: 41.

No values, ranges, windows or settings may be added or removed after results are observed.

## Fixed OrbitTrace association rule

The clustering itself does not use canonical membership labels. After every HDBSCAN fit, identify clusters using only their physical centroids and the already-fixed OrbitTrace validation template.

Fixed centre:

- Sun-centred longitude = -149.297555 deg
- ecliptic latitude = +7.450070 deg
- Vg = 37.422240 km/s
- solar longitude = 36.901963 deg

Fixed robust scales:

- Sun-centred longitude = 0.881191 deg
- ecliptic latitude = 0.579296 deg
- Vg = 1.099081 km/s
- solar longitude = 1.329625 deg

A cluster is OrbitTrace-associated when the four-dimensional squared standardized centroid distance is <= 9 and |delta lambda_sun| <= 3.989 deg. If more than one leaf cluster satisfies this rule, their members are unioned; this is recorded explicitly as fragmentation rather than silently selecting the most favourable leaf.

## Evaluation metrics

Only after clusters are frozen for a setting, compare the associated union with the fixed 2025-2026 subset of the canonical sample (63 meteors: 34 in 2025 and 29 in 2026). Report for every setting:

- number of associated leaf clusters;
- associated-union membership;
- exact canonical overlap;
- precision, recall, F1 and Jaccard overlap;
- canonical overlap separately for 2025 and 2026;
- associated-union membership separately for 2025 and 2026;
- nearest associated centroid distance from the fixed OrbitTrace centre;
- fraction of all trajectories labelled noise.

Summary reporting must include the fraction of the 41 settings reaching canonical recall >= 0.50, >= 0.75 and >= 0.90, plus the minimum/median/maximum recall, precision, F1, Jaccard and centroid displacement. No single threshold is allowed to replace the full table.

## Claim boundary

This is a retrospective parameter-robustness test of the discovered concentration, not a blinded rediscovery experiment. A positive result supports the claim that the physical concentration is not an artefact of one exact HDBSCAN/scaling choice. It does not show that every parameter setting ranks OrbitTrace identically in a blind all-sky catalogue, and it does not authorize choosing a new setting because it yields better overlap.
