# OrbitTrace GMN MST bottleneck topology v1 — binding result

## Verdict

`FAIL_GMN_MST_BOTTLENECK_TOPOLOGY_V1`

This is a clean scientific failure of the sole preregistered two-feature MST bottleneck-topology augmentation. The exact #1194 parent reproduced, the 36D successor was constructed, all five whole-shower OOF folds completed, the firewall/provenance checks passed, and the binding artifact uploaded.

## Frozen provenance

- protocol Git blob: `69fedaa7d26c96aa75b7af17e4b3a4deb149f6ba`
- workflow/execution head: `cda3b1cf8367ea806d2f76615a8e1f93c54b69cd`
- first technically valid binding run: `31641846380`
- binding artifact ID: `9159251525`
- artifact digest: `sha256:e213b630828395f082879b9ebb98b62a653642565a5bd016661e2e8cc870946a`
- result JSON SHA-256: `df85e5e9dacd8efa4a6e2b92eb8fec0f9aa80f207fafce20052b0d75d1e2c243`

## Exact parent reproduction

#1194 representative-share OOF parent:

- recovered@25: **22**
- recovered@50: **43**
- recovered@100: **80**
- recovered@500: **171**
- top-100 dominant precision: **0.8075287489258385**
- MRR: **0.02016666446026534**
- median first rank: **225.0**
- qualified matches: **256**
- order SHA-256: `a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592`

## Binding successor outcome

36D parent + annual MST largest-edge / total-tree-length features:

- recovered@25: **22** — PASS
- recovered@50: **45** — PASS
- recovered@100: **80** — **FAIL** (`>80` required)
- recovered@500: **172** — PASS
- top-100 dominant precision: **0.8075287489258385** — PASS
- MRR: **0.02010925471036058** — **FAIL**
- median first rank: **222.5**
- qualified matches: **256** — PASS

The successor therefore failed the primary @100 gate and the MRR non-worsening gate. Improvements at @50/@500 and median first rank cannot rescue the binding failure.

## Mechanistic interpretation

The topology statistic was nondegenerate in both years (2022 median `0.39434836953071933`, 2023 median `0.39135446724442957`) and changed the final ranking, so this was not a no-op. However, simple single-bridge dominance did not recover any additional qualified label in the top 100. Combined with prior member-scatter and cross-year energy-distance failures, low-dimensional summaries of within-family member-cloud shape/connectivity remain insufficient to realize the representative-share parent's remaining headroom.

## Permanent closure

The exact MST-bottleneck topology augmentation is permanently rejected. Do not rescue it with total/mean/median/quantile MST edges, second-largest-edge variants, entropy/Gini/CV, size/radial/covariance normalizations, thresholded cut counts, radius/k searches, persistence vectorizations selected from this outcome, higher-dimensional homology selected from this outcome, alternate linkage, mutual-reachability/core-distance/HDBSCAN trees, source/year rules, combinations with failed geometry features, model/target/fold/weight/diversity changes, or post-result topology-statistic search.

Any future successor must introduce a genuinely distinct observable or mechanism and be separately frozen before first outcome.

## Protected-data firewall

Binding execution preserved:

- protected solar-longitude exclusion `[20.0,55.0]`;
- `sonotaco_2013_2014_access = false`;
- `sonotaco_feature_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`.
