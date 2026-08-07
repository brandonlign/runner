# OrbitTrace v8 — Harvard 1968/1969 interface adjudication

## Status
Frozen and executed without opening any `har6869.tab` event row.

This stage decides only whether the fresh Harvard Radar Meteor Project 1968–1969 archive can supply the **already-frozen v8 discovery coordinates** without changing the detector or using orbital elements in discovery.

## Immutable prerequisites
Harvard freshness:
- run `31226182783`, artifact `9012163636`, ZIP SHA-256 `7b4d3dcc4118af1a69089e083fb5cd0a55ed9d8d8bc901d9c7d27b665d9eb0f5`;
- verdict `PASS_HARVARD_1968_1969_REPO_SCIENTIFIC_FRESHNESS_AUDIT`;
- zero prior exposure hits.

Harvard structure:
- run `31226367693`, artifact `9012222394`, ZIP SHA-256 `b87b47593a60c1ce3ee8e568a0760e87ce9f7527fb5683d11171fb2af10f2f7c`;
- verdict `PASS_HARVARD_1968_1969_STRUCTURE_AUDIT`;
- official `har6869.xml` declares 19,818 fixed-width records;
- scientific `har6869.tab` was never opened.

Frozen v8/fixed4 source:
- fixed4 source artifact `8972724498`, from run `31113601572`;
- inner `run_fixed4_support_wrapper_development.py` SHA-256 `fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62`.

## Exact v8 discovery-coordinate contract
The immutable fixed4 source must establish all of the following:
1. the input column mapping explicitly selects **geocentric ecliptic longitude** for `lam`;
2. it explicitly selects **geocentric ecliptic latitude** for `bet`;
3. it explicitly selects **geocentric velocity** for `vg`;
4. `feature_matrix` uses only `ecl_lon`, `ecl_lat`, and `vg`, with angular coordinates embedded on the unit sphere and speed scaled by `40 km/s`;
5. the family graph radius remains `1.5` in that frozen metric.

No external panel is allowed to substitute apparent/topocentric radiant or atmospheric-entry speed for those geocentric quantities.

## Harvard official interface facts
Use only the already-produced structure artifact, which contains official PDS label metadata but no event values.

The Harvard label must be adjudicated as follows:
- `RADIANT_RA`: B1950.0 right ascension of the **observed radiant**;
- `RADIANT_DEC`: B1950.0 declination of the **observed radiant**;
- `VINF`: velocity at the **top of the atmosphere**;
- no non-orbital field supplies an event-specific geocentric radiant, geocentric speed, observing-station/site vector, meteor position/height vector, or equivalent state needed to remove Earth rotation/gravitational zenith attraction exactly.

The orbital elements (`SEMIMAJOR_AXIS`, `ECCENTRICITY`, `PERIHELION_DISTANCE`, `INCLINATION`, `AOP`, `LAN`, etc.) are reserved for post-ranking corroboration. They may not be inverted to reconstruct discovery coordinates, because that would inject orbital information into the discovery stage and would no longer be the frozen v8 input interface.

## Physical adjudication rule
A deterministic coordinate-frame precession (B1950 -> a modern equinox) is not the issue. The incompatibility is **apparent/observed top-of-atmosphere state vs geocentric state**.

Published meteor trajectory/orbit methods distinguish the apparent radiant/pre-atmospheric speed from the geocentric radiant/speed after correcting Earth rotation and gravitational acceleration/zenith attraction. Such a correction depends on the event geometry/state (observer/meteor position and local zenith), not merely on RA/Dec, speed, and UTC.

Therefore:
- PASS only if the Harvard non-orbital interface itself contains the exact geocentric quantities or all event-specific non-orbital state required to recover them by a unique, source-fixed transform;
- FAIL if recovering v8 coordinates would require (a) orbital elements, (b) an assumed fixed station/site, (c) an assumed meteor height, (d) a fitted/learned correction from Harvard event values, or (e) treating observed/VINF values as geocentric by convention.

No approximate transform may be introduced after this structure result. The v8 2-degree / 2-km/s-scale discovery geometry is sensitive enough that such a substitution would constitute external-data adaptation, not transport normalization.

## Verdict vocabulary
- `PASS_HARVARD_1968_1969_V8_INTERFACE_COMPATIBILITY`: exact frozen v8 discovery coordinates are available/recoverable from non-orbital Harvard fields alone.
- `FAIL_HARVARD_1968_1969_V8_INTERFACE_COMPATIBILITY`: they are not. Preserve Harvard as a fresh but architecturally incompatible panel; do not open `har6869.tab`.

This adjudication is pre-scientific-data. It does not evaluate v8 performance or power and must not access OrbitTrace target information.
