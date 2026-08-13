# OrbitTrace GMN v31 Manhattan local geometry v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 successor to the passed `orbittrace_gmn_v31_principle_local_geometry_oof_v1` parent. It tests exactly one mechanism:

> Preserve the successful v31 strict-OOF nearest-positive / nearest-nonpositive local-reference construction, but replace ordinary Euclidean (`L2`) distance in the already-standardized 23D parent representation by fixed Manhattan (`L1`) distance.

Everything else remains unchanged: candidate universe, 23D representation, fold-training z-standardization, positive/nonpositive reference semantics, strict whole-shower folds, `k=1`, diversity, immutable hard order, equal rank-sum fusion, truth semantics, and evaluator.

This protocol is frozen before the first technically valid outcome. SonotaCo 2013/2014 is not accessed to evaluate, tune, or select this successor. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.

## Independent motivation fixed before outcome

The exact v31 GMN parent demonstrates that simple local nearest-reference geometry carries useful target-excluded signal in the frozen 23D family representation. The older balanced-Fisher lineage showed that stronger global supervised separation can improve GMN while transferring poorly to exposed SonotaCo, so this successor deliberately does **not** fit a global supervised metric, covariance, projection, or feature weight.

After fold-training z-standardization, Euclidean distance aggregates squared coordinate deviations. A held-out family that differs strongly from a reference on one coordinate can therefore have its neighbor identity dominated by that coordinate. Under cross-survey measurement/domain differences, that is a plausible failure mode even when the remaining intrinsic coordinates agree. Manhattan distance instead sums absolute standardized coordinate deviations. It remains simple, local, axis-symmetric, deterministic, and parameter-free, while reducing the relative leverage of one large coordinate discrepancy compared with `L2`.

This is motivated independently of the GMN outcome by the classic analysis of `L_k` proximity behavior in high-dimensional data:

- Aggarwal, C. C., Hinneburg, A., & Keim, D. A. (2001), *On the Surprising Behavior of Distance Metrics in High Dimensional Space*, ICDT 2001, LNCS 1973, 420–434, DOI `10.1007/3-540-44503-X_27`.

The successor does **not** search over `p`. `L1` is fixed here before outcome. Fractional norms, `L_infinity`, mixed norms, feature weighting, robust scaling, and learned metrics are not authorized.

## Relation to closed v31 lanes

This mechanism is distinct from the already-closed successors:

- shrinkage Mahalanobis: learned a training-fold covariance precision matrix and retained a quadratic `L2` form; this successor learns no matrix or weights and changes only the norm from `L2` to `L1`;
- relative-margin / class-conditional calibration / Mutual Proximity: transformed or normalized pairwise distance evidence; this successor uses raw `L1` distances without calibration;
- Tomek negative editing: changed the reference set; this successor deletes or reweights no reference;
- nearest-feature-segment: changed point prototypes into segments; this successor retains exact point prototypes;
- positive-support / one-class: removed the negative-class contrast; this successor retains both classes;
- LFDA / balanced Fisher / other metric-learning directions: supervised/global fitted transformations; this successor fits none;
- exact 1-NPC robustness: changed the score to exact decision-boundary perturbation radius and ended as a technical no-go; this successor remains the ordinary nearest-class distance gap.

No closed result supplies a threshold, weight, feature choice, or parameter to this successor.

## Authoritative deterministic GMN package

Use only the verified target-excluded GMN v31 offline package:

- package workflow run `31663453082`;
- artifact `9167087908`;
- artifact digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`;
- package manifest SHA-256 `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- exact 226x23 feature matrix SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- exact 226x8 centroid matrix SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent prelabel SHA-256 `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`;
- parent raw Euclidean OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

The package contains no raw GMN event rows, raw event IDs, raw hidden-label event mapping, SonotaCo data, target-region data, MAARSY, or DMS.

Before successor interpretation the evaluator must reproduce the immutable hard-order control:

- recovered@25 = 21;
- recovered@50 = 38;
- recovered@100 = 59;
- top-100 dominant precision = 0.6884631112636006;
- MRR = 0.046734076055452344;
- qualified matches = 95.

It must also reproduce the exact v31 fused control:

- recovered@25 = 23;
- recovered@50 = 41;
- recovered@100 = 66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified matches = 95.

Any package, hash, shape, fold, evaluator, truth, or firewall mismatch fails before successor evaluation.

## Immutable parent science

Everything below remains fixed:

