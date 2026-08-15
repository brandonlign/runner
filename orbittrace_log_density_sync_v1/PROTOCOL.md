# OrbitTrace log-density synchronous EOM v1 — frozen protocol

## Goal

Test one structural successor whose motivation is **cross-survey generalization**, not incremental reranking on GMN.

Current density-synchronous recurrent-EOM integrates recurrent alive mass over the raw HDBSCAN density coordinate `lambda`. Meteor surveys differ greatly in sampling density, sporadic-background structure, sensitivity, and event count. Meteor-stream literature repeatedly treats a stream as an overdensity relative to a nonuniform sporadic background; Sugar et al. (2017) explicitly validates density clustering against simulated sporadics, while Shober (2025) estimates statistical significance against a KDE sporadic background.

This successor therefore tests a local, scale-relative quantity: **multiplicative density contrast**.

## Sole scientific change

Start from the exact density-synchronous recurrent-EOM champion from PR #1263.

Do not change:

- target-excluded GMN 2022+2023 event population;
- GEO6 representation;
- Euclidean metric;
- `min_cluster_size=10`;
- `min_samples=10`;
- pooled HDBSCAN fit;
- mutual-reachability MST;
- condensed hierarchy;
- year identities;
- FOSC/EOM extraction;
- hidden-truth evaluator.

For each non-root condensed-tree node `C`, replace the raw-density synchronous objective

`S_sync(C) = integral min(A_2022^C(lambda), A_2023^C(lambda)) d lambda`

with

`S_log(C) = integral min(A_2022^C(lambda), A_2023^C(lambda)) d log(lambda)`

or equivalently

`S_log(C) = integral min(A_2022^C(lambda), A_2023^C(lambda)) / lambda d lambda`.

`A_y^C(lambda)` is the same annual normalized alive-mass curve used by #1263.

The condensed-tree root is excluded by `allow_single_cluster=False`; its successor quality is fixed to `0.0` because its birth density is zero and `log(lambda/lambda_birth)` is undefined.

No epsilon, bandwidth, learned coefficient, fitted exponent, blend weight, threshold, or extra hyperparameter is introduced.

## Why this is a distinct mechanism

This is **not** another post-hoc family-quality multiplier. It changes the hierarchy objective used by EOM to decide which nodes survive.

The hypothesis is specific: a real stream should remain a recurrent overdensity through a large **multiplicative** increase in local density relative to its birth/background level. Raw `d lambda` persistence can favor structures simply because the survey samples that region at a high absolute density. `d log(lambda)` measures density contrast on a ratio scale and is therefore a plausible route to better survey transfer.

Repo search before freezing found no prior OrbitTrace `log lambda`, multiplicative-density-contrast, or `d log(lambda)` hierarchy objective. Closed lanes remain closed: no kNN/year-mixing, rate-balance, year-shift, ECDF rank, cross-year core, reciprocal transfer, phase equalization, uncertainty cloning, or wavelet reranking is reused.

## Permanent protected-data rules

- Inclusive solar-longitude exclusion `[20.0,55.0]` remains in force before fitting or labels.
- OrbitTrace target information/events remain inaccessible.
- SonotaCo 2013/2014 remains unopened for this successor until it passes the frozen GMN gate below.
- ASFN and EFN may not be used to design, tune, rescue, or select this successor.
- AMOS remains pristine and inaccessible.
- MAARSY and DMS remain inaccessible.
- Hidden known-shower labels enter only after the complete successor node set, memberships, and order are persisted.

## Frozen GMN development gate — deliberately stronger than #1263

Parent is exact PR #1263 density-synchronous recurrent-EOM.

The successor passes GMN only if **all** conditions hold:

1. mechanism is active;
2. total recovered@100 across 2022+2023 improves by **at least +5** over the parent total `179`;
3. recovered@100 is not lower in either year;
4. recovered@50 is not lower in either year;
5. top-100 dominant precision is not lower in either year;
6. MRR is not lower in either year;
7. median top-500 fragmentation is not higher in either year.

This means `180` or `181` total is an automatic FAIL even if other metrics rise. The project goal is a meaningful improvement, not another one-shower development win.

No post-result rescue, exponent tuning, score blending, subset application, alternate root treatment, alternate integration measure, or threshold relaxation is allowed.

## If and only if GMN passes

Before opening SonotaCo for this successor, freeze a direct transfer protocol using the already-exposed 2013/2014 Sugar and HDBSCAN panels and their exact literature comparators.

Transfer success must require:

- no regression versus the current recurrent-EOM benchmark on any of the four established panels in macro-F1 or recovered count;
- strict improvement on at least two of the four panels in macro-F1 or recovered count;
- continued superiority to the corresponding frozen literature comparator on all four panels.

No SonotaCo tuning or rerun is allowed.

A successor that passes both GMN and SonotaCo may then be considered for the single untouched AMOS final test under a separately frozen pre-data protocol. AMOS remains the actual external-generalization endpoint.

## Failure rule

Any technically valid GMN FAIL permanently closes **log-density synchronous EOM v1**. Do not rescue it by changing logarithm base, adding offsets, clipping lambda, blending raw/log stability, applying only to selected nodes, retuning HDBSCAN, or reranking the failed catalogue.
