# OrbitTrace v26 — expanded-membership cohesion two-head OOF ranking

## Motivation

v22–v25 changed ranking targets/objectives while holding the same 71-dimensional pretruth feature representation fixed. Those features are built on the **pre-expansion candidate family**. The final SonotaCo literature score, however, evaluates the later fixed v19/v17 expanded membership. Thus every prior learned ranker was asked to predict final membership quality without seeing label-free geometric diagnostics of the actual membership being scored.

This is a distinct information-representation hypothesis, not another target/loss search.

## Sole feature change

v26 appends exactly the already-frozen **7-dimensional #839 v2 cohesion vector** from `orbittrace_urc_unseen_ranker_v1.application.cohesion_features_pair`, but computes that vector on the exact frozen **expanded v19 membership** instead of the sparse pre-expansion skeleton.

The seven values remain byte-for-definition identical to #839 v2:
1. minimum annual member count;
2. maximum annual member count;
3. annual count balance `min/max`;
4. median member-to-family-centroid distance;
5. 90th-percentile member-to-family-centroid distance;
6. maximum member-to-family-centroid distance;
7. worst annual 90th-percentile member-to-family-centroid distance.

No new radius, quantile, scale, threshold, statistic, transform, or feature search is introduced. The physical distance is exactly the existing frozen `support.centroid_distance`; the family centroid is the exact pre-expansion candidate centroid already frozen in the v22/v23/v24 payload. Only `event_ids` are replaced by the exact expanded membership for this second cohesion calculation.

The resulting v26 feature dimension is exactly **78 = 71 + 7**. The original 71 features remain unchanged and in the same order.

## Frozen pretruth identity

Before this feature augmentation, v26 must regenerate the exact v22-v25 scientific payload:
- memberships and centroid matrices byte-identical to the valid payload;
- original 71-feature matrix equal under the same frozen round-to-12-decimal semantic fingerprint used by valid v23-v25;
- exact v19 expanded-family identity preserved.

The 78-dimensional feature matrix is then generated and SHA-256 frozen **before SonotaCo truth is loaded**. Feature augmentation receives only label-free rows, the frozen memberships/centroids, and frozen detector geometry.

## Ranking objective

v26 does not search among the v22-v25 learning objectives. It reuses exactly the strongest prior balanced HDBSCAN architecture, v24:
- two independent copies of the exact #839 ExtraTrees regressor;
- one OOF head predicts membership F1 in 2013;
- one OOF head predicts membership F1 in 2014;
- exact deterministic five-fold whole-shower grouping across both Sugar and HDBSCAN routes;
- exact inverse-group training weights;
- final OOF family score `min(predicted_F1_2013, predicted_F1_2014)`;
- exact #839 diversity lambda `0.8`, scale `1.0`.

No model, target, fold, weighting, prediction-combiner, or diversity search is allowed.

## Frozen variants and gate

Exactly two successor orders are evaluated:
1. `expanded_cohesion_two_head_quality`: diversity order from the fixed two-head minimum score on 78 features.
2. `expanded_cohesion_two_head_v19_rank_sum`: parameter-free equal-weight rank-sum between that order and exact v19 rank-sum.

Exact v19 fixed-membership order is retained as an identity control and must reproduce all four v19 metrics.

PASS requires one frozen successor to beat the corresponding literature comparator in **all four** comparator/year panels: candidate macro-F1 strictly greater than the literature value and recovered F1>0.5 count at least equal to literature in every panel. The same robust four-panel lexicographic selector used by v22-v25 chooses between the two frozen successors.

Only an OOF all-panel PASS may fit and fingerprint two full-development 78-feature annual heads. Full-fit in-sample performance is ineligible as promotion evidence. A v26 failure permanently rejects this exact expanded-cohesion feature augmentation and does not authorize quantile/radius/statistic expansion.

## Firewall

SonotaCo 2013/2014 remains exposed development-only. No MAARSY, DMS, OrbitTrace target information, target-region event, or protected 20°–55° content is authorized. Any protected cross-survey validation requires a separate candidate-specific pretruth protocol after an OOF PASS.
