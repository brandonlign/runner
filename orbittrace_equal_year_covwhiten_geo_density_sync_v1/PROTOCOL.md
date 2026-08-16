# OrbitTrace equal-year covariance-whitened GEO density-sync v1 — frozen protocol

## Scientific goal
Test one survey-adaptive event-geometry change aimed at the failure mode seen in pooled component-wise Z-score GEO: unequal survey/year sampling and correlated GEO6 axes.

The prior Z-score endpoint is permanently failed at 178 recovered@100 versus the 179 binding winner. This successor is separately named and changes the geometry in a materially different way: use the full 6×6 unlabeled covariance structure with 2022 and 2023 contributing exactly 50/50, then whiten GEO6 before the otherwise unchanged density-synchronous recurrent-EOM detector.

This is not a reranker, member veto, background-weight feature, graph method, uncertainty proxy, supervised metric, or HDBSCAN parameter search.

## Binding baseline
Compare only with the frozen density-synchronous recurrent-EOM GMN winner:
- run `31852836840`
- artifact `9238142199`
- 2022 recovered@100 = 89
- 2023 recovered@100 = 90
- total recovered@100 = 179
- ordered-membership SHA256 `e8f374ad03e7072463118ee6440a54d96d11e3aab17202cfe336f866530224f2`

The baseline is read from its frozen artifact and is not recomputed.

## Data and firewall
- GMN 2022+2023 development only.
- Solar longitude 20°–55° excluded before every normalization or clustering operation.
- OrbitTrace target information and protected-region events forbidden.
- No known-shower label value may be indexed until the complete whitened hierarchy, selected nodes, memberships, order, and transform are persisted.
- SonotaCo 2013/2014, ASFN, EFN, AMOS, MAARSY, and DMS are not accessed in this GMN endpoint.

## Frozen input representation
Start from exact inherited GEO6:

`[cos(sol), sin(sol), sin(lon)*cos(lat), cos(lon)*cos(lat), sin(lat), vg/72]`.

No orbital element, seasonal-background score, quality flag, uncertainty field, or learned feature is added.

## Equal-year covariance whitening
For each year `y` separately, over all accessible target-excluded events:

- `mu_y = mean(X_y)`
- `C_y = mean((X_y-mu_y)(X_y-mu_y)^T)` using population covariance (`ddof=0`).

Define the shared equal-year covariance

`C = 0.5*C_2022 + 0.5*C_2023`.

Define the shared centering vector

`mu = 0.5*mu_2022 + 0.5*mu_2023`.

Compute the symmetric eigendecomposition `C = Q diag(lambda) Q^T`. All six eigenvalues must be finite and strictly positive; otherwise the run is a technical no-result. No shrinkage, ridge, clipping, eigenvalue floor, component deletion, or tuning is allowed.

Define the unique symmetric whitening matrix

`W = Q diag(lambda^-1/2) Q^T`

and transform every event by

`Z = (X-mu) W`.

Because HDBSCAN uses Euclidean distance, this is exactly a shared Mahalanobis metric induced by the equal-year covariance. The 50/50 year weighting is fixed independent of the unequal event counts (315,024 vs 423,658).

As a numerical audit, the 50/50 average of the two within-year population covariances after whitening must be identity to floating-point tolerance.

## Transfer rule fixed now
For a later two-year survey benchmark, recompute the same unlabeled transform on that survey's accessible two-year analysis corpus with each year weighted exactly 50/50. GMN numerical covariance values are never transferred to another survey. No labels may enter the transform.

## Detector architecture held fixed
After whitening, use exact `hdbscan==0.8.43` settings:
- `min_cluster_size=10`
- `min_samples=10`
- Euclidean metric
- EOM cluster selection
- `cluster_selection_epsilon=0`
- `allow_single_cluster=False`
- `prediction_data=False`

Then apply the exact existing density-synchronous recurrent-EOM stability, EOM node selection, candidate extraction, and ranking. The sole scientific change is `GEO6 -> equal-year covariance-whitened GEO6` before HDBSCAN.

## Pretruth freeze
Before truth access persist:
- exact input/source hashes and event counts;
- `mu_2022`, `mu_2023`, shared `mu`;
- `C_2022`, `C_2023`, shared `C`;
- six eigenvalues and full whitening matrix `W`;
- whitened equal-year covariance numerical audit;
- condensed-tree SHA256;
- selected density-synchronous nodes;
- full ordered candidate memberships and ordered-membership SHA256;
- candidate count and largest-family size;
- firewall state.

## Binding GMN success gate
PASS requires all:
1. total recovered@100 >= **184** (+5 over 179);
2. 2022 recovered@50 not lower and recovered@100 >= 89;
3. 2023 recovered@50 not lower and recovered@100 >= 90;
4. top-100 dominant precision not lower in either year;
5. MRR not lower in either year;
6. median top-500 fragmentation not higher in either year;
7. at least 100 candidate families and largest selected family <=1% of accessible events;
8. ordered memberships differ from the frozen winner;
9. all source, reproducibility, and firewall checks pass.

Anything else is FAIL. No post-result covariance blend, shrinkage, robust covariance, per-axis weighting, year-specific whitening, eigenvalue modification, HDBSCAN tuning, reranking, or rescue is authorized for v1.

## Goal/transfer rule
A GMN PASS is only a development win. It earns one separately frozen exposed-SonotaCo 2013/2014 transfer benchmark against the frozen literature comparators using the same survey-local equal-year whitening rule. Broad generalization still requires a genuinely untouched external survey.