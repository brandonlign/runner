# OrbitTrace v26 — strict-group relative representative-quality ranking

## Motivation

The exposed SonotaCo development chain has isolated the remaining failure to **representative ranking**, not detector coverage or fixed membership quality:

- v24 two annual quality heads reached HDBSCAN-2013 recovered count parity (10 vs 10) but still missed macro-F1, and HDBSCAN-2014 remained 7 vs 9;
- diagnostic run `31419852987` exactly replayed v24 and proved the same fixed candidate universe/memberships have equal-budget oracle fronts above HDBSCAN in both years (`RANK_PLACEMENT_HEADROOM_REMAINS`);
- v25 rank-percentile calibration regressed both HDBSCAN panels, so cross-head numerical scale mismatch is not the main problem.

The remaining mechanistic mismatch is that the learned quality target is **absolute family quality** even though the tiny-budget failure is often choosing a weak fragment while a much better representative of another shower sits below the cutoff. v19 already supplies a frozen absolute-quality/ranking backbone. v26 therefore asks the learned successor to model only **relative representative quality within each shower group**.

## Frozen scientific change

Candidate generation, family memberships, the 71 label-free feature vector, v22 best-label/group assignment, deterministic strict whole-shower folds, #839 ExtraTrees model class/hyperparameters, inverse-group sample weights, #839 diversity (`lambda=0.8`, `scale=1.0`), exact v19 rank-sum order, and exact #854 literature evaluation remain unchanged.

Inputs are the exact immutable v24 route payloads from artifact `9074742322`. The exact v24 scientific result and v24 artifact-only diagnosis are identity/authorization guards only; v24 itself is not retuned.

### Fixed base quality

For every family, construct the same v22 family truth object and the same strict group identity:

- if `best_label` exists: group `SHOWER/<best_label>`;
- otherwise: unique `NEG/<route>/<family_id>`.

For unchanged v22-positive families, compute annual membership F1 against that same fixed best label and define:

`W = min(F1_2013, F1_2014)`.

For unchanged v22-nonpositive families, define `W = 0`.

### Sole v26 target

Across the complete stacked Sugar+HDBSCAN exposed-development training table, compute the arithmetic mean `mean_W(group)` separately for every **already-fixed strict group**. The sole regression target is:

`T26 = W - mean_W(group)`.

Thus positive residual means “a better representative than the typical fragment attached to this same shower group”; negative residual means worse. Unique background/negative groups have mean zero and therefore target zero.

The group mean is a target-construction operation only. It is never an application-time input or feature. Because the deterministic OOF split keeps every member of each strict shower group in one fold, no `T26` value from a shower can enter training when that shower is being predicted.

No median/quantile/standardization, within-route centering, target mixture, clipping, threshold, or alternative residual definition is permitted.

## OOF ranking and final order

Train one exact #839-complexity ExtraTrees regressor under the unchanged deterministic five strict-group folds and unchanged inverse-group weights.

The OOF residual-quality predictions are passed directly into the unchanged #839 diversity ordering with `lambda=0.8`, `scale=1.0` and frozen centroid/tie semantics.

The **sole deployable v26 order** is the parameter-free equal rank-sum of that diversified relative-representative-quality order and the exact frozen v19 rank-sum order. v19 supplies absolute family quality; the v26 head supplies relative fragment quality. No alternate fusion is evaluated.

## Evaluation

Before v26 evaluation, the exact fixed-membership v19 control must reproduce its four frozen SonotaCo metrics under exact #854 equal-budget one-to-one F1 semantics.

The single v26 final order passes only if it wins all four frozen matched panels. A pairwise win requires:

- candidate macro-F1 > literature macro-F1; and
- candidate recovered-F1>0.5 count >= literature.

Only an all-four-panel strict-group OOF PASS may authorize fitting/fingerprinting the same single relative-quality model on all exposed SonotaCo development rows for later separately preregistered protected cross-survey validation. Its in-sample full-fit SonotaCo score is never promotion evidence.

## Prohibitions

- no candidate or membership change;
- no feature/model/hyperparameter search;
- no alternate centering statistic or residual target;
- no per-year residual heads;
- no target mixing with absolute F1;
- no diversity/fusion search;
- no comparator-budget-specific logic;
- no post-result v26 rescue;
- no MAARSY, DMS, OrbitTrace target information, target-region event, or 20°–55° target-content access.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.