- exact 226 P19 hard-family candidates and immutable hard order;
- exact 23D intrinsic family representation;
- exact deterministic five strict whole-shower folds;
- fold-training arithmetic mean / population-standard-deviation z-score, zero standard deviation mapped to 1.0;
- exact positive/nonpositive reference semantics;
- exactly one nearest positive and one nearest nonpositive training reference (`k=1`);
- exact 226x8 centroid matrix used only by inherited diversity;
- exact diversity `lambda=0.8`, `scale=1.0`;
- exact equal 1-based rank-sum fusion with immutable hard order;
- exact monotone evaluator over 355 eligible labels.

No candidate, membership, truth, fold, feature, scaling, reference, diversity, fusion, or evaluator change is allowed.

## Sole scientific change: fixed Manhattan nearest-reference margin

For each exact outer OOF fold independently, after fitting the parent z-score on the fold-training rows and applying it to training and held-out rows, let `P` be the positive training references and `N` the nonpositive training references.

For held-out standardized query `z`, define raw Manhattan distance

`d_1(z, r) = sum_j |z_j - r_j|`.

Compute

`d_positive_L1(z) = min_{p in P} d_1(z,p)`

`d_nonpositive_L1(z) = min_{n in N} d_1(z,n)`.

The raw successor local margin is

`m_L1(z) = d_nonpositive_L1(z) - d_positive_L1(z)`.

Higher is better, exactly preserving the parent sign semantics. Nearest-reference ties are resolved only by immutable hard-family rank and then family ID; no label-favorable tolerance or jitter is used.

For provenance, the same execution also recomputes the exact parent Euclidean margin

`m_L2(z) = min_n ||z-n||_2 - min_p ||z-p||_2`

and requires its complete 226-vector SHA-256 to equal the frozen parent margin hash before interpreting `m_L1`.

## Frozen metric-unit preservation

The inherited diversity routine subtracts a fixed proximity penalty directly from the local score. Changing from `L2` to `L1` changes score units and could therefore alter the *effective* diversity strength even if the scientific question were only the local norm.

To isolate the norm while preserving the already-frozen diversity strength, use the same preregistered unit-preservation principle previously used in the shrinkage-Mahalanobis lane:

- `S_L2 = median(abs(m_L2))`;
- `S_L1 = median(abs(m_L1))`;
- require both finite and strictly positive;
- `unit_factor = S_L2 / S_L1`;
- sole successor score entering diversity: `m_L1_scaled = m_L1 * unit_factor`.

This is positive scalar multiplication only. It cannot change the raw L1 score sign or pre-diversity ordering. It is fixed before outcome and is used only to keep diversity units comparable to v31.

No alternative scale statistic, clipping, centering, calibration, interpolation, or fitted transform is allowed.

## Post-score machinery

After all 226 strict-OOF `m_L1_scaled` values are computed:

1. apply exact inherited diversity with `lambda=0.8`, `scale=1.0` and the exact centroid matrix;
2. produce exactly one candidate by equal 1-based rank-sum fusion of the diversified L1 order with the immutable P19 hard order;
3. evaluate with the exact parent monotone evaluator.

No local-only result can rescue failure of the fused promotion candidate.

## Explicit no-search rules

There is:

- `p=1` only;
- no `p` search or fractional norm;
- no `L1/L2` blend;
- no weighted Manhattan distance;
- no feature subset or block norm;
- no robust/median/MAD rescaling;
- no learned metric or covariance;
- no k search (`k=1` only);
- no reference editing, deletion, relabeling, pruning, weighting, or prototype construction;
- no local density or distance calibration;
- no threshold, clipping, exponent, temperature, or confidence transform;
- no diversity or fusion search;
- no source/year/budget-specific rule;
- no post-result second search.

If the first technically valid result fails, no fractional-p, `L_infinity`, weighted-L1, L1/L2 blend, alternate unit normalization, robust scaling, feature weighting, k-neighbor, or result-informed metric rescue is authorized from this outcome.

## Frozen GMN promotion gate

The first technically valid result is binding. PASS requires every condition against exact v31:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 dominant precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified matches **= 95**;
7. exact package/evaluator/parent-margin/fold/firewall assertions pass.

Failure of any gate permanently rejects this exact Manhattan successor.

## SonotaCo boundary

Only a GMN PASS may authorize a separately frozen one-shot SonotaCo 2013/2014 comparison against exact v31 and the literature comparators. SonotaCo remains `EXPOSED_DEVELOPMENT_ONLY`, never external validation. No SonotaCo outcome may modify this method.

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
