# NOP solution 004 official-CAMS orbit recovery gate

This runner-only gate follows two completed findings:

1. the exact official `0149NOP_004.csv` lookup table is observationally coherent but contains no orbit columns;
2. both live and archived GMN products recover only 17 of 35 GMN-tagged lookup members and fail the frozen representativeness gate.

No GMN threshold is changed. This is an independent source-recovery test using the official IAU MDC CAMSv3 orbit archives.

## Frozen target

The lookup table contains exactly 100 CAMS-tagged members in years 2011–2016, the years covered by the current IAU MDC CAMSv3 annual archives:

- 2011: 2;
- 2012: 17;
- 2013: 15;
- 2014: 13;
- 2015: 20;
- 2016: 33.

Later CAMS-tagged rows are excluded prospectively because the IAU MDC annual CAMSv3 archive ends in 2016. They cannot influence thresholds or interpretation.

## Frozen inputs

- exact NOP solution-004 provenance artifact `8874517049`, ZIP SHA-256 `2707a7be1152967960703245e62049e74f4eb778c84098f27c2486385acd512c`;
- exact lookup CSV SHA-256 `9ec720202966f1eda18c99c8decaa338d9be0bae913be4c2ff6ed34f2661282e`;
- official IAU MDC archives `iaumdcCAMSv3_2011.csv.zip` through `iaumdcCAMSv3_2016.csv.zip`, downloaded from the current IAU MDC video-catalog archive page and checksum-locked during execution;
- solution-004 orbit fixed at q `0.207`, e `0.932`, inclination `16.7°`, argument of perihelion `310.5°`, and node `58.6°`.

## Frozen matching rule

A lookup row and CAMS orbit may form an edge only if all hold:

- absolute UTC difference ≤ `2.5 s`;
- circular solar-longitude difference ≤ `0.02°`;
- great-circle radiant separation ≤ `0.20°`;
- geocentric-speed difference ≤ `0.25 km/s`.

Eligible edges use the fixed normalized quadratic cost

`(dt/2.5)^2 + (dLS/0.02)^2 + (radiant/0.20)^2 + (dV/0.25)^2`.

A global Hungarian assignment enforces one-to-one matching. No lookup member or archive orbit may be reused. Matching thresholds cannot be widened after execution.

## Frozen recovery gates

All must pass:

1. exactly 100 eligible CAMS lookup rows from 2011–2016;
2. at least 80 unique matches;
3. at least five of the six frozen years represented;
4. at least 95% orbit completeness among matches;
5. median time residual ≤ `0.50 s`;
6. median radiant residual ≤ `0.05°`;
7. median speed residual ≤ `0.05 km/s`;
8. recovered orbit medoid has Southworth-Hawkins distance ≤ `0.15` from solution 004;
9. median member distance to solution 004 ≤ `0.20`;
10. 90th-percentile member distance to solution 004 ≤ `0.35`.

These are the same orbital-representativeness limits used for the prior GMN source recovery. No result-dependent relaxation is permitted.

## Verdicts

- `PROCEED_TO_SOURCE_MATCHED_BRANCH_DYNAMICS`: every gate passes.
- `KILL_CAMS_ORBIT_RECOVERY_INSUFFICIENT`: matching, year coverage, completeness, or residual gates fail.
- `KILL_CAMS_SUBSET_NOT_ORBITALLY_REPRESENTATIVE`: the observational join succeeds but the recovered orbit distribution fails one or more fixed solution-consistency gates.

A pass authorizes only a separately frozen, control-calibrated dynamics test. It does not itself classify GhostStream as distinct or as an NOP branch.
