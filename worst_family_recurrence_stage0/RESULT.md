# Worst-family calibrated recurrence: Stage-0 result

## Authoritative execution

Runner workflow `30877532051` completed the frozen benchmark after the source-integrity repair. The scientific source and protocol were unchanged.

Artifact `8880110068` was preserved with digest `sha256:f880510ace20ead3e826390214b382eb07c08f8e96dc6606a7d21a923fa2323c`.

The decoded frozen source had SHA-256 `4384dd0352174e57ca1f93a2c3bd070002f026cef8acace035ba4ec05e577dac`.

## Worst-family calibration

Each method used the larger of its independently estimated ideal-null and shared-structure-null complete-search thresholds.

For the leave-one-year-out product:

- ideal-family threshold: **6.57601**;
- shared-structure threshold: **10.44543**;
- deployed threshold: **10.44543**.

The correction achieved conditional null control:

- ideal-null catalog FWER: **0.00000**;
- shared-structure-null catalog FWER: **0.08333**.

Both frozen calibration gates passed.

## Recurrence and artifact result

Candidate recovery by meteors per active year:

- 4: **0.11667**;
- 6: **0.40000**;
- 8: **0.81667**;
- 12: **0.98333**.

The candidate recovered **zero** one-year artifacts at every tested strength.

Aggregate metrics:

- candidate weak recurrent recovery: **0.25833**;
- original hard third-year statistic: **0.28333**;
- candidate weak recurrence margin: **0.25833**;
- original hard third-year margin: **0.28333**;
- candidate strong recurrent recovery: **0.90000**;
- original hard third-year recovery: **0.90833**.

The candidate therefore lost **0.02500** weak recovery and recurrence margin relative to the strongest valid baseline. Its strong-power difference was **-0.00833**.

## Frozen gates

- PASS — ideal-null FWER at most 0.15;
- PASS — shared-structure-null FWER at most 0.15;
- PASS — weak recurrent power loss at most 0.05;
- PASS — one-year-artifact detection at most 0.20;
- **FAIL — recurrence-margin gain over the strongest baseline at least 0.05**;
- PASS — strong recurrent power did not materially collapse.

Verdict: **`KILL_WORST_FAMILY_RECURRENCE`**.

## Interpretation

Worst-family calibration solved the conditional false-alarm problem from PR #65, but the larger shared-structure threshold removed the soft product's apparent power advantage. Under valid family-wise control, the original hard third-strongest annual evidence statistic remained more effective.

This closes scalar combinations of the same annual template p-values as a justified development route. No weight, product, order statistic, family threshold, trial count, or gate will be changed. A new method must alter the annual evidence itself—for example by removing broad local spatial structure before recurrence aggregation—rather than recombining the same p-values.

This formulation is not authorized for a real-shower benchmark or GhostStream application.
