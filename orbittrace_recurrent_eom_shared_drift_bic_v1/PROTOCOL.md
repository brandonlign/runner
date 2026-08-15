# OrbitTrace recurrent-EOM shared-drift BIC v1 — frozen protocol

## Status

Frozen before implementation and before the first scientific outcome.

The scientific parent is exact recurrent-EOM HDBSCAN v1, selected as the current OrbitTrace paper/development method on PR #1243. This successor keeps the exact parent GEO6 representation, HDBSCAN parameters, pooled hierarchy, annual EOM calculation, and final ranking convention. Its sole scientific change is the scalar stability used inside HDBSCAN's EOM flat-cluster selection.

Scientific firewall remains binding:

- protected solar longitude `[20 deg,55 deg]` is inaccessible;
- no OrbitTrace target information/events;
- no MAARSY or DMS scientific access;
- no SonotaCo value enters this GMN development selection;
- no AMOS access or outreach;
- only target-excluded GMN 2022+2023 geometry and year identity may enter the new stability;
- parent and successor selected nodes, memberships, scores, and complete orders are frozen before shower truth is evaluated;
- the first technically valid GMN result is binding;
- no post-result response subset, polynomial order, BIC variant, prior, likelihood scale, annual threshold, stability blend, ranker, HDBSCAN setting, or other rescue is allowed.

## 1. Exact recurrent-EOM parent

Pinned recurrent-EOM implementation Git blob:

`30ac3fa3bc47910370df528fcf3ae8ecb6277b47`

Pinned recurrent-EOM development runner Git blob:

`fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`

Binding GMN parent run `31827903547`, artifact `9229646556`:

- prelabel SHA-256 `e304f6660697ed27a7e2e546ba2b9f2ecdb43f923745cb7424a3781ad55b9ad1`;
- result SHA-256 `433c641f57122b244b9476f5cbcb5e6f82956d9467270a9f24945600a32d2106`;
- recurrent candidate count `2,097`.

Exact parent configuration:

- GEO6 = `(cos(sol), sin(sol), sin(sun_lon)*cos(ecl_lat), cos(sun_lon)*cos(ecl_lat), sin(ecl_lat), vg/72)`;
- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- HDBSCAN EOM;
- `cluster_selection_epsilon=0`;
- `allow_single_cluster=False`;
- one pooled target-excluded GMN 2022+2023 hierarchy;
- annual normalized EOM `E_2022(C), E_2023(C)`;
- recurrent stability `E_rec(C)=min(E_2022(C),E_2023(C))`;
- recurrent-EOM extraction = standard HDBSCAN EOM with `E_rec` substituted for ordinary stability;
- parent rank = descending `E_rec`, descending ordinary stability, descending member count, ascending deterministic membership ID.

The fresh normal HDBSCAN fit used to expose the condensed hierarchy in this successor must reproduce the exact binding recurrent selected-node set and exact 2,097 parent membership/order before any new stability may be scientifically interpreted. Failure is an engineering no-result.

## 2. Physical motivation

The GEO representation uses Sun-centered ecliptic radiant coordinates because that frame substantially reduces meteor-shower radiant drift, but published Global Meteor Network measurements show that real showers generally retain small, statistically significant drift in Sun-centered radiant and often geocentric speed as solar longitude changes. Eleven of twelve major showers measured by Moorhead et al. exhibited significant drift in at least one Sun-centered radiant coordinate.

Recurrent-EOM asks whether a hierarchy branch has density persistence in both observing years, but it does not ask whether the **physical radiant/speed evolution is the same in both years**. A pooled branch can therefore receive high recurrent EOM even when its 2022 and 2023 members require different trajectories through observable space.

This successor adds a parameter-free model-comparison factor inside EOM selection: for every hierarchy node, compare one shared linear physical drift trajectory to two independent annual trajectories. Bayesian information criterion (BIC) supplies the complexity penalty; no empirical weighting coefficient is fitted.

This mechanism is distinct from prior closed lanes:

