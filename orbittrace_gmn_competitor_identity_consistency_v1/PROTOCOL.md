# OrbitTrace GMN competitor-identity consistency representation v1

## Status

**PRE-OUTCOME FREEZE.** This protocol defines one target-excluded GMN 2022/2023 representation-level successor before implementation and before its first scientific evaluation.

## Motivation from permitted GMN evidence only

This successor is motivated only by target-excluded GMN evidence already frozen in the repository:

1. The exact #1194 representative-share parent on the 4,504-family union recovers `22/43/80/171` qualified shower labels at @25/@50/@100/@500, with top-100 dominant precision `0.8075287489258385`, MRR `0.02016666446026534`, and 256 qualified labels.
2. The representative-share oracle diagnostic showed that the exact #1194 target and unchanged diversity operator can reach `25/50/100/242` when the target is scored perfectly. Therefore the current @100 gap is a representation/separability problem rather than candidate coverage or a target/diversity ceiling.
3. The preregistered member-exclusivity-margin successor supplied the first clean post-governance evidence that event-level competition against the complete frozen candidate catalogue contains additional signal absent from the 34D family summaries: recovery improved from `43→44` at @50, `80→82` at @100, and `171→172` at @500. It nevertheless failed promotion because @25 fell `22→20`, top-100 precision fell, and MRR fell. Its exact annual-mean distance-margin representation is permanently closed.
4. The current candidate tests a different property of that same permitted event-level competition. It discards every own-versus-alternative distance **magnitude** and records only the categorical identity of the nearest alternative family. The scientific question is whether members of a coherent family agree about *which competing family* best explains them, whereas heterogeneous accidental families distribute their members among many different alternatives.
5. This is not a rescue of the closed margin summary: no distance margin, ratio, normalized margin, quantile, threshold, nearest-k average, source restriction, graph fusion, or alternate parent ranker is used.
6. Repository searches before this freeze found no prior entropy, collision-probability, or nearest-competitor-identity consistency representation.

No SonotaCo 2013/2014 result, identity, rank, literature gap, missed family, or exposed transfer result is used to define or select this successor.

## Immutable parent

Use exactly the #1194 target-excluded GMN union and ranking machinery:

- hard families: 226;
- P19 families: 1,075;
- P20 families: 3,203;
- union: 4,504 unique families;
- eligible recurrent labels: 355;
- qualified labels: 256;
- exact #1194 scientific source Git blob: `340f9d54b42ba2500652d7f0a74f22bbd3354f2e`;
- exact #839 34-dimensional parent feature matrix;
- exact #1194 representative-share target;
- exact deterministic whole-shower five-fold OOF assignment;
- exact grouped sample weights;
- exact `ExtraTreesRegressor(n_estimators=600, max_depth=4, min_samples_leaf=5, max_features=None, random_state=20260809)`;
- exact diversity operator `lambda=0.8`, `scale=1.0`, with unchanged tie semantics.

The parent must reproduce before successor interpretation:

- recovered@25 = 22;
- recovered@50 = 43;
- recovered@100 = 80;
- recovered@500 = 171;
- top-100 dominant precision = `0.8075287489258385`;
- MRR = `0.02016666446026534`;
- qualified matches = 256;
- parent order SHA-256 = `a2f365e0a35fc3e8eef39022128c0444448671ab4c4d4b45c89f718de4505592`.

Any mismatch is a technical no-result.

## Sole new representation

Append exactly **two label-free features** to the exact 34D parent matrix, one for 2022 and one for 2023, yielding a fixed 36D successor matrix.

### Event-to-centroid physical distance

For event `e` in year `y` and candidate family `F` with frozen annual centroid `c_{F,y}`, use exactly the already inherited normalized four-coordinate physical distance:

1. circular solar-longitude residual / 10 degrees;
2. circular Sun-centered ecliptic-longitude residual / 4 degrees;
3. ecliptic-latitude residual / 4 degrees;
4. logarithmic geocentric-speed residual `log(vg_e/vg_c) / log(1.10)`;
5. ordinary Euclidean norm of those four normalized residuals.

These scales are inherited and immutable. They are not searched here.

### Nearest alternative identity

For every actual member event `e` of family `F` in year `y`, define

`g(e,F,y) = argmin_{G != F} d(e,G)`

over all other 4,503 frozen candidate families using their frozen annual centroid for the same year.

Only the current family `F` is excluded. Competitors are not excluded because they share an event, generator, source class, component, graph relation, or geometry with `F`.

