# OrbitTrace GMN member-scatter representation v1 — binding result

## Verdict

`FAIL_GMN_MEMBER_SCATTER_REPRESENTATION_V1`

This is a clean scientific failure of the sole preregistered 20-feature physical residual second-moment augmentation. It is not a technical failure. The exact #1194 parent reproduced, the 54D successor representation was constructed successfully, all five whole-shower OOF folds completed, the protected-data firewall remained intact, and the result artifact was uploaded successfully.

## Frozen provenance

- pre-outcome protocol freeze commit: `b167f039cf6a09e866e6cfd952171b8532859c08`
- protocol Git blob: `9e74bcda9d8c2d9a112ad1f05469e7697bf2fddd`
- frozen implementation commit: `9cc70b2963ddaa7a6cca6d3061b19b31035a09d6`
- implementation Git blob: `94310f14080a65ea847e290f30eb2180423ce856`
- execution-plumbing commit: `b3d1a8e9f2cf77806d421aeb95d9d2ff8c7a84bf`
- first technically valid binding run: `31617845783`
- binding job: `94185010039`
- binding artifact: `orbittrace-gmn-member-scatter-representation-v1`
- artifact ID: `9150086306`
- artifact digest: `sha256:a297a4e02f46043fb122b009540137a26ee49fdd680c2e675a74373ac8114f07`

## Sole scientific change

The exact #1194 34D feature matrix was augmented with 20 label-free member-morphology features: for each of 2022 and 2023, the ten unique upper-triangular entries of the 4×4 uncentered second moment of normalized physical event residuals about that family's frozen annual centroid.

No estimator, target, fold, sample weight, diversity parameter, candidate identity, family membership, or tie rule changed.

Hashes:

- exact parent 34D feature matrix SHA-256: `68de1b3e92a7cfcb9da557478a729a797fe51fc45dfbfc54ae7cd3c35b9acbf2`
- appended 20D scatter matrix SHA-256: `4b2a241debd4bb47af24468390be49026b29f93da406099bcca0beb4b2627730`
- complete 54D successor matrix SHA-256: `3438ce2d87b16e8d250cb8a259cd56880840f2070eefbd3c80f726fc69b507f9`

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

54D parent + member-scatter representation:

- recovered@25: **23**
- recovered@50: **45**
- recovered@100: **79**
- recovered@500: **168**
- top-100 dominant precision: **0.80764574399973**
- MRR: **0.019904366388279908**
- median first rank: **226.5**
- qualified matches: **256**
- order SHA-256: `e6173739ce6348cd242371667e487fe77a1a56040c629d289696278d50ff5838`

Gate results:

- recovered@100 > 80: **FAIL**
- recovered@50 >= 43: PASS
- recovered@25 >= 22: PASS
- recovered@500 >= 171: **FAIL**
- top-100 precision >= parent: PASS
- MRR >= parent: **FAIL**
- qualified matches == 256: PASS

No full successor model was frozen.

## Scientific interpretation

The directional second-order member morphology contains some real early-budget information: @25 improves by 1, @50 improves by 2, and top-100 precision increases slightly. But it does not improve the primary @100 objective and it worsens @500 recovery, MRR, and median first rank.

Therefore the exact raw physical residual second-moment augmentation is not a better successor to #1194. This result is consistent with the representative-share oracle diagnostic's conclusion that representation/separability remains the bottleneck, while showing that this particular second-order summary does not solve it.

The lane is closed exactly as preregistered. Do not rescue it with alternate covariance normalization, robust/shrunk covariance, eigenvalues/eigenvectors, trace/determinant/anisotropy ratios, different physical scales, marginal quantiles or higher moments, source-specific scatter features, feature subsets, estimator/hyperparameter changes, target changes/blends, diversity changes, parent-score fusion, or post-result feature selection.

A later representation successor must introduce a genuinely distinct observable/representation mechanism and be separately frozen before its first valid outcome.

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
