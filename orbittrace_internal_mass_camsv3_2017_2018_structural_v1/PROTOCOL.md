# OrbitTrace internal-mass CAMSv3 2017–2018 structural transport v1

## Status

**FROZEN BEFORE THE FIRST CAMSv3 2017/2018 METEOR-ROW VALUE IS READ.**

This is a structural transport gate for the already-developed support-resolved TopoModal + annual-density internal-mass method. It is not a scientific evaluation and cannot score a method.

A corrected repository-history freshness audit completed successfully in workflow run `31204903047` and established that CAMSv3 2017 and 2018 had zero potential scientific-exposure hits. The same audit detected spent CAMSv3 2015 and 2016 as positive controls. Its artifact `9004313104` records:
- verdict `PASS_CAMSV3_2017_2018_REPO_SCIENTIFIC_FRESHNESS_AUDIT`;
- `catalogue_access_this_audit = false`;
- `scientific_value_access_this_audit = false`;
- `label_access_this_audit = false`;
- `target_information_access = false`;
- no potential exposure hits for 2017 or 2018.

This structural gate must preserve that freshness by stopping before interpretation of any meteor-row value.

## Frozen official resources

Use only the IAU MDC video-catalogue archives:
- `https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline/iaumdcCAMSv3_2017.csv.zip`
- `https://ceres.ta3.sk/iaumdcdb/dataDBs/video_offline/iaumdcCAMSv3_2018.csv.zip`

For year `Y`, require exactly one safe CSV member whose basename is exactly `iaumdcCAMSv3_Y.csv`.

The prior CAMSv3 2011–2016 structural parser established a semicolon-delimited schema containing at least `Yr`, `Mn`, `Dayy`, `LS`, `RA`, `DECL`, and `Vg`. The 2017/2018 transport must require those same structural fields but may not read their data values.

## Allowed operations

For each archive only:
1. download bytes and record SHA-256/size;
2. verify ZIP CRC and safe paths;
3. identify the exact expected CSV basename;
4. decode UTF-8-SIG;
5. read **only the header row** as strings;
6. count later nonblank rows and verify each row has the same number of cells as the header, without interpreting, converting, comparing, logging, hashing, aggregating, or selecting on any cell value;
7. record row count and malformed-row count.

The two years must have byte-for-byte identical header field lists after BOM stripping/whitespace normalization.

## Binding structural gates

All must pass:
1. both official archives are valid ZIP files with no CRC failure;
2. all archive member paths are safe;
3. exactly one expected CAMSv3 CSV basename exists per year;
4. both files have nonempty unique headers;
5. required structural fields `Yr`, `Mn`, `Dayy`, `LS`, `RA`, `DECL`, `Vg` exist in both;
6. the 2017 and 2018 header lists are identical;
7. both have at least one nonblank meteor row;
8. zero row-width mismatches in both years;
9. no meteor-row value was interpreted and no label value was read.

The first technically valid result is binding. `PASS_CAMSV3_2017_2018_STRUCTURAL_TRANSPORT_V1` authorizes only a separately frozen scientific-transfer protocol. A failure closes this exact archive/schema route until a pre-result engineering repair is justified.

## Scientific firewall

Forbidden in this gate:
- parsing numeric or categorical values from any CAMSv3 2017/2018 meteor row;
- shower numbers/codes or labels;
- RA/DEC, solar longitude, velocity, orbital elements, magnitudes, dates, quality flags, or any other row value;
- OrbitTrace target information;
- candidate construction, ranking, HDBSCAN, TopoModal, M₂D, or any comparator;
- choosing a method, parameter, filter, threshold, budget, or metric from CAMSv3 content.

A PASS is transport evidence only, not external scientific validation.
