# Local-contrast hard recurrence: authoritative development result

Runner workflow `30877969736` completed the frozen exact-data development screen. Artifact `8880244804` was preserved with digest `sha256:1885babf888fb8f85a913b7b61b1bcc9f47f08ff3b29eda42ecf9d2badc5c1da`.

## Result

Worst-family thresholds were calibrated independently against ideal and persistent shared-structure nulls, then set to the larger family threshold.

- ideal-null FWER: **0.000**;
- shared-structure-null FWER: **0.200**;
- weak one-year-artifact detection: **0.000**;
- local-contrast weak recurrent recovery/margin: **0.5667 / 0.5667**;
- strongest baseline weak recovery/margin: **0.4167 / 0.4167**;
- recurrence-margin gain: **+0.1500**;
- strong recurrent recovery: **0.9333** versus **0.9000** for the strongest baseline.

Five of six frozen gates passed. The sole failure was the shared-structure null FWER ceiling:

- required at most **0.15**;
- observed **0.20**.

Verdict: **`KILL_LOCAL_CONTRAST_RECURRENCE`**.

## Interpretation

Spatially high-passing the annual evidence map produced a genuine power gain and rejected all one-year artifacts in the frozen panel. It still admitted too many persistent structured-background maxima under the separately frozen shared-structure family. The all-gates rule is binding: no Gaussian width, contrast truncation, recurrence order, family threshold, trial count, injection design, comparator, or FWER ceiling will be changed.

No real-shower, confirmation-year, catalogue, or GhostStream application is authorized.
