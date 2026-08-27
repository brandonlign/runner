# OrbitTrace P19 — MAARSY 2020/2021 schema-compatibility preflight

## Status

This is a **source/schema-only compatibility contract** for the permanent external-validation panel fixed by `orbittrace_governance/FIXED_DATA_SPLIT_V1.md`: MAARSY 2020 and 2021.

It is frozen before the P19 primary development result is known and before any MAARSY 2020/2021 scientific event value is accessed. It cannot make P19 externally eligible. Scientific MAARSY access remains dormant unless one final method first passes its target-excluded development requirements and the permanent one-shot SonotaCo 2013/2014 matched literature-superiority gate.

A schema-only preflight may later inspect object names, shapes, dtypes, chunk/compression metadata, and attribute **names** for the fixed 2020/2021 files. It may not read dataset values or attribute values.

## Frozen external dataset identity

Use the already-established MAARSY RCS public release lineage:

- Zenodo record `15553437`;
- DOI `10.5281/zenodo.15553437`;
- file `silseth_thesis_data.tar.gz`;
- exact byte size `21485785089`;
- published MD5 `01820c6a90ea1415b011bb013a4d9213`;
- selected external years exactly `[2020, 2021]`.

No other MAARSY year or alternate external dataset may replace this pair based on scientific values, family counts, power, or performance.

## Existing pre-value schema/source evidence

Earlier MAARSY work established the release interface before reading the first HDF5 scientific values:

- Stage-0G schema-only audit run `31232598941` found one-dimensional row-aligned datasets including `slat`, `slon`, `sun_lon`, and `vels` and a row-aligned `kepler` dataset;
- the frozen v8 geometry protocol documents the public-author mapping from `jvierine/pansy_receiver` commit `a9f40ab941fa6fec0a781de552c2a4341c8639ba`:
  - `sun_lon` is geocentric mean ecliptic solar longitude in degrees;
  - `slon` is geocentric ecliptic radiant longitude minus Sun longitude in degrees;
  - `slat` is geocentric ecliptic radiant latitude in degrees;
  - the norm of `vels` is geocentric speed in km/s;
- the frozen post-ranking orbital protocol documents the public DASST/pyorb mapping of `kepler` as six columns `[a_m, e, i_deg, omega_deg, Omega_deg, true_anomaly_deg]`, with `q_AU = abs((a_m / 149597870700.0) * (1-e))`.

Those historical interfaces may be used as source/schema provenance. Historical MAARSY scientific values or performance results may **not** be used to tune P19 or select an external rule.

## Exact P19 geometry interface

P19 and its v8 backbone require exactly four scientific geometry fields per event:

- internal `sol` <- MAARSY `sun_lon`, degrees;
- internal `sun_lon` <- inherited `wrap180(MAARSY slon)`, degrees;
- internal `ecl_lat` <- MAARSY `slat`, degrees;
- internal `vg` <- norm of MAARSY `vels`, km/s.

The stable external event identity is fixed as

`MAARSY|YEAR|ARCHIVE_MEMBER|ROW_INDEX_0BASED`.

No fitted coordinate transform, learned calibration, proxy radiant, alternate speed statistic, unit inference, imputation, or outcome-dependent mapping is permitted.

## Required 2020/2021 schema-only conformance

Before any 2020/2021 dataset value may be read, a schema-only audit must prove for every selected `data/2020/MM/kep_collect.h5` and `data/2021/MM/kep_collect.h5` member that is structurally present:

1. `sun_lon`, `slon`, and `slat` are numeric one-dimensional datasets with a common row count `n`;
2. `vels` is numeric and row-aligned with the same `n`, with a shape compatible with the already-frozen geocentric-velocity norm operation;
3. `kepler` is numeric, row-aligned with the same `n`, and has shape `(n, 6)`;
4. no schema decision requires reading a dataset value or attribute value;
5. member identity and calendar year/month are determined from archive/HDF5 structure, not meteor values;
6. no 2019 or 2022+ scientific member is opened under the 2020/2021 contract.

If any selected 2020/2021 member violates this frozen interface, return `ARCHITECTURE_INCOMPATIBLE_P19_MAARSY_2020_2021` before scientific-value access. Do not repair the schema by changing the scientific method or substituting another year.

## Blind access order for any later scientific external run

If and only if downstream authorization is eventually satisfied, the scientific external runner must preserve the already-frozen blind order independently for each selected member:

1. verify required paths/shapes/dtypes structurally;
2. read only `sun_lon` for all rows;
3. validate solar-longitude representation and remove every row with `20.0 <= sun_lon <= 55.0`;
4. only then read `slon`, `slat`, and `vels` for retained indices;
5. construct the exact mapped P19/v8 geometry event records;
6. build the full geometry-only family universe/ranking without `kepler`;
7. freeze and hash that universe/ranking;
8. only a separately authorized orbital-corroboration stage may read `kepler`, and only for event IDs already in the frozen family universe.

No radiant, speed, orbit, label, or target-region scientific value may be read before its permitted stage.

## Exact P19 method transfer

External P19 must transfer without retuning:

- exact label-free fixed4 proposal generation;
- exact within-year component floor and construction;
- exact hard cross-year recurrence graph and inherited radius;
- exact pooled same-year centroid repair;
- exact multiplicity scoring/ranking backbone;
- exact P19 unmatched-component soft recurrence rule with three-event trigger, inherited `1.5` geometry radius, pairwise coherence, reciprocity, intersection membership, non-recursion, and exact-event-set deduplication;
- exact rule that the v8 hard ranking is an immutable prefix and P19 soft families are appended afterward.

No MAARSY result may alter any of those rules.

## External truth/corroboration interface

If an eventual external scientific run reaches orbital corroboration, reuse the already-frozen native orbit mapping and established D_SH evaluator semantics rather than inventing a P19-specific truth system:

- `a_AU = a_m / 149597870700.0`;
- `q_AU = abs(a_AU * (1-e))`;
- `i = i_deg`;
- `arg = omega_deg mod 360`;
- `node = Omega_deg mod 360`;
- true anomaly is unused by D_SH.

Any external power floor and scientific effect-size gates must be frozen separately **before** 2020/2021 scientific values are opened and must compare P19 against its fixed reference method on one immutable family/event universe. This schema contract does not choose those performance thresholds.

## Firewall

This contract authorizes no MAARSY event-value access and no SonotaCo 2013/2014 access. It contains no OrbitTrace target coordinate, member, identity, target-containing result, or target-region event. The target and solar-longitude 20°–55° scientific region remain inaccessible until development, literature superiority, and no-retuning external generalization have all been satisfied.
