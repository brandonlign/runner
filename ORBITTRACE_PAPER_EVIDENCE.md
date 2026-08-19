# OrbitTrace recurrent-EOM — final paper-facing evidence summary

## Bottom line

**Selected full-catalogue paper method: recurrent-EOM HDBSCAN v1.**

Exact selected kernel Git blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`.

The current paper has no remaining scientific-method blocker. The two previously unresolved paper-facing questions are now closed:

1. the literature comparison has been rerun with equal temporal information and passed all four panels; and
2. the separately frozen locked-RRF catalogue scan has completed its exact-ID reveal and independently recovered OrbitTrace under the preregistered recovery rule.

The authoritative structured values are in `ORBITTRACE_PAPER_EVIDENCE.json`; claim boundaries are in `ORBITTRACE_CLAIM_AUDIT.md`.

## 1. Target-excluded recurrent-EOM development

Binding GMN run `31827903547` returned:

`PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT`

Recurrent-EOM uses the same pooled events, GEO6 representation, HDBSCAN parameters, mutual-reachability hierarchy and condensed tree as ordinary HDBSCAN EOM. It changes only the EOM extraction stability: for each hierarchy node, normalized annual EOM contributions are computed and the recurrence-aware objective uses the minimum annual support across the two observing years.

The protected OrbitTrace interval `[20°,55°]` was removed before development and evaluation. OrbitTrace therefore could not select or tune recurrent-EOM.

The frozen GMN gate passed: recurrent-EOM improved the intended fixed-budget recovery/ranking criteria while preserving the preregistered no-regression conditions. It is not claimed to dominate ordinary HDBSCAN at every cutoff or catalogue-wide metric.

## 2. Final fair literature comparison — 4/4 PASS

### Why the benchmark was rerun

The earlier SonotaCo diagnostic compared pooled-2013+2014 recurrent-EOM output with literature comparators that had been generated independently by year. Shower truth was still sealed, so this was not truth leakage, but recurrent-EOM had more temporal context. That old literature-superiority interpretation is withdrawn.

### Equal-temporal-information design

PR #1356 gives every method the same pooled 2013+2014 label-free rows before truth:

- recurrent-EOM HDBSCAN v1;
- the frozen uncertainty-aware Sugar reconstruction, including the native unsupervised epsilon rule and 1,000 Gaussian uncertainty-clone catalogues; and
- the published-configuration catalogue-HDBSCAN implementation.

Complete outputs are frozen before year-specific shower truth is loaded. Each year is then evaluated with the same one-to-one Hungarian-F1 semantics and a candidate budget equal to the comparator's complete returned catalogue.

Pretruth SHA-256:

`4d7cefdc9adc9078115ea15d895885f0fecd7082a816ae491648ceecf83c7084`

Binding result commit:

`496c9370744fa2b9e1a001a67bcb0d6c31236357`

Exact verdict:

`PASS_TEMPORAL_FAIR_LITERATURE_4_OF_4`

| Comparator | Year | Budget | recurrent-EOM F1 / recovered | literature F1 / recovered | Result |
|---|---:|---:|---:|---:|---|
| frozen uncertainty-aware Sugar reconstruction | 2013 | 40 | **0.393771 / 24** | 0.272745 / 17 | PASS |
| frozen uncertainty-aware Sugar reconstruction | 2014 | 43 | **0.428024 / 24** | 0.293790 / 16 | PASS |
| published-config catalogue HDBSCAN | 2013 | 14 | **0.220475 / 13** | 0.202064 / 12 | PASS |
| published-config catalogue HDBSCAN | 2014 | 14 | **0.234838 / 12** | 0.209606 / 11 | PASS |

The HDBSCAN advantage is modest and the Sugar advantage is larger. All four frozen gates require strict macro-F1 superiority plus no recovered-shower loss, and all four pass.

**Supportable claim:** under the final equal-temporal-information pooled SonotaCo benchmark, recurrent-EOM outperformed the tested frozen Sugar and catalogue-HDBSCAN implementations on all four year/method panels.

**Boundary:** SonotaCo is exposed development/validation data, not pristine external validation. Do not convert the 4/4 benchmark result into a claim of universal cross-survey superiority.

## 3. Secondary target-excluded GMN literature characterization

Run `32156065072` remains valid as a secondary target-excluded GMN characterization and returned:

`PASS_RECURRENT_EOM_GMN_MATCHED_CAPACITY_LITERATURE_4_OF_4`

That audit compared recurrent-EOM with a deterministic published Sugar DBSCAN core and published-configuration catalogue HDBSCAN at identical complete catalogue capacity. Because the final fair SonotaCo benchmark has cleaner temporal-information parity and uses the uncertainty-aware Sugar reconstruction, it should be the primary literature-comparison result in the manuscript.

## 4. Blind target-free recovery of OrbitTrace

The fixed-4° lineage now supplies a genuine target-free catalogue recovery in addition to its older targeted test.

The blind scan run `31112651984` generated and sealed a complete ranking of **766 recurrent families** before the OrbitTrace canonical member table, target coordinates or reveal result were available to the ranking stage.

A separately frozen exact-ID reveal then ran in `32204257498` without changing the detector, ranking, family construction, matching rule, thresholds or gates.

Selected family: `G88cc88b1e28a`.

- rank: **46 / 766**;
- total family events: **39**;
- years represented: **4**;
- exact canonical overlap: **29 / 95**;
- precision: **0.7436**;
- canonical recall: **0.3053**;
- overlap by year: 2022 `5`, 2023 `4`, 2024 `0`, 2025 `15`, 2026 `5`.

Exact verdict:

`PARTIAL_LOCKED_RRF_ORBITTRACE_RECOVERY`

The result passes the rule frozen before reveal: rank <=100, at least 3 years, at least 12 exact canonical members, and at least 4 members in at least 2 years. It does not pass the stronger top-25 full tier because the family ranked 46th.

Reveal artifact `9348567823`; digest `sha256:a05f6d501af2dd1db70b5ecb027d28b9c47d34b838221ba7784dc62daa1cc666`.

**Supportable prose:** “a separately frozen target-free catalogue scan independently recovered OrbitTrace as a recurrent family.” When discussing the formal preregistered tier, state that it met the partial-recovery gate but not the stricter top-25 full tier.

No post-reveal reranking or method tuning is authorized.

## 5. Older targeted fixed-4° recovery

PR #153 / run `30927310565` remains a separate targeted local-background test. It returned `FULL_FROZEN_GHOSTSTREAM_RECOVERY` with all 14 frozen gates passing.

This is useful corroboration but should not be confused with the later blind locked-RRF catalogue recovery or the historical HDBSCAN discovery procedure.

## 6. Sparse-sample robustness

Fixed-scale native TopoModal remains a separate sample-size robustness experiment within GMN:

- ~0.7k scale: recovery `20 -> 31`, dominant precision `0.3530 -> 0.5887`;
- ~5.8k scale: recovery `94 -> 140`, dominant precision `0.3396 -> 0.5544`;
- no qualified-recovery loss across the 16 frozen bucket-year panels.

Dense-scale TopoModal/Pareto translations failed their frozen gates. TopoModal is therefore not the full-catalogue paper method and is not evidence of cross-survey generalization.

## 7. Candidate validation remains distinct from method validation

OrbitTrace itself has strong independent candidate-level evidence:

- 95 canonical GMN members across five consecutive confirmed years;
- untouched 2022/2023 historical confirmation;
- source-preserving activity and orbital nulls;
- 1,000 uncertainty-clone trials;
- 20,000 year/night bootstrap replicates;
- three disjoint geographic station groups;
- 81/81 specification settings;
- 11 SonotaCo matches passing the candidate-replication gates;
- 9 compatible CAMS matches that narrowly miss the fixed activity threshold;
- four supplementary EDMOND matches;
- no hard duplicate in the frozen MDC comparison; and
- the separate target-free locked-RRF recovery above.

These candidate-level results are stronger cross-network evidence for OrbitTrace than the method-level cross-survey evidence for recurrent-EOM.

## 8. Cross-survey method limitation

Recurrent-EOM has **not** established pristine cross-survey generalization:

- ASFN: frozen superiority gate negative;
- EFN: recurrence mechanism inactive before truth, labels unopened;
- SonotaCo: positive but exposed benchmark;
- AMOS: preregistered historically but never executed or opened; acquisition lane closed.

The manuscript should retain this limitation explicitly.

## Final paper claim hierarchy

The final manuscript may state that:

1. OrbitTrace was discovered blindly in GMN and is a recurrent late-April observational concentration / meteor-stream candidate.
2. The candidate survives untouched-year, null, uncertainty, resampling, geographic, specification and independent catalogue tests.
3. A separately frozen target-free catalogue scan independently recovered OrbitTrace at rank 46 of 766 with 29 exact canonical members across four years.
4. Target-excluded recurrent-EOM passed its ordinary-EOM GMN development gate.
5. Under the final equal-temporal-information pooled SonotaCo benchmark, recurrent-EOM outperformed the frozen Sugar and catalogue-HDBSCAN implementations on all four panels.
6. Fixed-scale native TopoModal improves sparse-sample robustness within GMN.
7. Pristine or universal cross-survey generalization of recurrent-EOM is not claimed.

## Final freeze

Scientific method development is closed for the current paper. No recurrent-EOM successor, density-sync rescue, locked-RRF reranking, dense TopoModal rescue, replacement survey, target-informed tuning or gate relaxation is authorized.

Remaining work is manuscript/submission consistency and layout QA only.
