# OrbitTrace v58 nearest strict-group mean-distance local geometry v1

## Scientific role

This is a separately frozen **exposed-development successor** after binding v57 failure. It does not alter the closed v57 recurrence-label rule, rejected v56 block metric, or rejected v19/local fusion algebra.

The parent remains exact v31. v58 changes exactly one quantity inside v31's annual strict-OOF local geometry: how a held-out family measures its distance to the positive and nonpositive **reference classes** when a strict shower group contains multiple candidate fragments.

Exact v31 uses the single nearest training family (`k=1`). Because recurrent shower groups can contain multiple candidate fragments, a shower represented by more training fragments has more opportunities to supply an unusually close individual reference. The same strict groups already exist to prevent leakage and were designed to make shower identity the statistical unit. v58 therefore asks whether the local distance should make the strict group—not an individual fragment—the competing reference unit.

The construction is parameter-free and distinct from rejected v35. v35 replaced each training shower group by one arithmetic-mean **feature prototype** and measured Euclidean distance to that prototype. v58 retains every actual training-family feature vector and instead defines a group's distance as the arithmetic mean of the held-out candidate's Euclidean distances to the actual class-eligible members of that group. In general `mean_i ||z-x_i|| != ||z-mean_i x_i||`; group spread remains visible rather than being collapsed to a centroid.

No prior repository successor uses nearest strict group by mean member distance.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, not external validation.

## Immutable parent

v58 must first reproduce exact v31 unchanged:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDB 2013 `0.14888037368183737 / 9`;
- HDB 2014 `0.15198123772301594 / 9`.

Exact parent source blob:

`917e3cd6f9310ca1282e0efa58ed0924d03ed4da`.

Everything below remains exact v31 unless explicitly changed by the sole group-distance rule:

- immutable #950 candidates, memberships, 71D features and centroids;
- stacked Sugar+HDB training population;
- deterministic strict whole-shower five-fold OOF grouping across both routes;
- exact best-label/group semantics;
- fold-training mean and population-standard-deviation z-score, with zero std replaced by `1.0`;
- ordinary Euclidean distance over all 71 standardized dimensions;
- annual family-level positivity `annual_f1 > 0.5` for the same fixed best label;
- separate 2013 and 2014 annual heads;
- margin orientation `d_nonpositive-d_positive`;
- annual combiner `min(margin_2013,margin_2014)`;
- exact #839 diversity `lambda=0.8`, `scale=1.0`;
- immutable exact-v19 order and one equal rank-sum;
- same fixed budgets and literature evaluator;
- same rule on Sugar and HDB.

## Sole v58 scientific change

Within each outer fold and annual head, retain v31's exact family-level positive/nonpositive class assignment.

For each class separately, partition the fold-training families by their already-frozen strict group ID. A strict group may therefore have a positive subset, a nonpositive subset, or both; v58 does **not** propagate positivity or nonpositivity across sibling fragments.

For a held-out standardized candidate `z` and a nonempty class-specific group subset `G`, define

`D_G(z) = arithmetic_mean_{x in G} ||z - x||_2`.

Then define

`d_positive(z) = min over strict groups G containing >=1 annual-positive training family of D_G(z)`

and

`d_nonpositive(z) = min over strict groups G containing >=1 annual-nonpositive training family of D_G(z)`.

The annual v58 margin remains

`d_nonpositive - d_positive`.

The two annual margins still combine by exact v31 `min`, then exact diversity and exact-v19 equal rank-sum.

Every class-specific strict group has equal opportunity to be the nearest group regardless of how many fragments it contains. Within a chosen group all class-eligible member distances contribute equally. No group-size exponent, inverse-size coefficient, trimmed mean, median, RMS, minimum, maximum, quantile, soft minimum, or top-m member selection is allowed.

The fold fails closed if either annual class has no nonempty strict groups.

## Relation to earlier group work

This does not reopen:

- v35 group prototypes: rejected feature-centroid geometry;
- #1004 group-dense labels: v58 does not propagate a group's recoverability label to siblings;
- #1008 group-balanced pairwise learning: v58 trains no classifier/regressor and uses no pairwise objective or learned probability.

The only changed object is the deterministic class-distance functional applied to exact v31 fold-standardized Euclidean member distances.

## Evaluation

After exact v31 reproduction, evaluate exactly one v58 order per route:

1. exact strict-group OOF fold and scaling;
2. exact annual family-level positive/nonpositive labels;
3. nearest positive strict-group mean member distance and nearest nonpositive strict-group mean member distance;
4. annual margin `d_nonpositive-d_positive`;
5. exact annual `min`;
6. exact #839 diversity `0.8/1.0`;
7. one equal rank-sum with exact v19;
8. unchanged literature evaluator.

PASS requires all four frozen literature pair gates:

`candidate_macro_f1 > literature_macro_f1`

and

`candidate_recovered_f1_gt_0_5 >= literature_recovered_f1_gt_0_5`

for Sugar 2013, Sugar 2014, HDB 2013, and HDB 2014.

The first technically valid result is binding.

## No rescue

If v58 fails, permanently close this exact nearest-group mean-distance architecture. Do not retry with:

- median/RMS/min/max/trimmed group distance;
- group-size weights or exponents;
- top-m members;
- group prototypes/centroids;
- group-propagated labels;
- group-level F1 target;
- different annual threshold;
- joint-year labels;
- k/metric/scaling/feature changes;
- annual-combiner/diversity/fusion changes;
- route/year-specific rules;
- top-k/rank-window/budget exceptions;
- identity corrections;
- post-result second searches.

Any future successor must be independently motivated and separately frozen.

## Explicit prohibitions

No model/classifier/regressor, group-label propagation, group-distance aggregation search, metric search, k search, scaling search, feature search, threshold search, annual-combiner search, diversity search, fusion search, source-quota selection, block-weight rescue, v19/local fusion rescue, component/quality/topology/cross-route rescue, boundary identity, oracle identity, literature-budget-specific rule, or post-result tuning.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every output must assert these conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.