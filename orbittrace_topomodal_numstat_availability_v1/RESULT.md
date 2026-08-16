# OrbitTrace topomodal `Num (stat)` availability v1 — binding result

## 🟢 POSITIVE — PASS, station-weighted structural successor activated

Binding run: `31972929547`

Job: `95228057543`

Execution head: `d8da941a35670f66122d0ab6d0005eab9b65051f`

Artifact: `9270309302`

Artifact ZIP SHA-256: `15abf085e9e78f013e98183fb226b748151af4bc109629411b1185ea89c41e46`

Exact predecessor-universe manifest SHA-256: `3ed5c33216d7d1cf2cbc703da088b3a86132e50532fb996cfe475d7f6052d7f8`

Exact audited `event_id -> num_stat` mapping SHA-256: `92f6ce1961b0e8642f6bdd1cc455b07785ed8224c8f8f3d467d69fac2b82921c`

Exact verdict:

`PASS_TOPOMODAL_NUMSTAT_AVAILABILITY_V1`

## Exact sample reconstruction

Before any station count was opened, Stage A reconstructed the exact immutable #1284 sparse event universe from the frozen scan-parser validity, inclusive target exclusion, duplicate handling, and thinning rule.

The exact frozen subset counts reproduced:

- d128 b0: `5567`;
- d128 b1: `5840`;
- d128 b2: `5857`;
- d128 b3: `5816`;
- d1024 b0: `677`;
- d1024 b1: `739`;
- d1024 b2: `736`;
- d1024 b3: `766`.

Audited d128-union size: `23080`.

Only after that manifest was sealed did Stage B re-read the same byte-identical monthly sources and parse `Num (stat)` for manifest IDs only.

## Availability result

Every exact sparse event had a finite exact integer `Num (stat) >= 2`.

| panel | requested | usable | completeness | all usable |
|---|---:|---:|---:|---|
| d128 b0 | 5567 | 5567 | 1.000 | yes |
| d128 b1 | 5840 | 5840 | 1.000 | yes |
| d128 b2 | 5857 | 5857 | 1.000 | yes |
| d128 b3 | 5816 | 5816 | 1.000 | yes |
| d1024 b0 | 677 | 677 | 1.000 | yes |
| d1024 b1 | 739 | 739 | 1.000 | yes |
| d1024 b2 | 736 | 736 | 1.000 | yes |
| d1024 b3 | 766 | 766 | 1.000 | yes |

Year-level audited union:

- 2022: `9963 / 9963`, completeness `1.000`;
- 2023: `13117 / 13117`, completeness `1.000`.

All frozen 95% availability gates passed, and the separately preregistered stricter scientific prerequisite of **100% usable station support for every event in every frozen panel** is also satisfied.

## Firewall

The station join parsed only unique trajectory ID, solar longitude, and `Num (stat)` for IDs already in the exact predecessor manifest. Station codes, station geography, participating-station strings, shower truth, and meteor geometry were not parsed in the station-support join. Protected `[20.0,55.0]` station-count values were not emitted or used.

OrbitTrace target information/events, SonotaCo, ASFN/EFN event rows, AMOS, MAARSY, and DMS remained inaccessible.

## Consequence

The pre-frozen `orbittrace_station_weighted_topomodal_scale_v1` structural diagnostic is **activated exactly as written**. No station-count threshold, transform, cap, rank, clipping rule, exponent, ordinary-density blend, graph change, subset change, or gate change is authorized from this availability result.