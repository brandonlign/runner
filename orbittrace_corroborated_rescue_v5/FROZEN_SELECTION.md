# OrbitTrace v5 — frozen development selection

Workflow: `31147868124`

Job: `92771084720`

Artifact: `8982153140`

Artifact digest: `sha256:82310fb42d4e44bdf686c7b98fa7d55c7d5df56add91c13b1eb85bccdf2bbca3`

Scientific source commit: `c6d13b5c8263396a4b3597ead9b6b69a72eac72f`

Selector SHA-256: `6028e5764408490b40bad1a88939a142cb308739afe6b7fcee00c852c1afc845`

Verdict: **`PASS_V5_DEVELOPMENT_SELECTION`**

## Frozen rule

The 175-cell preregistered grid produced three feasible candidates. The deterministic selector chose:

- v3 primary rank `a = 4`;
- fixed4 sparse rank `b = 3`;
- v3 corroboration rank `c = 40`;
- denominator `129`.

The reporting decision is therefore frozen as:

`p_v3 <= 4/129 OR (p_fixed4 <= 3/129 AND p_v3 <= 40/129)`.

These three integer ranks may not be changed from any later year result.

## SonotaCo 2025 development metrics

- pooled FPR: **0.050781**;
- worst-sector FPR: **0.065104**;
- k=4 recall: **0.154412**;
- k=6 recall: **0.588235**;
- k=8 recall: **0.845588**;
- k=12 recall: **0.948529**;
- total recall slack over the four development gates: **0.097353**.

The continuous ranking remains frozen v3, with AUROC **0.836860** versus Brown-family **0.828506** on the same development benchmark.

## Evidence boundary

Selection used SonotaCo 2025 development records only. The already observed v4 SonotaCo 2023 failure motivated the v5 architecture but 2023 records were not supplied to the v5 selector. Consequently any v5 application to 2023 is retrospective, not untouched validation.
