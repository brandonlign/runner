# OrbitTrace GMN v31 empirical class energy score v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 architectural successor to the exact v31 local-geometry parent.

Two frozen GMN-only diagnostics establish the mechanism problem that motivates this successor without using SonotaCo:

1. at top 100, 21 of the 29 qualified labels missed by fused v31 are outside the same budget in both frozen hard and diversified-local constituents;
2. for all 21 of those constituent-absent labels, every positive family representative has raw v31 nearest-reference margin `d_nonpositive - d_positive <= 0`.

Thus the dominant unresolved v31 failure is not rank fusion or calibration of an already-correct local margin. The hard misses are genuinely placed on the nonpositive side of the parent one-prototype boundary.

This successor asks exactly one architectural question:

> Can a held-out family be scored by compatibility with the **entire empirical positive and nonpositive training distributions**, rather than requiring an individually nearest positive prototype, while preserving the exact parent representation, strict OOF structure, Euclidean geometry, diversity and hard-order fusion?

The sole new score is the parameter-free empirical multivariate **energy score** of the query under each class distribution. No covariance, projection, bandwidth, feature weight, fitted classifier, class prior, kernel or hyperparameter is introduced.

This protocol is frozen before the first technically valid scientific outcome. SonotaCo 2013/2014 is not accessed to design, select or tune it.

## Independent methodological basis fixed before outcome

Gneiting & Raftery (2007), *Strictly Proper Scoring Rules, Prediction, and Estimation*, Journal of the American Statistical Association 102(477), 359–378, DOI `10.1198/016214506000001437`, define the multivariate energy score. For Euclidean exponent 1, in loss orientation it is

`ES(F,z) = E_F ||X-z||_2 - 0.5 E_F ||X-X'||_2`,

where `X` and `X'` are independent draws from distribution `F`. Lower energy score means greater compatibility of observation `z` with `F`. The second term prevents a diffuse distribution from being judged only by its mean distance to the query; it explicitly accounts for the distribution's own internal dispersion.

Here each frozen class's fold-training empirical distribution is used directly as `F`. This is a nonparametric set-distribution score. It learns no discriminant direction and fits no covariance or density bandwidth.

The OrbitTrace-specific hypothesis is fixed from the GMN diagnostics above: because the remaining top-100 failures have no individually closer positive prototype, a distribution-level score may recognize positive-class compatibility that one-prototype support misses. This is a genuine class-support architecture change, not a scalar transform of `d_pos/d_neg`.

## Relation to already-closed lanes

This successor is distinct from the closed mechanisms:

- **v31 nearest-reference / relative-margin / calibration / Mutual Proximity**: those begin from one or a few query-reference distances; this score averages query distance over the complete class distribution and subtracts the class's complete internal pairwise dispersion;
- **positive-support / one-class**: that lane removed the negative contrast; this method symmetrically compares positive and nonpositive empirical distributions;
- **second-support radius**: changes query-directed neighbour order to k=2; this method has no k or neighbour selection;
- **reverse-1NN slack**: modifies support by per-reference local radii; this method uses no reference radii or density adjustment;
- **Tomek / reference reliability**: no training reference is deleted, relabeled, pruned or weighted;
- **group prototypes / feature segments**: no centroid, segment, simplex, hull or synthetic prototype is constructed;
- **shrinkage Mahalanobis / LFDA / balanced Fisher**: no supervised feature transform, covariance precision matrix or discriminant direction is learned. Balanced Fisher's poor SonotaCo transfer remains a warning against global fitted separation; this method deliberately retains the exact parent standardized Euclidean coordinates and uses only the canonical proper set score;
- **cross-year energy-distance representation**: that separate #1194 experiment computed one label-free event-distribution consistency feature inside each family and appended it to a 34D ExtraTrees representation. This successor adds no representation feature and instead scores the two **training family class distributions** in the exact v31 23D OOF geometry;
- **exact 1-NPC robustness**: no decision-boundary QP or robustness approximation is used.

No result from a closed lane supplies a parameter to this method.

## Authoritative deterministic GMN package

Use only the verified target-excluded v31 offline package:

- workflow run `31663453082`;
- artifact `9167087908`;
- artifact digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`;
- manifest SHA-256 `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- exact 226x23 feature matrix SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- exact 226x8 centroid matrix SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent prelabel SHA-256 `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`;
- parent raw OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

The package contains no raw GMN event rows, event IDs, hidden event-label mapping, SonotaCo, protected target-region, MAARSY or DMS data.

Before successor interpretation require exact hard and v31 controls:

Hard:
- @25 = 21;
- @50 = 38;
- @100 = 59;
- top-100 dominant precision = `0.6884631112636006`;
- MRR = `0.046734076055452344`;
- qualified = 95.

Exact v31 fused:
- @25 = 23;
- @50 = 41;
- @100 = 66;
- top-100 dominant precision = `0.7229521515453452`;
- MRR = `0.050244164168646674`;
- qualified = 95.

Any package, hash, fold, evaluator, truth or firewall mismatch is a technical no-result before successor interpretation.

## Immutable parent science

