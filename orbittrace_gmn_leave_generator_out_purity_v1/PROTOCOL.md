# OrbitTrace GMN leave-generator-out source-blind purity v1

## Purpose

Test one GMN-only domain-generalization architecture that explicitly prevents a purity model from learning the statistical signature of the generator source it is asked to rank.

The experiment uses only target-excluded GMN 2022/2023. It does not access SonotaCo, MAARSY, DMS, OrbitTrace target information, or protected 20°–55° target-region events.

## Motivation boundary

PR #977 established on GMN that removing all seven explicit generator/P20-specific ranking fields improves the purity architecture. PR #980 then showed that this source-blind model improves every exposed SonotaCo panel relative to the source-aware model, although it still fails literature superiority. PR #984/#986 established that global percentile normalization is not the missing fix.

These results motivate one stronger generator-robustness test without using SonotaCo truth: for every GMN prediction, train on the other generator sources only. Source identity is used solely to define which training domain is excluded; it is not an input feature, score bonus, quota, or post-hoc rank rule.

## Frozen universe and representation

Use exactly the #839/#840 target-excluded GMN union:

- hard: 226 families;
- P19: 1,075 families;
- P20: 3,203 families;
- total: 4,504 families.

Use exactly the 21 generic features from PR #977:

- 14 generic structural features;
- 7 generic membership-cohesion features;
- no hard/P19/P20 one-hot;
- no P20-native ranking fields.

Use the exact #839 positive predicate as the binary purity target, exact #840 diversity weights, exact HGB-31 classifier, and exact #839 diversity lambda `0.8`, scale `1.0`, complete backfill, no family deletion.

## Required controls

Before interpreting the candidate, reproduce exactly:

1. #839 quality+diversity: r25/r50/r100/r500 = 22/40/75/159, top100 precision `0.7645689180574315`, MRR `0.019037817654898162`, qualified 256;
2. PR #977 ordinary strict-group 21D source-blind purity+diversity: r25/r50/r100/r500 = 24/47/82/165, top100 precision `0.8558407874228419`, MRR `0.021025165849542556`, qualified 256.

## Sole leave-generator-out candidate

Each family retains its frozen generator source `hard`, `p19`, or `p20`. Let the exact #840 deterministic whole-shower fold be `f`.

For every source `s` and fold `f`:

- test rows are exactly families with source `s` and fold `f`;
- training rows must have source != `s` **and** fold != `f`;
- therefore the model sees neither the held-out generator domain nor any whole-shower group assigned to the held-out fold;
- fit the exact fixed HGB-31 model on those training rows using exact #840 weights;
- predict only the held-out `(source=s, fold=f)` rows.

Across 3 sources x 5 folds, every one of the 4,504 families receives exactly one prediction. No same-generator or same-fold training row may contribute to that prediction.

The resulting complete OOF score vector is passed through exact #839 geometric diversity (`lambda=0.8`, `scale=1.0`) with exact tie semantics and complete backfill.

No alternate source grouping, fold rule, model, target, feature subset, weighting, ensemble, source quota, calibration, threshold, fusion, diversity value, or parameter search is authorized.

## GMN promotion gate

The leave-generator-out candidate passes only if:

- recovery@100 >= 75;
- recovery@50 >= exact hard-v8 recovery@50;
- top100 dominant precision >= hard-v8 top100 precision - 0.05;
- qualified matches >= 230; and
- comparison key `(r100, r50, r25, top100 precision, MRR)` is lexicographically strictly greater than exact #839.

It is not required to beat ordinary PR #977 in-domain because the scientific question is generator-domain robustness, not another GMN leaderboard search.

## Full model freeze if PASS

Only a GMN PASS may freeze exactly three deployment models:

- `for_hard`: fit on all GMN P19 + P20 families, never hard;
- `for_p19`: fit on all GMN hard + P20 families, never P19;
- `for_p20`: fit on all GMN hard + P19 families, never P20.

All three use the same exact 21 features, target, HGB-31 specification, and #840 weights. At deployment, a family is scored only by the model that excluded its generator source from training. Generator source is therefore a routing key only, never a learned feature or rank quota.

A later separately named canonical SonotaCo application, if authorized by PASS, must use these three frozen models without SonotaCo fitting or source quota and must lock the full catalogue before truth.

## Firewall

- blind exclusion = `[20.0, 55.0]`;
- SonotaCo access = false;
- MAARSY scientific access = false;
- DMS scientific access = false;
- OrbitTrace target information access = false;
- target-region events accessed = false.