- candidate-internal predictive consistency used leave-one-out prediction only as a post-ranking diagnostic/fusion on a different candidate universe;
- recurrent flow-tube methods were separate candidate generators rather than HDBSCAN branch-selection objectives;
- directional morphology compared annual second moments rather than a shared-vs-separate physical drift model;
- consensus-EOM changed the vector decision rule without a physical trajectory likelihood;
- density-synchronous EOM compared annual density persistence across lambda scales, not physical drift agreement.

## 3. Fixed physical drift representation

For each accessible event use four response coordinates:

`Y = (r_x, r_y, r_z, log(vg))`

where the Sun-centered geocentric radiant unit vector is

- `r_x = cos(ecl_lat) cos(sun_lon)`;
- `r_y = cos(ecl_lat) sin(sun_lon)`;
- `r_z = sin(ecl_lat)`;

with angles in radians and positive geocentric speed `vg` in km/s.

The sole predictor is a fixed unwrapped accessible solar-longitude coordinate

`u = ((sol - 55 deg) mod 360 deg) / 10`.

Because the protected interval `[20,55]` is removed inclusively, the retained domain is one continuous 325-degree arc when unwrapped from 55 degrees. Division by 10 is the already-established numerical scaling used in the earlier label-free physical-predictability diagnostic; it changes coefficient units but not fitted values or BIC.

Every response coordinate uses the same ordinary least-squares design `[1,u]`. No quadratic term, spline, breakpoint, robust regression, clipping, response weighting, measurement uncertainty, or feature subset is permitted.

## 4. Sufficient statistics and annual model identifiability

For every HDBSCAN condensed-tree cluster node C and each year y, aggregate the exact descendant-event sufficient statistics needed for four ordinary least-squares regressions:

- `n`;
- `sum(u)`;
- `sum(u^2)`;
- `sum(Y_d)` for each of 4 responses;
- `sum(u Y_d)` for each response;
- `sum(Y_d^2)` for each response.

Statistics are additive and must be accumulated bottom-up on the exact condensed tree without using shower labels.

An annual design is identifiable only when:

- `n_y >= 3`; and
- `n_y * sum(u^2) - sum(u)^2 > 0`.

The `n_y>=3` requirement is mathematical rather than tuned: a two-parameter linear mean model needs at least one residual degree of freedom in each observing year for this model comparison. If either annual design is not identifiable, the shared-trajectory weight defined below is exactly `0` for that node.

No alternate minimum count is allowed.

## 5. Shared versus separate annual trajectory models

For an identifiable node C with total `N=n_2022+n_2023`, fit two nested Gaussian mean models independently for each of the four response dimensions.

### Shared model H_shared

Both years use one common intercept and slope:

`Y_d = a_d + b_d u + error`.

Across four responses this model has:

- 8 mean coefficients;
- 4 response-specific residual variances shared across years;
- total parameter count `k_shared=12`.

Let `RSS_shared,d` be the pooled OLS residual sum of squares for response d.

### Separate model H_sep

Each year has its own intercept and slope:

`Y_d = a_{d,y} + b_{d,y} u + error`.

Residual variance remains response-specific but shared across the two years, so the scientific comparison isolates annual changes in trajectory mean rather than changes in dispersion.

Across four responses this model has:

- 16 mean coefficients;
- 4 response-specific residual variances;
- total parameter count `k_sep=20`.

Let `RSS_sep,d = RSS_2022,d + RSS_2023,d`.

All RSS values must be finite and strictly positive. A nonpositive or nonfinite RSS is a fail-closed engineering error rather than a scientific degree of freedom.

Ignoring Gaussian constants common to both models, define

`BIC_shared(C) = sum_d [ N log(RSS_shared,d / N) ] + 12 log(N)`

and

`BIC_sep(C) = sum_d [ N log(RSS_sep,d / N) ] + 20 log(N)`.

Define the BIC evidence difference

`Delta_BIC(C) = BIC_sep(C) - BIC_shared(C)`.

Positive Delta_BIC favors one shared physical drift trajectory; negative Delta_BIC favors separate annual trajectories.

## 6. Parameter-free shared-trajectory weight

Use the standard equal-prior BIC approximation to the posterior weight of the shared model:

`W_shared(C) = 1 / [1 + exp(-Delta_BIC(C)/2)]`.

