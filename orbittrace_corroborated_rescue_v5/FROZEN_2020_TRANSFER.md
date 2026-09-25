# OrbitTrace v5 — frozen SonotaCo 2020 transfer

Workflow: `31148310728`

Job: `92772440795`

Artifact: `8982331085`

Artifact digest: `sha256:dce83176047ffc34299cea72db5bf5cf50716356dd92553842f4c2959bc385c1`

Scientific source commit: `130497f6fddcd1ae0c1be438477c55292d019d5b`

Adapted 2020 v3 runner digest: `sha256:5391a459ed55b6109e77c5496891ee3a63040c938ded4f31e0c5e6cb6588f85e`

Verdict: **`FAIL_V5_SONOTACO_2020_POST_SELECTION_TRANSFER`**

Evidence class: **independent post-selection year-level transfer on a previously scored 2020 benchmark**. SonotaCo 2020 was not used to design or select v5, but the archive had been scored previously by older methods, so this is not an untouched-archive claim.

## Frozen rule

No 2020-specific selection occurred. The transferred rule remained exactly:

`p_v3 <= 4/129 OR (p_fixed4 <= 3/129 AND p_v3 <= 40/129)`.

## Result

The continuous v3 ranking transferred successfully again:

- v3 weak AUROC: **0.802819**;
- Brown-family wavelet: **0.796782**;
- fixed4: **0.778504**.

The frozen v5 decision produced:

- pooled FPR: **0.045928**;
- worst-sector FPR: **0.062500**;
- k=4 recall: **0.118056** vs fixed4 **0.201389**;
- k=6 recall: **0.444444** vs Brown **0.486111**;
- k=8 recall: **0.687500** vs Brown **0.694444**;
- k=12 recall: **0.902778** vs Brown **0.909722**.

All source/provenance, original-runner integrity, count, calibration-grid, v3-AUROC, pooled-FPR, sector-FPR, k=8, and k=12 gates passed. Two preregistered gates failed:

- `k4_recall_at_least_fixed4`;
- `k6_within_003_of_wavelet`.

## Interpretation

This is a real failure of v5 as a **single combined binary detector**. The failure is not evidence against the v3 continuous ranking: v3 again exceeded the Brown-family wavelet on an independent post-selection year-level transfer.

Across the tested years, the stable transferable object is now the v3 ranking, while attempts to force the v3 and fixed4 strengths into one universal binary threshold rule create year-dependent sensitivity tradeoffs. v5 is frozen and may not be retuned from the 2020 result.
