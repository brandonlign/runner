# OrbitTrace topomodal `num_stat` availability v1

## Status

**FROZEN BEFORE ANY PROJECT `Num (stat)` VALUE IS READ.**

This is a truth-free, target-excluded feasibility audit only. It cannot rank a candidate, open shower truth, access station identities, or promote a method.

## Scientific motivation

The exact #1284 fixed-scale ToMATo architecture has demonstrated strong sample-size generalization and substantially higher sparse known-stream recovery, but its complete hierarchy remains difficult to prioritize early. A potentially independent observational-quality axis exists in the official GMN trajectory data: `Num (stat)`, the number of stations that observed a solved meteor.

A prior v31 station-count availability attempt never queried a project event because the separate GMN Explorer REST hostname failed TLS validation. The official monthly trajectory files used by OrbitTrace already contain `Num (stat)`, so this audit asks only whether that field is available for the exact #1284 sparse target-excluded event universes from the same monthly source files.

No scientific interpretation of the station-count distribution is allowed here.

## 1. Firewall

Use only GMN calendar years 2022 and 2023.

For every monthly trajectory row, read only the minimum fields needed for this audit:

- unique trajectory identifier;
- solar longitude;
- `Num (stat)`.

Remove rows with inclusive solar longitude `[20.0,55.0]` **before their station count can enter any subset statistic or emitted mapping**.

Forbidden:

- IAU shower number/code or any shower label;
- radiant, speed, orbit, uncertainty, fit error, station code, participating-station list, station geography, target information, or protected-region station count in any output/statistic;
- SonotaCo scientific access;
- ASFN/EFN event-level access;
- AMOS, MAARSY, or DMS scientific access;
- completeness-floor relaxation or subset change after outcome.

## 2. Authoritative source

Use only the official GMN monthly trajectory files under

`https://globalmeteornetwork.org/data/traj_summary_data/monthly/`

through pinned `gmn-python-api==0.0.13` monthly-file and trajectory-reader interfaces.

The expected camel-case fields are:

- index: `unique_trajectory_identifier`;
- `sol_lon_deg`;
- `num_stat`.

The audit must stop before any project mapping is emitted if `num_stat` is absent, nonnumeric, or the monthly parser schema changes.

Do not use the GMN Explorer REST API.

## 3. Exact sparse event universes

Reuse the exact PR #1272/#1284 identity rule:

`H(eid) = uint64_be(SHA256('ORBITTRACE_SCALE_STRESS_V1|' + eid)[0:8])`.

After the inclusive target exclusion, audit exactly:

- denominator `128`, buckets `0,1,2,3`;
- denominator `1024`, buckets `0,1,2,3`.

The expected event counts are frozen from #1284 structural evidence:

- d128: `5567, 5840, 5857, 5816`;
- d1024: `677, 739, 736, 766`.

Any count mismatch is an engineering/schema failure, not permission to alter the sample.

## 4. Availability checks

For every event in each of the eight exact sparse subsets, classify `num_stat` as usable iff it is:

- finite;
- integer-valued exactly;
- `>=2`.

This audit does not impute missing values and does not inspect the distribution to choose a later transform.

Reuse the already-established project schema-completeness floor from the prior station-count protocol: **95% usable in each calendar year and in each of the eight sparse subsets**.

The audit may report only:

- requested and usable counts by year;
- requested and usable counts by sparse subset;
- completeness fractions;
- an overall histogram of usable integer `num_stat` values across all target-excluded 2022+2023 rows and separately across the union of the eight audited sparse subsets;
- SHA-256 of the exact target-excluded `event_id -> num_stat` mapping for the audited union.

The histogram is descriptive only and cannot select a threshold, transform, clipping rule, cap, weight exponent, or later variant.

## 5. Frozen gate

Return

`PASS_TOPOMODAL_NUMSTAT_AVAILABILITY_V1`

iff:

1. all eight exact subset counts reproduce;
2. usable completeness is `>=0.95` separately in 2022 and 2023;
3. usable completeness is `>=0.95` in each of all eight exact sparse subsets;
4. every emitted event ID lies outside the protected solar-longitude interval and belongs to one of the exact audited subsets;
5. no forbidden field/source is accessed.

Otherwise return

`FAIL_TOPOMODAL_NUMSTAT_AVAILABILITY_V1`.

No mixed verdict, completeness relaxation, member deletion, year substitution, source substitution, or result-informed repair is authorized. A transport/parser technical failure before any complete mapping or gate statistic may receive an engineering-only repair if the source, event universe, field, and gate remain unchanged.

## 6. Consequence

A PASS authorizes only the separately pre-frozen zero-label station-support-weighted topomodal structural diagnostic. A FAIL permanently blocks that successor and does not authorize a different station-count statistic.