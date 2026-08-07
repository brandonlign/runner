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

## Ranking claim boundary

Continuous-ranking AUROC remains exactly the frozen v3 AUROC. The threshold selector may not change or re-evaluate the ranking score itself.

## Next-stage requirement

A 2025 development selection is not validation. The selected integer thresholds must next transfer unchanged across separately executed years. No threshold may be adjusted from transfer results. A final prospective validation corpus must be designated and frozen before its scientific scores are opened.
