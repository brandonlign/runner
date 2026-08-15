# OrbitTrace density-sync global-whitened GEO6 v1 — frozen protocol

## Purpose

Test one genuinely different geometry-level successor to density-synchronous recurrent-EOM v1 (#1263). This protocol is frozen before implementation and before any scientific outcome.

Three separately frozen post-selection recurrence rerankers have now failed (wavelet recurrence, annual geometry shift, and exposure-corrected annual rate balance). This successor therefore changes no final-family reranking rule. Instead it asks whether the plain Euclidean GEO6 metric feeding HDBSCAN is unnecessarily survey-specific because the six coordinates have unequal empirical variance and correlation.

## Exact parent and comparator

Comparator: density-synchronous recurrent-EOM HDBSCAN v1, PR #1263, binding head `182f07ade6bb5d4be2c80b88df9216bb2d6eee2d`.

Binding GMN run `31852836840`, artifact `9238142199`.

- prelabel SHA-256: `efce0617a738a0372ec5b007fb87b46912accd8419f0f768829c4c0cb7d62993`
- result SHA-256: `ca6aeed2b82739003ea5d39b59e869df876de2962164344a938fe4935ea38711`
- candidate count: `2,094`
- total recovered@100: `179` (`89 + 90`).

Exact density-synchronous kernel blob: `587a304f451e41b9503272f1783a6c6ebb295000`.
Exact recurrent-EOM kernel blob: `30ac3fa3bc47910370df528fcf3ae8ecb6277b47`.
Exact parent development runner blob: `fdc4f3f6e037014aadfcc3ce41b7344aa0a80b2c`.

## Sole scientific change: pooled global whitening

Use the exact inherited target-excluded GEO6 representation for every accessible 2022+2023 event:

`x = [cos(sol), sin(sol), sin(lon)cos(lat), cos(lon)cos(lat), sin(lat), vg/72]`.

Before fitting HDBSCAN, compute from all pooled accessible target-excluded 2022+2023 GEO6 rows, without labels:

1. pooled mean vector `mu`;
2. unbiased sample covariance `Sigma = cov(X, rowvar=False, ddof=1)`;
3. symmetric eigendecomposition `Sigma = Q diag(lambda) Q^T` using `numpy.linalg.eigh`;
4. require every eigenvalue to be finite and strictly positive; otherwise fail closed with no scientific result;
5. define exact symmetric whitening matrix `W = Q diag(lambda^-1/2) Q^T`;
6. transform every row by `Z = (X-mu) W`.

No ridge, shrinkage, clipping, eigenvalue floor, PCA truncation, robust-covariance choice, per-axis weight, learned metric, target label, shower label, or tunable hyperparameter is permitted.

Fit the exact same HDBSCAN configuration as #1263 on `Z`:

- `min_cluster_size=10`;
- `min_samples=10`;
- Euclidean metric;
- EOM;
- epsilon `0`;
- no single cluster.

On that whitened hierarchy, compute the exact frozen density-synchronous recurrent-EOM objective using exact year identities and the same annual normalization. Candidate ranking remains exactly:

1. synchronous stability;
2. ordinary stability;
3. member count;
4. stable family ID.

No post-selection reranking is added.

## Why this is a generalization test

Whitening is label-free and parameter-free and removes the pooled second-moment scale/correlation structure of each survey before density clustering. If the original fixed GEO6 metric embeds network-specific anisotropy, this can improve portability without knowing which families are showers.

For any later external survey, the same frozen rule would recompute `mu` and `Sigma` from that survey's complete retained target-excluded sample before clustering. No GMN covariance matrix would be transported to another survey.

## Scientific firewall

Development uses only target-excluded GMN 2022+2023 through the exact frozen parser/runtime used by #1263. The inclusive solar-longitude interval `[20.0,55.0]` remains removed before whitening, HDBSCAN, candidate generation, or truth handling.

Before known-shower truth or #1263 truth-derived metrics are opened, persist and hash-freeze:

- pooled `mu`, covariance, eigenvalues, whitening matrix;
- whitened covariance diagnostic;
- complete condensed-tree hash;
- complete selected-node set;
- complete candidate membership/order.

The following remain inaccessible during GMN development:

- OrbitTrace target information/events;
- SonotaCo 2013/2014;
- AMOS;
- MAARSY;
- DMS.

The first technically valid scientific outcome is binding.

## Strong GMN promotion gate

PASS requires all of:

1. whitening transform is non-identity and finite;
2. whitened covariance is identity to numerical tolerance `1e-10` maximum absolute element error;
3. successor mechanism is active relative to #1263 (candidate membership/order differs);
4. in each year separately, no regression versus #1263 on:
   - recovered@50;
   - recovered@100;
   - top-100 dominant precision;
   - MRR;
   - median top-500 fragmentation;
5. total recovered@100 improves by at least `+2`, from `179` to at least `181`.

A one-family gain is insufficient.

## Pre-frozen SonotaCo contingency

Only if the first technically valid GMN outcome passes may this exact unchanged whitening rule be evaluated on the already-exposed SonotaCo 2013/2014 development-validation benchmark. SonotaCo remains non-pristine.

For each SonotaCo panel universe, whitening must be recomputed label-free from that panel's complete retained geometry using the exact formula above before clustering. No GMN covariance is reused.

Promotion requires no macro-F1 or recovered-count regression on any of the four established Sugar/HDBSCAN panels, strict macro-F1 improvement on at least two panels, and continued superiority over the corresponding frozen literature comparator on all four panels.

Even a SonotaCo PASS is not pristine external validation. A separately frozen robustness diagnostic and a truly untouched external survey are still required before a broad generalization claim.

## Permanent no-rescue rule

After the first technically valid GMN outcome, do not change covariance estimator, centering, eigenvalue handling, regularization, shrinkage, PCA dimension, transform orientation, HDBSCAN parameters, density-synchronous objective, ranking, gate, metric definitions, or target exclusion. Failure permanently closes this exact version.