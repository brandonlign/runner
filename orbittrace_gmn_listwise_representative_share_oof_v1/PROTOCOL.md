# OrbitTrace GMN listwise representative-share OOF v1

## Scientific role

This is a **target-excluded GMN 2022/2023 method-development experiment only** under the binding post-v60 governance rule. It is motivated entirely by GMN evidence and must not access or use SonotaCo 2013/2014 outcomes, comparator identities, budgets, ranks, or any other exposed SonotaCo information in method definition or selection.

The protected OrbitTrace solar-longitude interval 20°–55° remains excluded before candidate generation, labels, folds, features, targets, scoring, and evaluation. OrbitTrace target information and target-region events remain inaccessible. MAARSY and DMS remain scientifically inaccessible.

## Motivation fixed before outcome

Exact #839 established a 4,504-family target-excluded GMN union with a 100/100 fixed-universe truth-aware ceiling but recovered 75 showers at rank 100. PR #1194 then addressed the independently documented fragmentation problem by replacing absolute family F1 with a strict-shower **representative-share target**; that GMN-only experiment passed at 80 recovered showers at rank 100 while keeping the same pointwise ExtraTrees squared-error regression architecture.

Thus a GMN-only gap remains after target-mass balancing: a pointwise squared-error learner predicts each family independently even though the scientific endpoint is a catalogue **ordering**. Pairwise preference objectives have already been tried elsewhere and are not reopened here. This experiment changes the loss/objective class once: it learns a single listwise score function by matching the complete training-fold ranking distribution induced by the already-frozen representative-share target.

## Immutable universe and controls

Use the exact #839 / #1194 target-excluded GMN 2022/2023 union:

- 226 hard families;
- 1,075 P19-soft families;
- 3,203 P20-soft families;
- 4,504 total families;
- exact 34D #839 family features;
- exact #839 eligible-label and family-truth definitions;
- exact deterministic five-fold strict whole-shower grouping, including all near-miss fragments associated with the same known shower;
- exact candidate memberships, centroids, tie order, and monotone GMN evaluator;
- exact #839 diversity order with lambda `0.8`, scale `1.0`, complete backfill and no family deletion.

The implementation must reproduce both frozen OOF controls before evaluating the new candidate.

### Exact #839 quality/diversity control

- recovered@25 = 22
- recovered@50 = 40
- recovered@100 = 75
- recovered@500 = 159
- qualified matches = 256
- top-100 dominant precision = `0.7645689180574315`
- MRR = `0.019037817654898162`

### Exact #1194 representative-share control

- recovered@25 = 22
- recovered@50 = 43
- recovered@100 = 80
- recovered@500 = 171
- qualified matches = 256
- top-100 dominant precision = `0.8075287489258385`
- MRR = `0.02016666446026534`

The exact #1194 representative-share target is reused unchanged. If `q_i` is the exact #839 absolute positive-family F1 and `G` is its strict known-shower group, then

`r_i = q_i / sum_{j in G} q_j`

for recoverable shower groups and `r_i = 0` otherwise. Every recoverable strict shower group therefore contributes exactly one unit of target mass. No target modification is permitted.

## Sole scientific change: listwise softmax cross-entropy

Replace only the pointwise ExtraTrees regression fit used for the representative-share candidate with one deterministic **linear listwise softmax model**.

For each OOF fold:

1. Fit per-feature arithmetic mean and population standard deviation on the training rows only. Replace an exactly zero standard deviation by 1. No clipping, robust scaling, rank transform, feature deletion, or feature weighting is allowed.
2. Standardize the exact 34 features with those training-only statistics.
3. Let `p_i = r_i / sum_train(r)` over all training candidates. Because each recoverable shower contributes unit representative-share mass, `p` is the normalized strict-shower target distribution for that training list.
4. Use one linear score `s_i = x_i^T beta`, with **no intercept**.
5. Fit `beta` from an all-zero initialization by minimizing the full-list cross-entropy

   `L(beta) = -sum_i p_i log softmax(s)_i`

   using SciPy `minimize(method='L-BFGS-B', jac=True)` with frozen numerical settings `maxiter=10000`, `ftol=1e-12`, `gtol=1e-8`, and no bounds.
6. There is **no L1/L2 regularization**, temperature, margin, pair sampling, negative sampling, class weight, target exponent, or hyperparameter.
7. To put held-out scores from different folds on a common parameter-free scale, compute the training partition function `logZ_train = logsumexp(s_train)` after fitting and score each held-out family as `s_test - logZ_train`. This is the log relative mass the held-out candidate would have against that fold's complete training reference list; no held-out label enters it.
8. Pool the five held-out score vectors, then apply the exact frozen #839 diversity order once with lambda `0.8`, scale `1.0` and the exact tie order.

Every strict shower group must be wholly absent from the training set used to score that group. Optimization must report successful convergence and finite objective/gradient/scores in every fold. A numerical failure before a complete candidate order is produced is a technical no-result, not a scientific failure.

## Frozen GMN promotion gate

The exact #839 and #1194 controls must reproduce first. The new listwise candidate is evaluated exactly once.

The candidate PASS requires **all** of the following relative to the stronger #1194 representative-share parent:

- recovered@100 **> 80**;
- recovered@50 **>= 43**;
- recovered@25 **>= 22**;
- recovered@500 **>= 171**;
- top-100 dominant precision **>= `0.8075287489258385`**;
- MRR **>= `0.02016666446026534`**;
- qualified matches **== 256**.

This deliberately requires a strict top-100 gain with no regression on the frozen secondary metrics. No SonotaCo result can enter the decision.

## Full-model freeze after PASS only

Only if the GMN gate passes, fit one full linear listwise model on all 4,504 target-excluded GMN families using the exact same objective and numerical settings. Freeze:

- the exact 34D feature matrix hash and feature-name hash;
- the exact representative-share target hash;
- full-data scaler mean/std;
- fitted coefficient vector;
- full-data training partition `logZ`;
- coefficient/scaler payload hash;
- exact deployment diversity lambda `0.8`, scale `1.0`.

A later external/exposed compatibility benchmark, if separately authorized, must use that exact frozen model without retraining or selection among alternatives.

## No rescue

Whether PASS or FAIL, this v1 defines exactly one listwise architecture. Do not use its result to search or retry:

- L1/L2/elastic-net strength;
- temperature or target exponent;
- intercept on/off;
- alternate optimizer/tolerance/iteration budget;
- nonlinear basis, interactions, feature subset, source quota, or source-specific model;
- ListMLE/Plackett-Luce variant, pairwise hybrid, negative sampling, or margin loss;
- alternate fold-score calibration/percentile transform;
- alternate diversity lambda/scale or fusion with #839/#1194/Fisher/other ranks;
- budget-specific reranking;
- SonotaCo-informed modification.

A failure closes this exact listwise representative-share lane. Any successor must change mechanism class and be independently motivated from non-SonotaCo evidence before freeze.

## Required firewall assertions

Every scientific output must assert:

- `scientific_role = GMN_2022_2023_TARGET_EXCLUDED_METHOD_DEVELOPMENT_ONLY`;
- `sonotaco_2013_2014_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- `blind_exclusion = [20.0, 55.0]`;
- `same_shower_all_fragments_same_fold = true`;
- `target_search = false`;
- `feature_search = false`;
- `hyperparameter_search = false`;
- `diversity_search = false`;
- `post_result_second_search = false`.
