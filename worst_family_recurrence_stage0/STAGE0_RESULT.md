# Worst-family calibrated recurrence: authoritative Stage-0 no-go

Runner workflow `30877532051` completed the full frozen benchmark. Artifact `8880110068` was preserved with digest `sha256:f880510ace20ead3e826390214b382eb07c08f8e96dc6606a7d21a923fa2323c`.

## Result

Using the maximum of separately estimated ideal-null and shared-structure thresholds successfully repaired family-wise calibration:

- ideal-null FWER: **0.000**;
- shared-structure-null FWER: **0.083**;
- weak one-year-artifact detection: **0.000**.

But the calibration cost removed the candidate's recurrence advantage:

- candidate weak recurrent recovery: **0.2583**;
- candidate weak recurrence margin: **0.2583**;
- strongest baseline weak recurrent recovery and margin: **0.2833 / 0.2833**;
- candidate margin gain: **−0.0250**;
- candidate strong recurrent recovery: **0.9000** versus **0.9083** for the strongest baseline.

Five of six frozen gates passed. The required recurrence-margin improvement of at least 0.05 failed.

Verdict: **`KILL_WORST_FAMILY_RECURRENCE`**.

The result shows that robust worst-family thresholding solves the earlier false-alarm failure but leaves no performance frontier over the simpler annual-replicate baseline. No null family, threshold, score, injection, comparator, trial count, or gate will be changed. No real-shower, held-out-year, catalogue, or GhostStream application is authorized.
