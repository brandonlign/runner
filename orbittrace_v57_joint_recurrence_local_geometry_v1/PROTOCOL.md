# OrbitTrace v57 joint-recurrence local geometry v1

## Scientific role

This is a separately frozen **exposed-development successor** after binding v56 failure. It does not tune the rejected v56 metric or the closed v19/local fusion line.

The parent remains exact v31. v57 changes exactly one architectural quantity inside v31's strict-OOF local geometry: **the definition of the positive reference population**.

Exact v31 defines two separate annual reference problems. In each fold, a training family is positive for the 2013 head when its fixed-label 2013 F1 exceeds `0.5`, and independently positive for the 2014 head when its 2014 F1 exceeds `0.5`. It computes two ordinary-Euclidean k=1 positive/nonpositive margins and ranks by the worse annual margin.

For a recurrent two-year catalogue family, that permits the positive reference population to change between annual heads and permits a training family that is recoverable in only one year to act as a positive archetype for that year. v57 tests a distinct recurrence hypothesis: a positive local-geometry reference should itself satisfy the already-established balanced-recovery event in **both** exposed years.

The exact predicate is not new. Earlier strict-group development (#997/#1004) already fixed the benchmark-defined event `F1_2013 > 0.5 AND F1_2014 > 0.5`; those experiments used it as a supervised classifier/group target and failed. No prior repository experiment uses that predicate as the positive-reference class for v31-style nearest-neighbor local geometry. v57 therefore reuses an established threshold/predicate in a scientifically distinct geometric role rather than selecting a new cutoff.

SonotaCo 2013/2014 remains `EXPOSED_DEVELOPMENT_ONLY`, not external validation.

## Immutable parent and representation

v57 must first reproduce exact v31 unchanged:

- Sugar 2013 `0.2719801488280529 / 16`;
- Sugar 2014 `0.31529041952487225 / 17`;
- HDB 2013 `0.14888037368183737 / 9`;
- HDB 2014 `0.15198123772301594 / 9`.

Exact parent source blob:

`917e3cd6f9310ca1282e0efa58ed0924d03ed4da`.

Everything below remains exact v31 unless explicitly replaced by the sole v57 reference-class change:

- immutable #950 candidate universe and final memberships;
- immutable 71D feature representation and centroids;
- stacked Sugar+HDB development table;
- deterministic strict whole-shower five-fold OOF grouping across routes;
- fold-training mean and population-standard-deviation z-score, with zero std replaced by `1.0`;
- ordinary Euclidean distance across all 71 standardized dimensions;
- k=`1` nearest positive and nearest nonpositive reference;
- margin orientation `d_nonpositive - d_positive`;
- exact #839 diversity `lambda=0.8`, `scale=1.0`, tie semantics unchanged;
- immutable exact-v19 order;
- one equal rank-sum with exact v19;
- fixed candidate memberships, literature budgets and evaluator;
- same rule on Sugar and HDB.

## Sole v57 scientific change

For every fold-training family `i`, retain the same exact best-label and annual own-family F1 values already constructed by v31/v24 under the strict OOF development semantics.

Define one joint recurrence label:

`joint_positive_i = (F1_2013_i > 0.5) AND (F1_2014_i > 0.5)`.

Define

`joint_nonpositive_i = NOT joint_positive_i`.

For each held-out family, after the exact v31 fold-training z-score:

1. compute ordinary 71D Euclidean distance to every `joint_positive` training family;
2. retain the single nearest distance `d_joint_positive`;
3. compute ordinary 71D Euclidean distance to every `joint_nonpositive` training family;
4. retain the single nearest distance `d_joint_nonpositive`;
5. define the sole v57 local score

`joint_margin = d_joint_nonpositive - d_joint_positive`.

There is **one** reference problem and **one** margin. There are no separate annual margins and therefore no annual scalar combiner in v57.

The fold must fail closed if either joint-positive or joint-nonpositive references are empty. No fallback to annual labels, union-positive, OR-positive, one-year-positive, soft quality, regression target, group-level target, or alternate threshold is allowed.

The exact joint predicate is family-level. Do not promote all siblings of a positive shower group as in #1004. A training family is joint-positive only when that same fixed family's own membership achieves `F1>0.5` in both years.

After all strict-OOF joint margins are produced:

1. apply exact #839 diversity with `lambda=0.8`, `scale=1.0`;
2. fuse once by equal rank-sum with immutable exact v19;
3. evaluate the resulting single order per route using the unchanged literature evaluator.

## Why this is not a combiner search

v57 does not replace v31's annual `min` with a mean/max/geometric/harmonic/weighted combiner. It removes the two-head reference construction entirely and tests one recurrence-defined reference population. The scientific question is whether the positive archetypes themselves must be two-year-recoverable, not how to aggregate two annual scores.

The failed #997/#1004 classifiers do not close this mechanism: they trained fixed ExtraTrees classifiers on the 71D representation using the joint predicate as a supervised target (and #1004 propagated group positivity). v57 uses no classifier/model fitting beyond fold z-scaling and uses the predicate only to partition training references for exact k=1 geometry.

## Evaluation gate

The same code and joint predicate apply to both routes.

PASS requires all four frozen literature pair gates:

`candidate_macro_f1 > literature_macro_f1`

and

`candidate_recovered_f1_gt_0_5 >= literature_recovered_f1_gt_0_5`

for Sugar 2013, Sugar 2014, HDB 2013, and HDB 2014.

The first technically valid result is binding.

## No rescue

If v57 fails, permanently close this exact joint-recurrence-reference geometry. Do not retry with:

- OR/union annual positivity;
- at-least-one-year positivity;
- group-propagated joint positivity;
- different F1 threshold;
- soft/minimum/mean annual quality as distance weight;
- separate positive and negative thresholds;
- k other than 1;
- blending joint and annual margins;
- adding an annual score back after the joint margin;
- route/year-specific labels;
- changing metric/scaling/features/diversity/fusion;
- top-k/rank-window/budget rules;
- identity corrections;
- post-result second searches.

Any future successor must be independently motivated and separately frozen.

## Explicit prohibitions

No target/threshold grid, class weighting, classifier/regressor, metric search, k search, scaling search, feature search, annual-combiner search, diversity search, fusion search, source-quota selection, component/quality/topology/cross-route rescue, block-weight rescue, v19/local fusion rescue, boundary identity, oracle identity, literature-budget-specific rule, or post-result tuning.

## Firewall

Protected OrbitTrace solar longitude `20°–55°` remains inaccessible. Do not access OrbitTrace target information or target-region events. Do not access MAARSY or DMS scientifically. Every output must assert these conditions and `SonotaCo = EXPOSED_DEVELOPMENT_ONLY`.