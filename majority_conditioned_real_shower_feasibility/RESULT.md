# Majority-conditioned recurrence seven-year real-shower feasibility: authoritative no-go

Runner workflow `30881333680` completed the exact frozen support-only audit under manifest v2. Artifact `8881469038` was preserved with digest `sha256:3d7c32036633f2fc2edf240be4ef6ae2b02755991e5a515d399103f5c3c7ab56`.

The workflow verified and parsed all 84 official GMN monthly trajectory summaries from 2019 through 2025 with the exact PR #14 quality parser. Solar longitude 20.0°–55.0° inclusive was removed before every label or quality parse. No event row, identity, geometry distribution, detector score, or GhostStream-region value was emitted.

## Corpus

- total data rows: **2,845,803**;
- malformed rows: **0**;
- blind-interval rows removed before parsing: **198,108**;
- post-boundary quality rows: **2,534,353**;
- post-boundary quality sporadics: **1,808,380**;
- distinct positive shower numbers: **400**.

Quality sporadics by year were:

- 2019: **32,760**;
- 2020: **77,841**;
- 2021: **129,162**;
- 2022: **206,219**;
- 2023: **284,333**;
- 2024: **456,246**;
- 2025: **621,819**.

The early years therefore failed the predeclared minimum-exposure gate despite abundant pooled volume.

## Active-year support

At k=4 members per active shower-year:

- transient, exactly one year: **26**;
- exactly two years: **8**;
- recurrence-eligible minority, exactly three years: **11**;
- majority-active, four through seven years: **353**;
- anonymous complex units represented by exactly-three-year showers: **11**.

At k=8:

- transient: **29**;
- exactly two years: **12**;
- exactly three years: **17**;
- majority-active: **335**;
- exactly-three-year complex units: **17**.

For completeness, exactly-three-year counts rose to **27** only at k=12, while **311** showers remained majority-active.

## Frozen-gate outcome

The formulation failed five gates:

- every year did not contain at least 80,000 quality sporadics;
- exactly-three-year k=4 showers were **11**, required at least **30**;
- exactly-three-year k=8 showers were **17**, required at least **25**;
- exactly-three-year k=4 complex units were **11**, required at least **25**;
- exactly-three-year k=8 complex units were **17**, required at least **20**.

All source, structural, blindness, total-volume, shower-diversity, transient-control, majority-active, and forbidden-output gates passed.

Verdict: **`KILL_MAJORITY_CONDITIONED_REAL_SHOWER_FEASIBILITY`**.

## Interpretation

The majority-conditioned statistic is valid and effective in the frozen simulation regime, but that regime does not represent the dominant real established-shower population. In seven consecutive GMN years, most catalogued showers are detected in a majority of years. A pointwise seven-year median would therefore treat much of the real shower signal as common mode and suppress it rather than isolate it.

The severe year-to-year exposure growth is a second incompatibility: calendar-year presence is confounded with observing coverage. The next methodology must model year-specific exposure and distinguish a spatially localized persistent component from smooth shared background. It may not rescue this result by lowering support gates, choosing a different active-year cutoff, shortening the corpus, or changing the median after observing these counts.

No real-shower benchmark, confirmation study, catalogue scan, or GhostStream application is authorized by this formulation.