Keep fixed:

- exact 226 P19 hard-family candidates and memberships;
- immutable hard order;
- exact 23D family representation and column order;
- target-excluded GMN 2022+2023 development universe;
- exact deterministic five strict whole-shower OOF folds;
- fold-training arithmetic mean / population-standard-deviation z-score, with zero standard deviation mapped to 1.0;
- exact positive/nonpositive recoverability truth semantics;
- ordinary Euclidean distance in standardized 23D;
- exact 226x8 centroid matrix used only by inherited diversity;
- diversity `lambda=0.8`, `scale=1.0`;
- equal 1-based rank-sum fusion with immutable hard order;
- exact monotone evaluator over 355 eligible labels.

No candidate, membership, fold, truth, feature, scaling, metric, diversity, fusion or evaluator change is allowed.

## Sole scientific change: empirical class energy score

For each exact outer OOF fold independently:

1. fit the exact parent z-score on fold-training rows only and transform training and held-out rows;
2. split fold-training standardized rows into the exact frozen positive set `P={p_1,...,p_m}` and nonpositive set `N={n_1,...,n_l}`;
3. require `m>=1` and `l>=1`;
4. compute the fixed empirical class self-dispersion terms using the deterministic **V-statistic**, i.e. all ordered pairs including diagonal self-pairs:

   `D_P = (1/m^2) sum_i sum_j ||p_i-p_j||_2`

   `D_N = (1/l^2) sum_i sum_j ||n_i-n_j||_2`.

For held-out standardized query `z`, compute

`ES_P(z) = (1/m) sum_i ||p_i-z||_2 - 0.5 D_P`

`ES_N(z) = (1/l) sum_i ||n_i-z||_2 - 0.5 D_N`.

Lower score means greater compatibility with that empirical class distribution. Define the sole raw successor score

`m_energy(z) = ES_N(z) - ES_P(z)`.

Higher is more positive/recoverable-like.

Exponent is fixed at ordinary Euclidean distance power **1**. There is no exponent search, squared-distance version, class prior, sample-size correction, leave-one-pair correction, U-statistic, bias correction or bandwidth.

In the same execution, recompute the exact ordinary v31 parent OOF nearest-reference margin and require its complete SHA-256 to equal the frozen parent margin before interpreting `m_energy`.

## Frozen score-unit preservation

Inherited diversity subtracts a fixed additive proximity penalty from the local score. The energy score has different numerical units from the nearest-reference gap despite using the same Euclidean metric.

Fix before outcome:

- `S_parent = median(abs(m_parent))`;
- `S_energy = median(abs(m_energy))`;
- require both finite and strictly positive;
- `unit_factor = S_parent / S_energy`;
- sole score entering inherited diversity: `m_energy_scaled = m_energy * unit_factor`.

If `S_energy` is zero or nonfinite, the method is a technical no-go. No alternate scale statistic, epsilon, nonzero-only median, centering, calibration or diversity removal is allowed.

Positive scalar multiplication cannot change the pre-diversity energy-score ordering or sign.

## Frozen post-score machinery

After all 226 strict-OOF scores are computed:

1. apply exact inherited diversity with `lambda=0.8`, `scale=1.0` and exact parent centroids;
2. build exactly one promotion candidate by equal 1-based rank-sum fusion of the diversified energy-score order with immutable P19 hard order;
3. evaluate exactly once with the parent monotone evaluator.

The diversified energy local-only order is diagnostic only and cannot rescue failure of the fused candidate.

## Fixed diagnostics recorded without tuning

Record for provenance only:

- per fold positive/nonpositive training counts;
- `D_P` and `D_N`;
- per held-out family `ES_P`, `ES_N`, raw energy margin and parent margin;
- counts of held-out families with positive/zero/negative energy margin;
- raw/scaled score hashes and fixed unit factor.

No diagnostic creates a second candidate.

## Explicit no-search / no-rescue rules

There is:

- Euclidean exponent 1 only;
- V-statistic including diagonal pairs only;
- no powered-distance search;
- no squared-distance or fractional-distance variant;
- no U-statistic/bias-corrected variant;
- no class prior or class-size weighting;
- no MMD/kernel/bandwidth method;
- no Wasserstein/optimal transport;
- no energy-score threshold or calibration;
- no local/global blend with v31 margin;
- no nearest-neighbour/energy blend;
- no class subset, archetype, cluster or mixture decomposition;
- no reference weighting/deletion/relabeling;
- no feature, metric, scaling or covariance change;
- no diversity or fusion search;
- no source/year/budget-specific rule;
- no post-result second class-energy variant.

If the first technically valid result fails, alternate exponents, MMD kernels, class priors, U-statistics, subset/mixture energy scores, local-energy blends or other result-informed set-score rescues are forbidden from this outcome.

## Frozen GMN promotion gate

The first technically valid result is binding. PASS requires every condition against exact v31:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 dominant precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified matches **= 95**;
7. exact package/evaluator/parent-margin/fold/firewall assertions pass.

Failure of any gate permanently rejects this exact empirical class-energy successor.

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
