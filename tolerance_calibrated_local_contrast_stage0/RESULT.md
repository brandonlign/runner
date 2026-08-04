# Tolerance-calibrated local-contrast recurrence: authoritative no-go

Runner workflow `30880046576` completed the exact frozen calibration and simulation design. Artifact `8881191796` was preserved with digest `sha256:0f7007d79a72c78093d2f4e42a5da4bb0e980f9787489315b93cbb179795398d`.

## Frozen design

- derived source SHA-256 `a97f207760234313b7949616fdbd506586da7b104a35a983104fdf7fb110cbfe`;
- seed `20260805`;
- 512 calibration catalogs per null family;
- frozen tolerance rank **473 of 512**;
- calibration confidence **0.95**;
- 200 fresh catalogs per null family;
- 100 recurrent and transient injections per strength;
- alpha `0.10`.

## Result

The tolerance construction restored robust false-positive control:

- ideal-null local-contrast FWER: **0.000**;
- shared-structure-null local-contrast FWER: **0.075**;
- weak one-year-artifact detection: **0.000**.

Power remained useful but missed the prospectively frozen margin gate:

- weak recurrent recovery: **0.355**;
- strongest comparator weak recovery: **0.310**;
- weak recurrence-margin gain: **+0.045**;
- required gain: at least **+0.050**;
- strong recurrent recovery: **0.895** versus strongest comparator **0.875**.

Seven of eight frozen gates passed. The sole failure was `recurrence_margin_gain_vs_best_baseline_at_least_0_05`.

Verdict: **`KILL_TOLERANCE_CALIBRATED_LOCAL_CONTRAST`**.

## Interpretation

The nonparametric tolerance bound solved the conditional-calibration problem without changing the score, but the additional threshold conservatism reduced the candidate's weak-stream advantage below the registered minimum. This exact calibration formulation will not be rescued by changing the confidence, rank, sample count, alpha, null family, score, seed, comparator, or power gate.

No real-shower benchmark, confirmation study, catalogue scan, or GhostStream application is authorized.