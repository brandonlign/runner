# One-shot SonotaCo 2023 fixed-4° replacement independent replication

Status: frozen before any SonotaCo 2023 data row is decoded or any detector score, p-value, fold, support count, or scientific endpoint is computed.

## Scientific status

PR #136 passed the complete standalone SonotaCo 2025 development standard and froze the final methodology as the coverage-normalized Mondrian anchored nearest-three complete-link four-clique detector with solar-longitude separation scaled at exactly 4° per distance unit.

The originally reserved SonotaCo 2024 panel was prematurely opened by PR #134 before the required 2025 final benchmark passed. SonotaCo 2024 is therefore consumed and cannot be called the formal untouched confirmation. Its observed values are prohibited from altering this source, model, gates, or interpretation.

SonotaCo 2023 was selected before scientific access as the most recent pre-2024 annual panel. PR #141 found no prior 2023 exposure across 140 pre-existing runner refs or commit messages. PRs #142 and #144 inspected only the header and immutable member hash. PR #146 then derived the exact row count from opaque LF/quote-byte structure, decoded no data row, and produced the exact executable used here.

This is one replacement independent replication. It is not a new development panel, not a second chance to tune the method, and not a restoration of the originally preregistered 2024 confirmation.

## Exact frozen inputs

- official archive URL: `https://www.astro.sk/iaumdcDB/public/data/SNMv3/023a.zip`;
- archive SHA-256: `9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430`;
- science member: `023a/_U2_20230101_S.csv`;
- member SHA-256: `3f1cfedf59553568d6471e022ad032ec5ba71ce5287a24071d30bcc1e8bac685`;
- exact data rows: `47,087`;
- GMN–MDC mapping audit: workflow `30855193522`, `audit.json` SHA-256 `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`;
- exact repaired-source artifact: workflow `30920687116`, artifact `8896931940`, digest `sha256:1b86288b46f777e8c4e6b1797f228d2625de1692aec50fe2ada49ef5af6572fd`;
- parser source SHA-256: `9619dfc0b339b39d287833778769f12a643e2b0157fdcd6115cd9c40be528322`;
- confirmation source SHA-256: `bc2636005cc25da33e8accb6bdb70beea6ab900862cd1e6342a481395ac8f3e6`;
- confirmation payload SHA-256: `2b09fafcb8a2d7886cb2e0b1b90f2447580b308d755269addd500535f2f4da0f`;
- baseline source SHA-256: `7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50`;
- scorer source SHA-256: `f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8`;
- phase-scale source SHA-256: `e5cdb6eb8d07fdbcc5c29a4d02139fff86386e8aebde83717fdc7485acda265d`.

## Frozen method

The executable must preserve exactly:

- removal of solar longitude 20°–55° inclusive before any label token or non-solar feature is read and before all reservoirs, windows, scores, folds, and endpoints;
- exact 128-event episodes and ±10° activity neighborhoods;
- exact globally anchored 10° Mondrian bins;
- exact anchored nearest-three complete-link quartet search;
- fixed solar-longitude scale 4° per unit;
- inherited 2° radiant-longitude, 2° radiant-latitude, and 2 km/s speed scales;
- 128 calibration negatives and 64 independent test negatives per supported bin;
- four positive replicates at k in {4,6,8,12};
- five complex/parent folds;
- exact split, density, and DBSCAN comparators;
- exact seed prefixes embedded in the repaired source;
- conservative empirical rank p-values and alpha levels 0.05 and 0.01.

No alternate scale, selector, fusion, drift model, seed panel, threshold, calibration size, fallback year, source edit, or rerun is permitted.

## Frozen parser gates

The run fails closed unless every exact archive/member/mapping/schema/row-count gate passes, the blind interval is removed before label access, native SonotaCo label syntax and frozen mapping coverage each reach 90%, at least 30 supported native codes and 30 distinct labeled showers remain, and at least 10,000 sporadic events remain after ESV exclusion.

## Frozen scientific gates

The replacement replication passes only if all of the following hold:

- at least 20 supported 10° bins;
- at least 30 eligible showers;
- pooled FPR at alpha 0.05 / 0.01 no greater than 0.060 / 0.020;
- worst 60° reporting-sector FPR at alpha 0.05 no greater than 0.120;
- candidate weak AUROC at least 0.75;
- candidate AUROC within 0.03 of the strongest fixed comparator;
- candidate AUROC strictly exceeds density and DBSCAN;
- at least four of five fold AUROCs at least 0.70 and none below 0.65;
- k=4 recall at least 0.15 / 0.05 at alpha 0.05 / 0.01;
- k=6 recall at least 0.30 / 0.15;
- k=8 recall at least 0.45 / 0.25;
- recall monotonic through k=12 at both alpha levels.

Any failed gate is the final result for this replacement panel. No post-result repair, threshold change, older-year fallback, rerun, or methodological revision is authorized.

## Interpretation rule

A complete pass supports independent replication of the frozen fixed-4° methodology on an untouched annual SonotaCo panel, while preserving the disclosure that the originally reserved 2024 protocol was lost.

A failure must be reported as a failed replacement replication with its exact failure anatomy. It may not be averaged away with 2024 or 2025, and it may not trigger another panel or detector revision.

No result authorizes a GhostStream application or catalogue scan in this workflow.
