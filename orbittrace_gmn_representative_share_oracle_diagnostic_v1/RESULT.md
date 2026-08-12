# OrbitTrace GMN representative-share oracle diagnostic v1 — binding result

## Scientific conclusion

The diagnostic decisively localizes the current #1194 gap to **prediction / representation separability**, not to the candidate universe, representative-share target, or frozen diversity operator.

When the already-frozen representative-share target is supplied as a perfect oracle score, the exact unchanged #1194 diversity operator reaches the known target-excluded GMN top-100 ceiling:

- recovered@25 = **25**
- recovered@50 = **50**
- recovered@100 = **100**
- recovered@500 = **242**
- top-100 dominant precision = **0.897219089102914**
- MRR = **0.023595698250011923**
- median first rank = **128.5**
- qualified matches = **256**

The deployable strict-OOF #1194 model remains 22/43/80/171 with precision 0.8075287489258385 and MRR 0.02016666446026534. Therefore the 80→100 gap is not an intrinsic ceiling of the frozen representative-share objective.

This is a truth-aware diagnostic only. Oracle scores are not deployable and do not authorize truth-conditioned ranking.

## Frozen provenance

- protocol-only freeze commit: `21bc2c54217bcbf87f201db0c3ba71cfb7b211c5`
- original implementation commit: `4881c693b1fe15c99ae01a00dad3b60c2182c9b8`
- first execution attempt: run `31616118967` — **technical no-result** only; the diagnostic reporting helper attempted `int(None)` for labels with no first rank, and no oracle result JSON was produced
- reporting-only null-handling repair commit: `bbbef712cf504545a143c8fad80cf1a5277d0841`
- repaired diagnostic source Git blob: `5a0b639aa77d4871135b5c666300591c8b987678`
- registered workflow/source pin commit: `d6ff48beade92df900fec623a18425b51d2c5a30`
- first technically valid binding run: `31616575384`
- binding job: `94180754234`
- binding artifact: `orbittrace-gmn-representative-share-oracle-diagnostic-v1`
- artifact ID: `9149562326`
- artifact digest: `sha256:888002334bc762579c67e3abcb3a127c79f8e6cfe3b2f22ed2a545888e9c1de1`

The technical repair changed only the reporting guard from converting every first-rank value to an integer to first excluding `None`. It did not change target construction, score vectors, diversity, family identities, truth semantics, parent model, OOF folds, or oracle evaluation.

## Exact parent reproduction

The exact #1194 strict-OOF parent reproduced before oracle interpretation:

- recovered@25: **22**
- recovered@50: **43**
- recovered@100: **80**
- recovered@500: **171**
- top-100 dominant precision: **0.8075287489258385**
- MRR: **0.02016666446026534**
- median first rank: **225.0**
- qualified matches: **256**
- order SHA-256: `a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592`

The exact #1194 scientific source Git blob remained `340f9d54b42ba2500652d7f0a74f22bbd3354f2e`.

## Representative-share oracle

The exact frozen #1194 representative-share target `y_share` was passed directly through the unchanged diversity operator (`lambda = 0.8`, `scale = 1.0`). No model was fit and no target or ranking parameter was changed.

Result:

- recovered@25: **25**
- recovered@50: **50**
- recovered@100: **100**
- recovered@500: **242**
- top-100 dominant precision: **0.897219089102914**
- MRR: **0.023595698250011923**
- median first rank: **128.5**
- qualified matches: **256**
- oracle order SHA-256: `09647a3980c3244300bb3a5ee0a6a96cff690ccfbd21e95549ad4f79a75c2d17`

Thus `representative_share_oracle_improves_at_100 = true` and `representative_share_oracle_reaches_known_100_at_100_ceiling = true`.

## Absolute-quality oracle control

The pre-existing #839 absolute-quality target `q_abs` was evaluated under the exact same unchanged diversity operator:

- recovered@25: **25**
- recovered@50: **50**
- recovered@100: **96**
- recovered@500: **230**
- top-100 dominant precision: **0.9079969107527794**
- MRR: **0.023317080984694344**
- median first rank: **135.5**
- qualified matches: **256**
- order SHA-256: `81e367b4f77d0349ac65f068e3531265b34db0c046ae82061eeac80caca1d331`

This is a control only. The representative-share oracle's 100@100 versus the absolute-quality oracle's 96@100 does not authorize target blending, target search, or any new truth-aware deployment rule.

## Top-100 decomposition

Without exposing shower identities:

- #1194 OOF distinct qualified labels in top 100: **80**
- representative-share oracle distinct qualified labels in top 100: **100**
- absolute-quality oracle distinct qualified labels in top 100: **96**
- #1194 / share-oracle top-100 family-ID overlap: **29**
- #1194 / share-oracle recovered-label overlap: **30**
- share-oracle-only recovered labels: **70**
- #1194-only recovered labels: **50**

The low family-ID and label overlap shows that the deployable OOF model is not merely misordering a few boundary candidates. Its first 100 differs substantially from the target-optimal ordering even though both use the same candidate universe, target definition, and diversity operator.

## Mechanistic implication

Three independent target-excluded GMN facts now align:

1. #838 showed the 4,504-family union admits 100 distinct qualified labels in the first 100 under a truth-aware ceiling construction.
2. The cross-generator consensus diagnostic showed a real high-purity duplicate relation, but its separately frozen spacing successor left #1194 recovery@25/@50/@100/@500 exactly unchanged. Duplicate crowding therefore is not the main early-budget limitation.
3. This oracle diagnostic shows the exact #1194 representative-share target itself reaches 100@100 when perfectly scored.

Therefore the strongest remaining development hypothesis is **representation / separability**: the current 34-dimensional family summary representation and/or its learnable mapping does not expose enough information to predict the frozen representative-share target accurately under strict whole-shower OOF evaluation.

This result does **not** by itself authorize an estimator swap. Many estimator/loss/ranking variants are already closed. A successor should only proceed after auditing existing representation-level experiments and must introduce genuinely new observable information or representation structure rather than another optimization rescue on the same 34D matrix.

## Prohibited rescue/search

Do not use this diagnostic to justify:

- oracle-guided family selection;
- target blending or target exponent/temperature changes;
- alternate diversity lambda/scale;
- target clipping/floors;
- top-k-specific truth rules;
- feature subsets chosen from oracle misses;
- post-result estimator grids;
- SonotaCo-guided representation design.

Any successor must be separately motivated from permitted target-excluded GMN evidence and frozen before its first valid outcome.

## Protected-data firewall

Binding execution preserved:

- protected solar-longitude exclusion `[20.0, 55.0]`;
- `sonotaco_2013_2014_access = false`;
- `sonotaco_feature_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- no target/diversity/threshold search and no successor selection occurred inside the diagnostic.
