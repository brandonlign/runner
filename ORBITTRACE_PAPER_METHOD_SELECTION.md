# OrbitTrace paper-method selection

## Selected method

**Recurrent-EOM HDBSCAN v1** is the preferred OrbitTrace full-catalogue paper methodology.

Exact recurrent-EOM kernel Git blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

This selection rests on the frozen target-excluded GMN development result, the direct tie with the later density-synchronous refinement, and the final equal-temporal-information SonotaCo literature benchmark. The separately frozen fixed-4° detector and locked-RRF catalogue scan are candidate-recovery evidence, not inputs to recurrent-EOM selection.

## Target-excluded GMN development

Recurrent-EOM passed its frozen GMN 2022+2023 development gate in run `31827903547` (`PASS_RECURRENT_EOM_HDBSCAN_V1_GMN_DEVELOPMENT`). It changed only HDBSCAN EOM extraction on the unchanged pooled hierarchy and improved the preregistered fixed-budget recovery/ranking objective without using any event from the protected OrbitTrace interval `[20°,55°]`.

The later density-synchronous successor #1263 produced no gain over recurrent-EOM on the direct pooled SonotaCo benchmark. PR #1269 / run `31889652785` returned exact ties on all four established panels. The added criterion therefore did not justify its complexity, and recurrent-EOM is retained by parsimony.

## Final equal-temporal-information literature benchmark

An audit found that the earlier SonotaCo literature comparison was temporally asymmetric: recurrent-EOM used a pooled 2013+2014 hierarchy while the old Sugar/HDBSCAN comparator outputs had been generated independently by year. That old 4/4 literature result remains a historical diagnostic but is **not** used as the paper's fair superiority claim.

PR #1356 reran the comparison with equal temporal information. Before truth, recurrent-EOM, the frozen uncertainty-aware Sugar reconstruction and the published-configuration catalogue-HDBSCAN comparator all received the same pooled 2013+2014 label-free rows on each pairwise route. Complete outputs were frozen before year-specific shower truth was loaded. Evaluation then used the same one-to-one Hungarian-F1 semantics and a candidate budget equal to the comparator's complete returned catalogue.

Pretruth SHA-256:

`4d7cefdc9adc9078115ea15d895885f0fecd7082a816ae491648ceecf83c7084`

Binding result commit:

`496c9370744fa2b9e1a001a67bcb0d6c31236357`

Exact verdict:

`PASS_TEMPORAL_FAIR_LITERATURE_4_OF_4`

| Comparator route | Year | Budget | recurrent-EOM macro-F1 / recovered | literature macro-F1 / recovered |
|---|---:|---:|---:|---:|
| frozen uncertainty-aware Sugar reconstruction | 2013 | 40 | **0.393771 / 24** | 0.272745 / 17 |
| frozen uncertainty-aware Sugar reconstruction | 2014 | 43 | **0.428024 / 24** | 0.293790 / 16 |
| published-configuration catalogue HDBSCAN | 2013 | 14 | **0.220475 / 13** | 0.202064 / 12 |
| published-configuration catalogue HDBSCAN | 2014 | 14 | **0.234838 / 12** | 0.209606 / 11 |

All four panels require strict macro-F1 superiority plus no recovered-shower loss, and all four pass. The HDBSCAN gains are modest; the Sugar gains are larger.

SonotaCo is still an **EXPOSED DEVELOPMENT / VALIDATION BENCHMARK**, not pristine external validation. The supportable claim is therefore that recurrent-EOM outperformed these tested literature implementations under the final equal-temporal-information benchmark, not that recurrent-EOM is universally superior across meteor surveys.

## Secondary target-excluded GMN literature characterization

The earlier target-excluded GMN matched-capacity audit remains valid as secondary characterization. Run `32156065072` returned `PASS_RECURRENT_EOM_GMN_MATCHED_CAPACITY_LITERATURE_4_OF_4` against a deterministic published Sugar DBSCAN core and a published-configuration catalogue-HDBSCAN implementation at identical complete catalogue capacity.

This audit is not the final paper's primary literature comparison because the fair pooled SonotaCo benchmark provides a cleaner same-information comparison and, on the Sugar route, uses the frozen uncertainty-aware reconstruction rather than only the deterministic core.

## Separate target-free blind OrbitTrace recovery

The fixed-4° lineage now has two distinct candidate-recovery results.

First, PR #153 / run `30927310565` returned `FULL_FROZEN_GHOSTSTREAM_RECOVERY` in the already-described targeted local-background application. That remains targeted corroboration.

Second, a separate locked-RRF full-catalogue scan was executed with OrbitTrace target information unavailable during scanning and ranking. The scan run `31112651984` froze 766 recurrent families before exact canonical member IDs were opened. The later exact-ID reveal run `32204257498` identified family `G88cc88b1e28a` at rank **46/766**, with **39 total events**, **29 exact canonical OrbitTrace members**, **0.7436 precision**, **0.3053 canonical recall**, and matches in four years (2022: 5; 2023: 4; 2024: 0; 2025: 15; 2026: 5).

The frozen reveal verdict was:

`PARTIAL_LOCKED_RRF_ORBITTRACE_RECOVERY`

This passes the preregistered recovery rule (rank <=100, >=3 years, >=12 exact canonical members, >=4 members in >=2 years) but not the stricter top-25 full tier. In paper prose it is accurate to say that the target-free catalogue scan **independently recovered OrbitTrace**; when the formal tier is named, it must be described as the preregistered partial-recovery tier rather than full recovery.

Reveal artifact: `9348567823`; artifact ZIP SHA-256 `a05f6d501af2dd1db70b5ecb027d28b9c47d34b838221ba7784dc62daa1cc666`.

No detector, ranking, family construction, reveal rule, threshold or gate was changed after the result. This blind recovery must not be used to rerank or tune the fixed-4° lineage or recurrent-EOM.

## Separate sparse-sample robustness result

Fixed-scale native TopoModal remains the sparse/sample-size robustness result. Its frozen GMN stress panels materially improved qualified recovery and dominant precision at both ~0.7k and ~5.8k scales, with no qualified-recovery loss across the frozen bucket-year panels. Later dense-scale TopoModal/Pareto translations failed their frozen gates.

TopoModal is therefore **not** a replacement for recurrent-EOM at full catalogue scale and does not reopen method selection.

## Cross-survey boundary

Recurrent-EOM has not established pristine cross-survey generalization. ASFN was negative under its frozen superiority gate; EFN's recurrence mechanism was inactive before truth; SonotaCo is exposed. The historical AMOS preregistration was never executed and the acquisition lane is closed.

The paper may state that recurrent-EOM is supported by the target-excluded GMN development result and the fair exposed SonotaCo literature benchmark while explicitly withholding a universal or pristine cross-survey claim.

## Final decision and closure

Choose **recurrent-EOM HDBSCAN v1** as the full-catalogue paper method. Retain fixed-scale native TopoModal only for sparse/sample-size robustness. Retain the fixed-4° targeted test and locked-RRF blind scan only as separate OrbitTrace candidate-recovery evidence.

For the current paper, scientific method development is closed. Do not restart recurrent-EOM successors, density-sync variants, locked-RRF reranking, dense TopoModal rescue, external-dataset shopping, result-informed thresholds or post-target-reveal tuning.

The remaining work is manuscript consistency, figures/tables, submission files and layout QA.
