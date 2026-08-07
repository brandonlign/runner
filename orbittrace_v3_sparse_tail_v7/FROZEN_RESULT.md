# OrbitTrace v3-primary fixed4 sparse-tail v7 — frozen two-year result

Authoritative repaired workflow: `31148429330`

Artifact: `8982408365`

Artifact digest: `sha256:195f6b24bb8c09d10fc8c5a9c5ffcf7e2aedffc50124d3fd591c42c33c9a1c6f`

Scientific method source commit: `38d5ead15484d36023061252438d8883b1e5f242`

Overall verdict: **`FAIL_V7_TWO_YEAR_DEVELOPMENT`**

The only source change between the initial technical attempt and this authoritative run was a synthetic pre-data self-test correction. The v7 score, inherited margin `0.25`, paired leave-one-out null calibration, final empirical p-value, alpha, and scientific gates were unchanged.

## SonotaCo 2025

Verdict: **`FAIL_V7_2025_DEVELOPMENT`**

- v7 weak-stream AUROC: **0.841837**;
- Brown-family wavelet AUROC: **0.828506**;
- frozen v3 AUROC: **0.836860**;
- fixed4 AUROC: **0.813250**;
- pooled FPR .05: **0.043457**;
- worst-sector FPR .05: **0.062500**;
- v7 recall k=4/6/8/12: **0.147059 / 0.566176 / 0.816176 / 0.941176**.

Every gate passed except k=4 recall at least fixed4. The fixed4 reference was `0.154412`, so v7 missed by one positive episode.

## SonotaCo 2023

Verdict: **`PASS_V7_2023_DEVELOPMENT`**

- v7 weak-stream AUROC: **0.834941**;
- Brown-family wavelet AUROC: **0.831972**;
- frozen v3 AUROC: **0.836263**;
- fixed4 AUROC: **0.811631**;
- pooled FPR .05: **0.046875**;
- worst-sector FPR .05: **0.062500**;
- v7 recall k=4/6/8/12: **0.201220 / 0.530488 / 0.780488 / 0.932927**.

Every preregistered gate passed.

## Interpretation

The inherited `0.25` sparse-tail offset improves the continuous evidence ranking substantially on 2025 and gives a complete pass on 2023, while maintaining strong false-positive control. It still does not fully absorb fixed4's 2025 four-member tail.

The failure is narrow and repeatable: v5 and v7 each miss the 2025 fixed4 k=4 reference by exactly one injected episode while passing the other requirements. This motivates one final explicitly developmental evidence-offset family on the already exposed 2025+2023 panel. The family must be frozen before scoring, preserve the complete table, and then lock exactly one winner before any SonotaCo-2016 scientific access.

No v7 parameter may be changed post-result or described as a two-year pass.
