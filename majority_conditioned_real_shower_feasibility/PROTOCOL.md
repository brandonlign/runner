# Majority-conditioned recurrence: frozen seven-year real-shower feasibility gate

Status: frozen before any real meteor histogram, detector score, calibration threshold, recovery endpoint, comparator, fold, or GhostStream-region value is computed.

## Authorization

PR #89 passed every independently seeded full simulation Stage-0 gate for exact candidate SHA-256 `3d60e3622d7ec406bb03cd4ab43faec84be1eff4d0dd70afa6ed79b8fd777281` and authorized one real-shower structural and label-support feasibility gate stratified by active-year count.

This branch is that gate. It cannot execute the candidate.

## Scientific feasibility question

Does a continuous seven-year labeled GMN corpus contain enough established showers with support in exactly three of seven observing years to test the majority-conditioned recurrence principle on real meteors?

For seven years, the pointwise annual median is the fourth order statistic. A shower supported in exactly three years is therefore recurrent enough for the frozen third-strongest-year rule but cannot itself control the median. Showers active in four or more years are measured separately as a known limitation stratum; they are not silently treated as valid positives.

## Frozen source boundary

- official GMN monthly trajectory summaries for every month of 2019 through 2025 inclusive: exactly 84 URLs under `https://globalmeteornetwork.org/data/traj_summary_data/monthly/`;
- exact PR #14 quality parser from commit `bbd3eb514df2c0af7e8648ebc3ced5edbb7eec87`;
- exact parser SHA-256 `4a029051230f7c6e99b09e911f8a9e5228a58783`;
- exact PR #14 audit artifact from runner workflow `30855193522`;
- audit SHA-256 `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`.

The prior audit supplies only the frozen IAU-number-to-complex mapping. New monthly source hashes and aggregate counts are recorded as outputs of this data gate.

## GhostStream blindness

For every raw row:

1. inspect only the solar-longitude field using the exact PR #14 field index;
2. reject invalid solar longitude;
3. remove solar longitude **20.0 degrees through 55.0 degrees inclusive**;
4. only then invoke the exact PR #14 quality parser, which may access the shower label and measurement fields.

No label, shower code, radiant, speed, uncertainty, orbit, event ID, or quality field from a blind-interval row may be parsed or counted.

## Frozen quality and support definitions

Outside the blind interval, preserve the exact PR #14 quality parser and its geocentric radiant, speed, uncertainty, `Qc`, fit-error, and station-count rules.

For each positive IAU shower number and each support threshold `k in {4, 6, 8, 12}`:

- an active shower-year has at least `k` quality members;
- `transient`: active in exactly one of seven years;
- `sub-recurrence`: active in exactly two years;
- `recurrence-eligible minority`: active in exactly three years;
- `majority-active`: active in four through seven years.

Complex units use the exact complex key recorded in the PR #14 audit when available and otherwise the deterministic fallback `SHOWER:<IAU number>`. The artifact reports only anonymous counts and histograms, never shower identities or complex names.

## Frozen aggregate outputs

Allowed outputs:

- source URL, bytes, SHA-256, year, and month for each of 84 files;
- total/raw/malformed/invalid-phase/blind-removed/quality counts;
- quality sporadic and labeled counts by year;
- anonymous active-year histograms for each `k`;
- counts of transient, sub-recurrence, exactly-three-year, and majority-active showers for each `k`;
- anonymous number of complex units represented by exactly-three-year k=4 and k=8 showers;
- gates and verdict.

Forbidden outputs:

- event rows or event IDs;
- shower numbers, codes, names, or per-shower counts;
- complex identities;
- radiant, speed, uncertainty, orbit, or date distributions;
- any detector score, histogram cell, calibration sample, p-value, AUROC, recall, threshold, or GhostStream-region statistic.

## Frozen continuation gates

Every gate must pass:

1. exactly 84 official monthly sources download and parse;
2. zero structurally malformed data rows;
3. the blind interval is applied before every label/quality parse;
4. each of seven years contains at least 80,000 post-boundary quality sporadic meteors;
5. total post-boundary quality sporadics are at least 1,000,000;
6. at least 200 distinct positive IAU shower numbers have post-boundary quality members;
7. at least 30 showers are recurrence-eligible in exactly three years at k=4;
8. at least 25 showers are recurrence-eligible in exactly three years at k=8;
9. at least 15 showers are transient at k=4, providing one-year-artifact controls;
10. at least 40 showers are majority-active at k=4, making the method's prevalence limitation measurable rather than hidden;
11. exactly-three-year k=4 showers span at least 25 anonymous complex units;
12. exactly-three-year k=8 showers span at least 20 anonymous complex units;
13. no forbidden identity, row-level, geometry, score, or GhostStream output is emitted.

A failure kills this exact seven-year real-shower feasibility formulation. Do not change years, months, source family, parser, blind interval, support thresholds, active-year strata, complex mapping, or gates after execution.

A pass authorizes only a separately frozen real-shower **development benchmark**. That benchmark must prospectively define a seven-year adaptation of the annual-median statistic, background construction, calibration, complex-disjoint evaluation, active-year strata, seeds, comparators, thresholds, and scientific gates before reading any score. It does not authorize confirmation data, catalogue scanning, GhostStream scoring, or a discovery claim.