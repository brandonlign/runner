# OrbitTrace GMN v31 Mutual-Proximity local-geometry OOF successor v1

## Scientific role

This is a **target-excluded GMN 2022/2023 method-development successor** to the passed v31-principle local-geometry OOF diagnostic. It is designed and frozen without SonotaCo 2013/2014 outcome access, OrbitTrace target information/events, MAARSY, DMS, or protected solar-longitude 20°–55° data. It does not alter candidate generation, memberships, labels, folds, diversity, fusion, or evaluation semantics.

The frozen parent is `agent/orbittrace-gmn-v31-principle-local-geometry-oof-v1` at commit `fd2bda7bc19de976e27d1fd08f0bd7aec358600c`, whose binding result passed with fused recovered@100 66, recovered@50 41, top-100 dominant precision 0.7229521515453452, MRR 0.050244164168646674, and 95 qualified families.

## Motivation frozen before outcome

The parent v31 mechanism depends entirely on strict-OOF nearest-positive versus nearest-nonpositive reference geometry in a 23-dimensional standardized representation. Nearest-neighbor geometry in moderate/high-dimensional spaces can suffer from **hubness**, where some reference points occur as nearest neighbors of many otherwise unrelated queries. Schnitzer, Flexer, Schedl, and Widmer (JMLR 2012, *Local and Global Scaling Reduce Hubs in Space*) proposed **Mutual Proximity (MP)** as an unsupervised transformation of an arbitrary distance space using the empirical distribution of distances. Their empirical definition evaluates how unusually close a pair is relative to the distances from both endpoints to the reference collection.

This successor tests one narrow hypothesis: **can empirical Mutual Proximity make the already-successful v31 nearest-reference margin more reliable by reducing hub-dominated nearest-neighbor relations, without changing any other part of the method?**

Repository provenance search before this freeze found no prior OrbitTrace implementation named or described as Mutual Proximity. This is distinct from the already-closed Euclidean relative-margin, covariance/Mahalanobis, member-scatter/covariance, density-contrast, Jaccard/overlap, thinning-persistence, MST-topology, and energy-distance lanes.

## Immutable candidate universe and representation

Inherit exactly from the frozen parent:

- the exact 226 P19 hard families in immutable hard order;
- the exact 23 label-free intrinsic hard-family dimensions and their order;
- exact memberships, centroids, truth semantics, and qualified-family definition;
- exact deterministic five-fold strict same-shower grouping;
- fold-training arithmetic mean and population standard deviation (`ddof=0`) for every feature, with exactly-zero standard deviations replaced by 1.0;
- training-only z-standardization of both training and held-out families.

No feature is added, dropped, selected, reweighted, transformed, or tuned.

## Sole scientific change: empirical Mutual Proximity distance

For each fold, after the exact parent z-standardization, let `R` be **all fold-training families**, regardless of positive/nonpositive class. Let ordinary Euclidean distance in the frozen 23D standardized space be `d(a,b)`.

For each held-out query family `x` and each training reference family `y in R`, compute the empirical Mutual Proximity similarity using only the fold-training reference population:

`MP(x,y) = |{j in R : d(x,j) > d(x,y) AND d(y,j) > d(x,y)}| / |R|`.

Define the transformed dissimilarity

`d_MP(x,y) = 1 - MP(x,y)`.

This is the sole scientific modification. The strict inequalities, inclusion of all training references in `R`, denominator `|R|`, ordinary Euclidean base distance, and empirical rather than parametric distribution are fixed here. The held-out query itself is not inserted into `R`; no other held-out family contributes to the transform. Labels play no role in construction of `d_MP`.

For each held-out family, use `d_MP` to identify the single nearest positive training reference and the single nearest nonpositive training reference. Define the successor local-geometry margin exactly analogously to the parent:

`margin_MP = d_MP_nonpositive - d_MP_positive`,

with larger values more recoverable-like.

There is no k search (`k=1` only), base-metric search, empirical/parametric choice, smoothing, pseudocount, tie jitter, neighborhood-size parameter, local-scaling variant, hubness threshold, class weighting, model fitting, or calibration.

Ties in transformed distance are resolved by the inherited stable training-reference order only; there is no label-favorable tie rule.

## Frozen post-score machinery

Keep the parent post-score machinery exactly:

1. apply geometric diversity `lambda=0.8`, `scale=1.0` to the OOF Mutual-Proximity margin with inherited immutable hard-rank/stable-ID tie semantics;
2. produce exactly one promotion candidate by equal rank-sum fusion of that diversified margin order with the immutable 226-family hard order.

No alternate diversity, rank product, score fusion, fusion weight, top-k rule, source quota, or sequential rescue is allowed.

## Binding development gate

The first technically valid execution is binding. The exact frozen parent is the benchmark, not the older hard baseline.

PASS requires the sole fused successor order simultaneously to:

- `recovered@100 > 66`;
- `recovered@50 >= 41`;
- `top100_dominant_precision >= 0.7229521515453452`;
- `MRR >= 0.050244164168646674`;
- qualified-family count remains exactly `95`.

For completeness, recovered@25 and recovered@500 must be reported but are not allowed to rescue failure of any binding gate. No post-outcome second search is permitted.

If any binding gate fails, this exact empirical-MP v1 is permanently rejected. No inequality change, denominator change, pseudocount, parametric Gaussian/Gamma MP, independence approximation, local scaling, k change, feature change, fold change, diversity change, fusion change, or hybrid with failed representation mechanisms is authorized as a rescue of this result.

A PASS authorizes only a **separately frozen** exposed-SonotaCo comparison of the exact successful successor against v31 and the literature comparators. It does not authorize MAARSY, DMS, protected-target access, or SonotaCo-informed tuning.

## Firewall

The implementation and workflow must affirm:

- scientific role is GMN 2022/2023 target-excluded method development only;
- protected solar longitude `[20.0,55.0]` was excluded before all truth/fold/score operations;
- `sonotaco_2013_2014_access = false`;
- `target_information_access = false`;
- `target_region_events_accessed = false`;
- `maarsy_scientific_access = false`;
- `dms_scientific_access = false`;
- no parameter search, feature search, model search, or post-result rescue occurred.
