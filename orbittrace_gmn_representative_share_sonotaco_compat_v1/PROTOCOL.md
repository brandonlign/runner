# OrbitTrace GMN representative-share SonotaCo compatibility v1

## Scientific role

This is a **single frozen SonotaCo 2013/2014 compatibility/generalization benchmark** of a method that was developed, selected, and fully model-frozen on target-excluded GMN 2022/2023 under the binding governance rule #1190.

It is not external validation: SonotaCo 2013/2014 is historically exposed development data. The scientific purpose is only to ask whether the independently GMN-selected representative-share ranking architecture transfers to the already-established SonotaCo literature benchmark without any SonotaCo-driven adaptation.

No SonotaCo outcome, label identity, literature result, budget boundary, v31 residual diagnosis, #1191 source-density result, or other post-closure SonotaCo information was used to choose the model, target, features, diversity rule, route handling, or deployment order.

The first technically valid result is binding. Regardless of PASS/FAIL, this exact benchmark must not be used to tune or select a follow-up SonotaCo method.

## Frozen GMN method authorization

Authoritative GMN development is PR #1194:

- run `31506465267`;
- artifact `9107360445`;
- artifact digest `sha256:b22688c4516c903553d34306d18ff04d6fc6ea10ed489b844a2d5d7a4cd08960`;
- binding result JSON SHA-256 `862ecbe4ffb30e4f1a26692d4ab1b13e7a632ec2b88bc571adfc8181244459c2`;
- full-model-freeze JSON SHA-256 `749d40fd8786b3f09270b098c4d96607bb5f6dd8972b6a389f9b22f629cd15fc`;
- frozen ExtraTreesRegressor model SHA-256 `acae7fa4b4702e8d3f823defb5f2b3a3e2922b12c3bb07269b6e354316a558cb`;
- frozen 34D GMN training feature SHA-256 `5d215c5562c0ccce967d81ff0a087ca83b1afda95a269888d2219ef669d198d1`;
- frozen representative-share target SHA-256 `4433b443030a568f9d5f6ddceab2077e9d78e50497f7ce2473bad5c113f8ab39`;
- frozen grouped-weight SHA-256 `4ee439f0f04c9763a3dcc1527be66681496ea730df369f3c2f1815c9ef4a67f6`.

The binding GMN result improved exact #839 from `75/40/22` recovered at ranks `100/50/25` to `80/43/22`, top-100 precision from `0.7645689180574315` to `0.8075287489258385`, and MRR from `0.019037817654898162` to `0.02016666446026534`. This GMN PASS is the sole authorization for the present benchmark.

No retraining on SonotaCo is allowed.

## Immutable SonotaCo pretruth representation

Use immutable #950 pretruth payload only:

- artifact `9074742322`;
- artifact digest `sha256:d940fa255804866f14bc34b1d72467d17adddcfb7d82c954ed5a8d1668aa307a`;
- Sugar family universe = `267`;
- HDBSCAN family universe = `229`;
- feature dimension = `71`;
- frozen feature blocks exactly `raw_839=34`, `relative_noncat_839=30`, `rank_percentiles=3`, `consensus_graph=4`.

The sole model input is the first `34` columns, the immutable `raw_839` block. No later 37 features are supplied to the model. No source feature is dropped or altered; the model receives exactly the 34D schema it was trained on.

For each route, use the immutable #950:

- family IDs;
- `features.npy` first 34 columns;
- `centroids.npy`;
- `tie_rank`;
- final `family_memberships.json` only for post-freeze evaluation.

No candidate generation, membership change, feature reconstruction, route-specific feature rule, feature normalization, calibration, score transform, or source quota is allowed.

## Exact deployment rule

For each route independently:

1. compute raw model score `s_i = frozen_GMN_model.predict(raw_839_features_i)`;
2. apply the exact #839 complete diversity order with:
   - lambda = `0.8`;
   - scale = `1.0`;
   - exact #839 centroid distance;
   - exact immutable `tie_rank`/family-ID tiebreak;
   - no family deletion and complete backfill;
3. the resulting complete route order is the sole benchmark order.

There is no v19 fusion, v31 local geometry, route mixing, source normalization, source quota, component transfer, second diversity pass, threshold, top-k intervention, budget-specific correction, or score blend.

## Complete truth-blind order commitments

The exact frozen GMN model and immutable #950 pretruth payload have already been combined **without SonotaCo truth** to determine the complete orders. The benchmark workflow must reproduce these before downloading exposed truth:

### Sugar

- score-array SHA-256: `51270f33c1a689a638a44d534df1bccebc29a149345bce7096d09b517313dc83`;
- complete 267-family order SHA-256: `ab60a11644ac5518ac686e44adacd039a8428d9b29c56a24d6ca3764b93a9b93`.

### HDBSCAN

- score-array SHA-256: `dfcf711a7d61ad05aeb4e4417a9e3ea4786bccad7c91a7ed46b4f951842aab01`;
- complete 229-family order SHA-256: `b9d1fcf75238e09ef3df766fb9eb296e4151a34ace6271b48a101adc5248c2b9`.

These hashes are outcome-free structural consequences and are immutable. Any mismatch fails closed before truth.

## Truth-access barrier

The workflow sequence is mandatory:

1. verify frozen protocol/source/workflow and #839 source;
2. restore and verify the frozen GMN model artifact;
3. restore and verify immutable #950 pretruth payload;
4. generate complete Sugar/HDB model scores and diversity orders;
5. reproduce all four frozen score/order hashes above;
6. write the complete pretruth order freeze and hash it;
7. **only then** download the immutable exposed SonotaCo truth artifact;
8. evaluate the already-frozen orders.

Truth artifact:

- artifact `9069505548`;
- digest `sha256:cdea3297c234b0b3a8f09c2208649c8607bb3e9a9004d299f6dcc18536ebb797`.

No truth-aware branch of the code may alter scores or orders.

## Evaluation gate

Use the unchanged literature evaluator and frozen comparator budgets from the immutable truth/evaluation artifact.

PASS requires all four pair gates:

`candidate_macro_f1 > literature_macro_f1`

and

`candidate_recovered_f1_gt_0_5 >= literature_recovered_f1_gt_0_5`

for:

- Sugar 2013;
- Sugar 2014;
- HDBSCAN 2013;
- HDBSCAN 2014.

The first technically valid outcome is binding.

## No rescue

After this result, do not retry this SonotaCo benchmark with:

- v19 or v31 fusion;
- alternate diversity lambda/scale;
- no-diversity order;
- source-blind/source-normalized features;
- source quotas or route-specific source handling;
- score calibration/standardization/ranking/percentiles;
- top-k/rank-window/budget-specific corrections;
- alternate candidate subsets or memberships;
- feature subsets or later #950 blocks;
- HDB-only or Sugar-only exceptions;
- boundary/oracle identities;
- threshold/model/feature/weight/target changes;
- any second SonotaCo search based on this result.

Any future method must return to non-SonotaCo development and independently satisfy #1190 before another benchmark view.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. OrbitTrace target information and target-region events remain inaccessible. MAARSY and DMS remain inaccessible. SonotaCo 2013/2014 is `EXPOSED_DEVELOPMENT_ONLY`, never pristine validation.