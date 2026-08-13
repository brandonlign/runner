# OrbitTrace GMN v31 exact nearest-prototype robustness v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 successor to the passed `orbittrace_gmn_v31_principle_local_geometry_oof_v1` parent. It tests exactly one mechanism:

> Replace v31's raw nearest-class distance-gap score by the **signed exact Euclidean robustness radius of the same frozen 1-nearest-prototype binary classifier** in each strict OOF fold.

The parent representation, standardization, positive/nonpositive reference sets, nearest-prototype classifier, candidates, folds, diversity, immutable hard order, equal rank-sum fusion, truth semantics, and evaluator remain unchanged.

This protocol is frozen before the first technically valid outcome. SonotaCo 2013/2014 is not accessed to evaluate, tune, or select this successor. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.

## Independent motivation fixed before outcome

The exact v31 local classifier in standardized 23D space is a binary nearest-prototype classifier: for a held-out family `x`, it predicts positive iff the nearest positive training reference is closer than the nearest nonpositive training reference. The parent ranking score

`m_v31(x) = d_nonpositive(x) - d_positive(x)`

has the same sign as that 1-NN decision and is useful on both target-excluded GMN and exposed SonotaCo.

Voráček & Hein (ICML 2022, *Provably Adversarially Robust Nearest Prototype Classifiers*) analyze exactly this classifier family. For Euclidean nearest-prototype classifiers, the familiar nearest-opposite minus nearest-same distance gap gives a lower bound on the minimal perturbation required to change class, while the **exact** Euclidean robustness radius is obtained by considering the full prototype arrangement. For a fixed opposite-class prototype `j`, one finds the smallest perturbation that places the query in the region where `j` is at least as close as every prototype of the current class; the exact class-flip radius is the minimum over all opposite-class prototypes.

This is scientifically distinct from the closed relative-margin/normalization lane. The exact radius is not a rescaling, ratio, denominator, monotone transform, or other function of only the nearest positive and nearest nonpositive distances. It depends on all prototypes of the currently predicted class and all opposite-class candidate prototypes through the nearest-prototype Voronoi decision geometry.

It is also distinct from Tomek/ENN editing and metric learning: no reference is deleted, relabeled, reweighted, or moved; ordinary Euclidean geometry is retained; no metric is fitted; no k, threshold, radius hyperparameter, feature subset, or learned coefficient is introduced.

Primary reference fixed before outcome:
- Voráček, V. & Hein, M. (2022), *Provably Adversarially Robust Nearest Prototype Classifiers*, Proceedings of ICML 2022, PMLR 162.

## Authoritative deterministic GMN package

Use only the verified target-excluded GMN v31 offline package:

- workflow run `31663453082`;
- artifact `9167087908`;
- artifact digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`;
- package manifest SHA-256 `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- exact 226x23 feature matrix SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- exact 226x8 centroid matrix SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent prelabel SHA-256 `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`;
- parent raw OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

The package contains no raw GMN event rows, raw event IDs, or raw hidden-label event mapping.

Before successor science, the evaluator must reproduce the exact immutable hard-order control:

- recovered@25 = 21;
- recovered@50 = 38;
- recovered@100 = 59;
- top-100 dominant precision = 0.6884631112636006;
- MRR = 0.046734076055452344;
- qualified matches = 95.

It must also require the package's exact v31 fused control:

- recovered@25 = 23;
- recovered@50 = 41;
- recovered@100 = 66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified matches = 95.

Any mismatch fails before successor evaluation.

## Immutable v31 parent science

Everything below remains fixed:

- exact 226 P19 hard-family candidates;
- exact 23D intrinsic representation;
- exact strict whole-shower groups and deterministic five folds;
- fold-training arithmetic mean / population-standard-deviation z-score, zero standard deviation mapped to 1.0;
- exact frozen positive/nonpositive family truth semantics;
- ordinary Euclidean metric;
- exact 1-nearest-prototype binary decision;
- exact 226x8 centroid matrix used only by inherited diversity;
- exact diversity `lambda=0.8`, `scale=1.0`;
- exact equal 1-based rank-sum fusion with immutable P19 hard order;
- exact monotone evaluator over 355 eligible labels.

No candidate, membership, truth, feature, fold, standardization, reference, diversity, fusion, or evaluation rule changes.

## Sole successor change: signed exact Euclidean 1-NPC robustness radius

For each outer OOF fold independently, after exact parent z-scoring, let training prototypes be split into `P` (positive) and `N` (nonpositive).

For each held-out query `z`:

### 1. Exact frozen 1-NPC class

Compute

`d_P = min_{p in P} ||z-p||_2`

`d_N = min_{n in N} ||z-n||_2`.

The current class `c(z)` is positive iff `d_P < d_N`; nonpositive iff `d_N < d_P`. An exact equality is broken deterministically by the immutable hard-family rank and then family ID of the tied nearest prototypes; no tolerance is used for the scientific tie rule.

