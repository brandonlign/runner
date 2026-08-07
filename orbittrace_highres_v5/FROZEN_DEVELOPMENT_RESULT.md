# OrbitTrace v5 — frozen high-resolution development result

Authoritative workflow: `31151459055`

Scientific source commit: `6ee64ef895047830dfe97647ee3a94b7beebf69b`

Artifacts:

- SonotaCo 2025: `8983514836`, `sha256:e15de4996c2325637a24ee9c5f16fe749f895402af7728f731cac9be55d1ebcd`;
- SonotaCo 2023: `8983496935`, `sha256:201d8bfb52d876c8cb5d1042198d8966e0b5cf052f458bed858985c9a0abb415`;
- cross-year selection: `8983519870`, `sha256:ebf2965878cc1b6f4fe2458d2b0f0f3f331f82f958e7aaa0b4c64e00871fe7db`.

Verdict: **`PASS_V5_HIGHRES_DEVELOPMENT`**

## Frozen architecture

The scoring functions remain unchanged:

- primary continuous ranking: `orbittrace_multi_anchor_wavelet_energy_v3`;
- sparse channel: frozen `orbittrace_fixed4`.

Calibration and reporting decision are now frozen as:

- source-preserving calibration nulls per Mondrian bin: **512**;
- conservative empirical denominator: **513**;
- v3 reporting rank: **20/513**;
- fixed4 sparse reporting rank: **10/513**;
- detection: `(p_v3 <= 20/513) OR (p_fixed4 <= 10/513)`.

The complete preregistered `26 x 26 = 676` pair grid was evaluated. Exactly **1/676** pairs satisfied every cross-year development gate. Therefore the selected pair is unique under the frozen feasible set, not one of many interchangeable successful choices.

The comparison targets were the exact immutable 128-null predecessor metrics. They were not recalibrated to make the v5 gates easier.

## SonotaCo 2025 development

- v3 weak AUROC: **0.836860**;
- frozen Brown-family AUROC: **0.828506**;
- combined pooled FPR: **0.054688**;
- combined worst-sector FPR: **0.072917**;
- combined recall k=4/6/8/12: **0.161765 / 0.647059 / 0.838235 / 0.955882**;
- frozen fixed4 k=4 reference: **0.154412**;
- frozen Brown k=6/8/12 references: **0.595588 / 0.830882 / 0.948529**.

## SonotaCo 2023 development

- v3 weak AUROC: **0.836263**;
- frozen Brown-family AUROC: **0.831972**;
- combined pooled FPR: **0.053504**;
- combined worst-sector FPR: **0.072917**;
- combined recall k=4/6/8/12: **0.189024 / 0.560976 / 0.780488 / 0.920732**;
- frozen fixed4 k=4 reference: **0.189024**;
- frozen Brown k=6/8/12 references: **0.542683 / 0.798780 / 0.920732**.

Maximum pooled FPR across development years: **0.054688**.

Minimum recall margin across all eight year-specific constraints: **0.000000**. The binding constraint is therefore real and the architecture should be described as passing the frozen gates, not as having a large safety margin.

## Promotion boundary

This is development evidence, not prospective validation. SonotaCo 2023 and 2025 are now development corpora for v5.

The next authorized scientific execution is **one prospective run on SonotaCo 2024**, using the architecture above unchanged. The 512-null calibration size, denominator 513, v3 score, fixed4 score, thresholds `(20, 10)`, OR decision, and validation gates may not be changed from any 2024 result.

No 2024 score or method-performance result was inspected before this development freeze was committed.
