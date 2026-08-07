# OrbitTrace corroborated sparse rescue — v5

## Status and ancestry

v5 is a separately named post-v4 development stage. It begins only after the frozen v4 SonotaCo 2023 transfer failure was recorded.

The continuous primary ranking remains **exactly frozen v3 multi-anchor wavelet energy**. The sparse channel remains **exactly frozen fixed4**. v5 changes only how their already calibrated empirical p-values are combined into a binary reporting decision.

No v1-v4 result, v3 score, fixed4 score, Brown-family comparator, catalogue result, or blind-recovery record may be modified.

Because the 2023 v4 result has already been observed, SonotaCo 2023 cannot serve as untouched validation for v5. It may only be used later as a labelled post-development retrospective transfer. v5 parameter selection uses SonotaCo 2025 development records only.

## Structural change

v4 used an unconditional union of marginal thresholds:

`v3 strong OR fixed4 strong`.

That transferred poorly because fixed4-only rescue can add background hits while the conservative v3 cutoff loses moderate-stream recall.

v5 uses a **corroborated rescue**:

`v3 primary OR (fixed4 sparse AND v3 corroboration)`.

The fixed4 channel can therefore rescue a sparse event only when the v3 ranking also supplies at least moderate evidence. This preserves the complementary sparse signal without treating the channels as independent marginal tests.

## Finite development grid

All p-values are exact empirical ranks over denominator 129.

The complete candidate grid is fixed before the selector opens the SonotaCo 2025 development records:

- v3 primary rank `a` in `{2,3,4,5,6}`;
- fixed4 sparse rank `b` in `{2,3,4,5,6}`;
- v3 corroboration rank `c` in `{10,15,20,25,30,35,40}`;
- require `c > a`.

For a candidate `(a,b,c)`, report a detection iff:

`p_v3 <= a/129 OR (p_fixed4 <= b/129 AND p_v3 <= c/129)`.

There are 175 finite predeclared combinations before the `c > a` restriction; the full evaluated table is preserved.

## Development gates

A candidate is feasible on SonotaCo 2025 only if all of these hold:

- pooled held-out-negative FPR <= **0.052**;
- worst reporting-sector FPR <= **0.075**;
- k=4 recall >= frozen fixed4 recall at nominal alpha=.05;
- k=6 recall >= Brown-family recall at nominal alpha=.05 minus 0.03;
- k=8 recall >= Brown-family recall at nominal alpha=.05 minus 0.03;
- k=12 recall >= Brown-family recall at nominal alpha=.05 minus 0.03;
- all upstream benchmark integrity gates pass;
- all v3/fixed4 p-values remain on the exact denominator-129 grid.

The stricter 0.052 pooled-FPR development ceiling deliberately reserves headroom below the final 0.055 reporting cap after v4's marginal-OR transfer proved too close to the boundary. It is a new v5 robustness criterion, not a change to v4.

## Deterministic selection

Among feasible candidates, choose in this exact order:

1. largest **total recall slack** across the four recall gates;
2. lower pooled FPR;
3. lower worst-sector FPR;
4. smaller total rank complexity `a + b + c`;
5. smaller `a`, then smaller `b`, then smaller `c`.

Total recall slack is the sum of the nonnegative margins above the four feasibility recall thresholds. This favors a rule with headroom across stream strengths rather than merely the lowest development FPR, which was the weakness exposed by v4.

If no candidate is feasible, v5 fails and no thresholds are authorized for transfer.

## Claim boundary

v5 does not create a new continuous ranking. AUROC claims remain those of frozen v3. v5 is a binary decision architecture only.

A 2025 development pass is not validation. Any selected `(a,b,c)` must be frozen before being applied to another year. SonotaCo 2023, if rerun, is explicitly retrospective because its v4 outcome informed the v5 architecture. A separate corpus not used to define or select v5 is required for independent validation.
