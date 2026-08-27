# OrbitTrace FPR-budgeted dual channel — v4 development

## Ancestry and preservation

The continuous primary ranking is frozen **v3 multi-anchor wavelet energy**. v4 does not alter that score, its 4°/10% Brown-family geometry, its top-four L2 aggregation, or any v3 result.

The sparse evidence channel is the already frozen **fixed4** empirical p-value. No fixed4 score or geometry is changed.

v1, v2, v3, Brown-family wavelet, prior dual-channel, Sugar, HDBSCAN, catalogue, and blind-recovery records remain untouched.

## Why a decision layer is now authorized

v3 development produced the first OrbitTrace-owned ranking above the Brown-family wavelet (`0.836860 > 0.828506`) while preserving k=6–12 recall. It failed only:

- the fixed4-level k=4 requirement; and
- the pooled FPR cap by a small amount (`116/2048 = 0.056641` vs <=0.055).

The next problem is therefore allocation of the finite empirical false-positive budget between a strong general ranking and the complementary sparse channel, not redesign of the ranking.

## Development-only threshold selection

This stage openly uses the already exposed SonotaCo 2025 v3 development records. It is parameter development, not prospective evidence.

The empirical calibration has 128 background episodes per Mondrian bin, so attainable p-values are integer ranks divided by 129. The finite candidate grid is:

- v3 primary threshold: `m_v3 / 129`, with `m_v3 in {1,2,3,4,5,6}`;
- fixed4 sparse threshold: `m_f4 / 129`, with `m_f4 in {1,2,3,4,5,6}`.

For each of the 36 pairs the reporting decision is:

`(p_v3 <= m_v3/129) OR (p_fixed4 <= m_f4/129)`.

A pair is feasible only if all are satisfied on the 2025 development records:

- pooled held-out-negative FPR <= 0.055;
- k=4 recall >= the frozen fixed4 recall at nominal alpha=.05;
- k=6 recall >= Brown-family wavelet recall minus 0.03;
- k=8 recall >= Brown-family wavelet recall minus 0.03;
- k=12 recall >= Brown-family wavelet recall minus 0.03.

Among feasible pairs, the selector chooses the pair with the **lowest pooled FPR**. Remaining ties are broken by, in order: higher k=4 recall, higher minimum recall margin over the four gates, smaller total rank budget `m_v3 + m_f4`, then smaller `m_v3`.

The complete 36-pair table is preserved. If no pair is feasible, v4 fails. If a pair is selected, that exact integer pair is frozen before any transfer year is evaluated.

## Frozen development selection

Workflow `31146852225` selected the exact reporting rule:

`(p_v3 <= 3/129) OR (p_fixed4 <= 4/129)`.

The integer thresholds `(3,4)` are frozen and cannot be changed from transfer or validation outcomes. Continuous-ranking AUROC remains the frozen v3 score; v4 is only the decision layer.

## SonotaCo 2023 unchanged-transfer protocol

SonotaCo 2023 is a transfer corpus, not a new prospective validation corpus. Its prior fixed4 and Brown-family benchmark results were already exposed before v4 development, but the **v3 score and v4 combined decision are executed with no 2023-specific tuning**.

Before the 2023 archive is opened by the v4 workflow, the workflow must verify:

- the exact source commit used by the successful prior 2023 transfer, `e23c7859bbcaf57b72be67c6ec834c496671c90d` (workflow `31105278114`);
- the exact frozen v3 source and its self-tests;
- the exact frozen v4 decision module and `(3/129, 4/129)` thresholds;
- the exact validated 2023 parser/confirmation source, GMN-MDC mapping audit, and archive hash.

The 2023 transfer is a full pass only if all of the following hold without threshold reselection:

- every upstream 2023 benchmark integrity gate passes;
- v3 weak-stream AUROC is at least the Brown-family wavelet AUROC on the same 2023 benchmark;
- pooled v4 held-out-negative FPR <= 0.055;
- worst reporting-sector v4 FPR <= 0.08;
- v4 k=4 recall >= nominal-alpha=.05 fixed4 k=4 recall on the same benchmark;
- v4 k=6 recall >= nominal-alpha=.05 Brown-family k=6 recall minus 0.03;
- v4 k=8 recall >= nominal-alpha=.05 Brown-family k=8 recall minus 0.03;
- v4 k=12 recall >= nominal-alpha=.05 Brown-family k=12 recall minus 0.03;
- all v3 and fixed4 empirical p-values used by the decision remain on the exact denominator-129 calibration grid.

A failed transfer is preserved as a failure and does not authorize any change to v3 or the frozen v4 thresholds.

## Ranking claim boundary

Continuous-ranking AUROC remains exactly the frozen v3 AUROC. The threshold selector may not change or re-evaluate the ranking score itself.

## Next-stage requirement

A 2025 development selection is not validation. The selected integer thresholds must next transfer unchanged across separately executed years. No threshold may be adjusted from transfer results. A final prospective validation corpus must be designated and frozen before its scientific scores are opened.
