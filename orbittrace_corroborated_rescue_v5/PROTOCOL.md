# OrbitTrace corroborated sparse rescue — v5

## Status and ancestry

v5 is a separately named post-v4 development stage. It begins only after the frozen v4 SonotaCo 2023 transfer failure was recorded.

The continuous primary ranking remains **exactly frozen v3 multi-anchor wavelet energy**. The sparse channel remains **exactly frozen fixed4**. v5 changes only how their already calibrated empirical p-values are combined into a binary reporting decision.

No v1-v4 result, v3 score, fixed4 score, Brown-family comparator, catalogue result, or blind-recovery record may be modified.

Because the 2023 v4 result had already been observed before v5 was designed, SonotaCo 2023 cannot serve as independent validation for v5. It is retained only as a labelled post-development retrospective transfer. v5 parameter selection used SonotaCo 2025 development records only.

## Structural change

v4 used an unconditional union of marginal thresholds:

`v3 strong OR fixed4 strong`.

That transferred poorly because fixed4-only rescue can add background hits while the conservative v3 cutoff loses moderate-stream recall.

v5 uses a **corroborated rescue**:

`v3 primary OR (fixed4 sparse AND v3 corroboration)`.

The fixed4 channel can therefore rescue a sparse event only when the v3 ranking also supplies at least moderate evidence. This preserves the complementary sparse signal without treating the channels as independent marginal tests.

## Finite development grid

All p-values are exact empirical ranks over denominator 129.

The complete candidate grid was fixed before the selector opened the SonotaCo 2025 development records:

- v3 primary rank `a` in `{2,3,4,5,6}`;
- fixed4 sparse rank `b` in `{2,3,4,5,6}`;
- v3 corroboration rank `c` in `{10,15,20,25,30,35,40}`;
- require `c > a`.

For a candidate `(a,b,c)`, report a detection iff:

`p_v3 <= a/129 OR (p_fixed4 <= b/129 AND p_v3 <= c/129)`.

The complete 175-cell table was preserved.

## Development gates

A candidate was feasible on SonotaCo 2025 only if all of these held:

- pooled held-out-negative FPR <= **0.052**;
- worst reporting-sector FPR <= **0.075**;
- k=4 recall >= frozen fixed4 recall at nominal alpha=.05;
- k=6 recall >= Brown-family recall at nominal alpha=.05 minus 0.03;
- k=8 recall >= Brown-family recall at nominal alpha=.05 minus 0.03;
- k=12 recall >= Brown-family recall at nominal alpha=.05 minus 0.03;
- all upstream benchmark integrity gates passed;
- all v3/fixed4 p-values remained on the exact denominator-129 grid.

The stricter 0.052 pooled-FPR development ceiling deliberately reserves headroom below the final 0.055 reporting cap after v4's marginal-OR transfer proved too close to the boundary. It is a new v5 robustness criterion, not a change to v4.

## Deterministic selection

Among feasible candidates, selection was fixed in this exact order:

1. largest **total recall slack** across the four recall gates;
2. lower pooled FPR;
3. lower worst-sector FPR;
4. smaller total rank complexity `a + b + c`;
5. smaller `a`, then smaller `b`, then smaller `c`.

Total recall slack is the sum of the nonnegative margins above the four feasibility recall thresholds.

## Frozen development selection

The authoritative first selector run is workflow `31147868124`, job `92771084720`, artifact `8982153140`, artifact SHA-256 `82310fb42d4e44bdf686c7b98fa7d55c7d5df56add91c13b1eb85bccdf2bbca3`.

Verdict: `PASS_V5_DEVELOPMENT_SELECTION`.

Exactly three of 175 candidates were feasible. The deterministic selector chose:

- `a = 4`;
- `b = 3`;
- `c = 40`;
- denominator `129`.

The frozen reporting decision is therefore:

`p_v3 <= 4/129 OR (p_fixed4 <= 3/129 AND p_v3 <= 40/129)`.

On SonotaCo 2025 development it produced pooled FPR `0.050781`, worst-sector FPR `0.065104`, and k=4/6/8/12 recall `0.154412 / 0.588235 / 0.845588 / 0.948529`. These integer ranks are final for v5 and may not change from any later result.

