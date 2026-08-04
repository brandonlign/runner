# SonotaCo 2023 fixed-4° replacement independent replication

Status: frozen after PR #146 passed and before any SonotaCo 2023 data row is decoded or detector score is computed.

## Scientific status

The exact fixed-4° coverage-normalized Mondrian anchored four-clique detector was frozen after its standalone SonotaCo 2025 final-development pass in PR #136. SonotaCo 2024 was subsequently exposed by a procedurally premature parallel workflow and is not a valid untouched confirmation panel.

PRs #141, #142, and #146 established SonotaCo 2023 as a previously unreferenced replacement panel, verified its exact archive/member/header structure, and generated an exact year-adapted confirmation wrapper. This run is therefore a **replacement independent replication**, not the originally preregistered 2024 confirmation.

## Exact immutable inputs

- source-repair workflow: `30920687116`;
- source-repair artifact: `8896931940`;
- artifact digest: `sha256:1b86288b46f777e8c4e6b1797f228d2625de1692aec50fe2ada49ef5af6572fd`;
- parser source SHA-256: `9619dfc0b339b39d287833778769f12a643e2b0157fdcd6115cd9c40be528322`;
- confirmation payload SHA-256: `2b09fafcb8a2d7886cb2e0b1b90f2447580b308d755269addd500535f2f4da0f`;
- decoded confirmation source SHA-256: `bc2636005cc25da33e8accb6bdb70beea6ab900862cd1e6342a481395ac8f3e6`;
- source-repair JSON SHA-256: `882c21f2ac48689ab7a0d7a990496f7e055ab571b10c6f00bb63d8a18f8f7b3f`;
- official archive: `023a.zip`, SHA-256 `9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430`;
- science member: `023a/_U2_20230101_S.csv`, SHA-256 `3f1cfedf59553568d6471e022ad032ec5ba71ce5287a24071d30bcc1e8bac685`;
- exact data-row count: 47,087;
- GMN-MDC mapping audit SHA-256: `f8ba2446dce96d69652727092189903c40493e2fe741eb746f7fb5181edea778`.

The execution must retrieve the exact PR #146 artifact, verify every listed file/source hash, and verify the exact inherited baseline, scorer, and phase-scale sources before archive access.

## Frozen method and boundaries

The run preserves unchanged:

- fixed solar-longitude scale 4° per normalized unit;
- exact four-dimensional coverage-normalized complete-link clique score;
- exact parser/native-label mapping and quality filters;
- removal of solar longitude 20°–55° inclusive before any label, reservoir, window, score, fold, or endpoint;
- 128-event windows, ±10° neighborhoods, anchored 10° Mondrian bins;
- exact support, calibration, negative, and positive seed prefixes with the 2023 corpus/year identity;
- 128 calibration negatives and 64 test negatives per supported bin;
- exact positive replicates, complex-held-out folds, fixed comparators, alpha levels, and every confirmation gate.

No scale, parser rule, label rule, source hash, row count, seed, calibration size, threshold, comparator, fold, endpoint, or gate may change after this run begins.

## Frozen decision rule

The replacement replication passes only if every parser and scientific gate encoded in exact confirmation source SHA-256 `bc2636005cc25da33e8accb6bdb70beea6ab900862cd1e6342a481395ac8f3e6` passes:

- at least 20 supported bins and 30 eligible showers;
- pooled FPR ≤ 0.060 / 0.020 at alpha 0.05 / 0.01;
- worst 60° reporting-sector FPR ≤ 0.120 at alpha 0.05;
- weak AUROC ≥ 0.75, within 0.03 of the strongest comparator, and greater than density and DBSCAN;
- at least four folds with AUROC ≥ 0.70 and none below 0.65;
- recall at alpha 0.05 ≥ 0.15 / 0.30 / 0.45 for k=4/6/8;
- recall at alpha 0.01 ≥ 0.05 / 0.15 / 0.25 for k=4/6/8;
- monotonic recall through k=12 at both alpha levels;
- all exact parser, archive/member, row-count, schema, label, support, and blindness gates.

Any failed gate is a final negative replacement-replication result. No repair, reseeding, threshold change, or detector tuning is authorized afterward.

GhostStream remains fully blinded. No GhostStream value and no SonotaCo 2024 artifact or endpoint may be accessed or used.