The implementation must evaluate this logistic transform with a numerically stable exact algebraic form but may not clip Delta_BIC or W_shared scientifically.

For an unidentifiable node, `W_shared(C)=0` exactly.

The sole successor stability is

`E_shared(C) = E_rec(C) * W_shared(C)`.

This is the **only** scientific change relative to recurrent-EOM v1.

No additive blend, exponent, prior odds, threshold on Delta_BIC, minimum weight, response-specific weight, or fitted coefficient is permitted.

## 7. Flat-cluster extraction and ranking

Run the exact same HDBSCAN EOM tree optimization used by recurrent-EOM, substituting `E_shared` for recurrent stability.

The root remains excluded exactly as in the parent. Label assignment uses the existing audited `eom_labels` pathway.

The successor rank intentionally stays the recurrent-EOM ranking convention so a positive result is attributable to branch selection rather than a second new ranker:

1. descending original `E_rec` of the selected node;
2. descending ordinary HDBSCAN stability;
3. descending member count;
4. ascending deterministic membership-derived family ID with provenance prefix `REOMBIC1`.

`W_shared` and `E_shared` are recorded but are **not** additional ranking keys.

No post-filter, candidate trim, reranker, v31 fusion, probability score, or outlier score is permitted.

## 8. Pretruth engineering invariants

Before shower truth can be evaluated, the binding runner must prove all of:

1. exact target-excluded event counts `315024 / 423658`, pooled `738682`;
2. exact inclusive protected `[20,55]` exclusion;
3. exact pinned recurrent-EOM source identity;
4. a normal HDBSCAN fit with the exact parent settings reproduces the binding recurrent selected-node set;
5. exact binding recurrent candidate count `2,097`;
6. complete parent candidate membership/order equals the binding recurrent prelabel artifact exactly;
7. bottom-up sufficient-statistic aggregation reproduces exact member counts for every binding recurrent selected node;
8. shared/separate BIC inputs and weights are finite for every identifiable cluster node;
9. the complete successor selected-node set, memberships, original recurrent scores, BIC quantities, and pooled order are persisted and SHA-256 frozen before shower truth is used.

Any pretruth mismatch is an engineering no-result and does not authorize modifying the scientific rule.

## 9. Binding GMN evaluation and gate

Use the exact recurrent-EOM annual evaluator and truth convention.

The first technically valid GMN result is binding. Shared-drift BIC v1 passes only if all conditions hold relative to exact recurrent-EOM:

1. successor selected-node set differs from recurrent-EOM (`mechanism_active=true`);
2. recovered@100 is strictly higher in at least one year and not lower in the other;
3. recovered@50 is not lower in either year;
4. top-100 dominant precision is not lower in either year;
5. MRR is not lower in either year;
6. median top-500 fragmentation is not higher in either year.

Recovered@25, recovered@500, full-catalogue qualified matches, candidate count, Delta_BIC distribution, and shared-weight distribution are reporting-only.

PASS token:

`PASS_RECURRENT_EOM_SHARED_DRIFT_BIC_V1_GMN_DEVELOPMENT`

FAIL token:

`FAIL_RECURRENT_EOM_SHARED_DRIFT_BIC_V1_GMN_DEVELOPMENT`

A scientific FAIL permanently closes this exact shared-linear-drift/BIC weighting mechanism. No polynomial-order change, different response coordinates, variance model, BIC/AIC substitution, prior odds, weight transform, stability blend, annual count rule, or reranking rescue is allowed from the outcome.

A PASS authorizes one separately frozen direct exposed SonotaCo benchmark against recurrent-EOM, v31, and the already-frozen matched literature comparators. It does not authorize target-region access.

## 10. Claim boundary if supported

If successful, the contribution is **physically recurrent EOM clustering**: HDBSCAN provides the density hierarchy, recurrent-EOM requires persistence across observing years, and BIC-weighted branch selection additionally rewards hierarchy nodes whose independent annual samples are statistically consistent with one shared radiant-and-speed drift trajectory.

HDBSCAN and the meteor-radiant-drift literature remain explicit antecedents; the novelty claim is the integration of cross-year physical model evidence into HDBSCAN EOM branch selection.