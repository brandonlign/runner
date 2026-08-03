# NOP solution 004 nominal-orbit reconstruction: J2000 convention correction

Status: separately frozen Stage-1b convention audit. Stage-1a remains a failed authoritative formulation and is not overwritten.

## Reason for a separate correction

Stage-1a reconstructed a median orbit extremely close to NOP solution 004 (`D_SH = 0.007561`) and passed eleven of twelve frozen gates. Its only failure was a median timestamp-derived solar-longitude error of `0.193427°`, above the frozen `0.15°` ceiling.

Stage-1a calculated apparent solar longitude in the geocentric true ecliptic of date. Independent IAU MDC documentation states that the Shower Database uses the mean equator and mean ecliptic of epoch J2000 and requires lookup-table solar longitude, geocentric radiant, and angular orbital elements in J2000. The failed diagnostic therefore compared unlike reference systems.

This documentation-based correction was specified after Stage-1a and must be tested as a new frozen formulation. The Stage-1a no-go remains part of the audit trail.

## Frozen evidence and source lineage

- exact solution-004 lookup artifact: `8874489453`;
- lookup artifact digest: `sha256:85ab59ef342afc2723ad1642426433d2dedf020abe17caf36815c096b098c6be`;
- exact Stage-1a source commit: `20553c89f52aaa9b5f9b0ceaea019f759c3506af`;
- exact input table: `results/0149NOP_004.csv`;
- required rows: 567 unique meteors.

The target solution and every numerical continuation threshold remain unchanged from Stage-1a:

- `a = 2.43 AU`;
- `q = 0.207 AU`;
- `e = 0.932`;
- `i = 16.7°`;
- `ω = 310.5°`;
- `Ω = 58.6°`;
- `Vg = 36.0 km/s`;
- `λ☉ = 58.6°`.

## Unchanged orbit reconstruction

The event-level heliocentric-state calculation is identical to Stage-1a:

1. parse the exact `Tobs` timestamp as UTC;
2. convert J2000 geocentric RA and Dec to an incoming ICRS velocity direction;
3. multiply by the reported geocentric speed and reverse the radiant direction;
4. obtain Earth and Sun barycentric states from Astropy's built-in ephemeris;
5. subtract the Sun state from the Earth state and add the geocentric meteoroid velocity;
6. rotate the heliocentric state from ICRS equatorial coordinates to the mean J2000 ecliptic with fixed obliquity `23.439291111°`;
7. calculate the same two-body osculating elements with the same nominal solar gravitational parameter;
8. summarize scalar elements by the median of finite bound rows and angular elements by the same circular-median rule;
9. compare the same reconstructed median orbit with the same solution-004 target using the same `D_SH` implementation.

No event, velocity, target parameter, ephemeris, averaging rule, orbit formula, threshold, or outlier policy changes.

## Sole corrected diagnostic

Stage-1b replaces only the solar-longitude diagnostic.

For every UTC timestamp, use the already calculated Earth heliocentric ICRS position, rotate it to the mean J2000 ecliptic with the same fixed rotation, reverse the vector to obtain the geocentric Sun direction, and calculate

`λ☉,J2000 = atan2(y_sun, x_sun) mod 360°`.

Compare that J2000 solar longitude directly with the submitted lookup `LS`. The lookup `LS` remains excluded from the orbit reconstruction itself.

## Frozen continuation gates

All Stage-1a gates and thresholds are retained unchanged:

1. exactly 567 unique input rows and 100% complete UTC/radiant/speed fields;
2. all timestamps parse successfully;
3. median absolute J2000 timestamp-derived solar-longitude error at most `0.15°`;
4. 95th-percentile J2000 solar-longitude error at most `0.35°`;
5. at least 95% of rows produce finite classical elements;
6. at least 90% of rows produce bound elliptical orbits;
7. reconstructed median `q` differs from 0.207 AU by at most `0.03 AU`;
8. reconstructed median `e` differs from 0.932 by at most `0.05`;
9. reconstructed median `i` differs from 16.7° by at most `3.0°`;
10. reconstructed median `ω` differs from 310.5° by at most `5.0°` circularly;
11. reconstructed median `Ω` differs from 58.6° by at most `1.0°` circularly;
12. reconstructed median-orbit `D_SH` to solution 004 is at most `0.08`.

## Decision boundary

- `PROCEED_TO_NOMINAL_ORBIT_BRANCH_CALIBRATION_J2000`: all gates pass. This authorizes only a separately frozen calibration on known official lookup populations.
- `KILL_NOMINAL_ORBIT_RECONSTRUCTION_J2000`: any gate fails.

Even a pass produces nominal orbits, not submitted orbital measurements or uncertainty clones. It does not authorize application to GhostStream, long-term integrations, or a branch/common-origin claim before a control-calibrated classification stage is frozen and passed.
