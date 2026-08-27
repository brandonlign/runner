# NOP solution 004 IAU-GMN snapshot recovery gate

The current GMN monthly products recovered only 17 of the 35 exact solution-004 lookup rows under the frozen one-to-one join. No matching tolerance is changed here.

This independent gate tests the official IAU MDC's fixed 2019 and 2020 GMN archive snapshots, which may preserve the trajectory reductions used when the 2023 lookup table was assembled.

## Frozen inputs

- exact official lookup artifact `8874517049`, artifact ZIP SHA-256 `2707a7be1152967960703245e62049e74f4eb778c84098f27c2486385acd512c`;
- exact `0149NOP_004.csv` SHA-256 `9ec720202966f1eda18c99c8decaa338d9be0bae913be4c2ff6ed34f2661282e`;
- official IAU MDC archives `iaumdcgmn2019.csv.zip` and `iaumdcgmn2020.csv.zip` from the current Version-2026 video-catalog page.

## Matching and gates

Use the identical frozen one-to-one matching rule from the live-GMN recovery:

- UTC difference ≤ `2.5 s`;
- solar-longitude difference ≤ `0.02°`;
- radiant separation ≤ `0.20°`;
- speed difference ≤ `0.25 km/s`;
- identical normalized quadratic edge cost and global Hungarian assignment.

Use the identical recovery and orbital-representativeness gates:

1. exactly 35 GMN lookup rows;
2. at least 30 unique matches;
3. both 2019 and 2020 represented;
4. orbit completeness at least 95%;
5. median time residual at most 0.50 s;
6. median radiant residual at most 0.05°;
7. median speed residual at most 0.05 km/s;
8. recovered orbit medoid `D_SH <= 0.15` from solution 004;
9. median member `D_SH <= 0.20`;
10. 90th-percentile member `D_SH <= 0.35`.

No archive field, delimiter, timestamp convention, threshold, or orbit statistic may be selected from the result. The parser may only normalize documented IAU MDC field names and convert `Yr`, `Mn`, and fractional UTC `Day` to time.

## Verdicts

- `PROCEED_TO_SOURCE_MATCHED_BRANCH_DYNAMICS` if every gate passes;
- `KILL_IAU_GMN_ARCHIVE_RECOVERY_INSUFFICIENT` if matching/completeness gates fail;
- `KILL_IAU_GMN_ARCHIVE_SUBSET_NOT_ORBITALLY_REPRESENTATIVE` if the join succeeds but orbital-representativeness gates fail.
