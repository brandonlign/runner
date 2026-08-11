# OrbitTrace v56 block-balanced local geometry v1

## Scientific role

This is a separately frozen **exposed-development successor** after the binding v55 failure. It is independent of the now-closed v19/local fusion-algebra line.

The parent remains exact v31. v56 changes exactly one scientific quantity inside v31's strict-OOF local geometry: the distance used to the same annual-positive and annual-nonpositive training references.

The motivation is structural and predates v56 outcome access. The immutable v22/#950 71-dimensional representation is already partitioned into four frozen semantic blocks:

- raw #839 family features: dimensions `[0,34)`, 34D;
- relative noncategorical #839 features: `[34,64)`, 30D;
- rank percentiles: `[64,67)`, 3D;
- consensus graph: `[67,71)`, 4D.

Ordinary Euclidean distance gives total block influence proportional to block dimensionality after per-feature z-scoring. The earlier #1028 feature-block attribution diagnostic explicitly used these exact four pre-existing blocks and did **not** select a feature subset, block weight, block-specific nearest reference, successor score, rank, or literature result. No prior exact block-balanced/RMS geometry successor exists in the repository.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, not external validation.

## Immutable parent

v56 must first reproduce exact v31 unchanged under the same immutable inputs:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDB 2013 `0.14888037368183737 / 9`;
- HDB 2014 `0.15198123772301594 / 9`.

Exact parent source blob:

`917e3cd6f9310ca1282e0efa58ed0924d03ed4da`.

All of these v31 properties remain fixed:

- exact immutable #950 candidate universe and memberships;
- exact immutable 71D features and centroids;
- same cross-route stacked training table;
- same deterministic strict whole-shower five-fold OOF grouping;
- same per-fold training mean and population-standard-deviation z-score, with zero std replaced by 1.0;
- same annual positive criterion `annual_f1 > 0.5`;
- same k=1 nearest annual-positive and nearest annual-nonpositive references;
- same local margin `d_nonpositive - d_positive`;
- same annual combiner `min(margin_2013, margin_2014)`;
- same #839 diversity `lambda=0.8`, `scale=1.0`, and tie semantics;
- same immutable exact-v19 order and one equal rank-sum;
- same literature budgets and exact evaluator;
- same rule on Sugar and HDB.

## Sole v56 scientific change

Let `z` be a held-out fold-standardized 71D feature vector and `r` a fold-training reference vector. For each frozen block `b`, define

`MSE_b(z,r) = mean_{j in block b} (z_j - r_j)^2`.

The sole v56 distance is

`d_v56(z,r) = sqrt((71 / 4) * [MSE_raw839 + MSE_relative_noncat839 + MSE_rank_percentiles + MSE_consensus_graph])`.

Equivalently, each of the four already-frozen semantic blocks contributes exactly `71/4 = 17.75` effective dimensions to squared distance regardless of its raw dimension count.

The factor `71/4` is not selected from data. It is the unique natural scale-preserving constant under the frozen four-block partition: if every block has the same mean squared standardized difference `m`, ordinary 71D Euclidean has squared distance `71*m`, and v56 also has squared distance `(71/4)*(4m)=71*m`. This avoids silently changing the global score scale relative to the inherited fixed diversity penalty.

No block is dropped. No block-specific coefficient is searched. No learned metric, whitening, covariance estimate, ridge, shrinkage, epsilon, exponent, normalization alternative, route-specific block rule, year-specific block rule, or block-specific nearest-reference identity is allowed.

For each annual head and held-out candidate, v56 computes this distance to **every** training-positive reference and every training-nonpositive reference, then retains k=1 exactly as v31.

## Evaluation

After exact v31 parent reproduction, evaluate exactly one v56 order per route under the unchanged pipeline:

1. fold-training z-score;
2. v56 block-balanced k=1 positive/nonpositive distances;
3. annual margin `d_nonpositive-d_positive`;
4. annual `min`;
5. exact #839 diversity `0.8/1.0`;
6. one equal rank-sum with exact v19;
7. exact frozen literature evaluator.

PASS requires all four literature pair gates:

`candidate_macro_f1 > literature_macro_f1`

and

`candidate_recovered_f1_gt_0_5 >= literature_recovered_f1_gt_0_5`

for Sugar 2013, Sugar 2014, HDB 2013, and HDB 2014.

The first technically valid result is binding.

## No rescue

If v56 fails, permanently close this exact block-balanced-distance architecture. Do not rescue it with:

- unequal block weights;
- dropping or combining blocks;
- dimension-proportional/interpolated block weighting;
- alternative global scale constants;
- blockwise L1/Linf/cosine/Mahalanobis distances;
- block-specific k;
- route/year-specific weighting;
- feature subset selection;
- fusion/diversity changes;
- thresholds/top-k/rank windows/budget exceptions;
- identity corrections;
- post-result second searches.

Any future successor must have a distinct independently motivated mechanism.

## Explicit prohibitions

No v19/local fusion-algebra rescue, v19-only rank, optimistic/minimax interpolation, component/quality/topology/cross-route rescue, block-weight search, block subset search, metric grid, k search, scaling search, annual combiner search, diversity search, fusion search, source-quota selection, literature-budget-specific rule, boundary identity, oracle identity, or post-result tuning.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every output must assert these conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.