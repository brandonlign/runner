# NOP solution 004 exact-GMN orbit recovery gate

This runner-only gate follows the authoritative finding that the official `0149NOP_004.csv` table is observationally coherent but lacks orbit columns.

## Narrow recovery target

The exact official lookup table contains 567 members from several surveys. Exactly 35 rows are tagged `GMN`, with second-resolution UTC timestamps and rounded solar longitude, geocentric radiant, and speed. The Global Meteor Network publishes the corresponding monthly trajectory summaries with full orbital elements.

This gate tests whether those 35 lookup rows can be joined deterministically to the original official GMN trajectories. It does not use GMN's IAU-149 shower labels and does not substitute the incompatible older low-speed NOP population.

## Frozen inputs

- NOP solution-004 provenance artifact `8874517049`, ZIP SHA-256 `2707a7be1152967960703245e62049e74f4eb778c84098f27c2486385acd512c`;
- exact lookup CSV SHA-256 `9ec720202966f1eda18c99c8decaa338d9be0bae913be4c2ff6ed34f2661282e`;
- official GMN monthly trajectory summaries for every year-month represented by the 35 GMN lookup rows;
- current solution-004 orbit fixed at q `0.207`, e `0.932`, i `16.7°`, argument of perihelion `310.5°`, node `58.6°`.

Every downloaded file and result is checksum-locked.

## Frozen matching rule

A lookup row and GMN trajectory may form an edge only if all hold:

- absolute UTC difference ≤ `2.5 s`;
- circular solar-longitude difference ≤ `0.02°`;
- great-circle radiant separation ≤ `0.20°`;
- geocentric-speed difference ≤ `0.25 km/s`.

Eligible edges receive the fixed cost

`(dt/2.5)^2 + (dLS/0.02)^2 + (radiant/0.20)^2 + (dV/0.25)^2`.

One-to-one assignment is solved globally with the Hungarian algorithm. No GMN event or lookup row may be reused. Matching thresholds cannot be widened after execution.

## Frozen recovery gates

All must pass:

1. exact lookup table still contains 35 GMN-tagged rows;
2. at least 30 of 35 rows are uniquely matched;
3. both 2019 and 2020 are represented among matches;
4. at least 95% of matches have complete q, e, inclination, argument of perihelion, and node;
5. median absolute time residual ≤ `0.50 s`;
6. median radiant residual ≤ `0.05°`;
7. median speed residual ≤ `0.05 km/s`;
8. recovered orbit medoid has Southworth-Hawkins distance ≤ `0.15` from solution 004;
9. median member distance to solution 004 ≤ `0.20` and 90th percentile ≤ `0.35`.

## Verdicts

- `PROCEED_TO_SOURCE_MATCHED_BRANCH_DYNAMICS`: every gate passes.
- `KILL_GMN_ORBIT_RECOVERY_INSUFFICIENT`: fewer than 30 unique rows or inadequate orbit completeness.
- `KILL_GMN_SUBSET_NOT_ORBITALLY_REPRESENTATIVE`: the observational join succeeds but recovered member orbits fail the frozen solution-004 consistency gates.

A pass authorizes only a source-matched dynamics calibration using the recovered GMN subset and established GMN branch controls. It does not itself classify GhostStream or establish common origin.
