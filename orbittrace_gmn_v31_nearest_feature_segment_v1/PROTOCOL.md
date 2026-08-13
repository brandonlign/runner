# OrbitTrace GMN v31 local nearest-feature-segment v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 successor to the passed `orbittrace_gmn_v31_principle_local_geometry_oof_v1` parent. It tests one structural mechanism only: replace each class's nearest **point prototype** distance by the distance to the closed segment joining the two nearest prototypes from that same class, while preserving the exact v31 representation, OOF split, labels, diversity, fusion, candidates, and metric evaluator.

This protocol is frozen before the first technically valid outcome. SonotaCo 2013/2014 is not accessed to evaluate, tune, or select this successor. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.

## Motivation fixed before outcome

The exact GMN v31-principle parent remains the champion on the immutable 226-family hard universe:

- recovered@25 = 23;
- recovered@50 = 41;
- recovered@100 = 66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified known-shower count = 95.

The surviving signal is specifically full-space strict-whole-shower-OOF Euclidean local geometry. Annual-min, physical-block consensus, local-scale relative margin, shrinkage Mahalanobis, fixed RRF, empirical Mutual Proximity, single-pass Tomek negative editing, margin-confidence fusion, and class-conditional nearest-distance calibration all failed their frozen promotion gates and remain closed.

Nearest Feature Line methods were introduced to generalize a finite set of point prototypes into simple within-class geometric objects; later work identified unrestricted line extrapolation as a failure mode and developed feature-line **segments**. Locally-nearest-neighbor line methods further restrict the construction to prototypes local to the query. This is scientifically aligned with the v31 problem: a recurrent-shower family class may occupy a locally continuous region of the frozen 23D family representation, so distance to a short local within-class segment can represent interpolation between observed reference fragments rather than requiring a held-out family to lie near one discrete point.

The closed-segment construction is deliberately chosen over an infinite line to prohibit extrapolation beyond the two observed prototypes. The two endpoints are the two nearest same-class training references to the query, making the construction deterministic and parameter-free. No pair search, segment selection threshold, class cleanup, learned manifold, or dimensionality parameter is introduced.

This is not a Tomek/ENN rescue. No training reference is deleted, relabeled, filtered, reweighted, or replaced. All exact parent references remain eligible for every held-out query. The Tomek no-go on k-neighbor generalization applies to boundary-editing variants; this successor performs no boundary editing.

## Immutable parent science

Before candidate science, reproduce the exact parent and require:

- candidate count = 226;
- feature dimension = 23;
- prelabel SHA-256 = `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`;
- feature-matrix SHA-256 = `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- raw parent OOF-margin SHA-256 = `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`;
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
- ordinary Euclidean geometry;
- exact diversity `lambda=0.8`, `scale=1.0`;
- exact equal 1-based rank-sum fusion with the immutable hard-family order;
- exact truth and metric evaluator.

No candidate, membership, feature, label, fold, scaling, diversity, fusion, truth, or metric rule changes.

## Sole successor change: nearest same-class closed segment

Within each exact parent outer OOF fold, after fitting the exact parent z-score on the training rows, consider one held-out query `x` and one reference class `C` (positive or nonpositive).

Let the standardized training references in `C` be `z_1,...,z_m`. Require `m >= 2`.

1. Compute ordinary Euclidean query-to-reference distances `||x-z_j||`.
2. Select the two distinct nearest class references `a` and `b` by ascending distance. Exact distance ties are broken by immutable hard-family rank, then family ID. No reference is removed from eligibility.
3. Define the closed segment

   `S_C(x) = { a + t(b-a) : 0 <= t <= 1 }`.

4. Compute the orthogonal projection coefficient

   `t_raw = ((x-a) dot (b-a)) / ||b-a||^2`.

   If `||b-a||^2 == 0`, define the segment distance as `||x-a||` and fail closed unless `a` and `b` are finite distinct candidate identities.

5. Otherwise clip `t = min(1,max(0,t_raw))` and define

   `d_C_segment(x) = ||x - (a + t(b-a))||`.

The successor local score is

`segment_margin(x) = d_nonpositive_segment(x) - d_positive_segment(x)`.

Higher is better, exactly matching the parent margin orientation.

After all 226 strict-OOF segment margins are computed, apply the exact parent diversity step and exact equal hard-order rank fusion unchanged.

## Explicitly fixed choices / no search

There is:

- exactly two nearest same-class endpoints;
- a **closed segment**, never an infinite line;
- no requirement that the two endpoints belong to different strict groups beyond the outer fold's existing test-group exclusion;
- no endpoint averaging or centroid replacement;
- no all-pairs feature-line search;
- no segment-length threshold;
- no interpolation/extrapolation weight;
- no local dimension or number-of-neighbors search;
- no metric, feature, scaling, fold, reference-definition, diversity, or fusion search;
- no reference deletion, relabeling, filtering, or weighting;
- no source/year/budget-specific rule;
- no post-result second search.

If the candidate fails, no infinite-line variant, all-pairs feature-line variant, nearest-three plane/simplex, endpoint group restriction, length cutoff, weighted point/segment blend, transformed segment margin, or result-informed rescue is authorized from this outcome.

## Frozen GMN promotion gate

The first technically valid result is binding. PASS requires the sole successor order simultaneously to satisfy against the exact reproduced parent:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 dominant precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified known-shower count **= 95**;
7. exact parent representation/candidate/firewall provenance checks pass.

If any gate fails, `GMN_V31_NEAREST_FEATURE_SEGMENT_V1` fails and this exact local closed-segment mechanism is permanently closed.

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
