# OrbitTrace v29 — nested whole-shower tree-capacity ranking

## Status and scope

This is an exposed-SonotaCo development successor frozen after v24-v28 established a narrow ranking bottleneck. It does not change candidate generation, family membership, the 71-dimensional v22 label-free representation, the deterministic whole-shower grouping, diversity, v19 fusion, comparator semantics, or any protected-data boundary.

The post-result truth-aware oracle showing a winning nested top-9/top-11 ordering inside exact v19 top100 is diagnostic only. No oracle family ID, oracle rank, oracle membership quality, target value, or oracle ordering is an input to v29.

## Scientific hypothesis

v24's fixed #839 ExtraTrees regressor (`max_depth=4`, `min_samples_leaf=5`) systematically shrank several rare high-quality held-out showers toward the target bulk. v25 changed the loss and failed; v26/v28 added structural/background features and failed. v29 therefore tests one distinct hypothesis: **tree capacity should be selected inside each outer training split, rather than fixed globally, while the held-out shower remains completely absent from both fitting and capacity selection.**

## Immutable scientific inputs

Before truth, v29 consumes the exact pretruth-only 71D v22 route payload preserved in run `31424616547`, artifact `9076752673` (`orbittrace-v27-postmembership-feature-pretruth-freeze-id-bound-v5`, GitHub digest `sha256:2a0c57bbc1ecbde8459d13c6bba35f6a3a6d981757eec0619af2e0702410914e`). The route payloads must reproduce the frozen v23/v24 semantic identities for `features.npy`, `centroids.npy`, `family_memberships.json`, family order, and v19 order.

Truth and comparator summaries are restored only for the supervised exposed-development stage from the immutable v15 final literature artifact/run already used by v22-v28. SonotaCo 2013/2014 remains exposed development-only.

## Fixed outer architecture

Exactly v24 semantics are retained:

- one shared stacked Sugar+HDBSCAN development table;
- exact annual targets `F1_2013` and `F1_2014` against the unchanged combined recurrent best label;
- every fragment/near-miss tied to one known shower has group `SHOWER/<label>` across both routes;
- every negative family retains its deterministic negative group;
- exact deterministic five outer folds from the existing group hash;
- grouped sample weights from exact #839;
- annual predictions combine only as `min(pred_2013, pred_2014)`;
- exact #839 diversity order with lambda `0.8`, scale `1.0`;
- one equal rank-sum fusion with exact v19;
- exact #854-compatible equal-budget Hungarian F1 evaluator.

The outer held-out fold contributes no label, target, example, or model-selection statistic to its own prediction.

## Sole scientific change: nested capacity selection

Within each outer training split, exactly three ExtraTrees capacities are eligible. Every model begins as an exact `ranker.model()` clone, so all #839 settings other than the two listed capacity parameters remain unchanged.

1. `baseline_d4_l5`: `max_depth=4`, `min_samples_leaf=5`.
2. `medium_d8_l3`: `max_depth=8`, `min_samples_leaf=3`.
3. `high_unbounded_l2`: `max_depth=None`, `min_samples_leaf=2`.

There is no fourth model, model-class search, feature subset, random-seed search, year weight, target transform, learning-rate search, tree-count search, or post-result capacity interpolation.

For a given outer fold, each capacity is evaluated only on the outer-training groups by four-fold inner OOF: the four remaining original deterministic fold IDs act as inner validation folds. Each inner validation group is therefore predicted by models that saw no member of that group.

For each capacity, the two annual inner-OOF predictions are combined by the unchanged minimum. Capacity selection uses one fixed **full-list group-level NDCG**:

- for each strict group, predicted group score = maximum combined inner-OOF prediction among its families;
- true group relevance = maximum `min(F1_2013,F1_2014)` among its families;
- groups are ranked by predicted score, stable group ID for ties;
- gain is `2^relevance - 1`;
- discount is `1/log2(rank+2)`;
- NDCG is DCG divided by the corresponding ideal DCG over the full outer-training group list.

This criterion has no top-k, comparator budget, F1 threshold, route weight, or oracle family input. It is intended to select capacity for ranking rare strong groups rather than minimize absolute squared error over the near-zero bulk.

Highest inner NDCG wins. An exact tie resolves toward lower capacity in the fixed order `baseline_d4_l5`, then `medium_d8_l3`, then `high_unbounded_l2`. The selected capacity is then refit separately for 2013 and 2014 on all outer-training examples and predicts only the untouched outer fold.

The five outer predictions together define one and only one v29 OOF quality vector. Capacity choices are diagnostics, not separately evaluated final variants.

## Evaluation and decision

Exactly two v29 outputs are scored:

1. `nested_capacity_oof_quality`;
2. `nested_capacity_oof_v19_rank_sum`.

Exact v19 is an identity control. v24's fixed-capacity OOF path is also reproduced as a scientific control and must reproduce all four exact v24 panel metrics before v29 is accepted.

PASS requires one single v29 output to beat the corresponding literature comparator in **all four** SonotaCo route/year panels: strictly larger macro-F1 and recovered-F1>0.5 count at least equal in every panel. Variant selection is the existing lexicographic panel-win / worst-ratio / mean-ratio rule; no result-dependent rescue is allowed.

If PASS occurs, a later full model may be frozen only after selecting one capacity by the same five-fold group-level NDCG procedure on the complete exposed development table. Its in-sample score is not promotion evidence. Protected cross-survey validation requires a separate candidate-specific preregistered protocol.

If FAIL occurs, this exact nested capacity library, NDCG rule, and v19 fusion are a permanent no-go. No depth/leaf grid expansion is authorized from the result.

## Firewalls

- no MAARSY scientific event/truth access;
- no DMS scientific event/truth access;
- no OrbitTrace target information;
- no target-region event access;
- no use of the post-result oracle order as a feature, target, tie-break, model library choice, or evaluation shortcut;
- no second search after the result.
