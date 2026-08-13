# OrbitTrace GMN v31 reverse-1NN slack local geometry v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 architectural successor to the passed v31 local-geometry parent.

The exact v31 parent uses query-directed 1-nearest-neighbour support: for a held-out family `z`, it compares the distance to the nearest positive training family against the distance to the nearest nonpositive training family.

Two already-frozen GMN diagnostics now localize the remaining top-100 failure:

1. the constituent-bottleneck diagnostic found that **21 of the 29** qualified labels missed by exact fused v31 are outside the top 100 of both frozen constituents;
2. the margin-sign bottleneck diagnostic found that **all 21 of those constituent-absent labels** have no positive family with raw v31 margin `> 0`; every positive representative is at least as close to a nonpositive training reference as to a positive one.

Therefore another fusion or scalar calibration of the same query-directed `d_neg-d_pos` evidence is poorly aligned with the measured failure mechanism. This successor changes the local support relation itself while retaining the same 23D standardized Euclidean representation, same training families, same strict folds, same diversity, and same fusion.

The sole scientific change is to use **reverse-1NN slack**: how deeply the held-out query enters each training reference's own label-blind nearest-neighbour radius.

This protocol is frozen before the first technically valid outcome. No SonotaCo result is accessed to design, tune, or select it.

## Independent methodological basis fixed before outcome

For a training point `r`, let `rho(r)` be its distance to its nearest *other training point*. A query `z` is a reverse 1-nearest-neighbour of `r` exactly when inserting `z` makes `z` at least as close to `r` as every pre-existing training neighbour, i.e. when `||z-r|| <= rho(r)` (with exact deterministic tie semantics fixed below).

Reverse nearest-neighbour queries are a standard geometric object: they return the data points for which the query becomes the nearest neighbour. See, for example:

- Cheong, Vigneron & Yon (2009), *Reverse nearest neighbor queries in fixed dimension*, arXiv:0905.4441.

Reverse-neighbour methods have also been used specifically to describe local density structure and varying-density clusters:

- Chowdhury & de Amorim (2018), *An efficient density-based clustering algorithm using reverse nearest neighbour*, arXiv:1811.07615.

The OrbitTrace hypothesis is narrower: if a positive training reference lies in a naturally sparse part of the frozen 23D family manifold, ordinary query-directed 1-NN gives it no larger sphere of influence than a reference in a dense region. Its label-blind training 1-NN radius `rho(r)` provides a parameter-free local support radius. A held-out positive family can therefore receive positive-class support from a sparse positive reference even when a somewhat closer nonpositive reference exists in a denser region.

This is not a fitted global metric or classifier. `rho(r)` is computed without using the class label and without any bandwidth, k search, covariance, feature weight, or learned transform.

## Relation to closed lanes

This successor is deliberately distinct from already-closed mechanisms:

- **relative-margin normalization** rescales the query's same two distances `d_pos` and `d_neg` by their own average; reverse-1NN slack instead changes each training reference's support boundary using a label-blind radius computed from training-to-training geometry;
- **class-conditional distance calibration / Mutual Proximity** calibrate query-reference distances by empirical distance distributions; this successor applies no empirical CDF, class conditional calibration, or pairwise probability transform;
- **Tomek negative editing** deletes ambiguous training negatives using mutual opposite-class nearest-neighbour pairs; this successor deletes, relabels, prunes, or multiplicatively weights no reference;
- **positive-support / one-class** removes the negative contrast; this successor retains a symmetric positive-versus-nonpositive support comparison;
- **second-support radius** changes query-directed neighbour order to k=2; this successor remains reverse `k=1` only and does not average or vote over query neighbours;
- **group prototypes / nearest-feature-segment** alter the reference geometry by averaging or interpolation; this successor keeps every exact observed family point and creates no segment, centroid, simplex, hull, or synthetic prototype;
- **shrinkage Mahalanobis / LFDA / balanced Fisher** learn global supervised geometry; this successor retains exact fold-standardized Euclidean 23D geometry and learns no supervised transformation;
- **margin-confidence / RRF** alter fusion; fusion is unchanged;
- **exact 1-NPC robustness** measures minimum perturbation to the full 1-NN decision boundary and is closed as a technical no-go; reverse-1NN support is a different directed neighbourhood relation and is not an approximate robustness radius or fallback solver.

## Authoritative deterministic GMN package

Use only the verified target-excluded GMN v31 offline package:

- workflow run `31663453082`;
- artifact `9167087908`;
- artifact digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`;
- manifest SHA-256 `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- feature matrix SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- centroid matrix SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent prelabel SHA-256 `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`;
- parent raw OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

The package contains no raw GMN event rows, raw event IDs, raw hidden event-label mapping, SonotaCo data, protected target-region data, MAARSY, or DMS.

Before successor interpretation require exact hard-order and exact v31 fused controls:

Hard:
- @25 = 21;
- @50 = 38;
- @100 = 59;
- precision = 0.6884631112636006;
- MRR = 0.046734076055452344;
- qualified = 95.

Exact v31 fused:
- @25 = 23;
- @50 = 41;
- @100 = 66;
- precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified = 95.

## Immutable parent science

Keep fixed:

- exact 226 P19 hard-family candidates and memberships;
- immutable hard order;
- exact 23D family representation and column order;
- target-excluded GMN 2022+2023 development universe;
- exact deterministic five strict whole-shower OOF folds;
- fold-training arithmetic mean / population-standard-deviation z-score, with zero standard deviation mapped to 1.0;
- exact positive/nonpositive recoverability truth semantics;
- ordinary Euclidean metric;
- exact 226x8 centroid matrix used only by inherited diversity;
- diversity `lambda=0.8`, `scale=1.0`;
- equal 1-based rank-sum fusion with immutable hard order;
- exact monotone evaluator over 355 eligible labels.

