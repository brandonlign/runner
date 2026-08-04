# Leave-one-year-out recurrence product: Stage-0 result

## Authoritative execution

Runner workflow `30877036663` completed the frozen benchmark from commit `c938d3e29c50449bbfa67fe545736f478ac6f9cf`.

Artifact `8879926798` was preserved with digest `sha256:549e47acf0eaaff41c544b463c05e8e2d06eddca9680245c526af1ce84109071`.

The decoded frozen source had SHA-256 `45f80c323cdab518d2aa7db15cef2222cd78442ff9b848a77e1d6730018069ce`.

## Result

The candidate improved the recurrence frontier relative to every robustly calibrated baseline:

- weak recurrent recovery: **0.450**;
- best baseline weak recurrent recovery: **0.400**;
- weak one-year-artifact detection: **0.000**;
- candidate recurrence margin: **0.450**;
- best baseline recurrence margin: **0.400**;
- strong recurrent recovery: **0.970**;
- best baseline strong recurrent recovery: **0.920**.

Per-strength candidate recovery was:

- 4 meteors per active year: **0.240**;
- 6 meteors: **0.660**;
- 8 meteors: **0.960**;
- 12 meteors: **0.980**.

The candidate never recovered any one-year artifact at any tested strength.

## Null calibration

- ideal independent-year null FWER: **0.000**;
- shared-structure null FWER: **0.240**;
- frozen shared-structure ceiling: **0.200**.

The 50/50 pooled calibration family controlled the average mixture but did not guarantee conditional control within each member of the null family. Ideal maxima were much lower than shared-structure maxima, so their inclusion lowered the pooled 90th-percentile threshold. The resulting threshold was conservative for the ideal null and insufficient for the shared-structure null.

## Frozen gates

- PASS — ideal-null FWER at most 0.15;
- **FAIL — shared-structure-null FWER at most 0.20**;
- PASS — weak recurrent power loss versus best baseline at most 0.05;
- PASS — one-year-artifact detection at most 0.20;
- recurrence-margin gain was mathematically exactly **0.050**, but binary floating-point represented it as `0.04999999999999999`, causing the source's strict `>= 0.05` comparison to report FAIL;
- PASS — strong recurrent power did not collapse.

The floating-point boundary does not alter the verdict because the independent shared-structure gate failed.

Verdict: **`KILL_SOFT_RECURRENCE_PRODUCT`**.

## Interpretation

Discarding the strongest year and combining the next two annual evidence channels was a genuine power improvement and preserved complete immunity to one-year injected artifacts. The failure was the calibration rule, not the recurrence statistic: a pooled mixture quantile controls average risk across null families, not the worst family.

No threshold, trial, distortion, score, or gate from this run will be changed. A separately frozen worst-family calibration may set each detector's threshold to the maximum of its independently estimated ideal-null and shared-structure-null quantiles. This would be a new robust-calibration formulation and must absorb its power cost prospectively.

This exact candidate is not authorized for a real-shower benchmark or GhostStream application.
