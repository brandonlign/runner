# LS-reconciled nominal-orbit reconstruction: 12-shower control calibration

Status: frozen Stage-2 control calibration. GhostStream and NOP solution 004 are excluded from control selection, thresholds, and continuation decisions.

## Scientific question

Stage-1c showed that one official lookup population, NOP solution 004, can reproduce its published mean orbit from mandatory UTC/radiant/speed/solar-longitude fields after bounded reconciliation of internally inconsistent timestamps against submitted J2000 solar longitude.

A result on the target population alone is not enough. This stage tests whether the same fixed reconstruction transfers across established showers spanning distinct speed and inclination regimes.

The contribution under test is narrow: whether official MDC lookup-table geocentric observables can recover catalogue-level nominal heliocentric orbits with predictable accuracy. This is not yet a branch classifier and does not use GhostStream.

## Frozen catalogue snapshot and controls

Use the exact MDC catalogue snapshot already preserved in provenance artifact `8874489453`, version `2026-06-25`.

Eligible solutions were selected before any control lookup was downloaded or reconstructed:

- established status (`s == 1`);
- official non-placeholder lookup filename;
- complete catalogue `LoS`, `Ra`, `De`, `Vg`, `q`, `e`, `inc`, `peri`, and `node`;
- catalogue membership `50 <= N <= 2000` to avoid tiny controls and very large downloads;
- NOP and GhostStream excluded.

Four physically populated strata were fixed:

1. `slow_low`: `Vg < 30 km/s`, `i < 60°`;
2. `mid_low`: `30 <= Vg < 50 km/s`, `i < 60°`;
3. `mid_high`: `30 <= Vg < 50 km/s`, `i >= 60°`;
4. `fast_high`: `Vg >= 50 km/s`, `i >= 60°`.

Within each stratum, solutions were ordered by SHA-256 of `IAUNo:Code:AdNo:lookup_filename`. The first three distinct shower codes were selected. The exact 12 controls, catalogue targets, lookup filenames, and selection hashes are frozen in `control_manifest.json`.

## Official lookup retrieval

For each frozen filename, retrieve only from the official MDC LuT host under `https://ceresiaumdc.ta3.sk/downloads/LuT/`.

The downloader may try the exact filename and fixed-width trailing-space encodings because the MDC site exposes some LuT filenames from padded database fields. It may not substitute a different shower solution, mirror, publication table, or locally reconstructed membership list.

Record every attempted URL, final URL, byte count, content type, and SHA-256. Preserve every successful raw lookup.

## Frozen table parsing

A generic parser may resolve only documented representation differences:

- UTF-8 BOM;
- comma, semicolon, tab, or pipe delimiter;
- header rows within the first ten non-comment lines;
- normalized aliases for UTC timestamp, right ascension, declination, geocentric speed, solar longitude, event identifier, and source catalogue;
- standard ISO-like UTC timestamp punctuation.

It may not infer missing RA, Dec, `Vg`, `LS`, or timestamps from the catalogue mean. Rows lacking any required field are reported and excluded. No source or event is dropped based on reconstructed orbital performance.

## Frozen reconstruction

For every usable row, apply the unchanged Stage-1c method:

1. parse the submitted timestamp;
2. calculate J2000 solar longitude from Astropy's built-in Earth/Sun ephemeris and the fixed mean-J2000 ecliptic rotation;
3. find the nearest local UTC epoch matching submitted J2000 `LS` by the same deterministic Newton update;
4. record the original timestamp, reconciled timestamp, shift, and residual;
5. form the incoming geocentric velocity from submitted J2000 RA, Dec, and `Vg`;
6. add that velocity to Earth's heliocentric velocity at the reconciled epoch;
7. rotate the state to the mean J2000 ecliptic using obliquity `23.439291111°`;
8. calculate the same two-body osculating elements with the same solar gravitational parameter;
9. summarize finite bound rows by the same scalar median and target-centered circular-median rules;
10. compare the reconstructed median with that control's frozen catalogue orbit using the unchanged Southworth-Hawkins `D_SH` implementation.

No control-specific correction, source exclusion, radiant drift, speed adjustment, clipping, ephemeris change, or threshold tuning is allowed.

## Per-control usability gates

A control is evaluable only if all hold:

1. official lookup retrieved and parsed;
2. at least 50 unique rows;
3. at least 90% of parsed rows contain complete timestamp, RA, Dec, `Vg`, and `LS`;
4. at least 50 complete rows remain;
5. every reconciled row has final `LS` residual at most `0.001°`;
6. median absolute timestamp shift at most `1 hour`;
7. 95th-percentile absolute timestamp shift at most `12 hours`;
8. maximum absolute timestamp shift at most `72 hours`;
9. no reconciled row changes calendar year;
10. at least 95% of complete rows produce finite classical elements;
11. at least 90% of complete rows produce bound elliptical orbits.

All failed controls remain in the report. They may not be replaced.

## Frozen panel continuation gates

All must pass:

1. all 12 frozen official lookups are successfully retrieved;
2. at least 10 of 12 controls are evaluable;
3. every stratum has at least two evaluable controls;
4. at least 9 of 12 frozen controls have reconstructed `D_SH <= 0.08`;
5. at least two controls in every stratum have `D_SH <= 0.08`;
6. median `D_SH` across evaluable controls at most `0.04`;
7. 90th-percentile `D_SH` across evaluable controls at most `0.10`;
8. no evaluable control has `D_SH > 0.20`;
9. median absolute `q` error across evaluable controls at most `0.03 AU`;
10. median absolute `e` error at most `0.05`;
11. median absolute inclination error at most `3.0°`;
12. median circular argument-of-perihelion error at most `5.0°`;
13. median circular node error at most `1.0°`.

## Decision boundary

- `PROCEED_TO_BRANCH_SEPARATION_CONTROL_DESIGN`: every panel gate passes.
- `KILL_GENERAL_NOMINAL_ORBIT_RECONSTRUCTION`: any panel gate fails.

A pass establishes only cross-shower catalogue-orbit reconstruction accuracy. It does not establish that nominal event-orbit distributions can distinguish branches, provide observational uncertainties, authorize long-term integrations, or permit application to GhostStream. A separate positive/negative branch-separation calibration must be frozen next.
