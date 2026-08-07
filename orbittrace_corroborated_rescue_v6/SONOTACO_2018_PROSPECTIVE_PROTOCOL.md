# OrbitTrace v6 — SonotaCo 2018 prospective validation protocol

## Status before execution

This protocol is committed **before any OrbitTrace detector score or method-performance metric is computed on SonotaCo 2018**.

Before this stage, 2018 access was limited to a transport-only audit and a separately frozen score-free eligibility audit. Those stages computed no fixed4 score, Brown-family wavelet coefficient, v3 score, v6 decision, empirical detector p-value, AUROC, recall, or FPR.

This protocol authorizes **one scientific execution** of the frozen v6 architecture on the committed 2018 eligibility universe. A failed result must be preserved and cannot be followed by same-corpus retuning.

## Frozen v6 architecture

No scientific parameter changes from the passing 2025+2023+2024 v6 development freeze:

- primary continuous score: frozen `orbittrace_multi_anchor_wavelet_energy_v3`;
- sparse score: frozen `orbittrace_fixed4`;
- source-preserving calibration nulls per supported bin: **512**;
- v6 empirical denominator: **513**;
- primary decision: `p_v3 <= 17/513`;
- sparse rescue condition: `p_fixed4 <= 15/513`;
- corroboration condition: `p_v3 <= 122/513`;
- v6 detection:

`(p_v3 <= 17/513) OR ((p_fixed4 <= 15/513) AND (p_v3 <= 122/513))`.

No threshold search, corroboration search, calibration-size search, score change, or model selection is allowed on 2018.

## Frozen 2018 universe

The prospective runner must reproduce `SONOTACO_2018_ELIGIBILITY_FREEZE.json` exactly before accepting any result:

- parser source SHA-256: `7293fe0191f98c8b87fcb56347a0c44a634d95face0477b60c299a06bb5cb92f`;
- supported bins: 33, exactly `[0,1,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35]`;
- eligible showers: 33, exactly the committed eligibility list;
- calibration episodes: **16,896**;
- held-out negative episodes: **2,112**;
- positive episodes: **528**;
- member counts: `4, 6, 8, 12`;
- positive replicates: `4`;
- five fixed folds.

Any universe mismatch invalidates the run before interpretation.

## Frozen predecessor comparison on 2018

The v6 calibration/decision architecture must not move the predecessor comparison standard.

Each calibration episode is scored once and two nested calibration panels are used:

1. **v6 panel:** all 512 source-preserving calibration nulls per bin; v3 and fixed4 p-values use denominator 513;
2. **predecessor panel:** the **first 128 calibration nulls** per bin, indices `0..127`; Brown-family wavelet and fixed4 reference p-values use denominator 129 with the exact conservative rank rule.

The first 128 nulls are the deterministic prefix of the frozen calibration seed sequence, not a panel selected after seeing 2018 results. Predecessor nominal alpha is exactly `0.05`.

Continuous-ranking AUROC uses raw scores and is independent of calibration size.

## Preregistered prospective gates

The verdict is `PASS_V6_SONOTACO_2018_PROSPECTIVE_VALIDATION` only if **all** gates pass:

1. every parser, source, eligibility, episode-count, calibration-prefix, and p-value-grid integrity check passes;
2. v3 weak-stream AUROC is at least Brown-family wavelet weak-stream AUROC on the same frozen 2018 weak-episode panel;
3. v6 pooled FPR <= 0.055 on the 2,112 frozen held-out negative episodes;
4. v6 worst-sector FPR <= 0.08;
5. v6 **k=4 recall** is at least predecessor fixed4 k=4 recall computed from the first-128/denominator-129 calibration at nominal alpha 0.05;
6. v6 recall at **k=6/8/12** is, separately, at least predecessor Brown-family wavelet recall at nominal alpha 0.05 minus `0.03`;
7. v6 p-values lie exactly on the denominator-513 empirical grid and predecessor p-values lie exactly on the denominator-129 empirical grid;
8. the v6 decision remains exactly `(p_v3 <= 17/513) OR ((p_fixed4 <= 15/513) AND (p_v3 <= 122/513))`.

## Reporting and claim boundary

The result must preserve v3/Brown/fixed4 weak AUROCs, v3-minus-Brown AUROC, v6 pooled/sector FPRs, v6 k=4/6/8/12 recall, predecessor fixed4 and Brown references, every gate individually, complete held-out-negative and positive records, and immutable source/input provenance.

A pass promotes v6 as the prospectively validated OrbitTrace **sparse-episode detector** under this common benchmark. It does **not** by itself establish blind catalogue rediscovery or OrbitTrace target recovery; catalogue-scale discovery remains a separate test.

No 2018 result may alter v3, fixed4, Brown, the 512/128 calibration panels, ranks 17/15/122, the corroborated-rescue rule, or any gate above.
