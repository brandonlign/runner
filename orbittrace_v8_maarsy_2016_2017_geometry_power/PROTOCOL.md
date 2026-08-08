# OrbitTrace v8 — MAARSY 2016/2017 external geometry-power stage

## Status

Frozen after MAARSY RCS Stage-0G schema-only run `31232598941` / artifact `9014318828` and **before any MAARSY HDF5 dataset value has been read**.

This is the first scientific-value stage for the separate MAARSY 2016–2024 Zenodo release. It is restricted to the first external power question: whether unchanged v8 generates at least `N >= 100` recurrent families on a fixed two-year MAARSY panel. It does **not** read `kepler`, does not perform orbital corroboration, does not claim an external pass, and does not authorize the final GMN target-containing discovery scan by itself.

## Immutable promoted method

Promoted v8 remains commit `c9d6c44704013ba0c9430100e98a29a56b453304`, development run `31217916558`, artifact `9009728299`, ZIP SHA-256 `88d2d607e05d027015c338f7e23b64a6195e55ae24f1b2ac745f5e9bc6df599e`, verdict `PASS_POOLED_YEAR_CENTROID_V8_DEVELOPMENT`.

No v8 parameter, threshold, family rule, ranking rule, episode size, power floor, or target boundary may be changed because of MAARSY.

## Frozen external dataset

Zenodo record:

- record `15553437`;
- DOI `10.5281/zenodo.15553437`;
- file `silseth_thesis_data.tar.gz`;
- exact byte size `21485785089`;
- Zenodo MD5 `01820c6a90ea1415b011bb013a4d9213`;
- content URL `https://zenodo.org/api/records/15553437/files/silseth_thesis_data.tar.gz/content`.

Stage-0F froze the first non-empty archive member as `data/2016/03/kep_collect.h5`, 139,028,822 bytes. Stage-0G then inspected only HDF5 structure and found 9,518 rows in that file with one-dimensional datasets including `slat`, `slon`, `sun_lon`, `t0`, and `vels`, while reading zero dataset values and zero attribute values.

## Fixed years before scientific values

Use **2016 and 2017 only**.

This pair is fixed before any MAARSY array value is read because it is the earliest consecutive calendar-year pair in the archive beginning with the structurally observed 2016 directory. No later pair may replace it based on family count, scores, coverage, or scientific performance.

All `data/2016/MM/kep_collect.h5` and `data/2017/MM/kep_collect.h5` members encountered in monotonically increasing archive path order are used. The stream stops at the first `data/2018/` member. Months are not added/dropped based on values. Duplicate year-month members or non-monotonic selected month order are integrity failures.

## Frozen field semantics before values

The mapping is frozen from public processing source by the same meteor-processing author and from the pre-access schema, not from observed MAARSY values.

Author source provenance:

- repository `jvierine/pansy_receiver` commit `a9f40ab941fa6fec0a781de552c2a4341c8639ba`;
- `simple_radiant.py` Git blob `8a02bd409cc07436c61b1a557bb26754485abbea`:
  - meteor velocity direction is reversed to form the radiant;
  - radiant is transformed to `geocentricmeanecliptic`;
  - returned latitude is geocentric ecliptic latitude in degrees;
  - returned longitude is the signed wrapped difference `radiant ecliptic longitude - Sun ecliptic longitude` in degrees;
  - returned Sun longitude is geocentric mean ecliptic solar longitude in degrees;
- `plot_simple_fits.py` Git blob `6383dfd00b0981c1c2f5d741353bda5a5b5b8969`:
  - `slat` is populated from the fit's `eclat`;
  - `slon` is populated from the fit's `eclon`;
  - velocity is the norm of the fitted meteor velocity;
  - the plotted velocity is labeled `Geocentric velocity (km/s)`.

Therefore the frozen MAARSY geometry interpretation is:

- `sun_lon` -> solar longitude `sol`, degrees;
- `slon` -> Sun-centered geocentric ecliptic radiant longitude, degrees; feed v8 as `wrap180(slon)`;
- `slat` -> geocentric ecliptic radiant latitude, degrees;
- `vels` -> geocentric speed, km/s;
- stable event ID -> `MAARSY|YEAR|ARCHIVE_MEMBER|ROW_INDEX_0BASED`.

