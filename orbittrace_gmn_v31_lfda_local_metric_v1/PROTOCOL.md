# OrbitTrace GMN v31 LFDA local-metric v1 — frozen protocol

## Scientific role

This is a target-excluded GMN 2022+2023 successor to the passed `orbittrace_gmn_v31_principle_local_geometry_oof_v1` parent. It tests one mechanism only:

> Can the successful v31 nearest-positive versus nearest-nonpositive local margin be improved by replacing the parent isotropic Euclidean metric with **Local Fisher Discriminant Analysis (LFDA)** fitted strictly inside each OOF training fold, while preserving the full 23-dimensional representation and every downstream v31 operation?

This protocol is frozen before the first technically valid outcome. SonotaCo 2013/2014 is not accessed to evaluate, tune, or select the successor. Protected solar longitude 20°–55°, OrbitTrace target information/events, MAARSY, and DMS remain inaccessible.

## Independent scientific motivation fixed before outcome

Two completed results motivate this exact hybrid:

1. Exact v31 local Euclidean geometry is the strongest demonstrated SonotaCo method and passes target-excluded GMN, so locality is empirically important.
2. The frozen balanced-shrinkage Fisher OOF successor improves GMN from recovered@100 66 to 69, top-100 precision from 0.7229521515453452 to 0.7677499561973543, and MRR from 0.050244164168646674 to 0.050559897668695646, demonstrating that supervised class-separating geometry contains useful GMN signal. However, its frozen SonotaCo transfer collapses to only 1/4 literature-pair wins, so replacing local geometry by one global discriminant direction is not transfer-robust.

Masashi Sugiyama's LFDA was introduced specifically as a localized Fisher variant for multimodal labeled data. Its objective preserves **local within-class structure** while separating classes, rather than forcing all same-class samples toward one global mean. The 2007 JMLR paper defines a classwise local-scaling affinity and uses the 7th nearest same-class neighbor throughout the paper; it then solves a generalized eigenproblem and recommends weighting generalized eigenvectors by the square root of their eigenvalues to determine a distance geometry in the embedding.

This successor therefore combines the two independently supported principles without using SonotaCo residual identities or result-informed tuning: retain v31's local nearest-reference decision rule, but learn the fold-training metric with LFDA rather than global Fisher.

References:
- Sugiyama, M. (2007), *Dimensionality Reduction of Multimodal Labeled Data by Local Fisher Discriminant Analysis*, JMLR 8:1027–1061.
- Exact algorithm follows the paper's classwise local scaling (`K=7`), local scatter definitions, generalized eigenproblem, and square-root eigenvalue weighting.

## Authoritative deterministic GMN package

Use only authoritative target-excluded GMN v31 development package:

- run `31663453082`;
- artifact `9167087908`;
- artifact digest `sha256:e8b019d84002e182d31399eb96cccbd96d47c3e4411ba7053b93ee2954f259e6`;
- manifest SHA-256 `16fb5ef3cd8dbbb3873e9bc23874fe7da3db68498772a5e992fbceed6cb980d7`;
- exact 226x23 feature matrix SHA-256 `fea3b063772c75b675e37a227b53a4aa3c5b86fdcbfcef1487b1e1448689cdf5`;
- exact 226x8 centroid matrix SHA-256 `a53b9862f1ec3d751745f80aec2625d7904128474c9263c55ea953cf60d0621f`;
- parent prelabel SHA-256 `b45c4ce1a45bff515e411e211bc51dee879229ee97f7fcb7d8e7e05bfc106d09`;
- parent raw OOF margin SHA-256 `f38c96e3fa4ea98f51217b36d639e96edbf3ebcb65123248f0f118d3298173bd`.

The package contains no raw GMN event rows, raw event IDs, or raw hidden-label event mapping. Before successor science, the offline evaluator must reproduce the exact hard-order control:

- recovered@25 = 21;
- recovered@50 = 38;
- recovered@100 = 59;
- top-100 dominant precision = 0.6884631112636006;
- MRR = 0.046734076055452344;
- qualified matches = 95.

The manifest must also reproduce the exact v31 fused control:

- recovered@25 = 23;
- recovered@50 = 41;
- recovered@100 = 66;
- top-100 dominant precision = 0.7229521515453452;
- MRR = 0.050244164168646674;
- qualified matches = 95.

Any mismatch fails before successor evaluation.

## Immutable v31 parent science

Everything below remains exactly fixed:

- 226 P19 hard-family candidates;
- exact 23D intrinsic representation;
- exact strict whole-shower groups and deterministic five folds;
- fold-training arithmetic mean / population-standard-deviation z-score, zero standard deviation replaced by 1.0;
- exact frozen positive/nonpositive family truth semantics;
- nearest positive and nearest nonpositive reference count `k=1`;
- local margin orientation `d_nonpositive - d_positive`;
- exact 226x8 centroid matrix;
- exact diversity `lambda=0.8`, `scale=1.0`;
- exact equal rank-sum fusion with immutable P19 hard order;
- exact monotone evaluator over 355 eligible labels.