Ties are resolved deterministically by the fixed #1194 family-array order: among equal minimum distances, the lowest array index wins. No distance value or margin is retained after the categorical competitor identity is determined.

### Competitor-identity collision probability

For a family-year containing `n` members, let `c_j` be the number of those members whose nearest alternative identity is competitor family `j`.

The sole annual feature is

`C = sum_j (c_j / n)^2`.

Equivalently, `C` is the probability that two independent draws with replacement from the family-year's members have the same nearest alternative-family identity.

This statistic is fixed and parameter-free:

- range: `[1/n, 1]`;
- if `n=1`, `C=1` by the same formula;
- no entropy/log transform;
- no normalization by the number of available competitors;
- no dominant-share companion feature;
- no cross-year minimum/mean/maximum;
- no threshold;
- no nearest-k alternative set;
- no distance weighting.

The complete two-feature table must be computed solely from target-excluded event observables, immutable candidate memberships, and immutable annual candidate centroids before and independently of GMN shower truth/targets.

## Scientific question

Does **categorical agreement of member events about their nearest competing family** carry quality information absent from the existing 34D family summaries?

A high collision probability means members repeatedly identify the same alternative family, consistent with structured fragmentation or a coherent neighboring explanation. A low value means the member set is competitively heterogeneous even if it is internally compact.

This is distinct from the failed exclusivity margin, which summarized how much closer members were to their own centroid than to the nearest alternative. This successor never retains or aggregates that distance difference.

## Binding evaluation

Run exactly the same strict whole-shower OOF evaluation twice in the same binding execution:

1. exact 34D #1194 parent control;
2. sole 36D parent + two annual competitor-identity collision-probability features.

The first technically valid execution is binding.

PASS requires **all**:

- recovered@100 **> 80**;
- recovered@50 **>= 43**;
- recovered@25 **>= 22**;
- recovered@500 **>= 171**;
- top-100 dominant precision **>= 0.8075287489258385**;
- MRR **>= 0.02016666446026534**;
- qualified matches **== 256**.

A PASS freezes exactly this 36D representation with unchanged #1194 learning/ranking machinery. It does not authorize SonotaCo execution; any transfer test must be separately frozen under the current post-v60 governance rule.

A FAIL permanently closes this exact competitor-identity collision-probability augmentation.

## Closed rescue space

Do not rescue a FAIL with:

- Shannon/Renyi/Gini entropy variants;
- unique-competitor counts;
- dominant-competitor fraction;
- Simpson diversity, inverse collision probability, or log transforms;
- without-replacement pair probability;
- median/quantile/minimum/maximum or cross-year summaries;
- nearest-k competitors or softmax/distance-weighted identities;
- source-restricted, generator-restricted, graph-restricted, or shared-event-excluding competitors;
- distance margins, ratios, normalizations, or thresholding;
- graph spacing, member scatter, energy distance, thinning stability, predictive-consistency, or local-background fusion;
- feature subsets/interactions;
- estimator/hyperparameter changes;
- target, fold, sample-weight, or diversity changes;
- parent-score blending or alternate parent rankers;
- post-result representation/parameter search.

Any later successor must introduce a genuinely distinct mechanism and be separately frozen before outcome.

## Required guards

Before scientific interpretation, execution must verify:

- exact #1194 source Git blob and exact parent metrics/order;
- exact #839 ranker source SHA-256 `dd14e899ac08c4081cfee7d2dac2e54d2f25f78427cc4bee30f30296cd24b990`;
- exact v8/P19/P20 input hashes;
- exact 4,504 family IDs and source counts;
- parent feature shape `(4504,34)`;
- collision-feature shape `(4504,2)`;
- successor feature shape `(4504,36)`;
- all physical event-to-centroid distances finite;
- every nearest alternative excludes exactly the current family and otherwise searches all 4,503 candidates;
- deterministic fixed-array-order tie handling;
- every family has at least one member in each year and all annual centroids are finite;
- all collision-feature construction finishes before family truth/target use;
- strict whole-shower OOF isolation remains exact;
- candidate identities and memberships remain unchanged.

## Protected-data firewall

Throughout execution:

- protected solar longitude `[20.0,55.0]` remains excluded before labels, features, folds, scores and endpoints;
- `sonotaco_2013_2014_access = false`;
- `sonotaco_feature_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`.

This protocol authorizes only target-excluded GMN 2022/2023 development.