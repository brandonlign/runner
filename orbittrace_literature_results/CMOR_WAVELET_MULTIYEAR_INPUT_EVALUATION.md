# CMOR-style wavelet multiyear input evaluation

## Purpose

The Brown et al. (2010) CMOR survey stacked seven years of radar orbits into a virtual year, divided that stack into one-degree solar-longitude bins, required at least 300 radiants contributing to a wavelet coefficient, and linked candidate maxima across at least three points separated by no more than two degrees of solar longitude.

A single SonotaCo year was already shown to provide only one necessary-support chain. The next preregistered question was whether a seven-year optical virtual year could support a fair global transfer without lowering the published sample floor or restricting the analysis to known high-density seasons.

## Frozen design

The input audit fixed the following before the seven archives were opened:

- years 2019–2025;
- raw concatenation into one virtual year;
- one-degree bins;
- the 300-radiant necessary floor;
- the <=2° / three-point temporal-linking rule;
- the same geometry-only quality filter and 20°–55° blind interval;
- no shower-label or OrbitTrace access;
- no wavelet coefficient, local maximum, recovery, or comparison endpoint;
- four all-required authorization gates, including at least 80% of available bins reaching 300 total events.

The first execution exposed only a known CSV-schema issue: annual files from 2019–2024 contain a trailing empty header field while their data rows use the effective header width. Every older row was therefore rejected before filtering. The resulting support values were invalid and were not used. A schema-only wrapper applied the exact trailing-empty-header reconciliation already validated for the SonotaCo 2023 benchmark. No year, field, quality filter, blind interval, support threshold, dominance threshold, or temporal rule changed.

## Valid execution

- Workflow: `31078486173`
- Artifact: `8958469799`
- Artifact digest: `sha256:8fee6f4de39e1719e1cc135827c0d00b1772b3a2495235113200785c16e287be`
- Result SHA-256: `5b972271b94456974eaf6183618c8063be0131fc70b297e6f9d9364255732464`
- Verdict: `PASS_CMOR_WAVELET_MULTIYEAR_INPUT_AUDIT`
- Decision: `DEFER_FULL_CMOR_WAVELET_COMPARATOR_UNTIL_A_BETTER_EXPOSURE_CONTROLLED_MULTYEAR_SURVEY_INPUT_EXISTS`

All seven archives, annual members, schemas, blind-interval removals, and retained-count reconciliations passed. No shower label, candidate value, wavelet coefficient, or detection endpoint was accessed.

## Annual inputs

| Year | Raw rows | Retained rows | Archive SHA-256 prefix | Header reconciliation |
|---:|---:|---:|---|---|
| 2019 | 28,587 | 18,955 | `d49c37f5a9f7` | trailing empty field removed |
| 2020 | 33,446 | 22,053 | `429c3a455623` | trailing empty field removed |
| 2021 | 41,177 | 26,720 | `8d58f089c413` | trailing empty field removed |
| 2022 | 48,788 | 30,955 | `945372460353` | trailing empty field removed |
| 2023 | 47,087 | 31,048 | `9f44696f9916` | trailing empty field removed |
| 2024 | 38,793 | 24,795 | `409bb958c6f1` | trailing empty field removed |
| 2025 | 36,826 | 23,662 | `f4eb716a4b90` | none required |

The raw seven-year stack contained 178,188 quality-retained, blind-interval-excluded events.

## Support and exposure result

| Quantity | Result | Frozen gate | Outcome |
|---|---:|---:|---|
| Available one-degree bins | 324 | — | — |
| Median stacked bin count | 393 | — | — |
| 10th / 90th percentile bin count | 132 / 1,124.6 | — | — |
| Bins with at least 300 total events | 199 / 324 = 61.4% | at least 80% | **FAIL** |
| Bins with events from at least five years | 313 / 324 = 96.6% | at least 80% | PASS |
| Supported bins dominated >50% by one year | 9 / 199 = 4.5% | at most 10% | PASS |
| Eligible three-point chains | 653 | at least 200 | PASS |
| Longest eligible chain | 118 points | — | — |

The stack is genuinely multiyear and is not generally dominated by one annual catalogue. The decisive problem is breadth: 125 available bins still contain fewer than 300 total events across all seven years. Because 300 total events in a bin is only a necessary condition for 300 events to contribute near a specific radiant-speed test point, those 125 bins cannot satisfy the published coefficient-support rule anywhere. Many of the remaining 199 bins may also fail locally.

## Decision

A global wavelet comparator is formally deferred. Running the kernel only in supported seasons, enlarging time bins, lowering the contributor floor, shortening temporal chains, or evaluating known coordinates would change the published survey task after seeing the data. Such a result could not be presented as a fair CMOR-style comparator.

This is a data-and-task compatibility decision, not a negative result for the wavelet method. The CMOR survey used a much denser radar catalogue; the available optical SonotaCo stack does not provide comparable global support. The defer decision therefore cannot be used to claim that fixed4 beat the wavelet method.

## Effect on the OrbitTrace literature comparison

The meaningful comparator work is now covered as follows:

- classical D_SH and D_N linkage: implemented on the common sparse-episode benchmark;
- deterministic Sugar core: implemented on the common sparse-episode benchmark;
- full uncertainty-aware Sugar catalogue reconstruction: implemented and transferred across 2025 and 2023;
- published HDBSCAN catalogue configuration: implemented and transferred across 2025 and 2023;
- CMOR-style wavelet survey: formally audited and deferred because the available optical input fails a frozen global-support gate.

The wavelet defer does not strengthen fixed4 by itself. The defensible fixed4 claim continues to rest on its frozen sparse-episode results and targeted OrbitTrace recovery, while HDBSCAN and Sugar establish that established catalogue methods remain strong for larger populations and weak in the smallest annual size strata.