## SonotaCo 2023 retrospective check

After freezing v5, the exact rule was applied once to the previously generated 2023 v3/fixed4 record artifact. This is explicitly **retrospective**, because the earlier v4 2023 failure motivated the v5 decision architecture.

Workflow `31147965595` produced `PASS_V5_2023_RETROSPECTIVE_TRANSFER`: pooled FPR `0.050189`, worst-sector FPR `0.075521`, and recall `0.201220 / 0.548780 / 0.780488 / 0.926829`. This supports the structural rationale but is not independent validation.

## SonotaCo 2020 post-selection transfer

SonotaCo 2020 is the next independent **post-selection year-level transfer**. Its archive and Brown/fixed4 outcomes were scored previously by an older, separately frozen study, so it must not be described as an untouched archive. However:

- SonotaCo 2020 was not supplied to the v5 selector;
- SonotaCo 2020 did not motivate the v5 architecture;
- no v3 score or v5 decision has been evaluated on SonotaCo 2020 before this frozen stage;
- the v5 `(4,3,40)` ranks are already immutable before the 2020 v3 computation begins.

The transfer must reconstruct the exact audited 2020 episode universe and scientific runner used by the prior successful study, extend that runner only by computing the frozen v3 score/p-value alongside the existing fixed4 and Brown-family channels, and then apply the frozen v5 rule. The old fixed4, Brown, and old dual-channel calculations must remain unchanged and serve as integrity references.

### 2020 frozen input and runner provenance

- prior successful 2020 source head: `70defb3d84e2124dd0e33f279955723e5e2bd756`;
- audited scientific runner SHA-256: `db310cbe83a4653e3cf4479e60e5d0554ae9b5474e47c55d5bbfcb714970f0c7`;
- prior runner-source audit artifact: `8972146681`, SHA-256 `d9088e6804c271e7e33cd6dc54f3d784cc9fe3a0453aa858d13a71da2a68dc5f`;
- archive `020a.zip`, SHA-256 `429c3a4556236c037051ecba2d5ecbe921a0a6865cac47df6f47ba2d44f43abc`;
- calibration episodes: `4224` = 33 bins × 128;
- held-out negatives: `2112` = 33 bins × 64;
- positives: `576` = 36 showers × 4 k-values × 4 replicates;
- calibration denominator: `129`.

### 2020 pass gates

The post-selection transfer passes only if every condition below holds without any threshold or source change:

- all original audited 2020 runner execution/integrity gates pass;
- exact counts remain 4,224 calibration episodes, 2,112 held-out negatives, and 576 positives with 144 positives at each k in `{4,6,8,12}`;
- v3/fixed4 empirical p-values remain exactly on the denominator-129 grid;
- the frozen v5 decision module passes all self-tests and exact ranks `(4,3,40)`;
- v3 weak-stream AUROC is at least the Brown-family weak-stream AUROC on the same 2020 universe;
- pooled v5 held-out-negative FPR <= **0.055**;
- worst reporting-sector v5 FPR <= **0.08**;
- v5 k=4 recall >= fixed4 nominal-alpha=.05 k=4 recall on the same 2020 universe;
- v5 k=6 recall >= Brown-family nominal-alpha=.05 k=6 recall minus `0.03`;
- v5 k=8 recall >= Brown-family nominal-alpha=.05 k=8 recall minus `0.03`;
- v5 k=12 recall >= Brown-family nominal-alpha=.05 k=12 recall minus `0.03`.

A failed 2020 transfer is preserved as a failure and does not authorize retuning v5. A pass supports cross-year transfer of the episode-level architecture but still does not establish blind catalogue rediscovery or historical discovery provenance.

## Claim boundary

v5 does not create a new continuous ranking. AUROC claims remain those of frozen v3. v5 is a binary decision architecture only.

Neither the 2023 retrospective pass nor a 2020 transfer pass may be represented as the historical OrbitTrace discovery. Catalogue-scale candidate generation, recurrence/family construction, target exclusion, and any later OrbitTrace application remain separate stages that require their own frozen protocols.
