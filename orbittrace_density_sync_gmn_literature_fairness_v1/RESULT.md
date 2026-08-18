# Density-synchronous recurrent-EOM — matched-capacity literature fairness result

## 🟢 Binding characterization result

`PASS_DENSITY_SYNC_GMN_MATCHED_CAPACITY_LITERATURE_4_OF_4`

The first technically valid execution completed successfully in GitHub Actions run `32193713209` from activation PR #1349.

- source-audit run: `32193670394` — PASS
- binding result artifact: `9345176417`
- artifact name: `orbittrace-density-sync-gmn-literature-fairness-v1-binding`
- artifact digest: `sha256:880cf49a658cfd34433527517c72d46674fd22de80cf47fa47a5255afbda3c34`
- binding result JSON SHA-256: `b4f4aea785ea309f66dda31f60f54f0a798b88f036493c456e9b89d4b7bf6619`
- pairwise gates passed: **4 / 4**

The audit used the immutable density-synchronous GMN catalogue from binding run `31852836840` (`prelabel efce0617...`, `result ca6aeed2...`) and the already-sealed direct literature comparator outputs from run `32152924956`. No density-sync membership, rank, method parameter, literature comparator, capacity rule, panel, truth metric, or gate was changed.

## Exact matched-capacity panels

A pairwise win required both strict macro-F1 superiority and no loss in recovered showers with assigned F1 > 0.5 at exactly the comparator's complete catalogue capacity.

### Published-configuration catalogue HDBSCAN 2025

**GMN 2022 — K = 74**

- density-sync macro-F1: `0.16040268706433455`
- HDBSCAN macro-F1: `0.11783144148783989`
- density-sync recovered: `69`
- HDBSCAN recovered: `43`
- verdict: PASS

**GMN 2023 — K = 88**

- density-sync macro-F1: `0.18852678235632633`
- HDBSCAN macro-F1: `0.13235618973750005`
- density-sync recovered: `80`
- HDBSCAN recovered: `57`
- verdict: PASS

### Deterministic published Sugar-2017 DBSCAN core

**GMN 2022 — K = 525**

- density-sync macro-F1: `0.41023649241770205`
- Sugar macro-F1: `0.15607673680944167`
- density-sync recovered: `159`
- Sugar recovered: `51`
- verdict: PASS

**GMN 2023 — K = 751**

- density-sync macro-F1: `0.43458443527625645`
- Sugar macro-F1: `0.18674791207442026`
- density-sync recovered: `169`
- Sugar recovered: `59`
- verdict: PASS

## Interpretation

This result directly supports matched-capacity superiority of the exact frozen density-synchronous recurrent-EOM catalogue to the **tested** published-configuration HDBSCAN-2025 and deterministic Sugar-2017-core implementations on target-excluded GMN 2022/2023.

It is deliberately not phrased as universal superiority to every meteor-stream method. In particular:

- the Sugar panel represents its deterministic published DBSCAN core, not the full uncertainty-resampling pipeline;
- the result is retrospective characterization of a method frozen before these literature outcomes, not a new method-selection round;
- it remains development-survey evidence, not cross-survey external validation;
- the historical pristine ASFN negative result remains binding;
- untouched AMOS 2023/2024 remains the sole planned pristine final external test.

The 2025 HDBSCAN stream-identification paper is the most directly comparable recent unsupervised catalogue-scale stream-identification method found in the current literature review. More recent 2026 meteor machine-learning work located in the review focuses on meteoroid physical/compositional classification rather than unsupervised meteor-stream discovery, while 2025 meteor-cluster DBSCAN work targets seconds-scale fragmentation clusters rather than recurring meteor showers.

## Firewall

No OrbitTrace target information/event, SonotaCo scientific data, AMOS event-level data, ASFN/EFN event-level data, MAARSY, or DMS scientific data were accessed. Inclusive `[20.0,55.0]` remained excluded from GMN. No method selection changed and no post-result parameter search was performed.
