# OrbitTrace UKMON 2020/2021 pre-scientific structure/interface audit — transport correction

## Status
Frozen before any scientific UKMON 2020/2021 field value is inspected.

The first frozen structure attempt (run `31225678351`, job `93019373431`, artifact `9012001791`, artifact ZIP SHA-256 `08dc0b6de876733c2de8ce6079487ee5b3bdb1245bb98bc63da84c41566e4dfa`) reached the fixed 2020 daily endpoint and failed because successful JSON was a non-list `dict`. It failed before converting, logging, persisting, comparing, or otherwise inspecting `_sol`, radiant, speed, orbit, orbname, source-label, or OrbitTrace target values. Preserve that failure.

This correction changes only transport handling. It does not add a target-year-derived parser shape. It copies the deterministic daily/period fallback already frozen in the pre-existing UKMON external runner source blob `fd554e1b25731439cff02711558ed2c009665004`, which existed before UKMON 2020/2021 access:

1. request daily `https://api.ukmeteors.co.uk/matches?reqtyp=summary&reqval=YYYYMMDD`;
2. accept only a top-level JSON list of record dictionaries;
3. if daily transport fails or JSON is not such a list, request exactly four period URLs in this fixed order: `0-6`, `6-12`, `12-18`, `18-24`;
4. every period response must be a top-level list; concatenate in fixed order;
5. no other endpoint, wrapper, date, period, parser branch, or repair is allowed.

Thus the correction is independently pre-specified transport reuse, not parser design learned from 2020/2021 values.

## Immutable freshness prerequisite
Required zero-data adjudication:
- run `31225516384`;
- job `93018899034`;
- artifact `9011943529`;
- artifact ZIP SHA-256 `d44e0673683045683ca78fd79642b4afa1b9495e3586aa6a3e4bd29a1445424a`;
- verdict `PASS_UKMON_2020_2021_ZERO_DATA_FRESHNESS_ADJUDICATION`;
- raw audit FAIL preserved;
- raw hit count exactly 1;
- additional hits forgiven exactly 0.

## Parser design source
Scientific field mapping remains copied only from the already-validated corrected UKMON 2022 interface work:
- trajectory id: `orbname`;
- solar longitude: `_sol`;
- geocentric radiant: `_ra_t`, `_dc_t`;
- geocentric speed: `_vg`;
- later orbital fields: `_q`, `_e`, `_incl`, `_peri`, `_node`.

No 2020/2021 scientific value may add or rename a field, select a date, change a key-presence floor, or redesign the parser.

## Frozen audit dates
Exactly:
- `2020-08-14`;
- `2021-08-14`.

These prospectively copy the month/day of the UKMON-published and already-validated 2022 example date `2022-08-14`. No date search is allowed.

## Allowed inspection
The corrected audit may inspect only:
- HTTP success/failure;
- JSON top-level type;
- whether a response is a top-level list of record dictionaries;
- whether the fixed period fallback was required;
- whether at least 5 record objects exist after deterministic concatenation;
- record key membership and required-key presence fractions.

It must not inspect, convert, summarize, print, persist, compare, hash, rank, or otherwise use the value of `_sol`, `_ra_t`, `_dc_t`, `_vg`, `_q`, `_e`, `_incl`, `_peri`, `_node`, or `orbname`; inspect source/shower/classification values; save raw payloads; run v8; or access OrbitTrace target information.

## Frozen structure gates
Each fixed date must satisfy all:
1. daily top-level list succeeds OR the pre-existing four-period fallback succeeds completely;
2. final rows are record dictionaries;
3. at least 5 records exist;
4. every required key is present in at least 95% of records.

The 95% key-presence floor is unchanged from the prior structure attempt and the validated 2022 interface audit.

## Decision
- `PASS_UKMON_2020_2021_STRUCTURE_TRANSPORT_CORRECTION`: both fixed dates pass all gates. This authorizes freezing the complete v8 scientific external protocol before any scientific UKMON 2020/2021 value is inspected.
- `FAIL_UKMON_2020_2021_STRUCTURE_TRANSPORT_CORRECTION`: any gate fails. Preserve it. Do not learn a new parser from target-year values.

A pass establishes only structural/transport usability. It is not a scientific v8 result and does not establish external power.
