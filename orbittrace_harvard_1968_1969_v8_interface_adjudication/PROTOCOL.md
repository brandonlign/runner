# OrbitTrace v8 — Harvard 1968/1969 interface adjudication (source-check correction)

## Status
Frozen and executed without opening any `har6869.tab` event row.

The first execution of this adjudication (run `31226997818`, job `93023212835`, artifact `9012436150`, ZIP SHA-256 `2bbbd28fd7eb68f3ca13bf13a491e4a02f9f00df1c5712552a6f30a68f0ab95b`) is preserved as an implementation-check failure. It correctly verified the frozen geocentric column mapping and family radius, then searched for `feature_matrix` in the wrapper source instead of the paired frozen blind-catalogue source. This correction changes only those source locations and corrects the textual description of the already-frozen metric. No Harvard event value has been accessed and no scientific criterion changes.

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

Frozen fixed4 source artifact:
- artifact `8972724498`, run `31113601572`;
- `run_fixed4_support_wrapper_development.py` SHA-256 `fa18a19c08c6824c66606cbd92095dc3605cbcc30f17a468c9e525e7c6ff4a62`;
- paired `run_fixed4_blind_catalogue.py` SHA-256 `48434df612f790924e6efce45b6b8d4de1401880f398994bc58eef2fce0987e5`.

## Exact v8 discovery-coordinate contract
The immutable sources must establish all of the following:
1. the wrapper input column mapping explicitly selects **geocentric ecliptic longitude** for `lam`;
2. it explicitly selects **geocentric ecliptic latitude** for `bet`;
3. it explicitly selects **geocentric velocity** for `vg`;
4. the blind-catalogue source converts geocentric ecliptic longitude to the detector's sun-centered longitude as `wrap180(lam - solar_longitude)`;
5. the frozen feature matrix uses solar-longitude offset scaled by 4°, the sun-centered/geocentric-radiant angular coordinates at a 2° scale, and geocentric speed at a 2 km/s scale;
6. the family graph radius remains `1.5`.

This corrects only a documentation typo in the first adjudication protocol, which incorrectly described an `e.ecl_lon` / `Vg/40` representation. The immutable implementation itself is unchanged.

No external panel is allowed to substitute apparent/topocentric radiant or atmospheric-entry speed for those geocentric quantities.

## Harvard official interface facts
Use only the already-produced structure artifact, which contains official PDS label metadata but no event values.

The Harvard label must establish:
- `RADIANT_RA`: B1950.0 right ascension of the **observed radiant**;
- `RADIANT_DEC`: B1950.0 declination of the **observed radiant**;
- `VINF`: velocity at the **top of the atmosphere**;
- `LMA`: ecliptic elongation of the radiant (`lambda minus the apex`), not a declared geocentric radiant coordinate;
- no non-orbital field supplies an event-specific geocentric radiant, geocentric speed, observing-station/site vector, meteor position/height vector, or equivalent state needed to recover the exact geocentric apparent-to-asymptotic correction.

The orbital elements (`SEMIMAJOR_AXIS`, `ECCENTRICITY`, `PERIHELION_DISTANCE`, `APHELION_DISTANCE`, `INCLINATION`, `AOP`, `LAN`, `LOP`) are reserved for post-ranking corroboration. They may not be inverted to reconstruct discovery coordinates, because that would inject orbital information into the discovery stage and would no longer be the frozen v8 input interface.

## Physical adjudication rule
A deterministic equinox/frame rotation by itself is not the incompatibility. The incompatibility is **observed/top-of-atmosphere state versus the geocentric state explicitly required by v8**.

Standard meteor reductions distinguish apparent/pre-atmospheric radiant and velocity from geocentric radiant and speed after correcting Earth's rotation and gravitational acceleration/zenith attraction. Exact radiant correction requires event geometry relative to the local zenith/observer or an equivalent state; Harvard's official non-orbital schema does not provide it.

Therefore:
- PASS only if the Harvard non-orbital interface itself contains the exact geocentric quantities or all event-specific non-orbital state required to recover them by a unique, source-fixed transform;
- FAIL if recovering v8 coordinates would require (a) orbital elements, (b) an assumed fixed station/site, (c) an assumed meteor height/position, (d) a fitted/learned correction from Harvard event values, or (e) treating observed/VINF values as geocentric by convention.

No approximate transform may be introduced after this structure result. At the frozen 2° / 2 km/s discovery scales, such a substitution would be external-data adaptation, not transport normalization.

## Verdict vocabulary
- `PASS_HARVARD_1968_1969_V8_INTERFACE_COMPATIBILITY`: exact frozen v8 discovery coordinates are available/recoverable from non-orbital Harvard fields alone.
- `FAIL_HARVARD_1968_1969_V8_INTERFACE_COMPATIBILITY`: they are not. Preserve Harvard as a fresh but architecturally incompatible panel; do not open `har6869.tab`.

This adjudication is pre-scientific-data. It does not evaluate v8 performance or power and must not access OrbitTrace target information.