### 2. Exact class-flip region for one opposite prototype

Let `C` denote all prototypes of the current class and let `w_j` be one prototype of the opposite class. A point `u` is classified at least as favorably for opposite prototype `j` as for every current-class prototype exactly when

`||u-w_j||_2^2 <= ||u-w_i||_2^2` for every `w_i in C`.

Each condition is the linear halfspace

`(w_i - w_j)^T u <= (||w_i||_2^2 - ||w_j||_2^2)/2`.

For fixed `j`, define `P_j` as the intersection of all these halfspaces.

Compute the Euclidean projection distance

`rho_j(z) = min_u ||u-z||_2 subject to u in P_j`.

### 3. Exact robustness radius

The exact nearest-prototype class-flip radius is

`rho(z) = min_{j in opposite class} rho_j(z)`.

This minimum is evaluated over **every** opposite-class training prototype; no candidate pruning, lower-bound screening, approximate nearest-opposite subset, or early scientific stopping is allowed.

### 4. Signed ranking score

Define

`robustness_score(z) = +rho(z)` if the frozen 1-NPC class is positive,

`robustness_score(z) = -rho(z)` if the frozen 1-NPC class is nonpositive.

Higher is better. This preserves the parent classifier sign while replacing the nearest-distance lower-bound magnitude with the exact distance to the full 1-NPC decision boundary.

After all 226 strict-OOF scores are computed, apply exact inherited diversity and exact equal hard-order rank fusion unchanged.

## Deterministic convex-QP implementation

For fixed opposite prototype `j`, write the halfspaces as `A u <= b` with one row per current-class prototype. Solve the strictly convex projection QP

`min_u 0.5 ||u-z||_2^2  subject to A u <= b`.

The implementation uses SciPy SLSQP only as a numerical solver for this fixed mathematical quantity; solver settings are engineering constants frozen before outcome:

- `method='SLSQP'`;
- analytic objective gradient `u-z`;
- analytic inequality Jacobian `-A` in SciPy's `b-Au >= 0` convention;
- `ftol = 1e-12`;
- `maxiter = 1000`;
- no bounds and no stochastic initialization;
- initial point `z` for every fixed-`j` QP.

A QP is accepted only if all of the following fixed numerical checks pass:

1. solver reports success;
2. solution/objective are finite;
3. maximum primal halfspace violation `max(Au-b) <= 1e-8`;
4. returned perturbation norm is not smaller than the analytic two-prototype lower bound to the nearest current/opposite bisector by more than `1e-8`;
5. the projected point satisfies `||u-w_j|| <= min_{i in C} ||u-w_i|| + 1e-7`.

If any fixed-`j` QP fails these checks, the entire method is technically invalid; it is not silently skipped and no alternate optimizer/tolerance is tried after scientific execution.

## Solver validation before GMN science

The workflow must pass deterministic analytic tests before reading the offline GMN package into the successor calculation:

- 1D single-prototype case with known midpoint robustness;
- 2D single-prototype-per-class case where the robustness is the perpendicular distance to the bisector;
- 2D multi-prototype case where the nearest-pair distance-gap lower bound is strictly smaller than the exact polyhedral robustness radius, verified against an independently constructed active boundary intersection;
- sign symmetry when positive/nonpositive labels are swapped.

These are engineering validation tests only; they do not use GMN/SonotaCo data or alter the scientific rule.

## Explicit no-search rules

There is:

- no k search (`k=1` classifier fixed);
- no prototype pruning/subsampling;
- no approximate radius or lower-bound blend;
- no relative-margin/ratio/log/normalization transform;
- no radius clipping, threshold, exponent, temperature, or calibration;
- no class-prior weighting;
- no reference deletion/relabeling/filtering/weighting;
- no learned metric;
- no feature/scaling/fold/reference/diversity/fusion search;
- no alternate optimizer after a technically valid scientific outcome;
- no source/year/budget-specific rule;
- no post-result second search.

If the first technically valid result fails, no lower-bound/exact-radius blend, alternate radius transform, prototype subset, solver-based variant, signed/unsigned variation, or result-informed rescue is authorized from this outcome.

## Frozen GMN promotion gate

The first technically valid result is binding. PASS requires every condition against exact v31 GMN parent:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 dominant precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified matches **= 95**;
7. all package/evaluator/fold/QP/firewall assertions pass.

## SonotaCo boundary

Only a GMN PASS may authorize a separately frozen one-shot SonotaCo 2013/2014 comparison against exact v31 and literature. SonotaCo remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation. No later SonotaCo outcome may modify this successor.

## Firewall

Every execution must assert:

- `blind_exclusion = [20.0, 55.0]`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `sonotaco_2013_2014_access = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- `raw_event_rows_accessed = false`;
- `raw_event_ids_accessed = false`;
- `raw_hidden_label_mapping_accessed = false`.
