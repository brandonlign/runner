# OrbitTrace GMN v31-principle local-geometry OOF diagnostic v1

## Scientific role

This is a **target-excluded GMN 2022/2023 mechanism diagnostic only**. It does not access SonotaCo, MAARSY, DMS, OrbitTrace target information, or the protected 20°–55° target region. It does not modify candidate generation or family memberships.

The motivation is frozen before outcome. The successful exposed-development v31 SonotaCo method is not a generic quality score: it uses strict whole-shower out-of-fold nearest-reference geometry, scoring each held-out family by the distance margin between the nearest recoverable-like and nearest nonrecoverable-like training references. Two later standalone quality mechanisms—predictive-consistency transfer and GMN local-background contrast—failed. This diagnostic therefore asks a narrower question: **does the v31 nearest-reference geometry principle itself carry independent signal on target-excluded GMN when applied to an intrinsic, label-free hard-family representation?**

No SonotaCo result is used to choose a GMN threshold, weight, metric, feature subset, or gate.

## Immutable candidate universe

Use exactly the 226 P19 hard families and their exact immutable hard order from target-excluded GMN 2022/2023. Do not add or delete families and do not recompute memberships.

Development truth is opened only after the target-excluded catalogue parser has removed the protected solar-longitude interval.

## Frozen intrinsic family representation

For each hard family construct exactly 23 label-free dimensions:

1. ten intrinsic structural features from the active URC representation, in their existing order: log event count, log anchor count, log quartet count, log component count, best score, minimum annual strength, maximum annual strength, annual-strength balance, member-year balance, cross-year centroid distance;
2. the exact seven URC-v2 cohesion features: minimum annual member count, maximum annual member count, member-count balance, all-member median centroid distance, all-member q90 centroid distance, all-member maximum centroid distance, worst annual q90 centroid distance;
3. the exact six active hard-family centroid-neighborhood descriptors from `neighbor_features`: log neighbor counts within 0.25/0.5/1.0/1.5 in the fixed centroid embedding, nearest-neighbor distance, and median distance to the nearest five neighbors.

Explicitly exclude source indicators, P19/P20-soft metadata, hard-rank percentile, and P20-only fields. There is no feature search.

## Strict OOF reference geometry

Define a GMN family as a positive reference exactly when the frozen GMN evaluator marks it qualified (`precision >= 0.5` and overlap >= 4 for its best eligible recurrent shower). All others are nonpositive references.

Use the existing deterministic five-fold assignment. Every family with a non-null best shower label uses group `SHOWER/<label>` whether qualified or not; families with no best label use unique group `NEG/<family_id>`. This prevents fragments associated with the same known shower from appearing in both train and held-out portions.

For each fold:

1. compute the arithmetic mean and population standard deviation (`ddof=0`) of every one of the 23 dimensions on fold-training families only; replace exactly-zero standard deviations by 1.0;
2. z-standardize training and held-out families using those training-only statistics;
3. for each held-out family, compute ordinary Euclidean distance to the single nearest positive training reference and the single nearest nonpositive training reference;
4. define local-geometry margin as `d_nonpositive - d_positive`; larger is more recoverable-like.

There is no k search (`k=1` only), metric search, covariance metric, feature weighting, calibration, class weighting, resampling, tree/model fit, probability model, or margin threshold.

## Frozen post-score machinery

Apply exactly the existing v31 diversity setting to the OOF margin: geometric diversity `lambda=0.8`, `scale=1.0`, with immutable hard-rank/stable-ID tie semantics. Then perform exactly one equal rank-sum fusion between that diversified margin order and the immutable 226-family hard order.

The diversified-margin-only order is diagnostic; the sole promotion candidate is the equal-rank fused order. No alternate diversity, rank product, sequential rule, fusion weight, or route/source quota is permitted.

## Binding GMN gate

The first technically valid execution is binding. PASS requires the sole fused order simultaneously to:

- recover strictly more families in the top 100 than the immutable hard baseline;
- recover at least as many families in the top 50;
- have top-100 dominant precision at least as high;
- have MRR at least as high.

Qualified-family count must remain identical because the universe and memberships are immutable.

If any gate fails, this exact GMN v31-principle transfer is permanently rejected. No k, metric, feature, scaling, diversity, fusion, threshold, fold, or reference-definition rescue is authorized.

A PASS is only evidence that the nearest-reference geometry principle generalizes on target-excluded GMN. Any later SonotaCo successor must be separately motivated and frozen before its first outcome; this diagnostic itself does not authorize tuning on SonotaCo.