No candidate, membership, truth, fold, feature, diversity, fusion, or evaluation rule changes.

## Sole successor change: fold-training LFDA metric

For each outer OOF fold independently:

1. Fit the exact parent z-score on **all outer-training rows** and transform outer-training and outer-test rows.
2. Assign binary class labels from the exact frozen v31 family truth (`positive` vs `nonpositive`).
3. Compute LFDA only on the standardized outer-training rows.

### Classwise affinity — exact paper heuristic

For each class `c` separately and each training row `i` in that class:

- require at least 8 training rows in the class;
- compute Euclidean distances from `i` to the other rows in the **same class**;
- let `sigma_i` be the distance to the **7th nearest other same-class row**;
- require `sigma_i > 0` and finite.

For same-class rows `i,j`, define

`A_ij = exp(-||z_i-z_j||^2 / (sigma_i sigma_j))`.

Set `A_ii = 1`. Different-class affinities are not needed by LFDA's local scatter weights.

No K search is allowed. `K=7` is the fixed local-scaling heuristic used throughout Sugiyama's LFDA paper.

### Exact local scatter matrices

Let `n` be outer-training count and `n_c` the training count of class `c`.

For every ordered pair `(i,j)` of training rows, define:

- if `y_i = y_j = c`:
  - `Ww_ij = A_ij / n_c`
  - `Wb_ij = A_ij * (1/n - 1/n_c)`
- if `y_i != y_j`:
  - `Ww_ij = 0`
  - `Wb_ij = 1/n`.

Then compute the paper's pairwise scatter matrices:

`Sw = 0.5 * sum_ij Ww_ij (z_i-z_j)(z_i-z_j)^T`

`Sb = 0.5 * sum_ij Wb_ij (z_i-z_j)(z_i-z_j)^T`.

Symmetrize both numerically as `(S + S.T)/2` and require all entries finite.

### Full-dimensional LFDA transform — no dimension tuning

Use the generalized symmetric eigenproblem

`Sb phi = lambda Sw phi`.

No ridge, covariance shrinkage, pseudoinverse, or regularization is allowed. `Sw` must be positive definite enough for the generalized symmetric eigensolver; otherwise the method fails closed as technically invalid rather than introducing a rescue parameter.

Use **all 23 generalized eigenvectors** (`r=23`, equal to input dimension), sorted by descending eigenvalue. Thus this experiment performs no dimensionality search or feature deletion. Require all generalized eigenvalues finite and strictly positive; otherwise fail closed.

Use the paper's recommended metric-resolving weighting:

`T = [sqrt(lambda_1) phi_1 | ... | sqrt(lambda_23) phi_23]`,

where generalized eigenvectors are normalized in the `Sw` metric by the eigensolver.

Transform standardized training and test rows as

`u = z T`.

### Exact v31 local decision after LFDA

For every held-out test family `x`:

- `d_positive = min ||u_x-u_p||` over positive outer-training references;
- `d_nonpositive = min ||u_x-u_n||` over nonpositive outer-training references;
- `lfda_margin = d_nonpositive - d_positive`.

Higher is better. Then apply exact v31 diversity and exact equal hard-order rank fusion unchanged.

## Explicit no-search rules

There is:

- local-scaling `K=7` only;
- full dimension `r=23` only;
- exact square-root eigenvalue weighting only;
- no eigenvalue cutoff;
- no ridge/regularization/shrinkage/pseudoinverse;
- no kernel LFDA;
- no SELF/semi-supervised variant;
- no alternative affinity, global affinity, sparsification, or affinity threshold;
- no class balancing modification beyond LFDA's published weights;
- no metric blend with Euclidean or Fisher;
- no k search for v31 nearest references (`k=1` only);
- no feature/scaling/fold/reference/diversity/fusion search;
- no source/year/budget-specific rule;
- no post-result second search.

A valid FAIL closes this exact LFDA local-metric mechanism. No alternate K, output dimension, eigenvalue weighting, regularization, kernel, affinity, Euclidean/LFDA blend, or result-informed rescue is authorized.

## Frozen GMN promotion gate

PASS requires every condition against exact v31 GMN parent:

1. recovered@100 **> 66**;
2. recovered@50 **>= 41**;
3. recovered@25 **>= 23**;
4. top-100 dominant precision **>= 0.7229521515453452**;
5. MRR **>= 0.050244164168646674**;
6. qualified matches **= 95**;
7. every package, evaluator, fold, LFDA, and firewall assertion passes.

The first technically valid outcome is binding.

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
