# OrbitTrace v36 annual-oriented expanded-membership count OOF ranker v1

## Scientific role

Separately frozen exposed-SonotaCo development successor after the v31 diagnostic line localized the remaining HDBSCAN failure to a small 1–2 shower-group top-budget set error. The representation audit found a specific mismatch in the frozen v24/v31 inputs: all 71 supervised features are year-symmetric, while the benchmark is annual, and the annual F1 target is evaluated on the fixed post-expansion memberships rather than the pre-expansion core. Historical v27/v28 post-membership work added only symmetric expanded-count summaries (`min`, `max`, balance) and therefore still could not distinguish "large 2013 expansion" from "large 2014 expansion".

This successor changes only that missing orientation information. It does not use the truth-derived identities from the substitution oracle and does not alter any family membership.

SonotaCo 2013/2014 remains exposed development-only.

## Sole scientific change from exact v24

Start from the exact immutable #950/v24 71-dimensional pretruth feature matrix and exact fixed expanded `family_memberships.json` for each matched route. Before truth, join membership event IDs only to the already-frozen label-free SonotaCo preparation rows, whose `year` field is detector-safe and contains no shower truth.

For every fixed family, count how many of its final fixed membership event IDs belong to 2013 and to 2014. Append exactly two features in this order:

1. `log1p(expanded_member_count_2013)`
2. `log1p(expanded_member_count_2014)`

The resulting feature dimension is exactly **73**. Every membership event ID must map to exactly one of the two label-free row-year universes; otherwise execution fails closed.

No count ratio, signed difference, min/max/balance duplicate, expansion/core ratio, accepted-conformal statistic, absolute centroid coordinate, or other feature is added. No transformation other than `log1p` is authorized.

## Everything else frozen to v24

- exact immutable #950/v22 71D base features, centroids, family IDs, sources, v19-expanded memberships, candidate universes, and v19 order;
- exact Sugar+HDBSCAN shared strict `SHOWER/<label>` whole-shower five-fold assignment;
- exact annual fixed-label F1 regression targets used by v24;
- exact #839 inverse-group sample weights;
- two exact #839 ExtraTrees regression heads through the frozen `model()` helper;
- exact annual score `min(pred_2013,pred_2014)`;
- exact #839 diversity `lambda=0.8`, `scale=1.0`;
- exact one parameter-free equal rank-sum with frozen v19;
- only that fused order is the promotion candidate;
- exact equal-budget one-to-one annual literature evaluator and pairwise superiority semantics.

The workflow must first regenerate and hash-freeze both 73D route matrices before any known-shower truth file is loaded. It must also reproduce exact v24 using the unaugmented 71D features in the same execution before accepting the v36 result.

## Binding gate

The first technically valid execution is binding. PASS requires the single v36 fused order to beat the corresponding literature comparator in all four Sugar/HDBSCAN 2013/2014 panels: macro-F1 strictly higher and recovered `F1>0.5` count at least equal in every panel.

Otherwise this exact two-feature annual-orientation augmentation is a permanent no-go. Failure does not authorize additional post-membership features, count ratios/differences, year-specific feature subsets, transforms, feature selection, model/hyperparameter changes, class/target changes, annual-combiner changes, diversity/fusion changes, source quotas, or post-result rescue within v36.

A full exposed-development model may freeze only after a 4/4 OOF PASS; in-sample full-fit scores may never determine promotion.

No MAARSY, DMS, OrbitTrace target information, target-region event, or protected solar-longitude 20°–55° content may be accessed.