# OrbitTrace GMN catalogue-relative source-blind purity v1

## Purpose

Test one pre-existing, parameter-free domain-normalization transform on the independently successful PR #977 source-blind purity architecture, using only target-excluded GMN 2022/2023.

This does not reopen PR #945's quality-ranker no-go. PR #945 established one exact transform—within-catalogue empirical percentile representation—for cross-survey feature-scale robustness. Here that unchanged transform is paired with the distinct source-blind purity objective/model that later passed GMN in PR #977 and improved every exposed SonotaCo panel in PR #980.

No SonotaCo, MAARSY, DMS, OrbitTrace target information, or protected 20°–55° target-region event is accessed in this experiment.

## Frozen universe and architecture

Use exactly the #839/#840 target-excluded GMN union: 226 hard + 1,075 P19 + 3,203 P20 = 4,504 families.

The underlying source-blind architecture remains exact PR #977:

- exact first 21 generic #840 features only: 14 structural + 7 membership-cohesion;
- no hard/P19/P20 one-hot and no P20-native source-specific fields;
- target = exact #839 positive predicate;
- exact strict whole-shower five-fold OOF grouping including near-misses;
- exact #840 diversity weights;
- exact HGB-31 classifier: learning rate 0.05, 250 iterations, 31 leaves, L2=1.0, seed 20260809;
- exact #839 geometric diversity lambda 0.8 / scale 1.0;
- complete 4,504-family backfill and no family deletion.

## Required controls

Before interpreting the candidate:

1. exact #839 quality+diversity comparison key must reproduce: r25/r50/r100/r500 = 22/40/75/159, top100 precision `0.7645689180574315`, MRR `0.019037817654898162`, qualified 256;
2. exact PR #977 raw 21D source-blind purity+diversity must reproduce: r25/r50/r100/r500 = 24/47/82/165, top100 precision `0.8558407874228419`, MRR `0.021025165849542556`, qualified 256.

## Sole catalogue-relative candidate

Apply the exact PR #945 transform to the 21D source-blind feature matrix:

- column 0 (`is_soft`) remains unchanged as categorical;
- every other column 1..20 is replaced by its within-catalogue average-tie empirical percentile `(rank - 1)/(N - 1)`;
- no feature is added, dropped, weighted, winsorized, standardized, clipped, or otherwise transformed;
- the complete 4,504-family unlabeled feature distribution is used, exactly as the pre-existing #945 transductive label-free representation.

Then train/evaluate the exact same PR #977 HGB-31 purity model and exact #839 diversity rule.

No alternate transform, categorical set, calibration, model, feature subset, threshold, fusion, diversity value, or parameter search is authorized.

## GMN gate

Because this experiment tests transfer representation rather than in-domain optimization, it need not beat the raw #977 model. It passes only if it remains a scientifically viable improvement over exact #839:

- recovery@100 >= 75;
- recovery@50 >= exact hard-v8 recovery@50;
- top100 dominant precision >= hard-v8 top100 precision - 0.05;
- qualified matches >= 230; and
- comparison key `(r100, r50, r25, top100 precision, MRR)` is lexicographically strictly greater than exact #839.

Only a PASS may freeze the full relative-21D GMN HGB-31 model for one separately named no-retuning canonical SonotaCo exposed-development application. A FAIL rejects this exact transform/objective combination and does not authorize transform or feature tuning.

## Deployment transform if PASS

A later application must compute the same 21 generic features on its complete canonical unlabeled candidate catalogue, keep column 0 categorical, convert columns 1..20 to empirical percentiles within that complete catalogue, then apply the frozen GMN model and exact #839 diversity. No SonotaCo fit parameters or labels may enter the transform.

## Firewall

`blind_exclusion = [20.0, 55.0]`; SonotaCo access = false; MAARSY scientific access = false; DMS scientific access = false; target information access = false; target-region events accessed = false.