No candidate, membership, fold, truth, feature, scaling, metric, diversity, fusion, or evaluator change is allowed.

## Sole scientific change: label-blind reverse-1NN slack

For each exact outer OOF fold independently:

1. fit the exact parent z-score on fold-training rows only;
2. transform fold-training and held-out rows with that z-score;
3. for every training reference `r_j`, compute its **label-blind training 1-NN radius**

   `rho_j = min_{k != j} ||r_j - r_k||_2`

   over **all** other fold-training references regardless of class;
4. require every `rho_j` finite and strictly positive.

No same-class radius, opposite-class radius, k>1 radius, averaged radius, median radius, clipping, floor, shrinkage, or global radius is evaluated.

For held-out standardized query `z`, define each reference's reverse-neighbour slack

`a_j(z) = rho_j - ||z-r_j||_2`.

Interpretation:

- `a_j(z) > 0`: `z` lies strictly inside `r_j`'s training 1-NN radius;
- `a_j(z) = 0`: exact boundary tie;
- `a_j(z) < 0`: `z` lies outside that radius.

Define class support by the **single maximum slack** in each frozen class:

`A_pos(z) = max_{j: positive} a_j(z)`

`A_neg(z) = max_{j: nonpositive} a_j(z)`.

The sole successor raw score is

`m_reverse(z) = A_pos(z) - A_neg(z)`.

Higher is better.

Equivalently, this is a 1-nearest-reference classifier in an **additively radius-adjusted** distance `||z-r_j||_2 - rho_j`, but `rho_j` is label-blind and fixed entirely by the fold-training geometry.

For exact ties in a class support maximum, choose the reference with earlier immutable hard rank and then lexicographically smaller family ID. This tie choice affects only provenance/reference identity, not the numeric score.

In the same execution, recompute the exact ordinary v31 parent OOF margin and require its full SHA-256 to equal the frozen parent margin before interpreting `m_reverse`.

## Frozen score-unit preservation

The inherited diversity penalty is additive in the local score units. Reverse slack is in Euclidean-distance units but can have a different empirical scale from the parent margin.

Before outcome, fix the same positive-scalar unit-preservation principle used in earlier v31 architectural comparisons:

- `S_parent = median(abs(m_parent))`;
- `S_reverse = median(abs(m_reverse))`;
- require both finite and strictly positive;
- `unit_factor = S_parent / S_reverse`;
- sole score entering inherited diversity: `m_reverse_scaled = m_reverse * unit_factor`.

If `S_reverse == 0` or is nonfinite, the method is a **technical no-go**. No mean, nonzero-only median, quantile, epsilon, fallback scaling, or diversity removal is permitted.

Positive scalar rescaling cannot alter the pre-diversity reverse-score ordering or sign.

## Frozen post-score machinery

After all 226 strict-OOF reverse scores are computed:

1. apply exact inherited diversity with `lambda=0.8`, `scale=1.0` and exact parent centroid matrix;
2. construct exactly one candidate by equal 1-based rank-sum fusion of the diversified reverse-slack order with immutable P19 hard order;
3. evaluate exactly once with the parent monotone evaluator.

The reverse local-only order and fixed support diagnostics are recorded but cannot rescue a failed fused candidate.

## Fixed support diagnostics recorded without tuning

For provenance only, record:

- per fold minimum/median/maximum training `rho_j`;
- per held-out family `A_pos`, `A_neg`, raw reverse score, and winning positive/nonpositive reference IDs;
- whether `A_pos > 0` and whether `A_neg > 0`;
- counts of held-out families falling inside at least one positive or nonpositive reverse-1NN radius.

These do not create alternate scores or gates.

## Explicit no-search / no-rescue rules

There is:

- reverse support order `k=1` only;
- all-class label-blind `rho_j` only;
- no same-class or opposite-class radius;
- no k search;
- no reverse-neighbour count score;
- no count/slack blend;
- no sum, mean, median, vote, kernel, or weighted aggregation over reverse neighbours;
- no clipping or positive-part transform of `a_j`;
- no query-directed parent-margin blend;
- no density exponent, bandwidth, temperature, threshold, epsilon, or radius multiplier;
- no reference deletion, relabeling, pruning, multiplicative weighting, or prototype construction;
- no metric, feature, scaling, or covariance change;
- no class-conditional calibration;
- no graph propagation;
- no diversity or fusion search;
- no source/year/budget-specific rule;
- no post-result second reverse-neighbour variant.

If the first technically valid result fails, reverse k>1, same-class radii, radius multipliers, RNN counts, clipped penetration, sum/mean reverse support, parent/reverse blends, or other result-informed reverse-neighbour rescues are forbidden from this outcome.

## Frozen GMN promotion gate

The first technically valid result is binding. PASS requires every condition against exact v31:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 dominant precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified matches **= 95**;
7. exact package/evaluator/parent-margin/fold/firewall assertions pass.

Failure of any gate permanently rejects this exact reverse-1NN-slack successor.

## SonotaCo boundary

Only a GMN PASS may authorize a separately frozen one-shot exposed SonotaCo 2013/2014 comparison against exact v31 and the literature comparators. The already-established exact 23D GMN→SonotaCo feature correspondence from the v62/v63 lineage must be reused unchanged. SonotaCo remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation. No SonotaCo outcome may modify this method.

## Firewall

Every execution must assert:

- `blind_exclusion = [20.0,55.0]`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `sonotaco_2013_2014_access = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- `raw_event_rows_accessed = false`;
- `raw_event_ids_accessed = false`;
- `raw_hidden_label_mapping_accessed = false`.
