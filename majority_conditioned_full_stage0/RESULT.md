# Majority-conditioned recurrence full Stage-0: authoritative pass

Runner workflow `30880347130` completed the independently seeded frozen benchmark. Artifact `8881171193` was preserved with digest `sha256:d0788148e4e3074b72c1e63cd2d1073555369a03330abd76e2020a9fb457fd5c`.

## Frozen design

- exact candidate SHA-256: `3d60e3622d7ec406bb03cd4ab43faec84be1eff4d0dd70afa6ed79b8fd777281`;
- seed: `20260806`;
- 100 calibration catalogs per null family;
- 100 fresh catalogs per null family;
- 100 recurrent and 100 transient injections per strength;
- alpha: `0.10`;
- exact public observed-subset MD5: `f57a2ac71832ceca9227441c00b8cd58`.

## Calibration and robustness

- ideal-null FWER: **0.020**;
- shared-structure-null FWER: **0.070**;
- weak one-year-artifact detection: **0.000**.

Both independently enforced full-stage FWER gates passed against the prospectively tightened **0.15** ceiling.

## Power

- weak recurrent recovery: **0.525**;
- strongest comparator weak recovery: **0.410**;
- weak recurrence margin: **0.525**;
- strongest comparator margin: **0.410**;
- recurrence-margin gain: **+0.115**;
- strong recurrent recovery: **0.965**;
- strongest comparator strong recovery: **0.910**.

The shared-structure family determined the deployed majority-conditioned threshold: **3.86844**, versus **3.08501** under the ideal null. The method therefore retained its advantage under the more conservative family-specific calibration rather than benefiting from an easy null threshold.

All six stricter full-stage gates passed.

Verdict: **`PASS_MAJORITY_CONDITIONED_RECURRENCE_FULL_STAGE0`**.

## Interpretation

Subtracting the pointwise median annual evidence successfully removed structure shared by most observing years while preserving a signal active in five of fifteen years. Unlike local spatial high-pass filtering, the cross-year common-mode operation materially reduced shared-structure false discoveries and increased weak recurrent recovery over the original hard third-year recurrence statistic.

This remains simulation validation, not a meteor-stream discovery result. The pass authorizes only a separately frozen real-shower structural and label-support feasibility gate that stratifies established showers by the number of active years. It does not authorize a confirmation panel, catalogue scan, GhostStream score, or discovery claim.