No `kepler`, `kepler_std`, `t0`, `fn`, CNN, RCS, altitude, pressure, path, or other field may enter proposal generation, component construction, family formation, or the N power decision.

### Representation-conformance rule

The interpretation above is **not adaptable after values are read**. If the selected files do not satisfy all of the following as stored, the result is `FAIL_MAARSY_GEOMETRY_INTERFACE_CONFORMANCE`, not a unit-conversion repair:

- `sun_lon` finite values intended for use lie in `[0,360)` degrees;
- `slat` finite values intended for use lie in `[-90,90]` degrees;
- `slon` is accepted at any finite degree representation and wrapped with the already-frozen v8 `wrap180` operation;
- `vels` is interpreted directly as km/s; no multiplication/division/unit inference is allowed.

## Blindness boundary

For every selected HDF5 member:

1. verify required dataset paths/shapes/dtypes structurally;
2. read **only `sun_lon`** for all rows;
3. validate solar longitude and construct the external blind mask;
4. remove rows with `20.0 <= sun_lon <= 55.0`;
5. only then read `slat`, `slon`, and `vels` for the retained row indices.

Thus no radiant or speed value from the excluded 20°–55° interval is read by this stage.

`kepler` and all orbital fields remain completely unread.

## Geometry validity and deterministic density normalization

After the blind cut, retain rows only if:

- all mapped geometry values are finite;
- `-90 <= slat <= 90`;
- `5 <= vels <= 75` km/s;
- `sun_lon` already passed `[0,360)` validation.

The resulting v8 event fields are exactly:

- `sol = sun_lon`;
- `sun_lon = wrap180(slon)`;
- `ecl_lat = slat`;
- `vg = vels`.

To preserve the frozen external density normalization used in the direct-v8 AMOR test, cap each fixed 10° solar-longitude bin at **10,000 events per year**. If a bin exceeds 10,000 eligible rows, retain the 10,000 smallest SHA-256 identities of the exact event ID string above. No geometry value enters the downsampling key.

## Exact v8 family construction

Use the promoted frozen sources and exact existing implementation:

- label-free fixed4 proposal generator from passed v6;
- first shortlist `64`, audit shortlist `128`;
- anchor multiplicity >=2;
- top 512 retained quartets per fixed 10° bin;
- exact v6 within-year component rules: >=4 events and >=2 quartets;
- exact v6 connected cross-year family graph;
- direct family edges only across different years;
- family-link radius exactly `1.5`;
- at least 2 distinct years per family;
- same-year components may coexist transitively exactly as in v6;
- v8 pooled same-year centroids may be computed after family formation, but may not alter family membership or N.

No score calibration threshold, shower label, orbit, target coordinate, target member, or old OrbitTrace rank enters this stage.

## Frozen power gate for this stage

Integrity gates:

- selected years exactly `[2016,2017]`;
- at least one frozen `kep_collect.h5` member encountered for each year;
- selected year-month member order monotonic with no duplicates;
- no selected member outside 2016/2017 is scientifically opened;
- 20°–55° cut occurs before radiant/speed reads;
- no orbital dataset is opened;
- at least 24 scannable fixed 10° bins in each year;
- exact promoted source/proposal/component/family constants verified;
- all family IDs unique and every retained family spans both 2016 and 2017;
- no target information access.

Geometry-power verdict:

- if any integrity/interface gate fails: `FAIL_MAARSY_GEOMETRY_INTERFACE_OR_INTEGRITY`;
- else if recurrent-family count `N < 100`: `INCONCLUSIVE_V8_MAARSY_EXTERNAL_POWER_N`;
- else: `PASS_V8_MAARSY_EXTERNAL_N_POWER_GATE`.

`PASS_V8_MAARSY_EXTERNAL_N_POWER_GATE` is **not** an external-validation pass. It only authorizes a separately frozen post-ranking orbital-corroboration stage on the already immutable MAARSY family/ranking universe. The existing second power floor `Q >= 30` and the frozen scientific pass/fail gates remain required later.

No result from this stage may be used to change v8, switch MAARSY years, relax N/Q floors, develop a successor, reveal OrbitTrace, or execute final GMN Stage A/Stage B.