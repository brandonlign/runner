# OrbitTrace v60 robust-MAD local geometry v1

## Scientific role

This is a separately frozen **exposed-development successor** after binding v59 failure. It does not rescue any closed v56–v59 target, group-distance, block-weight, recurrence-label, fusion, or annual-combiner architecture.

The parent remains exact v31. v60 changes exactly one quantity inside v31's strict-OOF local geometry: the **fold-local feature scaling rule** used before ordinary Euclidean distance.

The motivation is outcome-free geometry observed during frozen v59 execution: under the inherited v31 fold split and fold mean/std scaling, the mean nearest-training distance was approximately 2.44–2.82 in folds 0–3 but 81.85 in fold 4, with one zero-variance feature. This does not authorize changing folds, dropping features, clipping observations, or fitting a new metric. It motivates one canonical robust scale test that leaves the representation, folds, labels, metric and ranking architecture intact.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, not external validation.

## Immutable parent

v60 must first reproduce exact v31 unchanged:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDB 2013 `0.14888037368183737 / 9`;
- HDB 2014 `0.15198123772301594 / 9`.

Exact parent source blob:

`917e3cd6f9310ca1282e0efa58ed0924d03ed4da`.

Everything below remains exact v31 unless explicitly replaced by the sole v60 scaling rule:

- immutable #950 candidate universe, memberships, 71D features and centroids;
- stacked Sugar+HDB development table;
- deterministic strict whole-shower five-fold OOF grouping across routes;
- exact annual fixed-label family F1 targets and annual positivity `F1_y > 0.5`;
- separate 2013 and 2014 annual heads;
- ordinary Euclidean distance across all 71 scaled dimensions;
- k=`1` nearest annual-positive and annual-nonpositive reference;
- margin `d_nonpositive - d_positive`;
- annual combiner `min(margin_2013, margin_2014)`;
- exact #839 diversity `lambda=0.8`, `scale=1.0` and tie semantics;
- immutable exact-v19 order and one equal rank-sum;
- fixed candidate memberships, literature budgets and evaluator;
- same rule on Sugar and HDB.

## Sole v60 scientific change

Within each outer OOF fold, scaling parameters are computed **only from fold-training rows** and applied to both fold-training and held-out rows.

For every one of the 71 feature coordinates j:

1. `center_j = median(X_train[:, j])`;
2. `MAD_j = median(abs(X_train[:, j] - center_j))`;
3. primary robust scale `s_j = 1.4826 * MAD_j`.

The constant `1.4826` is frozen as the standard Gaussian-consistency factor for the median absolute deviation. It is not estimated or searched.

A deterministic fallback exists only for degenerate coordinates:

- if `s_j == 0`, replace it by the fold-training population standard deviation `std_j` (`ddof=0`);
- if that fallback is also zero, replace it by exactly `1.0`.

The scaled coordinate is

`Z_j = (X_j - center_j) / s_j`.

No epsilon, clipping, winsorization, percentile truncation, quantile transform, rank transform, IQR scale, Huber scale, alternate MAD constant, interpolation with ordinary z-scoring, per-route scale, per-year scale, per-block scale, or learned metric is allowed.

After this scaling, v60 executes exact v31 annual k=1 positive/nonpositive Euclidean geometry, exact annual `min`, exact diversity and exact-v19 rank-sum.

## Evaluation

The same v60 rule applies to both routes. The implementation must reproduce all four exact v31 parent controls first, then evaluate exactly one v60 order per route.

PASS requires all four frozen literature pair gates:

`candidate_macro_f1 > literature_macro_f1`

and

`candidate_recovered_f1_gt_0_5 >= literature_recovered_f1_gt_0_5`

for Sugar 2013, Sugar 2014, HDB 2013 and HDB 2014.

The first technically valid result is binding.

## No rescue

If v60 fails, permanently close this exact robust fold-scaling architecture. Do not retry with:

- IQR or percentile scaling;
- a different MAD consistency constant;
- median/MAD plus clipping or winsorization;
- quantile/rank/Gaussian transforms;
- Huber or other M-estimator scaling;
- interpolation or blending with mean/std scaling;
- route/year/block-specific scaling;
- feature dropping or zero-MAD feature removal;
- epsilon/pseudocount scale floors;
- k or metric changes;
- threshold/annual-combiner/diversity/fusion changes;
- top-k/rank-window/budget exceptions;
- boundary/oracle identity corrections;
- post-result second searches.

Any future successor must be independently motivated and separately frozen.

## Explicit prohibitions

No fold search/change, reference-pool change, classifier/regressor, target transformation, block weighting, feature subset, robust-scale search, clipping, metric search, k search, threshold search, annual-combiner search, diversity search, fusion search, source-quota selection, component/quality/topology/cross-route rescue, v19/local fusion rescue, boundary identity, oracle identity, literature-budget-specific rule, or post-result tuning.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every output must assert these conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.