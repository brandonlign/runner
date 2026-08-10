# OrbitTrace v23 — worst-year strict-group OOF ranking

## Motivation

Authoritative v22 exposed-development run `31418293036` completed cleanly and failed the all-panel literature-superiority gate. It still beat Sugar in both matched years but lost catalogue HDBSCAN in both. Post-result diagnosis showed that the v19/v22 family universe already contains strong balanced representatives below the tiny HDBSCAN cutoffs, while some higher-ranked representatives have highly unequal 2013/2014 membership quality.

v22 trained the exact #839-complexity ranker on a combined-two-year family F1 target. That target can reward a family that is excellent in one year and weak in the other, although the final literature claim must hold independently in both years.

v23 therefore changes **one scientific quantity only**: the regression target.

## Frozen target change

All v22 pretruth science remains exact:

- the same pair-portable hard/P19/P20 family universe;
- the same v15 density-safe hard ordering;
- the same fixed v19 rank-sum top-100 joint-conformal memberships;
- the same 71 label-free features;
- the same exact #839 ExtraTrees model class/hyperparameters;
- the same inverse-group weighting;
- the same deterministic five strict whole-shower grouped folds;
- the same diversity `lambda=0.8`, `scale=1.0`;
- the same parameter-free rank-sum fusion with v19;
- the same #854 equal-budget one-to-one evaluation and four-panel selection key.

The **best-label/group assignment is byte-for-semantics identical to v22**: it is determined by the same combined-two-year v22 family-truth function. Thus every fragment/near-miss associated with a shower remains in the same group logic as v22.

Only the positive regression target changes. For a family that v22 marks positive for its fixed best label, compute membership F1 independently in 2013 and 2014 against that same label, using only the matched-route truth IDs for the corresponding year. The v23 target is:

`min(F1_2013, F1_2014)`.

A family that is nonpositive under the unchanged v22 precision/overlap qualification retains target zero. No target mixture, exponent, weight, floor, threshold, or alternative label selection is searched.

## Execution order

1. Regenerate the exact v22 Sugar-route and HDBSCAN-route pretruth feature/membership payloads from exposed label-free rows.
2. Hash-freeze both route payloads before truth.
3. Only then load the immutable already-exposed SonotaCo truth/comparator artifact.
4. Reproduce the exact v19 fixed-membership control on all four panels.
5. Construct the unchanged v22 group identities and the single v23 worst-year targets.
6. Train one exact #839-complexity model in five strict grouped OOF folds.
7. Evaluate exactly two successor orders: worst-year OOF quality alone and its parameter-free rank-sum fusion with exact v19.
8. Select once using the same four-panel robust lexicographic key as v22.

A pairwise literature win requires candidate macro-F1 above the frozen comparator and candidate recovered-F1>0.5 count at least the comparator count. v23 passes only if one frozen successor wins all four panels.

Only an OOF all-panel PASS may authorize fitting and fingerprinting one full exposed-SonotaCo v23 model for a later separately preregistered protected cross-survey validation. The full-fit in-sample SonotaCo score is never promotion evidence.

## Prohibitions

- no feature search;
- no model/hyperparameter search;
- no target grid or target weighting search;
- no change to family generation or membership construction;
- no change to strict grouping or folds;
- no comparator-budget-specific training/ranking logic;
- no post-result second search within v23;
- no MAARSY, DMS, OrbitTrace target information, target-region event, or 20°–55° target-content access.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.
