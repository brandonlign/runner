# OrbitTrace v5 — frozen SonotaCo 2024 prospective result

Authoritative scientific workflow: `31153711851`

Artifact: `8984315572`

Artifact digest: `sha256:7551c1e06f9efabc09123941ef84429ebeb26ec73247f34a0d8f6f5586963a77`

Scientific source commit: `b5fee44547d2d500254c9d9ee1ba60b8f9e1c97a`

Verdict: **`FAIL_V5_SONOTACO_2024_PROSPECTIVE_VALIDATION`**

This was the single preregistered scientific execution after the exact source, parser, eligibility-universe, calibration-panel, threshold, and reporting gates all passed. Two earlier workflow attempts stopped before scientific archive access and produced no detector result.

## Continuous ranking

- frozen v3 weak AUROC: **0.855869**;
- Brown-family wavelet weak AUROC: **0.850314**;
- fixed4 weak AUROC: **0.828634**;
- v3 minus Brown: **+0.005555**.

The v3 continuous-ranking gate passed for the third independently executed year in this development line.

## Frozen v5 decision

The unchanged decision was:

`(p_v3 <= 20/513) OR (p_fixed4 <= 10/513)`.

Prospective result:

- pooled held-out-negative FPR: **0.060133**;
- worst-sector FPR: **0.070312**;
- recall k=4/6/8/12: **0.181818 / 0.568182 / 0.810606 / 0.954545**.

## Frozen predecessor references

These were computed from the deterministic first 128 calibration nulls per bin, denominator 129, nominal alpha 0.05, exactly as preregistered:

- fixed4 recall k=4/6/8/12: **0.181818 / 0.386364 / 0.689394 / 0.863636**;
- Brown recall k=4/6/8/12: **0.159091 / 0.545455 / 0.795455 / 0.931818**;
- fixed4 FPR: **0.049242**;
- Brown FPR: **0.058239**.

## Gates

Passed:

- parser and eligibility universe exact;
- frozen scoring-source self-tests;
- exact nested 512/128 calibration panels;
- denominator-513 v5 p-value grid;
- denominator-129 predecessor p-value grid;
- v3 weak AUROC at least Brown;
- worst-sector FPR <= 0.08;
- k=4 recall at least predecessor fixed4;
- k=6, k=8, and k=12 recall each within 0.03 of predecessor Brown;
- exact frozen v5 decision rule.

Failed:

- pooled FPR: **0.060133 > 0.055**.

No v5 threshold, score, calibration size, or gate may be changed in response to this result. SonotaCo 2024 is now exposed development evidence for any successor architecture and cannot be reused as that successor's prospective validation corpus.

The strongest surviving scientific result from v5 is the continuous v3 ranking: it beat the Brown-family ranking prospectively on 2024 while preserving strong moderate-stream behavior. The failed component is the fixed two-channel reporting decision's cross-year false-positive transfer.
