# OrbitTrace v4 — frozen SonotaCo 2023 transfer result

Workflow: `31147442432`

Artifact: `8982023596`

Artifact digest: `sha256:7e89ebbe8d1cbec9e8150a6d48211ee2805a6144dfa90a3fa6b5b274509c988e`

Executed source commit: `5184a49e448b5adee3a1f9b80b2348d451cfd2a1`

Exact previously successful 2023 benchmark source: `e23c7859bbcaf57b72be67c6ec834c496671c90d`

Verdict: **`FAIL_V4_SONOTACO_2023_TRANSFER`**

The frozen decision was applied unchanged:

`(p_v3 <= 3/129) OR (p_fixed4 <= 4/129)`.

No threshold was reselected from 2023.

## Result

- frozen v3 weak AUROC: **0.836263**;
- Brown-family wavelet weak AUROC: **0.831972**;
- pooled v4 FPR: **0.055871** (cap `0.055`);
- worst-sector v4 FPR: **0.072917** (cap `0.08`);
- v4 recall k=4/6/8/12: **0.201220 / 0.536585 / 0.762195 / 0.926829**;
- fixed4 k=4 reference: **0.189024**;
- Brown k=6/8/12 reference: **0.542683 / 0.798780 / 0.920732**.

## Gates

Passed:

- exact 2023 year and calibration denominator;
- frozen v3/v4 source and threshold audits;
- all upstream benchmark integrity checks;
- exact negative and positive record counts;
- empirical p-values on the denominator-129 grid;
- v3 AUROC at least Brown;
- worst-sector FPR;
- k=4 recall at least fixed4;
- k=6 and k=12 Brown-tolerance recall gates.

Failed:

- pooled FPR `0.055871 > 0.055`;
- k=8 recall `0.762195 < 0.798780 - 0.03 = 0.768780`.

This is a scientific transfer failure of the **v4 reporting decision**, not of the frozen v3 ranking. The v3 ranking transferred above Brown for a second year. The v4 thresholds and result remain frozen and may not be retuned. SonotaCo 2023 is development evidence for any successor architecture and cannot be reused as that successor's validation corpus.
