# OrbitTrace GMN v31 positive-support local geometry v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 successor to the passed `orbittrace_gmn_v31_principle_local_geometry_oof_v1` parent. It tests one mechanism only:

> Does the v31 local leg transfer more cleanly when it is used as a **one-class support score for recoverable recurrent-shower geometry**, rather than treating the heterogeneous complement of nonqualified families as a coherent negative class?

The sole local score is the negative Euclidean distance to the nearest positive training reference in the exact parent standardized 23D representation. The exact parent diversity step and immutable P19 hard-order fusion remain unchanged.

This protocol is frozen before the first technically valid outcome. SonotaCo 2013/2014 is not accessed to evaluate, tune, or select this successor. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.

## Independent scientific motivation fixed before outcome

The parent defines a positive reference as a family satisfying the frozen recurrent-shower recoverability semantics (`precision >= 0.5` and `overlap >= 4` for the best eligible shower). Its complementary `nonpositive` set is not a single physical population: it includes unrelated background-like families, weak fragments, insufficient-overlap shower fragments, and other families that fail one or more qualification conditions. Therefore the binary positive-versus-nonpositive geometry implicitly asks one nearest-neighbor contrast to model a heterogeneous open complement as though it were a coherent class.

One-class classification/data-description methods are specifically motivated by settings where a target class is characterized but the non-target distribution is absent, heterogeneous, or not meaningfully modelled as one class. Nearest-neighbor one-class methods use proximity to stored target examples as a nonparametric support/data-description quantity. This successor applies only that principle; it does not fit an acceptance threshold because OrbitTrace needs a ranking score, not a binary one-class decision.

The previously observed Tomek negative-edit near-pass is only contextual consistency with this motivation. It does **not** define this method: no Tomek identity, boundary relation, deleted reference, threshold, k value, or result-informed subset enters the successor. Every positive reference is exactly the parent positive set, and the local leg simply does not define a negative class.

## Authoritative deterministic development package

Use only the verified engineering package produced by exact parent run wrapper:

- package workflow run `31663453082`;
- artifact `9167087908`;
- artifact digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`;
- manifest SHA-256 `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- exact 226x23 X SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- exact 226x8 centroid matrix SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent prelabel SHA-256 `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`;
- parent OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

The package contains no raw GMN event rows, raw event IDs, or raw hidden-label event mapping. It contains only the already-frozen target-excluded family-level development representation, centroids, hard order, strict groups/folds, eligible-label names, and family truth summaries.

Before evaluating the successor, the offline evaluator must reproduce the exact parent hard-order metrics from those summaries:

- recovered@25 = 21;
- recovered@50 = 38;
- recovered@100 = 59;
- top-100 dominant precision = 0.6884631112636006;
- MRR = 0.046734076055452344;
- qualified matches = 95.

It must also require the authoritative parent fused control recorded by the package:

- recovered@25 = 23;
- recovered@50 = 41;
- recovered@100 = 66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified matches = 95.

If any package hash, schema, firewall assertion, hard-order metric, or parent control differs, the run fails before successor evaluation.

## Immutable parent science

Everything below remains exactly the passed v31 GMN parent:

- candidate universe: exact 226 P19 hard families;
- feature representation: exact 23D intrinsic matrix;
- strict group identities and deterministic five folds;
- fold-training arithmetic mean / population-standard-deviation z-score, with zero standard deviation mapped to 1.0;
- positive-reference truth semantics;
- ordinary Euclidean distance;
- query nearest-neighbor count `k=1`;
- exact centroid matrix used by diversity;
- exact diversity `lambda=0.8`, `scale=1.0`;
- exact equal 1-based rank-sum fusion with immutable P19 hard order;
- exact monotone recovery/precision/MRR evaluator and 355 eligible labels.

No candidate, membership, feature, truth, fold, scaling, metric, diversity, fusion, or evaluation rule changes.

## Sole successor change: one-class positive-support score

For each outer fold independently:

1. Fit the exact parent z-score on **all training rows** in that fold.
2. Transform training and held-out rows with that fold-training mean and scale.
3. Let `P` be the standardized training rows whose frozen family truth has `positive == true`.
4. Require `P` nonempty.
5. For each held-out family `x`, compute

   `d_positive(x) = min_{p in P} ||x - p||_2`.

6. Define the sole local score

   `positive_support(x) = -d_positive(x)`.

Higher is better. No nonpositive reference distance is computed or used in the local leg.

After all 226 strict-OOF scores are computed:

- apply the exact parent diversity order with `lambda=0.8`, `scale=1.0`;
- fuse that local order with the immutable hard order by the exact parent equal rank-sum;
- evaluate with the exact parent monotone metrics.

## Explicitly fixed choices / no search

There is:

- positive nearest-neighbor `k=1` only;
- raw `-d_positive` only;
- no one-class threshold;
- no radius, quantile, percentile, density ratio, local-density normalization, nearest-neighbor-of-nearest-neighbor normalization, or conformal calibration;
- no negative reference deletion/editing/weighting because the local mechanism is one-class by definition;
- no positive reference filtering or weighting;
- no positive prototype/centroid/segment/manifold construction;
- no feature subset, transform, metric, scaling, fold, diversity, or fusion search;
- no hard-order weight search;
- no source/year/budget-specific rule;
- no post-result second search.

A failure closes this exact positive-support mechanism. No `k>1`, normalized positive distance, target-density ratio, thresholded support, positive-reference pruning, hard/local blend weight, or result-informed rescue is authorized from this outcome.

## Frozen GMN promotion gate

The first technically valid result is binding. PASS requires the sole successor order simultaneously to satisfy against the exact v31 GMN parent:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 dominant precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified known-shower count **= 95**;
7. all package/provenance/firewall checks pass.

If any gate fails, `GMN_V31_POSITIVE_SUPPORT_V1` fails and the exact mechanism is permanently closed.

## SonotaCo boundary

Only a GMN PASS may authorize a separately frozen one-shot SonotaCo 2013/2014 comparison against exact v31 and the literature comparators. SonotaCo remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation. A later SonotaCo outcome may not be used to modify this successor.

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
