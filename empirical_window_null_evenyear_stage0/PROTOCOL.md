# Empirical-window null: frozen untouched even-year Stage-0 protocol

## Question

Does calibrating independent search windows against other windows drawn from the **same fixed empirical sporadic corpus** repair the conditional false-alarm instability observed when calibration and audit events were first split into separately realized background halves?

This Stage-0 PR tests null calibration only. It does not inspect established-shower power, perform a catalog scan, apply the method to GhostStream, or claim a discovery.

## Development boundary

The years 2019, 2021, 2023, and 2025 are development data. They exposed the failure of event-level background thinning and were used to choose the final mechanism.

The years 2020, 2022, and 2024 are untouched confirmation years. No result from those years may alter the score, window generator, sectors, counts, gates, or continuation rule.

## GhostStream blindness

Before any background pool, window, score, calibration distribution, or gate is formed, remove every event with solar longitude from 20.0 degrees through 55.0 degrees. This broad interval contains GhostStream-April-36.9.

No GhostStream radiant, speed, orbit, membership, event list, or detection score may be used.

## Fixed data construction

- Download the 36 official GMN monthly trajectory summaries for 2020, 2022, and 2024.
- Reuse the exact PR #14 parser and quality filters, verified by its source blob SHA `4a029051230f7c6e99b09e911f8a9e5228a58783`.
- Reuse the same IAU MDC complex/parent mapping logic and event reservoirs.
- Require established showers to have at least 200 quality events, representation in all three years, and at least 20 events in every year.
- Define a strong shower as at least 750 quality events represented in all three years.
- Data gates are frozen before download:
  - at least 30 eligible showers;
  - at least 10 strong showers;
  - at least 20 eligible complex units;
  - at least 5 multi-shower complex units;
  - at least 150,000 quality sporadics;
  - at least 95% completeness in the selected artifact.

The selected artifact may contain established-shower labels for a later separately frozen power stage. The Stage-0 null code discards the labeled return immediately and never reads a shower identity or complex label.

## Fixed window generator

Within each untouched year and each 60-degree solar-longitude sector:

1. Choose a sporadic center event uniformly from that year-sector.
2. Collect same-year sporadics within plus or minus 10 degrees of the center.
3. Keep the center and sample 127 additional events without replacement.
4. Build the same 128-event physical-geometry episode used in PR #23.

Calibration and audit windows are independent pseudorandom draws from this **same fixed corpus and same generator**. Events are deliberately not hash-split into two separately realized thinned backgrounds. Window overlap is allowed; the inferential unit is a Monte Carlo draw from the fixed empirical generator.

## Frozen cross-fitted score

For each 128-event window:

1. Compute the fixed PR #14 geometry distance using relative solar longitude, Sun-centered ecliptic radiant, and geocentric speed, with scales 2 degrees, 2 degrees, and 2 km/s.
2. For each of eight deterministic salts, split the window into exactly 64 reference and 64 query events.
3. For each query event, compute its distance to the second-nearest reference event.
4. Average the two smallest query distances and negate the result.
5. Use the median across the eight split scores.

No orbital elements, shower identity, absolute date, or absolute solar longitude enter the score.

## Frozen local Monte Carlo p-value

For each year-sector and audit batch:

- draw 256 calibration windows;
- draw 128 independent audit windows;
- compute `p = (1 + number of calibration scores >= audit score) / 257`.

Run four entirely separate seed batches. Each batch contains 18 year-sectors, for 2,304 audit windows and 4,608 calibration windows.

## Frozen gates

Every one of the four batches must satisfy all three gates:

1. pooled false-positive rate at alpha 0.05 is at most 0.060;
2. pooled false-positive rate at alpha 0.01 is at most 0.020;
3. worst year-sector false-positive rate at alpha 0.05 is at most 0.120.

Any failed data or null-calibration gate kills this formulation. No sector removal, seed replacement, threshold change, score change, or post-result recalibration is permitted.

A pass authorizes only a separately frozen untouched even-year established-shower power benchmark. It does not authorize catalog-level claims or a GhostStream application.
