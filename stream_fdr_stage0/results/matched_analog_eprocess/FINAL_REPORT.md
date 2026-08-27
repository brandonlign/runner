# Matched-analogue sequential evidence — final no-go

Authoritative runner workflow: `30845039780`

Artifact: `matched-analog-eprocess-stage0` (`8868342697`)

Artifact digest: `sha256:5817d0bbb514eb23b477c135209675f4d23f1a7c73bc0d8918a5de9f6795ca1f`

## Verdict

**KILL_MATCHED_ANALOG_EPROCESS_DIRECTION**

The redesign replaced the invalid geometric null with held-out-year ranks against fifteen prespecified solar-longitude analogue windows. GhostStream was excluded.

## What worked

- primary null acceptance: **0.000**, Wilson upper 95% **0.029**;
- recurring-moderate recovery: **0.990**;
- recurring-sparse recovery: **0.958** versus best nonadaptive baseline **0.740**;
- sparse paired gain: **0.219**, bootstrap 95% **[0.125, 0.313]**;
- strong-recurring recovery: **0.990**;
- one-year-artifact acceptance: **0.000**.

## Fatal failures

- intermittent-sparse recovery: **0.010**;
- late-onset-sparse recovery: **0.010**;
- diffuse-recurring recovery: **0.229**;
- untouched M2026-A1 primary E-value: **0.593**, not accepted, despite localization only **0.147** standardized units from the reference.

## Interpretation

Matched analogues repaired null validity but made evidence too conservative for realistic weak streams whose activity is intermittent, begins late, or is broader than the compact template. The untouched real control failed, so strong synthetic recurring performance is insufficient.

The protocol prohibited a second analogue-offset, p-calibrator, or threshold redesign. The sequential predictive-evidence direction is therefore closed for GhostStream. It may be useful for exceptionally stable compact annual streams, but it is not a suitable major methodological contribution for this project.
