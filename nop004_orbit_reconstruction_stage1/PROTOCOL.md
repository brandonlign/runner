# NOP solution 004 nominal-orbit reconstruction gate

Status: separately frozen feasibility gate. This stage does not classify GhostStream and does not authorize a common-origin integration.

## Why this gate exists

The official `0149NOP_004.csv` lookup contains exact UTC timestamps, geocentric right ascension and declination, geocentric speed, and solar longitude for 567 meteors. It does not contain submitted per-event heliocentric orbital elements.

Those geocentric observables may nevertheless be sufficient to reconstruct a nominal heliocentric state vector: the incoming geocentric velocity is added to Earth's heliocentric velocity at the recorded UTC epoch, and classical osculating elements are calculated from the resulting heliocentric position and velocity.

This gate asks only whether that independent reconstruction reproduces the published NOP solution 004. Failure kills the reconstruction route. Passing permits a later separately frozen calibration using other official lookup populations; it does not by itself establish uncertainty clones, a branch relationship, or a dynamical history.

## Frozen input

Use the exact successful runner artifact from the solution-004 provenance audit:

- artifact ID: `8874489453`;
- artifact digest: `sha256:85ab59ef342afc2723ad1642426433d2dedf020abe17caf36815c096b098c6be`;
- input table: `results/0149NOP_004.csv`;
- required rows: 567 unique meteors.

The target catalogue solution is fixed before reconstruction:

- `a = 2.43 AU`;
- `q = 0.207 AU`;
- `e = 0.932`;
- `i = 16.7°`;
- `ω = 310.5°`;
- `Ω = 58.6°`;
- `Vg = 36.0 km/s`;
- `λ☉ = 58.6°`.

## Frozen reconstruction

1. Parse each exact `Tobs` timestamp as UTC.
2. Treat the reported RA, Dec, and `Vg` as the geocentric radiant and speed already corrected to the geocentric pre-atmospheric convention used by the lookup.
3. Convert the radiant to an ICRS unit vector. The geocentric meteoroid velocity points opposite the radiant.
4. Obtain Earth and Sun barycentric positions and velocities from Astropy's built-in solar-system ephemeris at each timestamp.
5. Subtract the Sun state from the Earth state to obtain Earth's heliocentric state, then add the incoming geocentric meteoroid velocity to Earth's heliocentric velocity.
6. Rotate the heliocentric state from ICRS equatorial coordinates to the mean J2000 ecliptic using the fixed obliquity `23.439291111°`.
7. Calculate two-body osculating `a`, `q`, `e`, `i`, `ω`, and `Ω` using the IAU nominal solar gravitational parameter.

No event is adjusted toward the catalogue solution. No radiant drift, speed correction, outlier clipping, orbit averaging rule, or ephemeris choice is tuned after seeing the result.

## Internal convention check

The exact UTC timestamp must reproduce the lookup solar longitude independently. Solar longitude is calculated from Astropy's apparent Sun transformed to the geocentric true ecliptic of date.

This check is diagnostic of timestamp parsing and frame conventions; the submitted lookup `LS` is not used to calculate the heliocentric state.

## Frozen summary

- scalar elements: median across all finite bound event reconstructions;
- angular elements: circular median around the predeclared catalogue value;
- comparison metric: Southworth–Hawkins `D_SH` between the reconstructed median orbit and solution 004.

The catalogue solution is used only as the frozen evaluation target, not in event reconstruction.

## Continuation gates

All must pass:

1. exactly 567 unique input rows and 100% complete UTC/radiant/speed fields;
2. all timestamps parse successfully;
3. median absolute timestamp-derived solar-longitude error at most `0.15°`;
4. 95th-percentile solar-longitude error at most `0.35°`;
5. at least 95% of rows produce finite classical elements;
6. at least 90% of rows produce bound elliptical orbits;
7. reconstructed median `q` differs from 0.207 AU by at most `0.03 AU`;
8. reconstructed median `e` differs from 0.932 by at most `0.05`;
9. reconstructed median `i` differs from 16.7° by at most `3.0°`;
10. reconstructed median `ω` differs from 310.5° by at most `5.0°` circularly;
11. reconstructed median `Ω` differs from 58.6° by at most `1.0°` circularly;
12. reconstructed median-orbit `D_SH` to solution 004 is at most `0.08`.

## Decision boundary

- `PROCEED_TO_NOMINAL_ORBIT_BRANCH_CALIBRATION`: all gates pass. This authorizes only a new calibration stage on known official lookup populations.
- `KILL_NOMINAL_ORBIT_RECONSTRUCTION`: any gate fails.

A pass does not create measurement uncertainties that the lookup does not provide. It does not authorize long-term integrations, parent-body claims, or application to GhostStream until a separate branch-classification protocol is frozen and passes on known controls.
