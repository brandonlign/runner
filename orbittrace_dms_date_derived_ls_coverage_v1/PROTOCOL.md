# OrbitTrace DMS date-derived solar-longitude coverage v1

## Status

**FROZEN BEFORE THE FIRST DMS COVERAGE RESULT FROM DATE-DERIVED SOLAR LONGITUDE.**

The previous DMS coverage attempts are technical no-results. A complete two-header-row audit of the current official 42-column DMS1991-1998 archive established that it contains `Yr`, `Mn`, `Day`, shower ID, orbital elements, velocities, radiant fields, and quality fields, but **no solar-longitude (`LS`) column**. Therefore the original coverage-only audit cannot be repaired by column remapping without inventing a nonexistent field.

No DMS radiant, velocity, orbital-element, shower-label, or OrbitTrace-target data-row value has been used in any coverage statistic or method result. The only data-row values authorized so far remain date fields and unsuccessful attempts to parse a putative LS position.

This protocol replaces the nonexistent LS input with a deterministic astronomical solar-longitude calculation from the already-authorized Gregorian observation date. It is a new coverage-only protocol, not a post-result rescue: no valid DMS coverage result or eligible year pair has yet been observed.

## Official archive identity and allowed fields

Require the current official IAU MDC DMS archive to have:
- one non-directory text member;
- UTF-8/UTF-8-SIG;
- semicolon delimiter;
- exactly 910 nonblank rows;
- constant width 42;
- exactly two header rows followed by 908 public DMS records;
- header columns 2/3/4 equal to `Yr/year`, `Mn/month`, and `Day/dec_day` respectively.

Only data-row columns 2, 3, and 4 may be interpreted. Every other data-row cell is forbidden.

## Frozen Gregorian date → solar longitude conversion

For each row, parse year `Y`, month `M`, and decimal UTC day `D` exactly as in the parent coverage parser. Convert to Julian Date using the proleptic Gregorian calendar:

- if `M <= 2`, set `Y' = Y - 1`, `M' = M + 12`; otherwise `Y'=Y`, `M'=M`;
- `A = floor(Y'/100)`;
- `B = 2 - A + floor(A/4)`;
- `JD = floor(365.25*(Y'+4716)) + floor(30.6001*(M'+1)) + D + B - 1524.5`.

Define Julian centuries `T = (JD - 2451545.0)/36525`.

Compute mean solar longitude and anomaly in degrees:

- `L0 = 280.46646 + T*(36000.76983 + 0.0003032*T)`;
- `Msol = 357.52911 + T*(35999.05029 - 0.0001537*T)`.

Compute equation of center:

`C = (1.914602 - T*(0.004817 + 0.000014*T))*sin(Msol)
   + (0.019993 - 0.000101*T)*sin(2*Msol)
   + 0.000289*sin(3*Msol)`

with sine arguments interpreted in degrees.

Then:
- `true_longitude = L0 + C`;
- `omega = 125.04 - 1934.136*T`;
- `LS = (true_longitude - 0.00569 - 0.00478*sin(omega)) mod 360`.

This apparent geocentric solar longitude is frozen for coverage and any later DMS event embedding. No library ephemeris, fitted correction, DMS-specific offset, or post-result adjustment is permitted.

## Coverage logic inherited unchanged

After deriving LS, use the parent coverage gates exactly:
- exclude the inclusive interval `[20°,55°]` before statistics;
- year eligible iff it has at least 80 target-excluded rows, at least 12 occupied 10° LS bins, and at least 3 occupied LS quadrants;
- choose one consecutive eligible pair with the unchanged deterministic score: maximize minimum occupied bins, then minimum usable rows, then total occupied bins, then total usable rows, then prefer the earlier first year.

The first technically valid result is binding and may only reserve a pair or close DMS as coverage-ineligible.

## Firewall

Forbidden before the coverage result:
- IAU shower ID values;
- q/e/a/i/arg/nod or any orbital element;
- Vg/Vh/Vi or any velocity value;
- RA/DEC or any radiant value;
- quality/magnitude/height values;
- D-criteria or stream matching;
- OrbitTrace target information;
- any clustering method or comparator execution.

If a pair is reserved, a separate event-level transfer protocol must be committed before any of those scientific fields are opened.
