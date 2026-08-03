# NOP solution 004 nominal-orbit reconstruction: LS-reconciled epoch

Status: separately frozen Stage-1c feasibility test. Stage-1a and Stage-1b remain authoritative failed formulations and are not overwritten.

## Motivation

Stage-1b placed both the state-vector reconstruction and the timestamp diagnostic in the mean J2000 ecliptic required by the IAU MDC. It reproduced the NOP solution-004 median orbit at `D_SH = 0.007561` and reduced the median timestamp/lookup solar-longitude error to `0.010381°`.

Its sole failed gate was the p95 solar-longitude error: `0.368627°` versus a frozen `0.35°` ceiling. The residual tail is source-specific rather than global. Many affected CAMS, GMN, and EDMOND rows have near-midnight `Tobs` values and integer-like hour offsets; several SonotaCo rows imply one- to two-day date offsets. In contrast, the mandatory submitted J2000 `LS` field remains coherent with the official 567-event population and catalogue mean.

This stage tests a narrow data-reconciliation question: can the mandatory submitted J2000 solar longitude identify a nearby UTC epoch that restores internal timestamp consistency without materially changing the independently reconstructed solution-004 orbit?

This is not a relaxation of Stage-1b. It is a new formulation whose timestamp corrections, limits, and outputs are fully recorded.

## Frozen inputs and lineage

- exact solution-004 provenance artifact: `8874489453`;
- artifact digest: `sha256:85ab59ef342afc2723ad1642426433d2dedf020abe17caf36815c096b098c6be`;
- exact lookup: `results/0149NOP_004.csv`;
- required rows: 567 unique meteors;
- Stage-1a source commit: `20553c89f52aaa9b5f9b0ceaea019f759c3506af`;
- Stage-1b source commit: `aada89b4bfdb9a15da51333b07ec0f765bb94531`.

The target solution and all orbit-reproduction thresholds remain unchanged:

- `a = 2.43 AU`;
- `q = 0.207 AU`;
- `e = 0.932`;
- `i = 16.7°`;
- `ω = 310.5°`;
- `Ω = 58.6°`;
- `Vg = 36.0 km/s`.

## Frozen timestamp reconciliation

For each row:

1. parse the submitted `Tobs` as UTC;
2. calculate J2000 solar longitude from the geocentric Sun direction using the same Astropy built-in Earth/Sun ephemeris and fixed J2000 ecliptic rotation as Stage-1b;
3. calculate the signed circular difference between submitted `LS` and timestamp-derived J2000 solar longitude;
4. use deterministic vectorized Newton updates to find the nearest UTC epoch whose J2000 solar longitude equals the submitted `LS`;
5. constrain the solution to the continuous local branch around `Tobs`; no year, event identity, radiant, speed, or submitted `LS` value changes;
6. record the original timestamp, reconciled timestamp, signed shift in hours, and final solar-longitude residual for every row.

The submitted `LS` is used only to determine Earth's orbital phase. It is not a shower-mean target, orbital element, membership label, or GhostStream-derived quantity.

## Frozen reconstruction

At the reconciled epoch, use the unchanged state-vector reconstruction:

- reported J2000 RA and Dec define the opposite incoming geocentric velocity direction;
- reported `Vg` defines its magnitude;
- Earth and Sun barycentric states come from Astropy's built-in ephemeris;
- the meteoroid heliocentric velocity is Earth's heliocentric velocity plus the geocentric meteoroid velocity;
- position and velocity rotate to the mean J2000 ecliptic with obliquity `23.439291111°`;
- classical two-body elements use the same nominal solar gravitational parameter;
- scalar elements use the median of finite bound rows;
- angular elements use the unchanged circular-median rule;
- the median orbit is compared with solution 004 by the unchanged `D_SH` implementation.

No radiant, speed, event, source, target element, orbit formula, outlier rule, or orbit threshold changes.

## Frozen timestamp-reconciliation gates

The correction must remain bounded like an observing-night/date convention repair rather than an unconstrained fit:

1. every row converges to a final J2000 solar-longitude residual at most `0.001°`;
2. median absolute timestamp shift at most `1 hour`;
3. 95th-percentile absolute timestamp shift at most `12 hours`;
4. maximum absolute timestamp shift at most `72 hours`;
5. no row changes calendar year.

The one-hour median requires that most submitted timestamps were already close. The twelve-hour p95 allows a single-night timezone or observing-date convention. The 72-hour hard maximum permits bounded date-label displacement but kills grossly unrelated epochs.

## Unchanged orbit gates

All must also pass:

1. exactly 567 unique input rows and all timestamps parsed;
2. at least 95% of rows produce finite classical elements;
3. at least 90% of rows produce bound elliptical orbits;
4. reconstructed median `q` differs from 0.207 AU by at most `0.03 AU`;
5. reconstructed median `e` differs from 0.932 by at most `0.05`;
6. reconstructed median `i` differs from 16.7° by at most `3.0°`;
7. reconstructed median `ω` differs from 310.5° by at most `5.0°` circularly;
8. reconstructed median `Ω` differs from 58.6° by at most `1.0°` circularly;
9. reconstructed median-orbit `D_SH` to solution 004 is at most `0.08`.

## Decision boundary

- `PROCEED_TO_CONTROL_CALIBRATION_WITH_LS_RECONCILED_NOMINAL_ORBITS`: every timestamp and orbit gate passes.
- `KILL_LS_RECONCILED_NOMINAL_ORBIT_ROUTE`: any gate fails.

A pass authorizes only a new, independently frozen calibration on other known official lookup populations. It does not create reported measurement uncertainties, prove that every reconciled timestamp is the original event UTC, authorize long-term integrations, or permit a GhostStream branch/common-origin claim.
