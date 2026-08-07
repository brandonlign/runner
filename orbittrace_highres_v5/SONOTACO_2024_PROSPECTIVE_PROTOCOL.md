# OrbitTrace v5 — SonotaCo 2024 prospective validation protocol

## Status before execution

This protocol is committed **before any OrbitTrace detector score or method-performance metric is computed on SonotaCo 2024**.

The only 2024 information already exposed is transport/schema metadata and the separately frozen score-free eligibility universe. The eligibility audit explicitly computed no fixed4 score, Brown-family wavelet coefficient, v3 score, v5 decision, AUROC, recall, or FPR.

This protocol authorizes **one scientific execution** of the frozen v5 architecture on that predeclared 2024 universe. A failed result must be preserved and cannot be followed by same-corpus retuning.

The first workflow attempt stopped in the pre-data source audit because the prospective branch did not contain the frozen Brown comparator file. The repair vendors the exact byte-identical frozen comparator with Git blob SHA `493fcc7f2d2cc75ee35acf17e142e7ce7c1e03e8`; no scientific method, parameter, gate, data, or 2024 result changed or was exposed by that repair.

## Frozen v5 architecture

No scientific parameter changes from the passing 2025+2023 development freeze:

- primary continuous score: frozen `orbittrace_multi_anchor_wavelet_energy_v3`;
- sparse score: frozen `orbittrace_fixed4`;
- source-preserving Mondrian calibration nulls per supported bin: **512**;
- v5 empirical denominator: **513**;
- primary decision: `p_v3 <= 20/513`;
- sparse decision: `p_fixed4 <= 10/513`;
- v5 detection: `(p_v3 <= 20/513) OR (p_fixed4 <= 10/513)`.

The complete development search is closed. No threshold search, scale search, weight search, calibration-size search, or model selection is allowed on 2024.

## Frozen 2024 universe

The prospective runner must reproduce the committed `SONOTACO_2024_ELIGIBILITY_FREEZE.json` exactly before accepting any result:

- parser source SHA-256: `502712f062d6bdc2a4a464106fd7e3fa944f6bee49317daae2950eac31f9082f`;
- supported bins: 33, exactly `[0,1,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35]`;
- eligible showers: 33, exactly the committed eligibility list;
- calibration episodes: **16,896**;
- held-out negative episodes: **2,112**;
- positive episodes: **528**;
- member counts: `4, 6, 8, 12`;
- positive replicates: `4`;
- five fixed folds.

Any universe mismatch invalidates the run before interpretation.

## Frozen predecessor comparison on 2024

The v5 calibration improvement must not move the literature baselines.

The prospective job therefore scores each calibration episode once and uses two nested calibration panels:

1. **v5 panel:** all 512 source-preserving calibration nulls per bin; v3 and fixed4 p-values use denominator 513;
2. **predecessor panel:** the **first 128 calibration nulls** per bin, indices `0..127`; Brown-family wavelet and fixed4 reference p-values use the exact conservative rank rule with denominator 129.

The first 128 nulls are not newly selected from 2024. They are the deterministic prefix of the already frozen calibration seed sequence. This reproduces the predecessor 128-null calibration architecture while allowing v5 to use the higher-resolution 512-null extension.

Nominal predecessor alpha is exactly `0.05`; because the denominator is 129 this corresponds automatically to the attainable conservative-rank grid without any manually chosen rank threshold.

Continuous-ranking AUROC is computed from raw scores and is independent of either calibration size.

## Preregistered prospective gates

The verdict is `PASS_V5_SONOTACO_2024_PROSPECTIVE_VALIDATION` only if **all** gates below pass:

1. every parser, source, eligibility, episode-count, and p-value-grid integrity check passes;
2. v3 weak-stream AUROC is **at least** Brown-family wavelet weak-stream AUROC on the same frozen 2024 weak-episode panel;
3. v5 pooled FPR <= 0.055 on the 2,112 frozen held-out negative episodes;
4. v5 worst-sector FPR <= 0.08;
5. v5 **k=4 recall** is at least the predecessor fixed4 k=4 recall computed with the first-128/denominator-129 calibration at nominal alpha 0.05;
6. v5 recall at **k=6/8/12** is, separately for each k, at least the predecessor Brown-family wavelet recall at nominal alpha 0.05 minus `0.03`;
7. v5 p-values lie exactly on the denominator-513 empirical grid and predecessor p-values lie exactly on the denominator-129 empirical grid;
8. the v5 decision remains exactly `(p_v3 <= 20/513) OR (p_fixed4 <= 10/513)`.

The FPR and recall gates are identical in meaning to development. The only prospective reference values not knowable in advance are the 2024 Brown/fixed4 outcomes themselves; their algorithms, calibration panel, alpha, and comparison formula are frozen here before scoring.

## Reporting

The result must preserve at minimum:

- v3, Brown, and fixed4 weak AUROCs;
- v3 minus Brown AUROC difference;
- v5 pooled and sector FPRs;
- v5 k=4/6/8/12 recall;
- predecessor fixed4 k=4 recall;
- predecessor Brown k=4/6/8/12 recall;
- every gate individually;
- complete held-out-negative and positive score/p-value records;
- immutable source/input hashes and workflow artifact provenance.

Passing authorizes promotion of v5 as the prospectively validated OrbitTrace sparse-episode detector. It does **not** by itself establish blind catalogue rediscovery or OrbitTrace target recovery; those remain separate catalogue/discovery claims.

No 2024 result may alter v3, fixed4, Brown, the 512/128 calibration panels, the 20/513 or 10/513 thresholds, the OR rule, or any gate above.