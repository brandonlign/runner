# NOP solution 004 final multi-source orbit-recovery gate

This runner-only gate is the final source-recovery attempt for the official NOP solution-004 member table. It does not weaken or rerun the completed GMN and CAMS gates.

## Locked prior evidence

- exact solution-004 lookup artifact `8874517049`, ZIP SHA-256 `2707a7be1152967960703245e62049e74f4eb778c84098f27c2486385acd512c`;
- exact lookup CSV SHA-256 `9ec720202966f1eda18c99c8decaa338d9be0bae913be4c2ff6ed34f2661282e`;
- exact-GMN recovery artifact `8874644285`, ZIP SHA-256 `a823c88444645bfb255ce0eea35ff5f1eae9d7e009b0a35babc5f11f6e4f96a0`, containing 17 exact source matches;
- official-CAMS recovery artifact `8875056837`, ZIP SHA-256 `da4c1eecf3092536e0b4fe93fb04c124807fe22586e61cfa4a150f46783b3fd4`, containing 48 exact source matches.

The prior 65 orbits are imported exactly as preserved. Their matching thresholds, assignments, and orbit values cannot be changed.

## Remaining official source archives

The current IAU MDC video-catalog archive provides annual orbit files covering every lookup member in these source/year ranges:

- EDMOND, 2011–2016: exactly 75 lookup members;
- SonotaCo/SNMv3, 2011–2020: exactly 60 lookup members.

Together with the archive-covered CAMS and GMN rows, the final target population contains exactly 270 source-tagged lookup members:

- CAMS 2011–2016: 100;
- EDMOND 2011–2016: 75;
- SonotaCo 2011–2020: 60;
- GMN 2019–2020: 35.

CMN rows and CAMS rows after 2016 are excluded prospectively because no corresponding annual orbit archives are listed in the current IAU MDC video catalog.

## Frozen exact matching rule

For EDMOND and SonotaCo, a lookup row and archive orbit may form an edge only if all hold:

- absolute UTC difference ≤ `2.5 s`;
- circular solar-longitude difference ≤ `0.02°`;
- great-circle radiant separation ≤ `0.20°`;
- geocentric-speed difference ≤ `0.25 km/s`.

Eligible edges use

`(dt/2.5)^2 + (dLS/0.02)^2 + (radiant/0.20)^2 + (dV/0.25)^2`.

A global Hungarian assignment is solved independently inside each source. No lookup row or archive orbit may be reused. The limits cannot be widened.

## Frozen new-source gates

### EDMOND

All must pass:

1. exactly 75 eligible lookup rows;
2. at least 50 unique matches;
3. at least five of six years represented;
4. orbit completeness at least 95%;
5. median time/radiant/speed residual no greater than `0.50 s / 0.05° / 0.05 km/s`.

### SonotaCo

All must pass:

1. exactly 60 eligible lookup rows;
2. at least 40 unique matches;
3. at least eight of ten years represented;
4. orbit completeness at least 95%;
5. median time/radiant/speed residual no greater than `0.50 s / 0.05° / 0.05 km/s`.

## Frozen combined-population gates

The final exact source-matched orbit pool combines the locked CAMS and GMN assignments with newly recovered EDMOND and SonotaCo assignments. All must pass:

1. exactly 270 archive-covered lookup members in the target definition;
2. at least 150 unique recovered lookup members;
3. CAMS, EDMOND, SonotaCo, and GMN all represented;
4. at least nine distinct observing years represented;
5. orbit completeness at least 95%;
6. no source contributes more than 70% of the recovered pool;
7. recovered orbit medoid has Southworth-Hawkins distance ≤ `0.15` from solution 004;
8. median member distance to solution 004 ≤ `0.20`;
9. 90th-percentile member distance to solution 004 ≤ `0.35`.

Solution 004 remains fixed at q `0.207`, e `0.932`, inclination `16.7°`, argument of perihelion `310.5°`, and node `58.6°`.

## Verdicts

- `PROCEED_TO_CONTROL_CALIBRATED_BRANCH_DYNAMICS`: every EDMOND, SonotaCo, and combined gate passes.
- `KILL_MULTISOURCE_RECOVERY_INSUFFICIENT`: any count, coverage, completeness, residual, or source-balance gate fails.
- `KILL_MULTISOURCE_POPULATION_NOT_ORBITALLY_REPRESENTATIVE`: all recovery gates pass but one or more combined orbital-distribution gates fail.

A pass only authorizes a separately frozen dynamics benchmark on established branch and matched-distinct controls. A failure ends public-source orbit recovery. It cannot be rescued by wider matching, omitted outliers, source reweighting, or unofficial orbit files.
