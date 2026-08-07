# OrbitTrace UKMON 2020/2021 pre-scientific structure/interface audit

## Status
Frozen before the first HTTP request to any UKMON 2020 or 2021 meteor endpoint.

This stage is not a scientific evaluation and may not inspect meteor scientific values. It exists only to determine whether the already-validated UKMON 2022 parser/interface contract is structurally usable on the fresh 2020/2021 panel before the full v8 external protocol is exposed to scientific values.

## Immutable freshness prerequisite
The corrected raw repository audit remains a conservative FAIL, but its sole hit was separately adjudicated from immutable source evidence as the spent-SAAMER positive control rather than UKMON 2020/2021 use.

Required adjudication:
- run `31225516384`;
- job `93018899034`;
- artifact `9011943529`;
- artifact ZIP SHA-256 `d44e0673683045683ca78fd79642b4afa1b9495e3586aa6a3e4bd29a1445424a`;
- verdict `PASS_UKMON_2020_2021_ZERO_DATA_FRESHNESS_ADJUDICATION`;
- raw audit FAIL preserved;
- raw hit count exactly 1;
- additional hits forgiven exactly 0;
- no UKMON/API/scientific/label/target access in adjudication.

## Parser design source
Parser/interface design is copied only from the already-validated corrected UKMON 2022 interface work:
- endpoint shape: `https://api.ukmeteors.co.uk/matches?reqtyp=summary&reqval=YYYYMMDD`;
- required keys: `orbname`, `_sol`, `_ra_t`, `_dc_t`, `_vg`, `_q`, `_e`, `_incl`, `_peri`, `_node`;
- accepted response containers: top-level list of records; dictionary list under `data`, `results`, `matches`, or `summary`; dictionary of records.

No 2020/2021 value may be used to add a parser branch, rename a field, select a date, change a key-presence floor, or otherwise redesign the interface.

## Frozen audit dates
Use exactly two dates:
- `2020-08-14`;
- `2021-08-14`.

They are chosen prospectively by copying the month/day of the UKMON-published and already-used 2022 documented example date `2022-08-14`. There is no date search or fallback date selection.

For each date issue exactly one daily summary request. Do not use period fallback in this structure audit. A transport failure is preserved as a structure/transport failure; it is not repaired by searching other dates.

## Allowed inspection
The audit may inspect only:
- HTTP success/failure;
- whether JSON decoding succeeds;
- response container type/shape;
- whether at least 5 record objects exist;
- record key names and required-key membership counts/fractions.

The audit must not:
- convert, compare, summarize, print, store, hash, rank, or otherwise inspect the value of `_sol`, `_ra_t`, `_dc_t`, `_vg`, `_q`, `_e`, `_incl`, `_peri`, or `_node`;
- inspect the value of `orbname`;
- inspect any source/shower/classification value;
- print or save raw rows/payloads;
- compute event densities beyond the boolean `rows_at_least_5` and key-presence fractions needed for interface viability;
- run v8 or any detector/comparator;
- access OrbitTrace target information.

## Frozen structure gates
Each of the two fixed dates must satisfy all of:
1. HTTP request succeeds and JSON decodes;
2. the payload matches one of the already-allowed 2022 container shapes;
3. at least 5 record objects are present;
4. every required key is present in at least 95% of records.

The 95% key-presence floor is copied from the frozen 2022 live-interface audit and is not adjustable after 2020/2021 access.

## Decision
- `PASS_UKMON_2020_2021_STRUCTURE_AUDIT`: all gates pass on both fixed dates. This authorizes freezing the complete v8 external scientific protocol before any scientific 2020/2021 value is inspected.
- `FAIL_UKMON_2020_2021_STRUCTURE_AUDIT`: any gate fails. Preserve the failure. Do not inspect scientific values and do not redesign the parser using 2020/2021 payload values.

A pass says only that the already-fixed UKMON interface is structurally usable. It is not evidence of v8 power or scientific performance.
