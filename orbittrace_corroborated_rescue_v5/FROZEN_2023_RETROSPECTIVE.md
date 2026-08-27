# OrbitTrace v5 — frozen SonotaCo 2023 retrospective

Workflow: `31147965595`

Job: `92771376588`

Artifact: `8982191121`

Artifact digest: `sha256:f6b2a564ec9b7c86c367cf7ee20f365296140a8195c700b916fd197b2f91ced4`

Scientific source commit: `de821c8dcadc97e28504baac3ccb2f728020503b`

Decision-module SHA-256: `fdbac4bc46377ee22044689e39ce23849be443ca847584f6d92ecde530dbe06d`

Verdict: **`PASS_V5_2023_RETROSPECTIVE_TRANSFER`**

Evidence class: **post-development retrospective transfer; not untouched validation**.

Frozen rule:

`p_v3 <= 4/129 OR (p_fixed4 <= 3/129 AND p_v3 <= 40/129)`.

Results:

- v3 AUROC: **0.836263** vs Brown-family **0.831972**;
- pooled FPR: **0.050189**;
- worst-sector FPR: **0.075521**;
- k=4 recall: **0.201220**;
- k=6 recall: **0.548780**;
- k=8 recall: **0.780488**;
- k=12 recall: **0.926829**.

Every frozen transfer gate passed, including the two gates that failed under v4: pooled FPR <=0.055 and k=8 within 0.03 of Brown-family recall.

This result supports the structural rationale for corroborated rescue, but it cannot be counted as independent validation because the earlier v4 SonotaCo 2023 failure was observed before v5 was designed. The v5 ranks remain unchanged for the next independent post-selection year-level test.
