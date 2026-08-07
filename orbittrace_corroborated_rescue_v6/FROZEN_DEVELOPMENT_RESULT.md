# OrbitTrace v6 — frozen corroborated-rescue development result

Authoritative workflow: `31154450523`

Artifact: `8984586266`

Artifact digest: `sha256:87e6786b10540510ae458c12029a1c1653a8b936483801260bf98ca7ec1f01d1`

Scientific source commit: `8d3f82757862b1710303ba990c307dbabb55fd79`

Verdict: **`PASS_V6_CORROBORATED_RESCUE_DEVELOPMENT`**

## Frozen architecture

The scoring functions are unchanged predecessors:

- primary continuous ranking: `orbittrace_multi_anchor_wavelet_energy_v3`;
- sparse score: frozen `orbittrace_fixed4`;
- calibration: 512 source-preserving null episodes per Mondrian bin;
- conservative empirical denominator: 513.

The frozen v6 reporting rule is:

`(p_v3 <= 17/513) OR ((p_fixed4 <= 15/513) AND (p_v3 <= 122/513))`.

Thus fixed4 may rescue an episode only when the continuous v3 score also supplies weaker corroborating evidence. V3, fixed4, Brown-family wavelet, v1-v5, Sugar, HDBSCAN, catalogue, and blind-recovery records are not modified by v6.

## Development search

The preregistered finite family contained exactly **69,628** rules:

- primary v3 ranks 1–26;
- fixed4 ranks 1–26;
- v3 corroboration ranks 26–128.

All 69,628 rules were evaluated against the exact frozen 2025, 2023, and exposed-failed-2024 development records. Exactly **4** rules were feasible under every per-year FPR, sector-FPR, sparse k=4, and Brown-relative k=6/8/12 gate.

The deterministic selector chose:

- primary v3 rank: **17/513**;
- fixed4 sparse rank: **15/513**;
- v3 corroboration rank: **122/513**.

The selected rule's minimum recall margin across all 12 year-specific recall constraints is **0.000000**. This is a binding-gate result and must not be described as having a large safety margin.

Maximum pooled FPR across the three development years: **0.054924**.

## SonotaCo 2025 development

- pooled FPR: **0.053223**;
- worst-sector FPR: **0.070312**;
- recall k=4/6/8/12: **0.154412 / 0.625000 / 0.845588 / 0.955882**.

## SonotaCo 2023 development

- pooled FPR: **0.054924**;
- worst-sector FPR: **0.072917**;
- recall k=4/6/8/12: **0.189024 / 0.554878 / 0.774390 / 0.932927**.

## SonotaCo 2024 successor-development evidence

The frozen failed v5 prospective result was preserved before being used as v6 development evidence.

- pooled FPR under v6: **0.053030**;
- worst-sector FPR: **0.065104**;
- recall k=4/6/8/12: **0.181818 / 0.560606 / 0.818182 / 0.962121**.

## Promotion boundary

This is development evidence, not prospective validation. SonotaCo 2025, 2023, and 2024 are development corpora for v6.

**SonotaCo 2018 is reserved for one prospective validation sequence and was not accessed for method performance during v6 development.** Before any 2018 score or performance metric is computed, transport-only and score-free eligibility audits must be completed and frozen.

No 2018 result may change the v3 score, fixed4 score, 512-null calibration, denominator 513, ranks `(17, 15, 122)`, corroborated-rescue Boolean rule, or prospective gates. A prospective failure must be preserved and may not trigger same-2018 retuning.
