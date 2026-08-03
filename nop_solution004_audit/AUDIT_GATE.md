# NOP solution 004 provenance and coherence gate

This runner-only gate follows the failed GMN-member classification gate. It does not reinterpret GMN's older low-speed IAU-149 population as the 2023 NOP solution 004.

## Exact target

- current IAU MDC shower: `00149 / NOP`;
- exact additional solution: `004`;
- declared lookup table: `0149NOP_004.csv`;
- reported members: `567`;
- published center: solar longitude `58.6°`, RA `258.0°`, Dec `-14.0°`, geocentric speed `36.0 km/s`;
- published orbit: q `0.207 AU`, e `0.932`, inclination `16.7°`, argument of perihelion `310.5°`, node `58.6°`.

## Frozen provenance search

The audit fetches the live MDC JSON and the live NOP detail page, records both hashes, inventories every page link and same-origin script, and tests:

1. exact page- or script-discovered CSV links;
2. the exact filename joined to every same-origin directory exposed by those links;
3. a fixed list of conventional public MDC paths declared before execution.

Every attempted URL and response is preserved. An HTML error page, redirect to a generic page, third-party copy, or file with fewer than 500 unique rows is rejected.

## Observation/coherence gates

All must pass:

1. live MDC still contains exact solution 004 and declares `0149NOP_004.csv`;
2. the NOP detail page is accessible;
3. an official same-origin CSV is accessible;
4. at least 500 unique rows;
5. at least 95% of rows have solar longitude, RA, Dec, and geocentric speed;
6. median solar longitude is within `3°` of 58.6°;
7. median radiant is within `3°` of the published radiant;
8. median speed is within `2 km/s` of 36.0 km/s.

## Orbit-clone gates

Dynamics are authorized only if all also pass:

1. q, e, inclination, argument of perihelion, and node columns are present;
2. at least 90% of rows have complete orbit fields;
3. the table's median orbit is within Southworth-Hawkins `D <= 0.08` of solution 004.

## Frozen verdicts

- `PROCEED_TO_EXACT_SOLUTION004_DYNAMICS`: every observation and orbit gate passes.
- `SOLUTION004_OBSERVATIONALLY_COHERENT_BUT_NO_ORBIT_CLONES`: the lookup table reproduces the observational solution but cannot support member-level orbit dynamics.
- `KILL_SOLUTION004_COMPARISON_PROVENANCE`: the official table is inaccessible, incomplete, or does not reproduce solution 004.

No result permits falling back to the incompatible GMN-labelled NOP population, changing tolerances, using an unofficial table, or treating a mean catalogue orbit as 567 uncertainty clones.
