# OrbitTrace calibrated evidence-offset v8 — frozen two-year development result

Authoritative workflow: `31148916722`

Artifact: `8982584656`

Artifact digest: `sha256:cc2f36c3128a696027aeae9195277cebe5576691ea75191077ef764283c87348`

Authoritative repaired head: `6127f19a3adfe1a6de252c430a970dda4866ae34`

Development verdict: **`PASS_EVIDENCE_OFFSET_V8_DEVELOPMENT`**

Feasible candidates: **1/6**.

Selected method: **`orbittrace_v3_fixed4_offset_pos050_v8`**

Selected offset: **`+0.50`**

The initial workflow attempt failed before data access because the runner-adapter script omitted its local `evidence_offset_v8` import. Commit `6127f19a3adfe1a6de252c430a970dda4866ae34` repaired only that adapter import. The six scientific offsets, component methods, statistic, empirical calibration, selector, development years, and gates were unchanged.

## Frozen selected statistic

Components:

- primary: frozen `orbittrace_multi_anchor_wavelet_energy_v3`;
- sparse: frozen `orbittrace_fixed4`.

For empirical component p-values `p_v3` and `p_fixed4` in a Mondrian bin:

`T = max(-log(p_v3), -log(p_fixed4) - 0.50)`.

For every calibration episode, paired leave-one-out component p-values generate the null `T` distribution. The final candidate p-value is the empirical upper-tail p-value of the target `T` against that paired null distribution. Reporting detection is final `p <= 0.05`.

No parameter may be altered after this freeze.

## SonotaCo 2025 development

- selected AUROC: **0.8417597752**;
- Brown-family wavelet AUROC: **0.8285055722**;
- AUROC margin: **+0.0132542030**;
- pooled FPR .05: **0.0527343750**;
- worst-sector FPR .05: **0.0651041667**;
- recall k=4/6/8/12: **0.1544117647 / 0.5735294118 / 0.8455882353 / 0.9558823529**;
- fixed4 k=4 reference: **0.1544117647**;
- Brown k=6/8/12 reference: **0.5955882353 / 0.8308823529 / 0.9485294118**;
- every preregistered gate passed.

## SonotaCo 2023 development

- selected AUROC: **0.8350333557**;
- Brown-family wavelet AUROC: **0.8319715832**;
- AUROC margin: **+0.0030617725**;
- pooled FPR .05: **0.0506628788**;
- worst-sector FPR .05: **0.0729166667**;
- recall k=4/6/8/12: **0.2012195122 / 0.5426829268 / 0.7865853659 / 0.9329268293**;
- fixed4 k=4 reference: **0.1890243902**;
- Brown k=6/8/12 reference: **0.5426829268 / 0.7987804878 / 0.9207317073**;
- every preregistered gate passed.

## Complete frozen candidate outcome

| Offset | Two-year feasible | Minimum annual AUROC margin over Brown | Minimum k4 margin vs fixed4 |
|---:|:---:|---:|---:|
| -0.75 | no | -0.004777 | -0.014706 |
| -0.50 | no | -0.001662 | -0.007353 |
| -0.25 | no | +0.000920 | -0.007353 |
| 0.00 | no | +0.001343 | -0.007353 |
| +0.25 | no | +0.002970 | -0.007353 |
| **+0.50** | **yes** | **+0.003062** | **+0.000000** |

The selector was frozen before scoring and chose only among candidates passing every gate in both years. The selected +0.50 candidate was the sole feasible candidate.

## Scientific status

This is a **two-year development pass**, not prospective validation. The exact selected method is now frozen before any SonotaCo-2016 scientific scoring.

The next authorized stage is a transport/schema/eligibility-only audit of the preregistered preferred prospective year **SonotaCo 2016**, followed by a source-only prospective-runner audit. Those stages may not compute the selected detector score, AUROC, recall, FPR, or any other prospective scientific endpoint. Only after both audits pass may one one-shot 2016 scientific validation run occur.
