# OrbitTrace sparse-support multiplicity catalogue v5

## Status

Prospectively preregistered target-excluded holdout protocol. This file must be committed before the 2020–2021 GMN catalogue is fetched or parsed by this methodology.

The 2020–2021 panel was selected because the exact frozen fixed4 support source audited before this protocol has `YEARS = (2022, 2023, 2024, 2025)`. Thus 2020–2021 is outside that scanner's prior catalogue universe while preserving two complete annual cycles and the exact two-year recurrence structure used in 2022–2023 development.

This stage cannot access OrbitTrace coordinates, activity, members, identity, or any event inside the closed solar-longitude interval 20°–55°.

## Scientific motivation frozen before holdout access

Sparse-support v4 failed only its fixed equal-weight RRF recovery gate. Artifact-only diagnosis showed that all v3 and Brown empirical recurrence p-values saturated at `1/513`, while total v3 energy was nearly rank-identical to Brown.

A separately frozen factorization diagnostic then isolated the only dimensionless multi-anchor information in v3:

`M = (E_v3 / B_Brown)^2 = sum(top4_positive_coefficients^2) / B_Brown^2`.

On already-exposed 2022–2023 development artifacts, without reopening a catalogue, this multiplicity ranking recovered 60 known showers in the top 100 versus 54 for Brown, 55 for total v3 energy, and 61 for fixed4 persistence. Its rank Spearman correlation with fixed4 was 0.5453. These numbers motivate this successor but do not count as prospective evidence.

## Immutable proposal generator

Candidate proposal generation is the exact frozen fixed4 support-normalized scanner with support-source SHA-256:

`fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62`.

The candidate, baseline, scorer, geometry, calibration, shortlist/audit, quartet, component, and family-link rules remain unchanged. In particular:

- candidate scale: 4.0°;
- episode/window size: 128 / 10.0°;
- fixed4 calibration: exact frozen 128 negatives per supported bin;
- 64-neighbor shortlist and 128-neighbor audit remain unchanged inside the frozen source;
- anchored nearest-three quartet construction remains unchanged;
- fixed component gates remain unchanged;
- family link radius: 1.5;
- minimum family years: 2.

Only the temporal parser globals are substituted before any catalogue call:

- `YEARS = (2020, 2021)`;
- `MONTH_KEYS = 2020-01 ... 2020-12, 2021-01 ... 2021-12`.

No detector or ranking constant is changed when those globals are substituted.

## Blindness boundary

For every monthly file, geometry validity and the closed solar-longitude exclusion `20° <= sol <= 55°` are applied before shower-label normalization. Candidate generation receives only geometry with labels replaced by hidden placeholders. Only events labelled `SPORADIC` after the exclusion may enter the fixed4 background calibration.

Native shower labels may be consulted only after all fixed4 components, cross-year families, local episodes, multiplicity scores, and ranking orders have been completed and serialized in memory.

## Local episode and ranking signal

For every recurrent fixed4 family and each of 2020 and 2021:

1. take the frozen per-year family centroid;
2. construct the exact deterministic 10° local window used by sparse-support v4;
3. select the exact 128 nearest events under the frozen wavelet geometry;
4. run the exact frozen multi-anchor v3 scorer and independent Brown comparator;
5. require Brown equivalence within `1e-10`;
6. compute `M = (v3_energy / Brown_peak)^2`.

`M` is not assigned a new empirical p-value. Fixed4 proposal generation already supplies the source-preserving significance/calibration layer. v5 deliberately separates proposal significance from the continuous ranking feature so the v4 p-value saturation cannot recur by construction.

### Frozen rankings

Primary ranking, **multiplicity recurrence**:

1. larger `min(M_2020, M_2021)`;
2. larger geometric mean `sqrt(M_2020 * M_2021)`;
3. stable family identifier.

Comparators only:

- unchanged frozen fixed4 `persistence` order;
- Brown amplitude recurrence: larger minimum per-year Brown peak, then stable family identifier;
- total-v3 recurrence: larger minimum per-year v3 energy, then stable family identifier.

There is no RRF, no Boolean union, no threshold search, no weight search, and no top-k search.

## Known-shower evaluation

Labels remain hidden until all rankings are complete.

An eligible known shower must have at least eight labelled events across the 2020–2021 panel and at least four events in each year. For evaluation only, the best matching family is chosen by F1, then precision, overlap, and stable family identifier. A match qualifies only with at least four exact labelled events and precision at least 0.5.

For every ranking report:

- qualified known-shower matches;
- recovery at top 100;
- recovery at top 500;
- mean reciprocal rank;
- median rank;
- macro F1;
- mean dominant-label precision among the top 100 families.

Also report family-rank Spearman correlations and top-100 family overlaps among multiplicity, Brown, total-v3, and fixed4 persistence. Correlations are descriptive, never pass gates.

## Holdout validity gates

The scientific result is interpretable only if all are true:

1. exact frozen source/hash/self-test guards pass;
2. the temporal substitution is exactly `(2020, 2021)` and exactly 24 monthly keys;
3. all 24 requested monthly files are retrieved and hashed;
4. the target exclusion is applied before labels;
5. each year has at least 24 supported fixed4 calibration bins;
6. every retained recurrent family has both 2020 and 2021 centroids;
7. every ranked family receives exact 128-event local episodes in both years;
8. maximum independent Brown-equivalence difference is at most `1e-10`;
9. at least 100 recurrent fixed4 families are produced;
10. at least 30 known showers qualify under the frozen evaluation rule.

If gates 9 or 10 fail, the verdict is **inconclusive for holdout power**, not a scientific pass and not permission to inspect OrbitTrace.

## Prospective scientific pass rule

If all validity gates pass, v5 passes the target-excluded holdout only if all are true:

1. multiplicity top-100 recovery is at least **one shower higher** than Brown amplitude recurrence;
2. multiplicity top-100 recovery is at least **90%** of unchanged fixed4 persistence top-100 recovery, using `ceil(0.90 * fixed4_recovery)`;
3. multiplicity top-100 dominant-label precision is at least **0.50**.

These gates are frozen before any 2020–2021 catalogue access. No gate may be changed after the holdout starts.

## Consequences

A pass freezes sparse-support multiplicity v5 as the catalogue-ranking architecture. It does **not** itself reveal OrbitTrace. Before the 20°–55° interval is opened, a separate final target-free discovery-application protocol must freeze the exact catalogue years, candidate-generation rules, ranking endpoint, output depth, and criterion for calling an independently generated family OrbitTrace-consistent.

A failure or underpowered result is preserved as such. It does not authorize weight tuning, threshold tuning, alternative top-k selection, or target access. Any successor must be separately named and structurally motivated.
