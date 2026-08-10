# OrbitTrace v28 contingency — post-membership two-head strict-group OOF reranking

## Dormant preregistration

This protocol is frozen while v27 pretruth feature-freeze run `31424166342` is still in progress and **before any successful v27 87-feature artifact exists**. It contains no execution workflow and no RUN marker.

v28 remains dormant unless v27 produces a valid `PASS_V27_POSTMEMBERSHIP_FEATURE_PRETRUTH_FREEZE` artifact for both exposed SonotaCo matched routes with all truth/target/external flags false. A v27 technical failure does not authorize changing this v28 scientific design; v27 must be repaired without altering its frozen 16 post-membership feature definitions.

## Motivation fixed before feature values are seen

The v24 artifact-only diagnosis established that the fixed expanded candidate universe has enough equal-budget membership quality to exceed HDBSCAN in both years, while v25/v26 ruled out simple annual-score normalization and within-group target centering. The architectural audit then identified that all previous learned ranking features were computed before the exact conformal membership expansion even though literature F1 is scored after expansion.

v28 tests one hypothesis only: **does giving the strongest previously surviving two-head ranking architecture label-free descriptors of the final expanded memberships improve representative selection?**

## Frozen stage boundary

Stage 1 is exact frozen v19:

1. construct the full hard/P19/P20 candidate universe;
2. compute exact frozen v19 rank-sum order;
3. apply the exact frozen #461/v17 joint-conformal membership expansion to v19 ranks 1–100 only.

Stage 2 may reorder **only those exact same 100 expanded families**. It cannot add a family from rank 101+, delete a family, change membership, change a centroid, or regenerate a candidate. After the stage-2 top-100 order, all v19 families ranked 101+ remain appended in exact original v19 order.

## Frozen input interface

For each matched route, v28 consumes only the successful v27 artifact:

- exact v19 top-100 family IDs/order;
- exact expanded final memberships;
- 71 frozen pre-membership/base features restricted to those IDs;
- exactly 16 preregistered v27 post-membership features;
- combined feature dimension exactly **87**.

No feature subset, ablation, scaling variant, interaction expansion, or new descriptor is permitted.

## Truth target and strict grouping

Only after the v27 pretruth artifact is identity/hash verified may the already-exposed immutable SonotaCo truth package be loaded.

For every route family, determine `best_label` and positive qualification with the same v22 family-truth semantics applied to the **final expanded membership**:

- same combined-two-year best-label selection;
- same overlap/precision qualification;
- nonpositive families retain zero targets.

All copies/fragments associated with the same fixed best shower label across both matched routes use the common strict group `SHOWER/<label>`. Non-shower/background families use unique route/family groups. The exact deterministic five-fold group assignment inherited from v22/v24 is unchanged. A shower group is entirely train or test in each fold.

## Exact two annual targets

v28 reuses the strongest structured target design from preregistered v24 without modification:

- head 2013 target = expanded-membership `F1_2013` against the unchanged fixed best label;
- head 2014 target = expanded-membership `F1_2014` against the unchanged fixed best label;
- unchanged nonpositive families = zero in both heads.

There is no worst-year target replacement, target centering, year weighting, clipping, calibration, pairwise target, or target grid.

## Model and OOF score

Train exactly two copies of the exact frozen #839 ExtraTrees regression model under the same strict five OOF folds and the exact frozen inverse-group sample weights. No hyperparameter search or alternate model is permitted.

For each held-out family, the sole stage-2 learned quality score is exactly the v24 combiner:

`Q28 = min(predicted_F1_2013, predicted_F1_2014)`.

No percentile conversion, mean, product, learned combiner, or calibration is permitted.

The exact #839 geometric diversity ordering is then applied to the 100 stage-2 families only with unchanged `lambda=0.8`, `scale=1.0`, original centroid matrix, and stable tie semantics.

## Sole final deployable order

The sole v28 top-100 order is the parameter-free equal **rank-sum** of:

1. the diversified `Q28` post-membership order; and
2. exact frozen v19 order restricted to the same 100 families.

The already-frozen v19 rank-sum helper defines the combination. No rank-product, weight, consensus-only, alternate diversity setting, or selector is evaluated.

The complete deployable catalogue is:

`v28 reranked v19 top100 + unchanged v19 ranks101+`.

## Mandatory controls

Before accepting any v28 result:

1. v27 artifact must prove 87 dimensions, exact top-100 IDs, exact membership identity, no truth/model/evaluation, and all external/target flags false;
2. exact v19 fixed-membership top-100 control must reproduce all four frozen v19 SonotaCo metrics under #854 semantics;
3. the stage-2 input family set must equal exact v19 top100 on each route;
4. no rank >100 may enter stage 2.

Any control failure makes the run invalid rather than a scientific result.

## Literature evaluation gate

Use the exact immutable #854 equal-budget one-to-one maximum-total-F1 evaluator. A pairwise literature win requires:

- candidate macro-F1 > frozen comparator macro-F1; and
- candidate recovered-F1>0.5 count >= frozen comparator recovered count.

v28 passes only if its **single frozen final order wins all four matched panels**:

- Sugar 2013;
- Sugar 2014;
- catalogue HDBSCAN 2013;
- catalogue HDBSCAN 2014.

No per-panel method selection is allowed.

## Full model freeze after PASS only

Only an all-four-panel strict-group OOF PASS may fit exactly the same two heads once on all exposed SonotaCo development examples and fingerprint them for a later separately preregistered protected cross-survey deployment. The full-fit in-sample SonotaCo score is never computed as promotion evidence.

## Prohibitions

- no execution before a valid v27 pretruth PASS artifact;
- no feature search/ablation/new feature after v27;
- no candidate/membership/centroid change;
- no target/model/hyperparameter/fold/group change;
- no alternative two-head combiner;
- no diversity/fusion search;
- no promotion of v19 rank101+ into the stage-2 set;
- no comparator-budget-specific ranking logic;
- no post-result v28 rescue or second search;
- no MAARSY, DMS, OrbitTrace target information, target-region event, or 20°–55° target-content access.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`.
