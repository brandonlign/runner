# OrbitTrace jointly calibrated Tippett v5 — frozen two-year development result

Scientific source commit: `9a245b591cbee55057049d48d407b91fd18e99e1`

Workflow: `31147511873`

## SonotaCo 2023

Artifact: `8982049041`

Artifact digest: `sha256:b21c600be04045932d79b41eb7b068e20d858adfd29958c0a64731d9f3512a30`

Verdict: **`PASS_V5_2023_DEVELOPMENT`**

- frozen v3 AUROC: **0.836263** vs Brown **0.831972**;
- joint FPR .05: **0.054924**;
- worst-sector FPR: **0.067708**;
- joint recall k=4/6/8/12: **0.207317 / 0.536585 / 0.792683 / 0.951220**;
- every preregistered gate passed.

## SonotaCo 2025

Artifact: `8982079595`

Artifact digest: `sha256:b2588d0795dedeaa0202b28ec01fda9a5fd1e834b6971d92ddf1559fc8bac74b`

Verdict: **`FAIL_V5_2025_DEVELOPMENT`**

- frozen v3 AUROC: **0.836860** vs Brown **0.828506**;
- joint FPR .05: **0.044434**;
- worst-sector FPR: **0.062500**;
- joint recall k=4/6/8/12: **0.147059 / 0.566176 / 0.816176 / 0.941176**.

Every gate except `joint_k4_at_least_fixed4` passed. The fixed4 reference was `0.154412`, so v5 missed the k=4 gate by one positive episode.

## Overall decision

Overall verdict: **`FAIL_JOINT_TIPPETT_V5_TWO_YEAR_DEVELOPMENT`** because the protocol required every gate in both years.

The result nevertheless establishes two stable findings that remain preserved:

1. the frozen v3 multi-anchor ranking exceeded Brown-family wavelet AUROC in both years without retuning;
2. joint empirical calibration substantially improved false-positive control and moderate-stream reporting, but still did not fully absorb fixed4's 2025 four-member advantage.

Adding a post-hoc fixed4 rescue to v5 was checked diagnostically after the frozen result. The minimum-p rescue adds no detections because such extreme fixed4 cases are already admitted by the jointly calibrated Tippett rule. Looser fixed4 rescue thresholds cannot satisfy the complete two-year FPR/recall gates simultaneously. They are not promoted.

v5 is frozen as a failed reporting-layer experiment and may not be silently retuned. A successor may develop a new multi-anchor aggregation family on the now-exposed 2025+2023 panel, but must be separately named and prospectively validated after selection.
