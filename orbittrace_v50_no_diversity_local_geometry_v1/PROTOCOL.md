# OrbitTrace v50 no-diversity local-geometry v1

## Scientific role

Separately frozen exposed-development successor after the binding v49 2/4 failure.

The accumulated HDB evidence now brackets auxiliary reranking: broad quality/component promotions (v42/v44/v48) degrade the tiny HDB prefixes, while conservative shared-support and adjacent-dominance rules (v43/v49) do not change the relevant HDB endpoints. The residual v31 error was already localized by #1050/#1053/#1071 to only a very small number of HDB substitutions. A remaining inherited operation inside v31 has never been separately tested: after strict-OOF local-geometry scoring, v31 applies the #839 centroid-diversity penalty (`lambda=0.8`, scale `1.0`) before the frozen v19 rank-sum.

v50 changes exactly that one operation.

- immutable #950 memberships/features remain unchanged;
- exact v31 strict whole-shower 5-fold OOF construction remains unchanged;
- exact 71D fold-training z-score remains unchanged;
- exact ordinary Euclidean k=1 distances to annual-positive and annual-nonpositive references remain unchanged;
- exact annual margin `d_nonpositive - d_positive` remains unchanged;
- exact annual combiner `min(margin_2013, margin_2014)` remains unchanged;
- **the centroid-diversity penalty is removed**;
- the local order is therefore the frozen #839 `diversity_order` implementation evaluated with zero diversity penalty, preserving its exact score/tie semantics while making centroid distance irrelevant;
- exact v19 order and one equal rank-sum with that local order remain unchanged;
- Sugar and HDB are governed by the same v50 rule; there is no route-specific exception.

This is not a search over diversity coefficients. Only the scientifically distinct endpoint “no diversity penalty” is evaluated. The old `lambda=0.8` v31 parent is reproduced separately as a control in the same frozen run.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, not external validation.

## Immutable inputs and parent

Use only the same immutable inputs as v31:

1. #950 pretruth payload, artifact `9074742322`, ZIP SHA-256 `d940fa255804866f14bc34b1d72467d17adddcfb7d82c954ed5a8d1668aa307a`;
2. immutable #839 ranker source from run `31344632499`, source SHA-256 `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`;
3. immutable exposed SonotaCo truth artifact `9069505548`, ZIP SHA-256 `cdea3297c234b0b3a8f09c2208649c8607bb3e9a9004d299f6dcc18536ebb797`;
4. frozen v31 scientific source blob `917e3cd6f9310ca1282e0efa58ed0924d03ed4da`.

Before accepting v50, reproduce the exact four v31 controls:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDB 2013 `0.14888037368183737 / 9`;
- HDB 2014 `0.15198123772301594 / 9`.

Any mismatch fails closed.

## Sole v50 evaluation

After exact v31 reproduction, rerun the identical v31 pipeline with one monkeypatch only: when v31 calls immutable #839 `diversity_order(scores, centroids, 0.8, 1.0, tie)`, delegate to that same immutable function as `diversity_order(scores, centroids, 0.0, 1.0, tie)`.

No other code path, score, tie rank, centroid, fold, label, feature, annual combiner, v19 order, rank fusion, budget, or evaluator changes.

The wrapper must record the resulting complete Sugar and HDB fused-order SHA-256 identities and all four literature panels.

PASS requires all four existing literature pair gates to win. The first technically valid v50 result is binding.

## Explicit prohibitions

No nonzero diversity coefficient other than the frozen v31 parent control, no coefficient search, no alternate diversity scale, no route/year-specific diversity, no second diversity pass, no centroid metric change, no tie-rule change, no local-score transform, no k/metric/scaling/feature/threshold/annual-combiner change, no v19 replacement, no fusion-weight/rank-algebra search, no top-k/rank-window/budget-specific rule, no candidate/membership change, no quality/component/cross-route rescue, no oracle identity, and no post-result second search.

If v50 fails, the exact no-diversity endpoint is permanently closed; do not rescue it with intermediate diversity coefficients or alternate scales.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every result must assert these conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.
