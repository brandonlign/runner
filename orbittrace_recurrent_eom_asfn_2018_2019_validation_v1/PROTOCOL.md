# Recurrent-EOM HDBSCAN v1 — NASA ASFN 2018/2019 pristine cross-survey validation protocol

## Status

**Frozen before the first ASFN scientific/event-row inspection.**

NASA All Sky Fireball Network (ASFN) event values have not previously been scientifically used by OrbitTrace. The raw zero-data audit's sole `ASGARD` hit was independently adjudicated as a disjoint SonotaCo literature/software-name collision; all NASA-network/release-specific indicators had zero prior history hits. Subsequent ASFN stages accessed only official interface metadata, the primary Kingery et al. WGN publication, the ZIP HEAD response, the ZIP central directory, and `nasfn_2013-2019_readme.txt`. `nasfn_2013-2019_data.txt` remains unopened at this freeze.

This is the first intended **pristine cross-survey validation** of promoted recurrent-EOM HDBSCAN v1.

## 1. Frozen external object

Exact primary-paper archive:

`https://fireballs.ndc.nasa.gov/public_data/nasfn_2013-2019.zip`

Pinned archive SHA-256 from the readme-only preaccess stage:

`c091b0f3f87f10badbe5fa38e6c45ba818af99f1c27c2fd6a23be286074c89a4`

Pinned readme SHA-256:

`74bacb50b225032461ba8b200eec0d5274799ef3c2700cb9a3465b4d5c02a2bf`

Scientific member basename: `nasfn_2013-2019_data.txt` (11,275,430 uncompressed bytes from ZIP central-directory metadata).

## 2. Frozen validation years

Use **calendar years 2018 and 2019 only**.

This choice is frozen before event-row access and is determined solely from publication-level survey metadata: they are the final two complete calendar years in the fixed 2013–2019 release, avoiding row-count-informed or performance-informed year selection. Years 2013–2017 do not enter fitting, ranking, labels, diagnostics, or endpoints.

A data row receives deterministic event ID `ASFN:<physical-data-row-index>`, where the index is its 1-based physical record order after an optional header. This avoids assumptions about timestamp uniqueness.

## 3. Protected-region firewall and parsing order

The protected OrbitTrace solar-longitude interval `[20°,55°]` remains inaccessible.

The parser must use the readme-defined field order, allowing an optional first-line header containing the same field names. For every physical record:

1. decode only `time` and `slon` first;
2. reject rows not in calendar year 2018 or 2019;
3. reject rows with `20 <= slon <= 55` **before** decoding `lam_g`, `bet_g`, `v_g`, or `shw`;
4. for retained rows only, decode `lam_g`, `bet_g`, and `v_g` for clustering;
5. do not access `shw` until the complete parent and recurrent candidate memberships/ranks are serialized and SHA-256 frozen.

Rows from 2013–2017 and protected-region rows may be traversed only enough to obtain their time/year and solar longitude; their radiant, speed, shower label, orbital elements, and other scientific fields remain semantically undecoded and must not be reported.

## 4. Frozen event eligibility

For retained 2018/2019 rows outside `[20°,55°]`, use a row iff:

- `slon`, `lam_g`, `bet_g`, `v_g` parse as finite numbers;
- `v_g > 0` km/s.

The primary paper documents zero geocentric radiant/orbit values for events below the geocentric-solution speed limit; `v_g <= 0` is therefore treated as unavailable geocentric solution and excluded.

No cut on station count `n`, `Qstar`, saturation `sat`, radiant uncertainty, speed uncertainty, magnitude, trajectory residual, or shower code is authorized. No row-quality threshold may be introduced after seeing the data.

## 5. Frozen coordinate map

Use ASFN fields exactly as documented:

- solar longitude = `slon`;
- Sun-centered ecliptic radiant longitude = `(lam_g - slon) mod 360`;
- ecliptic latitude = `bet_g`;
- geocentric speed = `v_g`.

Use the promoted recurrent-EOM GEO6 representation unchanged:

`[cos(slon), sin(slon), sin(lon_sc)*cos(bet_g), cos(lon_sc)*cos(bet_g), sin(bet_g), v_g/72]`

