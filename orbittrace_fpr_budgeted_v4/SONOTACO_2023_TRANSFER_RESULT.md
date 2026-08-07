# OrbitTrace v4 SonotaCo 2023 unchanged transfer — frozen result

Workflow: `31147096012`

Artifact: `8981886834`

Artifact digest: `sha256:19644a2ea5b527340f3b451b7373ebd93b6047d00a1486c0e0672882cd296057`

Transfer source commit: `2c3ca927686bbc866c235ffb41264e9210fe1802`

Verdict: **`FAIL_V4_SONOTACO_2023_TRANSFER`**

## Ranking transfer

The frozen v3 continuous ranking transferred successfully:

- v3 weak-stream AUROC: **0.836263**;
- Brown-family wavelet AUROC: **0.831972**;
- fixed4 AUROC: **0.811631**.

Thus the v3 ranking exceeded Brown on both the 2025 development year (`0.836860 > 0.828506`) and the unchanged 2023 transfer (`0.836263 > 0.831972`).

## Frozen v4 decision transfer

Using unchanged thresholds `(p_v3 <= 3/129) OR (p_fixed4 <= 4/129)`:

- pooled FPR: **0.055871**;
- worst-sector FPR: **0.072917**;
- recall k=4/6/8/12: **0.201220 / 0.536585 / 0.762195 / 0.926829**.

Passed gates:

- v3 AUROC above Brown;
- k4 at least fixed4;
- k6 within 0.03 of Brown;
- k12 within 0.03 of Brown;
- worst-sector FPR <=0.08;
- all transfer/integrity/source gates.

Failed gates:

- k8 within 0.03 of Brown (`0.762195` vs Brown `0.798780`);
- pooled FPR <=0.055 (`0.055871`).

## Interpretation

The v3 ranking is retained as a strong cross-year result. The v4 fixed rank-budget decision allocation is rejected as a general reporting layer because the specific 2025-selected threshold split did not fully transfer to 2023. No threshold may be changed post-transfer under v4.

A successor decision layer may keep v3 unchanged and replace manual per-channel rank allocation with a standard joint p-value combination or jointly calibrated reporting statistic developed transparently on already exposed years, then frozen before a new prospective year.
