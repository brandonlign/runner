# OrbitTrace GMN cross-year energy-distance representation v1 — binding result

## Verdict

`FAIL_GMN_CROSSYEAR_ENERGY_DISTANCE_V1`

This is a clean scientific failure of the sole preregistered one-feature cross-year empirical energy-distance augmentation. It is not a technical failure. The exact #1194 parent reproduced, the 35D successor was constructed successfully, all five strict whole-shower OOF folds completed, all provenance/firewall assertions passed, and the binding artifact uploaded successfully.

## Frozen provenance

- pre-outcome protocol freeze commit: `d2136e68f97f867a6b8784c156c88ee26d779268`
- protocol Git blob: `98593aa6cd888363a7874aee732323e64b2e0999`
- frozen implementation commit: `1c808e8ab28e26ff3e7c951b5f30f2f754026d9b`
- implementation Git blob: `bea22e0e11654275e4783f8d39e8ecd716cb9211`
- execution-plumbing commit: `9f0f58fe45a5a136da77f525a659273f0f4c570e`
- first technically valid binding run: `31618745520`
- binding job: `94187961310`
- binding artifact: `orbittrace-gmn-crossyear-energy-distance-v1`
- artifact ID: `9150433804`
- artifact digest: `sha256:2faa7421dae1a1e0e713724d65e9e4bbaf3b4faea1a150b96e02ee06723e2e90`

## Sole scientific change

The exact #1194 34D feature matrix was augmented with one label-free scalar: the standard empirical multivariate energy-distance V-statistic between each family's complete 2022 and 2023 member-residual distributions after centering each year on that family's frozen annual centroid.

Residual coordinates were exactly the preregistered physical normalized coordinates:

- circular solar-longitude residual / 10 degrees;
- circular Sun-centered ecliptic-longitude residual / 4 degrees;
- ecliptic-latitude residual / 4 degrees;
- log(vg_event/vg_centroid) / log(1.10).

No bandwidth, radius, matching, optimal transport, kernel, coordinatewise variant, normalization, target/model/fold/weight/diversity change, family membership change, or feature search was used.

Energy feature:

- SHA-256: `3049c3e4d1cbae67bc684321c5d05a7f9c045dc602b3e96121d764f7b99700ec`
- minimum: `0.002500747270152112`
- median: `0.0855506074035236`
- maximum: `0.8127476602873838`
- complete 35D successor matrix SHA-256: `987f28843aa2cdd39fc05adae03f3254cb43a4b2d83a494ddb5232288310c2ad`

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

35D parent + cross-year energy-distance representation:

- recovered@25: **21**
- recovered@50: **44**
- recovered@100: **80**
- recovered@500: **169**
- top-100 dominant precision: **0.8053177613963475**
- MRR: **0.020001861937395986**
- median first rank: **238.0**
- qualified matches: **256**
- successor order SHA-256: `2d54dbbc40e837befb65bb2ff83a9e6cdae9a2e67b0c2a37597da49367bbb8bc`

Gate results:

- recovered@100 > 80: **FAIL**
- recovered@50 >= 43: PASS
- recovered@25 >= 22: **FAIL**
- recovered@500 >= 171: **FAIL**
- top-100 precision >= parent: **FAIL**
- MRR >= parent: **FAIL**
- qualified matches == 256: PASS

No full successor model was frozen.

## Scientific interpretation

The complete cross-year distribution-shape discrepancy carries a small amount of ranking information—the successor gains one recovered label at @50—but it does not improve the primary @100 objective and worsens @25, @500, precision, MRR, and median first rank.

Combined with the preceding member-scatter failure, this says the representative-share oracle's demonstrated 80→100 headroom is not recovered by simply adding either directional second moments or a global year-to-year distribution discrepancy to the current 34D family summaries. The representation/separability bottleneck remains, but low-order/global member-distribution summaries are not sufficient.

This exact lane is permanently closed. Do not rescue it with coordinatewise energy distances, alternate norms or powered distances, square-root/normalized/bias-corrected variants, MMD/kernel features, Wasserstein/optimal-transport variants selected from this result, matching-radius features, within-year dispersion additions, member-scatter combinations/fusion, source-specific distribution features, feature subsets/interactions, estimator/hyperparameter changes, target/diversity changes, or post-result parameter searches.

A later successor must introduce a genuinely distinct observable or representation mechanism and be separately frozen before first outcome.

## Protected-data firewall

Binding execution preserved:

- protected solar-longitude exclusion `[20.0, 55.0]`;
- `sonotaco_2013_2014_access = false`;
- `sonotaco_feature_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- no representation search, feature selection, or post-result second search occurred.
