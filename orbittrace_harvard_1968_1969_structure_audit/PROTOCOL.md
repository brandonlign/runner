# OrbitTrace Harvard 1968/1969 pre-scientific structure/interface audit

## Status
Frozen after the repository-history freshness PASS and before any `har6869.tab` scientific record is decompressed or interpreted.

Freshness prerequisite:
- run `31226182783`;
- job `93020838317`;
- artifact `9012163636`;
- artifact ZIP SHA-256 `7b4d3dcc4118af1a69089e083fb5cd0a55ed9d8d8bc901d9c7d27b665d9eb0f5`;
- verdict `PASS_HARVARD_1968_1969_REPO_SCIENTIFIC_FRESHNESS_AUDIT`;
- 400 remote refs scanned;
- zero exposure hits;
- AMOR and UKMON positive controls true;
- no catalogue/scientific/label/target access in that audit.

## Fixed source
Use only the NASA/PDS Small Bodies Node PDS4 bundle advertised for Steel Meteoroid Orbits:

`https://sbnarchive.psi.edu/pds4/non_mission/meteoroid.steel.orbits.zip`

Public catalogue metadata fixed before this audit states that the Harvard Radar Meteor Project 1968–1969 survey is `har6869.tab`, contains 19,818 individual orbits, and that Steel files share a common format containing observation time, orbital elements, radiant coordinates, and velocity.

## Allowed access
This stage may:
1. download the PDS4 ZIP as opaque bytes;
2. compute and record the ZIP SHA-256;
3. inspect the ZIP central directory/member names, compressed/uncompressed sizes, and metadata;
4. identify the member whose basename is exactly `har6869.tab` case-insensitively;
5. identify and read only official non-data metadata/label members (`.xml`, `.lbl`) associated with `har6869`;
6. parse and record structural schema declarations from that official label: record count/length, field names, field positions/lengths, data types, units, and descriptions.

This stage must NOT:
- open, decompress, sample, hash separately, print, persist, or inspect any byte from `har6869.tab` itself;
- read any Harvard event value, date value, radiant, speed, solar/ecliptic longitude, or orbital value;
- inspect any shower/source/classification label from event records;
- run v8 or any comparator;
- access OrbitTrace target information or the excluded 20°–55° contents.

## Frozen structure gates
PASS only if all are true:
1. bundle download succeeds and is a valid ZIP;
2. exactly one data member has basename `har6869.tab`;
3. an official companion label/metadata member for `har6869` exists and can be parsed without opening the data table;
4. the label explicitly references `har6869.tab`;
5. the declared record count, if present, is exactly 19,818; absence of a declared record count is not by itself a failure because the authoritative PDS dataset metadata already fixes 19,818;
6. the label supplies a deterministic fixed-width/delimited schema sufficient to map, by official field metadata rather than by event values, observation time/year, radiant coordinates, velocity, and orbital elements needed for later validation;
7. no `har6869.tab` member is opened by the audit implementation.

## Decision
- `PASS_HARVARD_1968_1969_STRUCTURE_AUDIT`: structure is sufficient to freeze the full scientific parser and external protocol before first event-value access.
- `FAIL_HARVARD_1968_1969_STRUCTURE_AUDIT`: preserve the failure; do not inspect `har6869.tab` values to repair the parser.

A structure PASS is not evidence of external power or v8 performance.