with angular quantities converted to radians inside the trigonometric functions.

## 6. Frozen HDBSCAN parent and successor

Fit exactly one pooled 2018+2019 HDBSCAN hierarchy with the promoted settings:

- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- standard EOM;
- `cluster_selection_epsilon=0`;
- `allow_single_cluster=false`;
- no z-scoring, quality weighting, or probability trimming.

**Parent:** vanilla HDBSCAN EOM selected on ordinary stability.

**Successor:** exact promoted recurrent-EOM v1 on the unchanged hierarchy:

- split ordinary EOM contribution by descendant year;
- normalize each year's contribution by that year's accessible event count;
- cluster objective = minimum of normalized 2018 and normalized 2019 EOM;
- rerun HDBSCAN's own `get_clusters` with that recurrent stability.

Candidate ranking rules remain exactly the promoted rules:

- vanilla: descending ordinary stability, then member count, deterministic family ID;
- recurrent-EOM: descending recurrent stability, then ordinary stability, member count, deterministic family ID.

No ASFN-specific HDBSCAN or score parameter exists.

## 7. Prelabel freeze

Before `shw` is accessed, serialize a `PRELABEL` object containing:

- eligible event IDs/year/slon/radiant/speed used by clustering;
- HDBSCAN condensed-tree provenance hashes;
- vanilla selected nodes and exact memberships/order;
- recurrent selected nodes and exact memberships/order;
- candidate-order hashes;
- event counts by year;
- firewall declarations.

SHA-256 freeze this object before the second pass that reads `shw`.

## 8. Sealed external reference labels

After prelabel freeze only, reopen the exact data member and access only `time`, `slon`, and `shw` for already-retained event IDs.

The primary paper states that `shw` is a pre-existing ASFN shower-association code and uses `...` for sporadic/unassociated events. Treat exact `...` and blank/nonpresent code as `SPORADIC`; otherwise use the exact code as the external reference label.

These labels are acknowledged as an externally generated catalogue association, not perfect physical truth. They are sufficient only for the frozen **relative recurrent-EOM vs vanilla-HDBSCAN generalization test**; no stronger absolute completeness claim is authorized.

## 9. Frozen evaluator

Use exactly the promoted GMN family evaluator, separately for 2018 and 2019 while retaining each method's single pooled rank order:

- eligible reference shower: at least 4 retained events in that year;
- candidate is positive for a shower only if precision `>=0.5` and overlap `>=4`;
- report recovered @25/@50/@100/@500, top-100 dominant precision, MRR, full-catalogue qualified matches, and median top-500 fragmentation.

No ASFN-specific matching threshold or metric is added.

## 10. Binding pristine-validation gate

Use the **same no-regression gate** recurrent-EOM passed on target-excluded GMN 2022/2023:

1. recovered@100 strictly higher than vanilla in at least one of 2018/2019 and not lower in the other;
2. recovered@50 not lower in either year;
3. top-100 dominant precision not lower in either year;
4. MRR not lower in either year;
5. median top-500 fragmentation not higher in either year;
6. recurrent selected-node set differs from vanilla, proving mechanism activity.

Pass token:

`PASS_RECURRENT_EOM_HDBSCAN_V1_ASFN_2018_2019_PRISTINE_VALIDATION`

Otherwise:

`FAIL_RECURRENT_EOM_HDBSCAN_V1_ASFN_2018_2019_PRISTINE_VALIDATION`.

The first technically valid outcome is binding. No result-informed year change, quality cut, label subset, HDBSCAN setting, ranking change, feature change, or gate relaxation is authorized.

## 11. Claim boundary

A PASS is a genuine cross-survey, pre-frozen validation that recurrent-EOM's improvement over vanilla HDBSCAN generalizes to a scientifically untouched NASA network catalogue under externally pre-existing shower associations. It does **not** establish perfect absolute shower truth or authorize OrbitTrace target access.

A FAIL remains a binding pristine external result and does not authorize rescue.

## 12. Absolute firewall

- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
- protected `[20°,55°]` inaccessible before radiant/speed/label decode
- SonotaCo 2013/2014 not accessed
- GMN 2020/2021 not accessed
- `post_result_parameter_search=false`
