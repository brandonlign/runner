# Local-contrast recurrence full Stage-0: authoritative no-go

Runner workflow `30879216007` completed the entire independently seeded frozen benchmark before the known stale Markdown-report key caused the executable to exit. The authoritative JSON, full provenance, and environment were preserved in artifact `8880781420`, digest `sha256:d235b015cd174a10f41c5091b8e2bd79f154609007a0f2c4fc4f9f38b45084d8`.

## Frozen design

- seed: `20260804`;
- 100 worst-family calibration catalogs;
- 100 fresh ideal-null catalogs;
- 100 fresh shared-structure-null catalogs;
- 100 recurrent and transient injections per strength/condition;
- catalog alpha: `0.10`;
- exact candidate SHA-256: `b7589d8d140a37596f19d4993be1e2fdd99a18b8eaa087a02e3c4ce585000071`;
- exact public observed-subset MD5: `f57a2ac71832ceca9227441c00b8cd58`.

## Result

The local high-pass recurrence statistic retained the power benefit seen in the reduced screen:

- weak recurrent recovery: **0.545** versus strongest comparator **0.470**;
- weak recurrence margin: **0.545** versus strongest comparator **0.470**;
- recurrence-margin gain: **+0.075**;
- strong recurrent recovery: **0.925** versus strongest comparator **0.920**;
- weak one-year-artifact detection: **0.000**.

Ideal-null calibration was strong:

- local-contrast ideal-null FWER: **0.010**.

But the predeclared shared-structure robustness gate failed:

- local-contrast shared-structure FWER: **0.220**;
- frozen maximum: **0.150**.

For context, the original hard recurrence statistic had shared-structure FWER **0.230**, while the soft recurrence comparator achieved **0.120**. Spatial high-pass filtering improved power and only marginally reduced the original recurrence detector's vulnerability to persistent shared annual structure.

Five of six frozen gates passed. Verdict: **`KILL_LOCAL_CONTRAST_RECURRENCE`**.

## Interpretation

The result supports the scientific premise that recurrent local contrast carries useful weak-stream information, but this exact statistic is not robust enough for a discovery method. A smooth structure shared across observing years can still generate repeated local evidence peaks after high-pass subtraction, producing unacceptable catalog-level false discoveries.

Do not alter the Gaussian width, recurrence order, active-year count, shared-distortion model, calibration family, seed, trial counts, alpha, threshold, comparator, or gate to rescue this formulation. No real-shower feasibility gate, confirmation study, catalogue scan, or GhostStream application is authorized.

The Markdown reporter's stale metric name is a reporting-only defect: `stage0_result.json` was written after every simulation and contains the complete design, metrics, gates, runtime, and explicit kill verdict. It does not change the scientific outcome.