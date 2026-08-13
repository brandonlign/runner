# OrbitTrace GMN v31 class-conditional nearest-distance calibration v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 successor to the passed `orbittrace_gmn_v31_principle_local_geometry_oof_v1` parent. It tests exactly one mechanism: **calibrate the positive and nonpositive nearest-reference distances against their own fold-training class geometry before taking the class contrast**, rather than subtracting two raw nearest distances drawn from reference pools with different sizes and spacing.

This protocol is frozen before the first technically valid outcome. SonotaCo 2013/2014 is not accessed to evaluate, tune, or select this successor. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.

## Motivation fixed before outcome

The exact GMN v31-principle parent remains the champion on the immutable 226-family hard universe:

- recovered@25 = 23;
- recovered@50 = 41;
- recovered@100 = 66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified known-shower count = 95.

The successful mechanism is full 23D strict-whole-shower-OOF Euclidean nearest-positive versus nearest-nonpositive local geometry. Annual-min, physical-block consensus, local-scale relative margin, shrinkage Mahalanobis, fixed RRF, empirical Mutual Proximity, single-pass Tomek negative editing, and margin-confidence fusion all failed their frozen gates and remain closed.

A structural issue remains in the parent that those failures do not directly test: each held-out family is compared with the **single nearest positive** and **single nearest nonpositive** reference even though the two class-specific reference pools have different cardinalities and different internal spacing. The minimum of more distances is expected to be smaller even when the underlying geometry is otherwise comparable. Raw `d_nonpositive - d_positive` therefore mixes class affinity with class-specific nearest-neighbor scale/order-statistic effects.

Conformal prediction provides a parameter-free way to convert a nonconformity quantity into an empirical tail probability using only exchangeable calibration examples. Shafer & Vovk (JMLR 2008, *A Tutorial on Conformal Prediction*) explicitly note that conformal methods can be built on nearest-neighbor scores. OrbitTrace's earlier local-conformal work calibrated event-level sporadic-background scores; it did not calibrate v31 family-level positive/nonpositive reference distances and therefore does not constitute this experiment.

This successor is not a rescue of the failed v36 relative-distance normalization. v36 divided the two query-to-class distances by a local scale and retained an absolute-distance contrast. Here each class distance is evaluated against a **class-specific, group-leakage-safe training distribution of nearest-same-class distances**, yielding two empirical conformity probabilities before their contrast. No density radius, scale factor, metric parameter, or fitted coefficient is introduced.

## Immutable parent science

Before the successor is accepted as technically valid, reproduce the exact parent controls on the same code/input path:

- candidate count = 226;
- feature dimension = 23;
- recovered@25 = 23;
- recovered@50 = 41;
- recovered@100 = 66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified matches = 95.

Everything below remains exactly the passed parent:

- GMN 2022+2023 only;
- protected 20°–55° exclusion before scientific operations;
- immutable 226 P19 hard-family candidate universe and memberships;
- exact 23D intrinsic representation: 10 structural + 7 cohesion + 6 centroid-neighborhood;
- explicit hard-rank feature excluded from the local representation;
- exact deterministic five strict whole-shower folds;
- fold-training arithmetic mean / population-standard-deviation z-score, with zero standard deviation mapped to 1.0;
- exact positive/nonpositive truth/reference semantics;
- ordinary Euclidean distance;
- query-to-class nearest `k=1` only;
- exact diversity step `lambda=0.8`, `scale=1.0`;
- exact equal 1-based rank-sum fusion with the immutable hard-family order;
- exact truth and metric evaluator.

No candidate, membership, feature, metric, fold, reference label, diversity, fusion, truth, or evaluation change is authorized.

## Sole successor change: class-conditional empirical conformity of nearest distances

For each outer fold independently, after fitting the exact parent z-score on its training rows, let:

- `P` = positive training-reference rows;
- `N` = nonpositive training-reference rows;
- `g(i)` = the inherited strict whole-shower group identity of training row `i`;
- `d(a,b)` = ordinary Euclidean distance in the frozen standardized 23D representation.

### 1. Training-only class calibration distributions

For every positive training row `i in P`, define

`a_P(i) = min d(i,j)` over `j in P` with `g(j) != g(i)`.

For every nonpositive training row `i in N`, define

`a_N(i) = min d(i,j)` over `j in N` with `g(j) != g(i)`.

Thus a training example is calibrated as if its **entire strict shower group were absent**, matching the parent's anti-leakage semantics rather than merely excluding itself. If any row lacks an eligible same-class, different-group reference, the run fails closed.

No held-out row contributes to either calibration distribution. No outer-test truth, score, rank, or metric is used to construct the calibration distributions.

### 2. Held-out class distances

For each held-out query family `x`, compute the exact parent nearest-class distances against the outer-fold training references:

`d_P(x) = min_{j in P} d(x,j)`

`d_N(x) = min_{j in N} d(x,j)`.

### 3. Conservative empirical class-conformity values

For class `C in {P,N}`, define

`p_C(x) = (1 + |{i in C : a_C(i) >= d_C(x)}|) / (|C| + 1)`.

Larger `p_C` means the held-out query's nearest reference in class `C` is at least as geometrically plausible as more of the training-only leave-group-out class examples. The `+1` numerator/denominator convention is fixed before outcome.

### 4. Successor local score

Define the sole successor local-geometry score

`score_CC(x) = p_P(x) - p_N(x)`.

Larger scores mean stronger positive-class conformity relative to nonpositive-class conformity.

Apply the exact parent diversity step and exact equal rank-sum with the immutable hard order. No other scientific change is made.

## Explicitly fixed choices / no search

There is:

- no p-value threshold;
- no significance level;
- no logit, log-p, ratio, odds, Fisher/Stouffer combination, or other p-value transform;
- no class weight or prior correction;
- no smoothing beyond the fixed conservative `+1` convention;
- no alternative inequality direction;
- no query insertion into the calibration set;
- no held-out-fold pooling for calibration;
- no leave-one-family rather than leave-one-group calibration;
- no k search (`k=1` only);
- no metric, feature, scaling, fold, reference-definition, diversity, or fusion search;
- no source/year/budget-specific rule;
- no post-result second search.

## Frozen GMN promotion gate

The first technically valid result is binding. PASS requires the sole successor order simultaneously to satisfy against the exact reproduced parent:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 dominant precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified known-shower count **= 95**;
7. exact parent representation/candidate/firewall provenance checks pass.

If any gate fails, `GMN_V31_CLASS_CONDITIONAL_DISTANCE_V1` fails and this exact class-conditional calibration is permanently closed. No alternate p-value transform, threshold, pseudocount, calibration pooling, leave-one-family calibration, class-prior correction, weighted contrast, k, metric, feature, scaling, diversity, fusion, or result-informed rescue is authorized.

## SonotaCo boundary

Only a GMN PASS may authorize a separately frozen one-shot SonotaCo 2013/2014 comparison against exact v31 and the literature comparators. SonotaCo remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation. A later SonotaCo outcome may not be used to modify this successor.

## Firewall

Every execution must assert:

- `blind_exclusion = [20.0, 55.0]`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `sonotaco_2013_2014_access = false` during GMN development;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`.
